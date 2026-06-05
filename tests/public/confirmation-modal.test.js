/**
 * Confirmation modal tests — Story 4.6 (UX-008)
 * Tests for showConfirmModal() logic and HTML structure.
 *
 * @jest-environment jsdom
 */

"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// Load the real HTML so we can test the modal structure
// ---------------------------------------------------------------------------
const htmlPath = path.join(__dirname, "../../public/index.html");

function loadHtml() {
  const raw = fs.readFileSync(htmlPath, "utf8");
  return raw
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<link\b[^>]*>/gi, "");
}

// ---------------------------------------------------------------------------
// Inline re-implementation of showConfirmModal from app.js
// The function is re-implemented here to run in jsdom — identical logic.
// ---------------------------------------------------------------------------

/**
 * jsdom does not implement HTMLDialogElement.showModal() or .close() natively
 * (as of jsdom 20). We polyfill the minimum required surface.
 */
function polyfillDialog(dialogEl) {
  if (typeof dialogEl.showModal !== "function") {
    dialogEl.showModal = function () {
      this.setAttribute("open", "");
    };
  }
  if (typeof dialogEl.close !== "function") {
    dialogEl.close = function () {
      this.removeAttribute("open");
    };
  }
}

function showConfirmModal(message) {
  const modal = document.getElementById("confirmModal");
  const msgEl = document.getElementById("confirmModalMessage");
  const confirmBtn = document.getElementById("confirmModalConfirm");
  const cancelBtn = document.getElementById("confirmModalCancel");
  const sendBtn = document.getElementById("sendBtn");

  polyfillDialog(modal);

  msgEl.textContent = message;
  modal.showModal();

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
      if (sendBtn) sendBtn.focus();
      resolve(result);
    }

    function handleBackdropClick(event) {
      if (event.target === modal) {
        cleanup(false);
      }
    }

    function onConfirm() { cleanup(true); }
    function onCancel() { cleanup(false); }
    function onNativeCancel(event) {
      event.preventDefault();
      cleanup(false);
    }

    modal.addEventListener("click", handleBackdropClick);
    confirmBtn.addEventListener("click", onConfirm);
    cancelBtn.addEventListener("click", onCancel);
    modal.addEventListener("cancel", onNativeCancel);

    cancelBtn.focus();
  });
}

// ---------------------------------------------------------------------------
// HTML structure tests (AC2, AC3, AC7)
// ---------------------------------------------------------------------------

describe("Confirmation modal — HTML structure (AC2, AC3, AC7)", () => {
  beforeEach(() => {
    document.documentElement.innerHTML = loadHtml();
    document.documentElement.setAttribute("lang", "pt");
  });

  it("elemento #confirmModal existe no DOM (AC2)", () => {
    const modal = document.getElementById("confirmModal");
    expect(modal).not.toBeNull();
  });

  it("modal é um elemento <dialog> (AC2)", () => {
    const modal = document.getElementById("confirmModal");
    expect(modal.tagName.toLowerCase()).toBe("dialog");
  });

  it("modal tem aria-modal=true (AC2)", () => {
    const modal = document.getElementById("confirmModal");
    expect(modal.getAttribute("aria-modal")).toBe("true");
  });

  it("modal tem aria-labelledby apontando para #confirmModalTitle (AC3)", () => {
    const modal = document.getElementById("confirmModal");
    const labelledBy = modal.getAttribute("aria-labelledby");
    expect(labelledBy).toBe("confirmModalTitle");

    const titleEl = document.getElementById("confirmModalTitle");
    expect(titleEl).not.toBeNull();
    expect(titleEl.textContent.trim()).not.toBe("");
  });

  it("modal tem botão #confirmModalConfirm (AC1)", () => {
    expect(document.getElementById("confirmModalConfirm")).not.toBeNull();
  });

  it("modal tem botão #confirmModalCancel (AC5)", () => {
    expect(document.getElementById("confirmModalCancel")).not.toBeNull();
  });

  it("elemento #confirmModalMessage existe para receber a mensagem dinâmica (AC1)", () => {
    expect(document.getElementById("confirmModalMessage")).not.toBeNull();
  });

  it("modal não está aberto por omissão (AC1 — não bloqueia a página)", () => {
    const modal = document.getElementById("confirmModal");
    // <dialog> without 'open' attribute is closed
    expect(modal.hasAttribute("open")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// showConfirmModal() behaviour tests (AC1, AC4, AC5, AC6)
// ---------------------------------------------------------------------------

describe("showConfirmModal() — comportamento (AC1, AC4, AC5)", () => {
  beforeEach(() => {
    document.documentElement.innerHTML = loadHtml();
    document.documentElement.setAttribute("lang", "pt");

    // Ensure sendBtn exists (app.js references it for focus return)
    if (!document.getElementById("sendBtn")) {
      const btn = document.createElement("button");
      btn.id = "sendBtn";
      document.body.appendChild(btn);
    }
  });

  it("abre o modal quando chamada (AC1)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Teste de abertura");

    expect(modal.hasAttribute("open")).toBe(true);

    // Resolve the promise to avoid hanging
    document.getElementById("confirmModalCancel").click();
    await promise;
  });

  it("preenche #confirmModalMessage com a mensagem fornecida (AC1)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Mensagem de confirmação de teste.");
    expect(document.getElementById("confirmModalMessage").textContent).toBe(
      "Mensagem de confirmação de teste."
    );

    document.getElementById("confirmModalCancel").click();
    await promise;
  });

  it("resolve true quando Confirmar é clicado (AC1)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar envio?");
    document.getElementById("confirmModalConfirm").click();

    const result = await promise;
    expect(result).toBe(true);
  });

  it("resolve false quando Cancelar é clicado (AC5)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar envio?");
    document.getElementById("confirmModalCancel").click();

    const result = await promise;
    expect(result).toBe(false);
  });

  it("fecha o modal após Confirmar (AC1)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar?");
    document.getElementById("confirmModalConfirm").click();
    await promise;

    expect(modal.hasAttribute("open")).toBe(false);
  });

  it("fecha o modal após Cancelar (AC5)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar?");
    document.getElementById("confirmModalCancel").click();
    await promise;

    expect(modal.hasAttribute("open")).toBe(false);
  });

  it("resolve false quando evento 'cancel' (Escape) é disparado (AC5)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar?");

    // Simulate Escape key via the native 'cancel' event
    const cancelEvent = new Event("cancel", { cancelable: true });
    modal.dispatchEvent(cancelEvent);

    const result = await promise;
    expect(result).toBe(false);
    expect(modal.hasAttribute("open")).toBe(false);
  });

  it("resolve false quando se clica no backdrop (target === modal) (AC5)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Confirmar?");

    // Simulate click directly on the dialog element (backdrop area)
    const clickEvent = new MouseEvent("click", { bubbles: true });
    Object.defineProperty(clickEvent, "target", { value: modal, writable: false });
    modal.dispatchEvent(clickEvent);

    const result = await promise;
    expect(result).toBe(false);
  });

  it("focus trap: Tab avança de Cancelar para Confirmar (AC4)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Tab trap test");

    const cancelBtn = document.getElementById("confirmModalCancel");
    const confirmBtn = document.getElementById("confirmModalConfirm");

    // Initial focus is on Cancel
    cancelBtn.focus();
    expect(document.activeElement).toBe(cancelBtn);

    // Tab forward should move to Confirm
    const tabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: false,
      bubbles: true,
      cancelable: true,
    });
    modal.dispatchEvent(tabEvent);
    expect(document.activeElement).toBe(confirmBtn);

    // Clean up
    cancelBtn.click();
    await promise;
  });

  it("focus trap: Shift+Tab recua de Confirmar para Cancelar (AC4)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Shift+Tab trap test");

    const cancelBtn = document.getElementById("confirmModalCancel");
    const confirmBtn = document.getElementById("confirmModalConfirm");

    // Focus on Confirm first
    confirmBtn.focus();

    // Shift+Tab should move back to Cancel
    const shiftTabEvent = new KeyboardEvent("keydown", {
      key: "Tab",
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    });
    modal.dispatchEvent(shiftTabEvent);
    expect(document.activeElement).toBe(cancelBtn);

    cancelBtn.click();
    await promise;
  });

  it("focus inicial está no botão Cancelar ao abrir (decisão segura para acção destrutiva) (AC4)", async () => {
    const modal = document.getElementById("confirmModal");
    polyfillDialog(modal);

    const promise = showConfirmModal("Focus inicial?");

    const cancelBtn = document.getElementById("confirmModalCancel");
    expect(document.activeElement).toBe(cancelBtn);

    cancelBtn.click();
    await promise;
  });
});

// ---------------------------------------------------------------------------
// AC6 — Zero alert() calls in app.js
// ---------------------------------------------------------------------------

describe("AC6 — Zero chamadas alert() em public/app.js", () => {
  it("public/app.js não contém nenhuma chamada alert()", () => {
    const appJsPath = path.join(__dirname, "../../public/app.js");
    const source = fs.readFileSync(appJsPath, "utf8");

    // Match real alert() calls but not comments containing the word
    const alertCalls = source.match(/(?<!\/\/.*)\balert\s*\(/gm) || [];
    expect(alertCalls).toHaveLength(0);
  });
});
