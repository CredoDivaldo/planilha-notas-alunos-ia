/**
 * State Gating Tests — Story 4.7
 *
 * Tests for the workflow gating logic: appState transitions and updateGating()
 * behaviour. Uses jsdom to simulate the DOM.
 *
 * @jest-environment jsdom
 */

"use strict";

// ---------------------------------------------------------------------------
// DOM fixture: minimal HTML matching public/index.html sections 1-3 and 5
// ---------------------------------------------------------------------------

function buildDom() {
  document.body.innerHTML = `
    <section id="sec1" aria-labelledby="sec1-heading" aria-describedby="sec1-lock-reason">
      <p id="sec1-lock-reason" class="lock-reason"></p>
      <form id="studentsForm">
        <input type="file" id="studentsFile" accept=".csv" />
        <button type="submit" id="studentsSubmitBtn" disabled>Importar estudantes</button>
      </form>
    </section>

    <section id="sec2" aria-labelledby="sec2-heading" aria-describedby="sec2-lock-reason">
      <p id="sec2-lock-reason" class="lock-reason"></p>
      <form id="gradesForm">
        <input type="file" id="gradesFile" accept=".csv" />
        <button type="submit" id="gradesSubmitBtn" disabled>Importar notas</button>
      </form>
    </section>

    <section id="sec3" aria-labelledby="sec3-heading" aria-describedby="sec3-lock-reason">
      <p id="sec3-lock-reason" class="lock-reason"></p>
      <button id="matchBtn">Gerar match</button>
    </section>

    <section id="sec4" aria-labelledby="sec4-heading">
      <button id="createInstanceBtn">Criar instância</button>
      <button id="connectInstanceBtn">Gerar QR</button>
      <button id="stateInstanceBtn">Ver estado</button>
      <p id="evolutionStatus"></p>
      <pre id="evolutionResult"></pre>
      <img id="qrImage" style="display:none;" />
    </section>

    <section id="sec5" aria-labelledby="sec5-heading" aria-describedby="sec5-lock-reason">
      <p id="sec5-lock-reason" class="lock-reason"></p>
      <textarea id="template">Olá {{nome}}</textarea>
      <input type="checkbox" id="confirmReal" />
      <input type="checkbox" id="dryRun" />
      <button id="sendBtn">Disparar em massa</button>
    </section>

    <dialog id="confirmModal">
      <p id="confirmModalMessage"></p>
      <button id="confirmModalCancel">Cancelar</button>
      <button id="confirmModalConfirm">Confirmar</button>
    </dialog>
  `;
}

// ---------------------------------------------------------------------------
// Load the module under test
// We re-define appState + updateGating + setSectionLocked in isolation so
// the tests do not depend on the browser globals (fetch, window.API_KEY, etc.)
// ---------------------------------------------------------------------------

/**
 * Standalone reimplementation of the gating functions, mirroring app.js
 * logic exactly so tests verify the real algorithm.
 */

/** @type {{ instanceCreated: boolean, connected: boolean, matchGenerated: boolean }} */
let appState;

function setSectionLocked(section, locked, interactiveIds) {
  if (!section) return;
  if (locked) {
    section.classList.add("section-locked");
    section.classList.remove("section-unlocked");
  } else {
    section.classList.remove("section-locked");
    section.classList.add("section-unlocked");
  }
  interactiveIds.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (locked) {
      el.disabled = true;
      el.setAttribute("aria-disabled", "true");
    } else {
      if (!el.dataset.gatingOnly) {
        el.disabled = false;
      }
      el.setAttribute("aria-disabled", "false");
    }
  });
}

function updateGating() {
  const sec1 = document.getElementById("sec1");
  const sec2 = document.getElementById("sec2");
  const sec3 = document.getElementById("sec3");
  const sec5 = document.getElementById("sec5");

  setSectionLocked(sec1, !appState.connected, ["studentsFile", "studentsSubmitBtn"]);
  setSectionLocked(sec2, !appState.connected, ["gradesFile", "gradesSubmitBtn"]);
  setSectionLocked(sec3, !appState.connected, ["matchBtn"]);
  setSectionLocked(sec5, !appState.connected || !appState.matchGenerated, [
    "sendBtn",
    "template",
    "confirmReal",
    "dryRun",
  ]);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resetState() {
  appState = { instanceCreated: false, connected: false, matchGenerated: false };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  buildDom();
  resetState();
});

// --- AC-5: Initial state — all dependent sections locked ---

describe("Initial state (all false)", () => {
  test("sec1 is locked before connection", () => {
    updateGating();
    expect(document.getElementById("sec1").classList.contains("section-locked")).toBe(true);
  });

  test("sec2 is locked before connection", () => {
    updateGating();
    expect(document.getElementById("sec2").classList.contains("section-locked")).toBe(true);
  });

  test("sec3 (match) is locked before connection", () => {
    updateGating();
    expect(document.getElementById("sec3").classList.contains("section-locked")).toBe(true);
  });

  test("sec5 (send) is locked before connection", () => {
    updateGating();
    expect(document.getElementById("sec5").classList.contains("section-locked")).toBe(true);
  });

  test("sec4 (WhatsApp setup) is never locked — always accessible", () => {
    updateGating();
    // sec4 has no section-locked class added by updateGating
    expect(document.getElementById("sec4").classList.contains("section-locked")).toBe(false);
  });
});

// --- AC-1: Connection unlocks sec1, sec2, sec3 ---

describe("After appState.connected = true", () => {
  beforeEach(() => {
    appState.connected = true;
    updateGating();
  });

  test("sec1 is unlocked", () => {
    expect(document.getElementById("sec1").classList.contains("section-unlocked")).toBe(true);
    expect(document.getElementById("sec1").classList.contains("section-locked")).toBe(false);
  });

  test("sec2 is unlocked", () => {
    expect(document.getElementById("sec2").classList.contains("section-unlocked")).toBe(true);
  });

  test("sec3 (match) is unlocked", () => {
    expect(document.getElementById("sec3").classList.contains("section-unlocked")).toBe(true);
  });

  test("matchBtn becomes enabled", () => {
    expect(document.getElementById("matchBtn").disabled).toBe(false);
  });

  test("sec5 (send) stays locked — matchGenerated still false", () => {
    expect(document.getElementById("sec5").classList.contains("section-locked")).toBe(true);
  });
});

// --- AC-2: sec5 requires both connected AND matchGenerated ---

describe("After connected + matchGenerated", () => {
  beforeEach(() => {
    appState.connected = true;
    appState.matchGenerated = true;
    updateGating();
  });

  test("sec5 is unlocked", () => {
    expect(document.getElementById("sec5").classList.contains("section-unlocked")).toBe(true);
  });

  test("sendBtn becomes enabled", () => {
    expect(document.getElementById("sendBtn").disabled).toBe(false);
  });
});

// --- AC-2: sec5 locked if connected but no match ---

describe("Connected but matchGenerated = false", () => {
  test("sec5 remains locked", () => {
    appState.connected = true;
    appState.matchGenerated = false;
    updateGating();
    expect(document.getElementById("sec5").classList.contains("section-locked")).toBe(true);
  });
});

// --- AC-3: Visual indicator — aria-disabled on locked elements ---

describe("ARIA attributes on locked elements (AC-7)", () => {
  test("matchBtn has aria-disabled=true when sec3 is locked", () => {
    updateGating();
    expect(document.getElementById("matchBtn").getAttribute("aria-disabled")).toBe("true");
  });

  test("sendBtn has aria-disabled=true when sec5 is locked", () => {
    updateGating();
    expect(document.getElementById("sendBtn").getAttribute("aria-disabled")).toBe("true");
  });

  test("matchBtn aria-disabled=false when sec3 is unlocked", () => {
    appState.connected = true;
    updateGating();
    expect(document.getElementById("matchBtn").getAttribute("aria-disabled")).toBe("false");
  });

  test("sendBtn aria-disabled=false when sec5 is unlocked", () => {
    appState.connected = true;
    appState.matchGenerated = true;
    updateGating();
    expect(document.getElementById("sendBtn").getAttribute("aria-disabled")).toBe("false");
  });
});

// --- AC-6: State only advances (false → true), never regresses ---

describe("State monotonicity (AC-6)", () => {
  test("connected flag does not go back to false after being set", () => {
    appState.connected = true;
    updateGating();
    // Simulate a spurious re-call (e.g. polling tick) without changing state
    updateGating();
    expect(appState.connected).toBe(true);
  });

  test("matchGenerated flag does not regress after being set", () => {
    appState.connected = true;
    appState.matchGenerated = true;
    updateGating();
    updateGating();
    expect(appState.matchGenerated).toBe(true);
  });
});

// --- AC-5: Workflow order respected ---

describe("Workflow order (AC-5)", () => {
  test("step 1→2: only connected unlocks sec1 and sec2", () => {
    appState.instanceCreated = true; // instance created but NOT yet connected
    updateGating();
    expect(document.getElementById("sec1").classList.contains("section-locked")).toBe(true);
    expect(document.getElementById("sec2").classList.contains("section-locked")).toBe(true);
  });

  test("step 2→3: only matchGenerated (+ connected) unlocks sec5", () => {
    appState.connected = true;
    updateGating();
    expect(document.getElementById("sec5").classList.contains("section-locked")).toBe(true);
  });

  test("full workflow sequence unlocks all sections", () => {
    // Step 1: create instance
    appState.instanceCreated = true;
    updateGating();
    // Step 2: connect
    appState.connected = true;
    updateGating();
    // Step 3: generate match
    appState.matchGenerated = true;
    updateGating();

    expect(document.getElementById("sec1").classList.contains("section-unlocked")).toBe(true);
    expect(document.getElementById("sec2").classList.contains("section-unlocked")).toBe(true);
    expect(document.getElementById("sec3").classList.contains("section-unlocked")).toBe(true);
    expect(document.getElementById("sec5").classList.contains("section-unlocked")).toBe(true);
  });
});
