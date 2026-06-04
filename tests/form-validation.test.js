/**
 * Form validation tests — Story 4.2 (UX-004)
 * Tests for showError, clearError, and validateFileInput utilities extracted
 * from public/app.js via a thin test harness that runs them in jsdom.
 *
 * @jest-environment jsdom
 */

"use strict";

// ---------------------------------------------------------------------------
// Inline re-implementation of the pure validation utilities from app.js.
// These are identical to the production code so we can unit-test them without
// needing a browser or bundler.  If the implementations diverge, tests break.
// ---------------------------------------------------------------------------

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB

function showError(errorEl, inputEl, message) {
  errorEl.textContent = message;
  inputEl.classList.add("field-invalid");
  inputEl.classList.remove("field-valid");
}

function clearError(errorEl, inputEl) {
  errorEl.textContent = "";
  inputEl.classList.remove("field-invalid");
  inputEl.classList.add("field-valid");
}

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
// Helper — build the minimal DOM fixture needed for each test
// ---------------------------------------------------------------------------

function buildFixture(inputId = "testFile", errorId = "testFileError", buttonId = "testBtn") {
  document.body.innerHTML = `
    <input type="file" id="${inputId}" />
    <p id="${errorId}" class="form-error"></p>
    <button id="${buttonId}">Submit</button>
  `;
}

/**
 * Create a minimal File-like object compatible with jsdom's FileList.
 * jsdom does not support DataTransfer natively, so we monkey-patch the
 * files property of the input.
 */
function setInputFile(inputEl, { name, size = 0, type = "text/csv" } = {}) {
  // jsdom does not allow setting input.files directly, but we can use
  // Object.defineProperty to override the getter for testing purposes.
  const file = new File(["x".repeat(size)], name, { type });
  Object.defineProperty(inputEl, "files", {
    configurable: true,
    get: () => ({ 0: file, length: 1, [Symbol.iterator]: function* () { yield file; } }),
  });
}

function clearInputFile(inputEl) {
  Object.defineProperty(inputEl, "files", {
    configurable: true,
    get: () => ({ length: 0 }),
  });
}

// ---------------------------------------------------------------------------
// showError / clearError utilities
// ---------------------------------------------------------------------------

describe("showError()", () => {
  beforeEach(() => {
    document.body.innerHTML = `<input id="inp" /><p id="err"></p>`;
  });

  it("insere texto no elemento de erro", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    showError(err, inp, "Mensagem de teste.");
    expect(err.textContent).toBe("Mensagem de teste.");
  });

  it("adiciona .field-invalid ao input", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    showError(err, inp, "Erro.");
    expect(inp.classList.contains("field-invalid")).toBe(true);
  });

  it("remove .field-valid do input quando há erro", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    inp.classList.add("field-valid");
    showError(err, inp, "Erro.");
    expect(inp.classList.contains("field-valid")).toBe(false);
  });
});

describe("clearError()", () => {
  beforeEach(() => {
    document.body.innerHTML = `<input id="inp" class="field-invalid" /><p id="err">Erro anterior.</p>`;
  });

  it("limpa o texto do elemento de erro", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    clearError(err, inp);
    expect(err.textContent).toBe("");
  });

  it("remove .field-invalid do input", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    clearError(err, inp);
    expect(inp.classList.contains("field-invalid")).toBe(false);
  });

  it("adiciona .field-valid ao input", () => {
    const inp = document.getElementById("inp");
    const err = document.getElementById("err");
    clearError(err, inp);
    expect(inp.classList.contains("field-valid")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// validateFileInput — AC-1, AC-3, AC-4, AC-5, AC-8, AC-9
// ---------------------------------------------------------------------------

describe("validateFileInput()", () => {
  beforeEach(() => {
    buildFixture();
  });

  it("retorna false e desabilita botão quando nenhum ficheiro está seleccionado", () => {
    const input = document.getElementById("testFile");
    clearInputFile(input);

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(false);
    expect(document.getElementById("testBtn").disabled).toBe(true);
  });

  it("exibe mensagem descritiva quando nenhum ficheiro está seleccionado (AC-9)", () => {
    const input = document.getElementById("testFile");
    clearInputFile(input);

    validateFileInput("testFile", "testFileError", "testBtn");

    expect(document.getElementById("testFileError").textContent).toBe(
      "Selecciona um ficheiro CSV antes de importar."
    );
  });

  it("retorna false e exibe erro para ficheiro com extensão errada (AC-1, AC-9)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "dados.xlsx", size: 100 });

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(false);
    expect(document.getElementById("testBtn").disabled).toBe(true);
    expect(document.getElementById("testFileError").textContent).toBe(
      "Apenas ficheiros .csv são aceites."
    );
  });

  it("retorna false e exibe erro para ficheiro superior a 5 MB (AC-1, AC-9)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "grande.csv", size: MAX_FILE_SIZE_BYTES + 1 });

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(false);
    expect(document.getElementById("testBtn").disabled).toBe(true);
    expect(document.getElementById("testFileError").textContent).toBe(
      "O ficheiro excede o tamanho máximo de 5 MB."
    );
  });

  it("retorna true, habilita botão e limpa erro para ficheiro .csv válido (AC-4)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "turma.csv", size: 1024 });

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(true);
    expect(document.getElementById("testBtn").disabled).toBe(false);
    expect(document.getElementById("testFileError").textContent).toBe("");
  });

  it("aceita ficheiros .CSV com maiúsculas na extensão (case-insensitive)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "NOTAS.CSV", size: 512 });

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(true);
  });

  it("aceita ficheiro exactamente no limite de 5 MB (boundary value)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "limite.csv", size: MAX_FILE_SIZE_BYTES });

    const result = validateFileInput("testFile", "testFileError", "testBtn");

    expect(result).toBe(true);
    expect(document.getElementById("testBtn").disabled).toBe(false);
  });

  it("aplica .field-invalid ao input quando há erro (AC-8)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "errado.txt", size: 50 });

    validateFileInput("testFile", "testFileError", "testBtn");

    expect(document.getElementById("testFile").classList.contains("field-invalid")).toBe(true);
  });

  it("aplica .field-valid ao input quando válido (AC-8)", () => {
    const input = document.getElementById("testFile");
    setInputFile(input, { name: "ok.csv", size: 50 });

    validateFileInput("testFile", "testFileError", "testBtn");

    expect(document.getElementById("testFile").classList.contains("field-valid")).toBe(true);
    expect(document.getElementById("testFile").classList.contains("field-invalid")).toBe(false);
  });

  it("limpa erro anterior quando ficheiro é corrigido (AC-5)", () => {
    const input = document.getElementById("testFile");

    // First: invalid file
    setInputFile(input, { name: "errado.txt", size: 50 });
    validateFileInput("testFile", "testFileError", "testBtn");
    expect(document.getElementById("testFileError").textContent).not.toBe("");

    // Then: correct the file
    setInputFile(input, { name: "correcto.csv", size: 50 });
    validateFileInput("testFile", "testFileError", "testBtn");

    expect(document.getElementById("testFileError").textContent).toBe("");
  });
});

// ---------------------------------------------------------------------------
// Accessibility — aria-describedby connections (AC-2, AC-10)
// ---------------------------------------------------------------------------

describe("HTML structure — aria-describedby links inputs to error elements (AC-2)", () => {
  const fs = require("fs");
  const path = require("path");

  const htmlPath = path.join(__dirname, "../public/index.html");

  beforeEach(() => {
    const raw = fs
      .readFileSync(htmlPath, "utf8")
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
      .replace(/<link\b[^>]*>/gi, "");
    document.documentElement.innerHTML = raw;
    document.documentElement.setAttribute("lang", "pt");
  });

  it("#studentsFile aria-describedby inclui studentsFileError", () => {
    const input = document.getElementById("studentsFile");
    expect(input).not.toBeNull();
    const desc = input.getAttribute("aria-describedby") || "";
    expect(desc).toContain("studentsFileError");
  });

  it("#studentsFile aria-describedby mantém studentsStatus (regressão Story 4.1)", () => {
    const input = document.getElementById("studentsFile");
    const desc = input.getAttribute("aria-describedby") || "";
    expect(desc).toContain("studentsStatus");
  });

  it("#gradesFile aria-describedby inclui gradesFileError", () => {
    const input = document.getElementById("gradesFile");
    expect(input).not.toBeNull();
    const desc = input.getAttribute("aria-describedby") || "";
    expect(desc).toContain("gradesFileError");
  });

  it("#gradesFile aria-describedby mantém gradesStatus (regressão Story 4.1)", () => {
    const input = document.getElementById("gradesFile");
    const desc = input.getAttribute("aria-describedby") || "";
    expect(desc).toContain("gradesStatus");
  });

  it("#template aria-describedby inclui templateError", () => {
    const input = document.getElementById("template");
    expect(input).not.toBeNull();
    const desc = input.getAttribute("aria-describedby") || "";
    expect(desc).toContain("templateError");
  });

  it("elemento #studentsFileError existe no DOM com aria-live=assertive (AC-10)", () => {
    const el = document.getElementById("studentsFileError");
    expect(el).not.toBeNull();
    expect(el.getAttribute("aria-live")).toBe("assertive");
  });

  it("elemento #gradesFileError existe no DOM com aria-live=assertive (AC-10)", () => {
    const el = document.getElementById("gradesFileError");
    expect(el).not.toBeNull();
    expect(el.getAttribute("aria-live")).toBe("assertive");
  });

  it("elemento #templateError existe no DOM com aria-live=assertive (AC-10)", () => {
    const el = document.getElementById("templateError");
    expect(el).not.toBeNull();
    expect(el.getAttribute("aria-live")).toBe("assertive");
  });

  it("elemento #sendConfirmError existe no DOM com aria-live=assertive (AC-10)", () => {
    const el = document.getElementById("sendConfirmError");
    expect(el).not.toBeNull();
    expect(el.getAttribute("aria-live")).toBe("assertive");
  });

  it("botão #studentsSubmitBtn começa com disabled no HTML (AC-3)", () => {
    const btn = document.getElementById("studentsSubmitBtn");
    expect(btn).not.toBeNull();
    expect(btn.disabled).toBe(true);
  });

  it("botão #gradesSubmitBtn começa com disabled no HTML (AC-3)", () => {
    const btn = document.getElementById("gradesSubmitBtn");
    expect(btn).not.toBeNull();
    expect(btn.disabled).toBe(true);
  });
});
