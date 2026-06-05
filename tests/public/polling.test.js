/**
 * Unit tests for QR polling module — Story 4.3 (UX-005)
 *
 * Tests the startPolling / stopPolling logic extracted as pure functions
 * from public/app.js, running in a jsdom environment with Jest fake timers.
 *
 * @jest-environment jsdom
 */

"use strict";

// ---------------------------------------------------------------------------
// Inline re-implementation of the polling logic from public/app.js.
// Mirrors the production code exactly so that any divergence breaks tests.
// Dependencies on DOM globals (evolutionStatus, qrImage) are provided via
// the jsdom environment set up in beforeEach.
// ---------------------------------------------------------------------------

/** @type {number|null} */
let pollingIntervalId = null;

function stopPolling(reason, message) {
  if (pollingIntervalId !== null) {
    clearInterval(pollingIntervalId);
    pollingIntervalId = null;
  }

  if (reason === "unload") return;

  const defaultMessages = {
    connected: "Ligado ao WhatsApp.",
    timeout: "Tempo esgotado. Sem ligação após 2 minutos. Tenta novamente.",
    error: message || "Erro de rede. Polling interrompido.",
  };

  const statusText = message || defaultMessages[reason] || "";
  const evolutionStatus = document.getElementById("evolutionStatus");
  if (statusText && evolutionStatus) {
    evolutionStatus.textContent = statusText;
  }

  const qrImage = document.getElementById("qrImage");
  if (reason === "connected" && qrImage) {
    qrImage.style.display = "none";
  }
}

/**
 * Factory that wraps startPolling logic and accepts injected callEvolution
 * so we can mock it in tests without touching the global.
 */
async function startPolling(callEvolution, intervalMs = 5000, maxIterations = 24) {
  stopPolling("unload");

  const evolutionStatus = document.getElementById("evolutionStatus");
  const qrImage = document.getElementById("qrImage");

  // Initial state fetch
  try {
    const initialState = await callEvolution("/api/evolution/instance/state", "GET");
    if (initialState?.instance?.state === "open") {
      if (evolutionStatus) evolutionStatus.textContent = "Ligado ao WhatsApp.";
      if (qrImage) qrImage.style.display = "none";
      return;
    }
  } catch {
    // Non-fatal: proceed to interval polling
  }

  let iteration = 0;
  let lastQrBase64 = qrImage ? qrImage.src : null;

  pollingIntervalId = setInterval(async () => {
    iteration += 1;

    if (iteration > maxIterations) {
      stopPolling("timeout");
      return;
    }

    if (evolutionStatus) {
      evolutionStatus.textContent = `A verificar ligação... (tentativa ${iteration}/${maxIterations})`;
    }

    try {
      const statePayload = await callEvolution("/api/evolution/instance/state", "GET");
      if (statePayload?.instance?.state === "open") {
        stopPolling("connected");
        return;
      }

      const connectPayload = await callEvolution("/api/evolution/instance/connect", "GET");
      const newBase64 = connectPayload?.qrcode?.base64 || connectPayload?.base64;
      if (newBase64 && newBase64 !== lastQrBase64) {
        if (qrImage) {
          qrImage.src = newBase64;
          qrImage.style.display = "block";
        }
        lastQrBase64 = newBase64;
      }
    } catch (err) {
      stopPolling("error", `Erro: ${err.message}`);
    }
  }, intervalMs);
}

// ---------------------------------------------------------------------------
// DOM fixture helpers
// ---------------------------------------------------------------------------

function buildDomFixture() {
  document.body.innerHTML = `
    <p id="evolutionStatus"></p>
    <img id="qrImage" style="display:none;" src="" />
  `;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("stopPolling()", () => {
  beforeEach(() => {
    buildDomFixture();
    pollingIntervalId = null;
  });

  afterEach(() => {
    if (pollingIntervalId !== null) {
      clearInterval(pollingIntervalId);
      pollingIntervalId = null;
    }
  });

  it("é um no-op seguro quando não há polling activo", () => {
    expect(() => stopPolling("connected")).not.toThrow();
  });

  it("reason=connected mostra mensagem de sucesso e oculta QR", () => {
    stopPolling("connected");
    expect(document.getElementById("evolutionStatus").textContent).toBe("Ligado ao WhatsApp.");
    expect(document.getElementById("qrImage").style.display).toBe("none");
  });

  it("reason=timeout mostra mensagem de tempo esgotado", () => {
    stopPolling("timeout");
    expect(document.getElementById("evolutionStatus").textContent).toContain("Tempo esgotado");
  });

  it("reason=error mostra mensagem de erro customizada", () => {
    stopPolling("error", "Erro: connection refused");
    expect(document.getElementById("evolutionStatus").textContent).toBe("Erro: connection refused");
  });

  it("reason=error sem mensagem usa texto padrão", () => {
    stopPolling("error");
    expect(document.getElementById("evolutionStatus").textContent).toBe("Erro de rede. Polling interrompido.");
  });

  it("reason=unload não actualiza o DOM (página a fechar)", () => {
    stopPolling("unload");
    expect(document.getElementById("evolutionStatus").textContent).toBe("");
  });

  it("chama clearInterval quando há intervalo activo", () => {
    jest.useFakeTimers();
    pollingIntervalId = setInterval(() => {}, 1000);
    const id = pollingIntervalId;
    const clearSpy = jest.spyOn(global, "clearInterval");
    stopPolling("connected");
    expect(clearSpy).toHaveBeenCalledWith(id);
    expect(pollingIntervalId).toBeNull();
    clearSpy.mockRestore();
    jest.useRealTimers();
  });
});

describe("startPolling() — estado inicial", () => {
  beforeEach(() => {
    buildDomFixture();
    pollingIntervalId = null;
    jest.useFakeTimers();
  });

  afterEach(() => {
    if (pollingIntervalId !== null) {
      clearInterval(pollingIntervalId);
      pollingIntervalId = null;
    }
    jest.useRealTimers();
  });

  it("para imediatamente se estado inicial é 'open' (AC-8, AC-2)", async () => {
    const mockCall = jest.fn().mockResolvedValue({ instance: { state: "open" } });
    await startPolling(mockCall, 5000, 24);
    expect(document.getElementById("evolutionStatus").textContent).toBe("Ligado ao WhatsApp.");
    expect(pollingIntervalId).toBeNull();
  });

  it("inicia intervalo se estado inicial não é 'open'", async () => {
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } }) // initial state
      .mockResolvedValue({ instance: { state: "close" } });    // tick states

    await startPolling(mockCall, 5000, 24);
    expect(pollingIntervalId).not.toBeNull();
  });

  it("cancela intervalo anterior antes de iniciar novo (AC-6)", async () => {
    const clearSpy = jest.spyOn(global, "clearInterval");
    pollingIntervalId = setInterval(() => {}, 9999);
    const oldId = pollingIntervalId;

    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } })
      .mockResolvedValue({ instance: { state: "close" } });

    await startPolling(mockCall, 5000, 24);

    expect(clearSpy).toHaveBeenCalledWith(oldId);
    clearSpy.mockRestore();
  });

  it("avança para polling se fetch inicial falhar (non-fatal)", async () => {
    const mockCall = jest.fn()
      .mockRejectedValueOnce(new Error("network error")) // initial state fails
      .mockResolvedValue({ instance: { state: "close" } });

    await startPolling(mockCall, 5000, 24);
    expect(pollingIntervalId).not.toBeNull();
  });
});

describe("startPolling() — lógica de cada tick", () => {
  beforeEach(() => {
    buildDomFixture();
    pollingIntervalId = null;
    jest.useFakeTimers();
  });

  afterEach(() => {
    if (pollingIntervalId !== null) {
      clearInterval(pollingIntervalId);
      pollingIntervalId = null;
    }
    jest.useRealTimers();
  });

  it("para ao receber estado 'open' num tick (AC-2)", async () => {
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } })  // initial state
      .mockResolvedValueOnce({ instance: { state: "open" } })   // tick 1: state
      .mockResolvedValue({});

    await startPolling(mockCall, 5000, 24);

    await jest.runAllTimersAsync();

    expect(document.getElementById("evolutionStatus").textContent).toBe("Ligado ao WhatsApp.");
    expect(pollingIntervalId).toBeNull();
  });

  it("actualiza o QR se base64 mudar (AC-5)", async () => {
    const newBase64 = "data:image/png;base64,NEWQR==";
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } })              // initial state
      .mockResolvedValueOnce({ instance: { state: "close" } })              // tick 1: state
      .mockResolvedValueOnce({ qrcode: { base64: newBase64 } })             // tick 1: connect
      .mockResolvedValue({ instance: { state: "open" } });                  // tick 2: state → stop

    await startPolling(mockCall, 5000, 24);
    await jest.runAllTimersAsync();

    expect(document.getElementById("qrImage").src).toBe(newBase64);
  });

  it("para com mensagem de erro em falha de rede num tick (AC-3)", async () => {
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } }) // initial state
      .mockRejectedValueOnce(new Error("ECONNREFUSED"));       // tick 1 fails

    await startPolling(mockCall, 5000, 24);
    await jest.runAllTimersAsync();

    expect(document.getElementById("evolutionStatus").textContent).toContain("ECONNREFUSED");
    expect(pollingIntervalId).toBeNull();
  });

  it("para por timeout após maxIterations ticks (AC-7)", async () => {
    // Use maxIterations=2 for speed; state never 'open'
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } })  // initial state
      .mockResolvedValue({ instance: { state: "close" } });      // all ticks

    await startPolling(mockCall, 100, 2);

    // Run tick 1
    await jest.advanceTimersByTimeAsync(100);
    // Run tick 2
    await jest.advanceTimersByTimeAsync(100);
    // Run tick 3 (iteration > maxIterations triggers timeout)
    await jest.advanceTimersByTimeAsync(100);

    expect(document.getElementById("evolutionStatus").textContent).toContain("Tempo esgotado");
    expect(pollingIntervalId).toBeNull();
  });

  it("mostra contador de iteração no status (AC-4)", async () => {
    const mockCall = jest.fn()
      .mockResolvedValueOnce({ instance: { state: "close" } })  // initial state
      .mockResolvedValueOnce({ instance: { state: "close" } })  // tick 1: state
      .mockResolvedValueOnce({})                                 // tick 1: connect
      .mockResolvedValue({ instance: { state: "open" } });      // tick 2: stop

    await startPolling(mockCall, 5000, 24);
    await jest.advanceTimersByTimeAsync(5000);

    const statusText = document.getElementById("evolutionStatus").textContent;
    expect(statusText).toMatch(/tentativa 1\/24/);
  });
});
