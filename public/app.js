const studentsForm = document.getElementById("studentsForm");
const gradesForm = document.getElementById("gradesForm");
const matchBtn = document.getElementById("matchBtn");
const sendBtn = document.getElementById("sendBtn");

const studentsStatus = document.getElementById("studentsStatus");
const gradesStatus = document.getElementById("gradesStatus");
const matchStats = document.getElementById("matchStats");
const matchTableBody = document.querySelector("#matchTable tbody");
const sendResult = document.getElementById("sendResult");

const createInstanceBtn = document.getElementById("createInstanceBtn");
const connectInstanceBtn = document.getElementById("connectInstanceBtn");
const stateInstanceBtn = document.getElementById("stateInstanceBtn");
const evolutionStatus = document.getElementById("evolutionStatus");
const evolutionResult = document.getElementById("evolutionResult");
const qrImage = document.getElementById("qrImage");

// ---------------------------------------------------------------------------
// Form validation utilities — Story 4.2 (UX-004)
// ---------------------------------------------------------------------------

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

/**
 * Show an inline validation error for a field.
 * @param {HTMLElement} errorEl - The <p class="form-error"> element
 * @param {HTMLElement} inputEl - The <input> or <textarea> element
 * @param {string} message - Descriptive error message in Portuguese
 */
function showError(errorEl, inputEl, message) {
  errorEl.textContent = message;
  inputEl.classList.add("field-invalid");
  inputEl.classList.remove("field-valid");
}

/**
 * Clear an inline validation error for a field.
 * Marks the field as valid (field-valid) after a successful selection.
 * @param {HTMLElement} errorEl - The <p class="form-error"> element
 * @param {HTMLElement} inputEl - The <input> or <textarea> element
 */
function clearError(errorEl, inputEl) {
  errorEl.textContent = "";
  inputEl.classList.remove("field-invalid");
  inputEl.classList.add("field-valid");
}

/**
 * Validate a file input for .csv extension and 5 MB size limit.
 * Updates the error element and submit button state.
 *
 * @param {string} inputId - ID of the file <input>
 * @param {string} errorId - ID of the <p class="form-error"> element
 * @param {string} buttonId - ID of the submit <button>
 * @returns {boolean} true when the input is valid
 */
function validateFileInput(inputId, errorId, buttonId) {
  const input = document.getElementById(inputId);
  const errorEl = document.getElementById(errorId);
  const button = document.getElementById(buttonId);
  const file = input.files[0];

  if (!file) {
    showError(errorEl, input, "Selecciona um ficheiro CSV antes de importar.");
    button.disabled = true;
    return false;
  }

  if (!file.name.toLowerCase().endsWith(".csv")) {
    showError(errorEl, input, "Apenas ficheiros .csv são aceites.");
    button.disabled = true;
    return false;
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    showError(errorEl, input, "O ficheiro excede o tamanho máximo de 5 MB.");
    button.disabled = true;
    return false;
  }

  clearError(errorEl, input);
  button.disabled = false;
  return true;
}

// ---------------------------------------------------------------------------
// DOMContentLoaded — initialise validation state
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  // Ensure submit buttons start disabled (AC-3)
  const studentsBtn = document.getElementById("studentsSubmitBtn");
  const gradesBtn = document.getElementById("gradesSubmitBtn");
  if (studentsBtn) studentsBtn.disabled = true;
  if (gradesBtn) gradesBtn.disabled = true;

  // Real-time validation on file selection (AC-1, AC-4, AC-5, AC-8)
  const studentsFileEl = document.getElementById("studentsFile");
  if (studentsFileEl) {
    studentsFileEl.addEventListener("change", () => {
      validateFileInput("studentsFile", "studentsFileError", "studentsSubmitBtn");
    });
  }

  const gradesFileEl = document.getElementById("gradesFile");
  if (gradesFileEl) {
    gradesFileEl.addEventListener("change", () => {
      validateFileInput("gradesFile", "gradesFileError", "gradesSubmitBtn");
    });
  }

  // Clear template / confirm errors when user corrects them (AC-5 / AC-6 / AC-7)
  const templateEl = document.getElementById("template");
  const templateErrorEl = document.getElementById("templateError");
  if (templateEl && templateErrorEl) {
    templateEl.addEventListener("input", () => {
      if (templateEl.value.trim().length > 0) {
        clearError(templateErrorEl, templateEl);
      }
    });
  }

  const confirmRealEl = document.getElementById("confirmReal");
  const dryRunEl = document.getElementById("dryRun");
  const sendConfirmErrorEl = document.getElementById("sendConfirmError");
  function clearConfirmError() {
    if (sendConfirmErrorEl) {
      sendConfirmErrorEl.textContent = "";
    }
  }
  if (confirmRealEl) confirmRealEl.addEventListener("change", clearConfirmError);
  if (dryRunEl) dryRunEl.addEventListener("change", clearConfirmError);

  // T5: Cleanup polling when the page is unloaded (AC-6)
  window.addEventListener("beforeunload", () => stopPolling("unload"));
});

// ---------------------------------------------------------------------------
// Upload helper
// ---------------------------------------------------------------------------

async function uploadCsv(inputId, endpoint) {
  const fileInput = document.getElementById(inputId);
  if (!fileInput.files.length) {
    throw new Error("Selecciona um ficheiro CSV antes de importar.");
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "X-API-Key": window.API_KEY || "" },
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Falha no upload");
  }

  return payload;
}

studentsForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  // Client-side validation guard (AC-1, AC-5) — belt-and-suspenders for keyboard submit
  if (!validateFileInput("studentsFile", "studentsFileError", "studentsSubmitBtn")) {
    return;
  }

  studentsStatus.textContent = "A importar...";

  try {
    const payload = await uploadCsv("studentsFile", "/api/students/upload");
    studentsStatus.textContent = `Estudantes importados: ${payload.total}`;
  } catch (error) {
    studentsStatus.textContent = `Erro: ${error.message}`;
  }
});

gradesForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  // Client-side validation guard (AC-1, AC-5)
  if (!validateFileInput("gradesFile", "gradesFileError", "gradesSubmitBtn")) {
    return;
  }

  gradesStatus.textContent = "A importar...";

  try {
    const payload = await uploadCsv("gradesFile", "/api/grades/upload");
    gradesStatus.textContent = `Notas importadas: ${payload.total}`;
  } catch (error) {
    gradesStatus.textContent = `Erro: ${error.message}`;
  }
});

matchBtn.addEventListener("click", async () => {
  matchStats.textContent = "A gerar match...";
  matchTableBody.innerHTML = "";

  const response = await fetch("/api/match/generate", { method: "POST", headers: { "X-API-Key": window.API_KEY || "" } });
  const payload = await response.json();

  if (!response.ok) {
    matchStats.textContent = payload.error || "Erro ao gerar match";
    return;
  }

  matchStats.textContent = `Total notas: ${payload.stats.total_grades} | Matched: ${payload.stats.matched} | Sem match: ${payload.stats.unmatched} | WhatsApp inválido: ${payload.stats.invalidPhones}`;

  payload.matched.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.numero_estudante}</td>
      <td>${item.nome}</td>
      <td>${item.turma}</td>
      <td>${item.whatsapp}</td>
      <td>${item.nota}</td>
    `;
    matchTableBody.appendChild(tr);
  });
});

async function callEvolution(endpoint, method = "GET") {
  const response = await fetch(endpoint, { method, headers: { "X-API-Key": window.API_KEY || "" } });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Falha na Evolution API");
  }

  evolutionResult.textContent = JSON.stringify(payload, null, 2);
  return payload;
}

function setQrFromPayload(payload) {
  const qrcode = payload?.qrcode?.base64 || payload?.base64;
  if (qrcode) {
    qrImage.src = qrcode;
    qrImage.style.display = "block";
    return true;
  }
  return false;
}

// ---------------------------------------------------------------------------
// QR Polling — Story 4.3 (UX-005)
// ---------------------------------------------------------------------------

/** @type {number|null} Active interval ID; null when polling is stopped. */
let pollingIntervalId = null;

/**
 * Stop the active polling interval and update the status message.
 * Safe to call when no polling is running (no-op).
 *
 * @param {"connected"|"error"|"timeout"|"unload"} reason - Why polling stopped
 * @param {string} [message] - Custom status message (overrides default)
 */
function stopPolling(reason, message) {
  if (pollingIntervalId !== null) {
    clearInterval(pollingIntervalId);
    pollingIntervalId = null;
  }

  if (reason === "unload") return; // page is closing — no DOM updates needed

  const defaultMessages = {
    connected: "Ligado ao WhatsApp.",
    timeout: "Tempo esgotado. Sem ligação após 2 minutos. Tenta novamente.",
    error: message || "Erro de rede. Polling interrompido.",
  };

  const statusText = message || defaultMessages[reason] || "";
  if (statusText) {
    evolutionStatus.textContent = statusText;
  }

  if (reason === "connected") {
    qrImage.style.display = "none";
  }
}

/**
 * Start interval-based polling for WhatsApp connection state.
 * Cancels any previous polling before starting a new one.
 *
 * @param {number} [intervalMs=5000] - Polling interval in milliseconds
 * @param {number} [maxIterations=24] - Max ticks before timeout (24×5s = 120s)
 */
async function startPolling(intervalMs = 5000, maxIterations = 24) {
  // Cancel any existing polling before starting (AC-6)
  stopPolling("unload");

  // T2: Fetch initial state before polling starts (AC-8)
  try {
    const initialState = await callEvolution("/api/evolution/instance/state", "GET");
    if (initialState?.instance?.state === "open") {
      evolutionStatus.textContent = "Ligado ao WhatsApp.";
      qrImage.style.display = "none";
      return; // Already connected — no need to poll
    }
  } catch (_err) {
    // Non-fatal: if initial fetch fails, start polling anyway
  }

  let iteration = 0;
  let lastQrBase64 = qrImage.src || null;

  pollingIntervalId = setInterval(async () => {
    iteration += 1;

    // Timeout check (AC-7)
    if (iteration > maxIterations) {
      stopPolling("timeout");
      return;
    }

    evolutionStatus.textContent = `A verificar ligação... (tentativa ${iteration}/${maxIterations})`;

    try {
      // Check connection state (AC-2)
      const statePayload = await callEvolution("/api/evolution/instance/state", "GET");
      if (statePayload?.instance?.state === "open") {
        stopPolling("connected");
        return;
      }

      // Try to refresh QR if still pending (AC-5)
      const connectPayload = await callEvolution("/api/evolution/instance/connect", "GET");
      const newBase64 = connectPayload?.qrcode?.base64 || connectPayload?.base64;
      if (newBase64 && newBase64 !== lastQrBase64) {
        qrImage.src = newBase64;
        qrImage.style.display = "block";
        lastQrBase64 = newBase64;
      }
    } catch (err) {
      // AC-3: network/HTTP error stops polling immediately
      stopPolling("error", `Erro: ${err.message}`);
    }
  }, intervalMs);
}

createInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A criar instância...";
    const payload = await callEvolution("/api/evolution/instance/create", "POST");
    setQrFromPayload(payload);
    await startPolling();
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

connectInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A solicitar QR...";
    const payload = await callEvolution("/api/evolution/instance/connect", "GET");
    setQrFromPayload(payload);
    await startPolling();
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

stateInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A consultar estado...";
    const payload = await callEvolution("/api/evolution/instance/state", "GET");
    const state = payload?.instance?.state || "desconhecido";
    evolutionStatus.textContent = `Estado actual: ${state}`;
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

// ---------------------------------------------------------------------------
// Confirmation modal — Story 4.6 (UX-008)
// ---------------------------------------------------------------------------

/**
 * Show a confirmation modal and return a Promise that resolves to true
 * (user confirmed) or false (user cancelled / pressed Escape / clicked backdrop).
 *
 * Relies on the native <dialog> element's .showModal() API.
 *
 * @param {string} message - Descriptive text to show inside the modal
 * @returns {Promise<boolean>}
 */
function showConfirmModal(message) {
  const modal = document.getElementById("confirmModal");
  const msgEl = document.getElementById("confirmModalMessage");
  const confirmBtn = document.getElementById("confirmModalConfirm");
  const cancelBtn = document.getElementById("confirmModalCancel");

  msgEl.textContent = message;
  modal.showModal();

  // Focus trap: cycle between Cancel and Confirm buttons only (AC4)
  const focusableEls = [cancelBtn, confirmBtn];

  function trapFocus(event) {
    if (event.key !== "Tab") return;
    event.preventDefault();
    const currentIndex = focusableEls.indexOf(document.activeElement);
    const nextIndex = event.shiftKey
      ? (currentIndex - 1 + focusableEls.length) % focusableEls.length
      : (currentIndex + 1) % focusableEls.length;
    focusableEls[nextIndex].focus();
  }

  modal.addEventListener("keydown", trapFocus);

  return new Promise((resolve) => {
    function cleanup(result) {
      modal.removeEventListener("keydown", trapFocus);
      modal.removeEventListener("click", handleBackdropClick);
      confirmBtn.removeEventListener("click", onConfirm);
      cancelBtn.removeEventListener("click", onCancel);
      modal.removeEventListener("cancel", onNativeCancel);
      modal.close();
      // Return focus to the trigger button (AC5)
      sendBtn.focus();
      resolve(result);
    }

    // Close on backdrop click: event.target is the <dialog> itself when clicking
    // outside the modal box (AC5)
    function handleBackdropClick(event) {
      if (event.target === modal) {
        cleanup(false);
      }
    }

    function onConfirm() { cleanup(true); }
    function onCancel() { cleanup(false); }
    // Native <dialog> cancel event fires on Escape key (AC5)
    function onNativeCancel(event) {
      event.preventDefault(); // prevent browser from closing before we resolve
      cleanup(false);
    }

    modal.addEventListener("click", handleBackdropClick);
    confirmBtn.addEventListener("click", onConfirm);
    cancelBtn.addEventListener("click", onCancel);
    modal.addEventListener("cancel", onNativeCancel);

    // Initial focus on Cancelar (safer default for a destructive action)
    cancelBtn.focus();
  });
}

sendBtn.addEventListener("click", async () => {
  const dryRun = document.getElementById("dryRun").checked;
  const confirmReal = document.getElementById("confirmReal").checked;
  const templateEl = document.getElementById("template");
  const template = templateEl.value;
  const templateErrorEl = document.getElementById("templateError");
  const sendConfirmErrorEl = document.getElementById("sendConfirmError");

  // Clear previous inline errors before re-validating (AC-5)
  if (templateErrorEl) templateErrorEl.textContent = "";
  if (sendConfirmErrorEl) sendConfirmErrorEl.textContent = "";

  let hasError = false;

  // AC-6: validate template is not empty
  if (!template.trim()) {
    if (templateErrorEl) {
      showError(templateErrorEl, templateEl, "A mensagem não pode estar vazia.");
    }
    hasError = true;
  } else if (templateErrorEl) {
    clearError(templateErrorEl, templateEl);
  }

  // AC-7: replace alert() with inline error for missing confirmation (AC-9)
  if (!dryRun && !confirmReal) {
    if (sendConfirmErrorEl) {
      sendConfirmErrorEl.textContent =
        "Marca a confirmação de envio real ou activa a simulação.";
    }
    hasError = true;
  }

  if (hasError) return;

  // AC1: Show confirmation modal before executing bulk send (Story 4.6)
  const confirmed = await showConfirmModal(
    "Confirmas o envio de mensagens WhatsApp para todos os estudantes com match?"
  );
  if (!confirmed) return;

  sendResult.textContent = "A enviar...";

  const response = await fetch("/api/send/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": window.API_KEY || "" },
    body: JSON.stringify({ template, dryRun }),
  });

  const payload = await response.json();
  sendResult.textContent = JSON.stringify(payload, null, 2);
});
