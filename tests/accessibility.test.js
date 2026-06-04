/**
 * Accessibility tests using axe-core (WCAG 2.2 AA)
 * Story 4.1 — Accessibility Basics (UX-003)
 *
 * @jest-environment jsdom
 */

"use strict";

const fs = require("fs");
const path = require("path");
const axe = require("axe-core");

const htmlPath = path.join(__dirname, "../public/index.html");

function loadHtml() {
  const raw = fs.readFileSync(htmlPath, "utf8");
  // Strip script tags to avoid browser-only execution in jsdom
  return raw
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<link\b[^>]*>/gi, "");
}

describe("Accessibility — WCAG 2.2 AA (axe-core)", () => {
  beforeEach(() => {
    document.documentElement.innerHTML = loadHtml();
    // jsdom resets lang when setting innerHTML on documentElement — restore it
    document.documentElement.setAttribute("lang", "pt");
    axe.configure({ allowedOrigins: ["<unsafe_all_origins>"] });
  });

  it("tem zero violações CRITICAL ou SERIOUS", async () => {
    const results = await axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
      },
    });

    const critical = results.violations.filter((v) => v.impact === "critical");
    const serious = results.violations.filter((v) => v.impact === "serious");

    if (critical.length > 0 || serious.length > 0) {
      const descriptions = [...critical, ...serious]
        .map(
          (v) =>
            `[${v.impact.toUpperCase()}] ${v.id}: ${v.description}\n  nodes: ${v.nodes.map((n) => n.html).join(", ")}`
        )
        .join("\n");
      throw new Error(
        `axe-core encontrou ${critical.length} CRITICAL e ${serious.length} SERIOUS violações:\n${descriptions}`
      );
    }

    expect(critical).toHaveLength(0);
    expect(serious).toHaveLength(0);
  });

  it("todos os campos de formulário têm <label> associado", () => {
    const inputs = document.querySelectorAll("input, textarea, select");
    inputs.forEach((input) => {
      const id = input.getAttribute("id");
      if (!id) return; // skip inputs without id (checked via axe above)
      const label = document.querySelector(`label[for="${id}"]`);
      const wrappedLabel = input.closest("label");
      const ariaLabel = input.getAttribute("aria-label");
      const ariaLabelledBy = input.getAttribute("aria-labelledby");

      const hasLabel =
        label !== null ||
        wrappedLabel !== null ||
        ariaLabel !== null ||
        ariaLabelledBy !== null;

      if (!hasLabel) {
        throw new Error(
          `Input #${id} não tem label associado (label[for], aria-label, ou aria-labelledby)`
        );
      }
      expect(hasLabel).toBe(true);
    });
  });

  it("todas as secções têm aria-labelledby", () => {
    const sections = document.querySelectorAll("section");
    sections.forEach((section, i) => {
      const labelledBy = section.getAttribute("aria-labelledby");
      const ariaLabel = section.getAttribute("aria-label");
      const hasLabel = labelledBy !== null || ariaLabel !== null;

      if (!hasLabel) {
        throw new Error(`Secção ${i + 1} sem aria-labelledby ou aria-label`);
      }
      expect(hasLabel).toBe(true);

      if (labelledBy) {
        const heading = document.getElementById(labelledBy);
        expect(heading).not.toBeNull();
      }
    });
  });

  it("elementos de status dinâmico têm aria-live ou role=alert", () => {
    const statusIds = [
      "studentsStatus",
      "gradesStatus",
      "matchStats",
      "evolutionStatus",
      "evolutionResult",
      "sendResult",
    ];

    statusIds.forEach((id) => {
      const el = document.getElementById(id);
      expect(el).not.toBeNull();

      const ariaLive = el.getAttribute("aria-live");
      const role = el.getAttribute("role");
      const hasLiveRegion =
        ariaLive !== null || role === "alert" || role === "status";

      if (!hasLiveRegion) {
        throw new Error(
          `Elemento #${id} não tem aria-live ou role=alert/status`
        );
      }
      expect(hasLiveRegion).toBe(true);
    });
  });

  it("não usa tabindex maior que 0", () => {
    const elementsWithTabindex = document.querySelectorAll("[tabindex]");
    elementsWithTabindex.forEach((el) => {
      const tabindex = parseInt(el.getAttribute("tabindex"), 10);
      expect(tabindex).toBeLessThanOrEqual(0);
    });
  });

  it("estrutura HTML semântica: header e main presentes", () => {
    expect(document.querySelector("header")).not.toBeNull();
    expect(document.querySelector("main")).not.toBeNull();
    expect(document.querySelector("h1")).not.toBeNull();
  });

  it("imagem QR Code tem alt descritivo", () => {
    const img = document.getElementById("qrImage");
    expect(img).not.toBeNull();
    const alt = img.getAttribute("alt");
    expect(alt).not.toBeNull();
    expect(alt.trim()).not.toBe("");
  });
});
