const express = require("express");
const multer = require("multer");
const { parseCsv, normalizeGrade } = require("../services/csv-parser");
const { saveGrades, loadGrades } = require("../services/storage");
const { validateGradesCsv, checkFileSize } = require("../services/csv-validator");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();
const upload = multer({ limits: { fileSize: 2 * 1024 * 1024 } });

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

    const sizeCheck = checkFileSize(req.file.size);
    if (!sizeCheck.valid) {
      return res.status(400).json({ error: sizeCheck.error });
    }

    const rows = parseCsv(req.file.buffer);
    const headers = rows.length > 0 ? Object.keys(rows[0]) : [];

    const validation = validateGradesCsv(headers, rows);
    if (!validation.valid) {
      return res.status(400).json({ error: validation.error });
    }

    const grades = rows
      .map(normalizeGrade)
      .filter((g) => g.numero_estudante || g.nome);

    await saveGrades(grades);
    res.json({ total: grades.length, grades });
  })
);

module.exports = router;
