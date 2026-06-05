const express = require("express");
const multer = require("multer");
const { parseCsv, normalizeStudent } = require("../services/csv-parser");
const { saveStudents, loadStudents } = require("../services/storage");
const { validateStudentsCsv, checkFileSize } = require("../services/csv-validator");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();
const upload = multer({ limits: { fileSize: 2 * 1024 * 1024 } });

router.get(
  "/",
  asyncHandler(async (_req, res) => {
    const students = await loadStudents();
    res.json({ students, total: students.length });
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

    const validation = validateStudentsCsv(headers, rows);
    if (!validation.valid) {
      return res.status(400).json({ error: validation.error });
    }

    const students = rows
      .map(normalizeStudent)
      .filter((s) => s.numero_estudante && s.nome);

    await saveStudents(students);
    res.json({ total: students.length, students });
  })
);

module.exports = router;
