const express = require("express");
const { loadMatch } = require("../services/storage");
const { buildMessage, sendMessage } = require("../services/evolution-client");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();

router.post(
  "/bulk",
  asyncHandler(async (req, res) => {
    const { template, dryRun = false } = req.body || {};

    if (!template || !String(template).trim()) {
      return res.status(400).json({ error: "Template de mensagem é obrigatório" });
    }

    const match = await loadMatch();
    const items = match.matched || [];

    if (!items.length) {
      return res.status(400).json({ error: "Sem dados matched para envio" });
    }

    const results = [];

    for (const item of items) {
      const text = buildMessage(template, item);

      if (dryRun) {
        results.push({
          numero_estudante: item.numero_estudante,
          nome: item.nome,
          whatsapp: item.whatsapp,
          status: "simulado",
          message: text,
        });
        continue;
      }

      try {
        const apiResponse = await sendMessage({ phone: item.whatsapp, message: text });
        results.push({
          numero_estudante: item.numero_estudante,
          nome: item.nome,
          whatsapp: item.whatsapp,
          status: "enviado",
          apiResponse,
        });
      } catch (error) {
        results.push({
          numero_estudante: item.numero_estudante,
          nome: item.nome,
          whatsapp: item.whatsapp,
          status: "falhou",
          error: error.message,
        });
      }
    }

    const summary = {
      total: results.length,
      enviados: results.filter((r) => r.status === "enviado").length,
      falhas: results.filter((r) => r.status === "falhou").length,
      simulados: results.filter((r) => r.status === "simulado").length,
    };

    res.json({ summary, results });
  })
);

module.exports = router;
