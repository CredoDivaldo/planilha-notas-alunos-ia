const fs = require("fs/promises");
const path = require("path");

const dataDir = path.join(process.cwd(), "data");
const studentsPath = path.join(dataDir, "students.json");
const gradesPath = path.join(dataDir, "grades-last-upload.json");
const matchPath = path.join(dataDir, "match-last.json");

async function ensureDir() {
  await fs.mkdir(dataDir, { recursive: true });
}

async function readJson(filePath, fallback = null) {
  try {
    const content = await fs.readFile(filePath, "utf8");
    return JSON.parse(content);
  } catch (error) {
    if (error.code === "ENOENT") {
      return fallback;
    }
    throw error;
  }
}

async function writeJson(filePath, payload) {
  await ensureDir();
  await fs.writeFile(filePath, JSON.stringify(payload, null, 2), "utf8");
}

async function saveStudents(students) {
  await writeJson(studentsPath, students);
}

async function loadStudents() {
  return readJson(studentsPath, []);
}

async function saveGrades(grades) {
  await writeJson(gradesPath, grades);
}

async function loadGrades() {
  return readJson(gradesPath, []);
}

async function saveMatch(matchResult) {
  await writeJson(matchPath, matchResult);
}

async function loadMatch() {
  return readJson(matchPath, { matched: [], unmatched: [], invalidPhones: [] });
}

module.exports = {
  saveStudents,
  loadStudents,
  saveGrades,
  loadGrades,
  saveMatch,
  loadMatch,
};
