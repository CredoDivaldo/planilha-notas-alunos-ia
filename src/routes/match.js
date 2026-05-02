const express = require("express");
const { loadStudents, loadGrades, saveMatch, loadMatch } = require("../services/storage");
const { buildMatch } = require("../services/matcher");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();

router.get(
  "/",
  asyncHandler(async (_req, res) => {
    const match = await loadMatch();
    res.json(match);
  })
);

router.post(
  "/generate",
  asyncHandler(async (_req, res) => {
    const students = await loadStudents();
    const grades = await loadGrades();

    const result = buildMatch(students, grades);
    await saveMatch(result);

    res.json(result);
  })
);

module.exports = router;
