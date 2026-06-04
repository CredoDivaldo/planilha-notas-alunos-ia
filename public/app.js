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

async function waitForQr(maxAttempts = 20, delayMs = 1500) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    evolutionStatus.textContent = `A aguardar QR... tentativa ${attempt}/${maxAttempts}`;

    const statePayload = await callEvolution("/api/evolution/instance/state", "GET");
    const state = statePayload?.instance?.state;

    if (state === "open") {
      evolutionStatus.textContent = "Instância conectada (estado open).";
      return;
    }

    const connectPayload = await callEvolution("/api/evolution/instance/connect", "GET");
    if (setQrFromPayload(connectPayload)) {
      evolutionStatus.textContent = "QR gerado. Escaneia no WhatsApp.";
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  evolutionStatus.textContent = "Sem QR após várias tentativas. Verifica logs da Evolution e tenta novamente.";
}

createInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A criar instância...";
    const payload = await callEvolution("/api/evolution/instance/create", "POST");
    if (setQrFromPayload(payload)) {
      evolutionStatus.textContent = "QR gerado no create. Escaneia no WhatsApp.";
      return;
    }
    await waitForQr();
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

connectInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A solicitar QR...";
    const payload = await callEvolution("/api/evolution/instance/connect", "GET");
    if (setQrFromPayload(payload)) {
      evolutionStatus.textContent = "QR gerado. Escaneia no WhatsApp.";
      return;
    }
    await waitForQr();
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

  sendResult.textContent = "A enviar...";

  const response = await fetch("/api/send/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": window.API_KEY || "" },
    body: JSON.stringify({ template, dryRun }),
  });

  const payload = await response.json();
  sendResult.textContent = JSON.stringify(payload, null, 2);
});
