const express = require("express");
const multer = require("multer");
const { parseCsv, normalizeGrade } = require("../services/csv-parser");
const { saveGrades, loadGrades } = require("../services/storage");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();
const upload = multer();

router.get(
  "/",
  asyncHandler(async (_req, res) => {
    const grades = await loadGrades();
    res.json({ grades, total: grades.length });
  })
);

router.post(
  "/upload",
  upload.single("file"),
  asyncHandler(async (req, res) => {
    if (!req.file) {
      return res.status(400).json({ error: "Ficheiro CSV é obrigatório" });
    }

    const rows = parseCsv(req.file.buffer);
    const grades = rows
      .map(normalizeGrade)
      .filter((g) => g.numero_estudante || g.nome);

    await saveGrades(grades);
    res.json({ total: grades.length, grades });
  })
);

module.exports = router;
