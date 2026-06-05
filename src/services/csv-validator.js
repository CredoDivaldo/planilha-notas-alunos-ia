const IDENTIFIER_COLS = ["numero_estudante", "numero", "numeroAluno", "id"];
const NAME_COLS = ["nome", "aluno"];
const MAX_FILE_SIZE = 2 * 1024 * 1024;

function hasAnyCol(headers, candidates) {
  return candidates.some((c) => headers.includes(c));
}

function validateStudentsCsv(headers, rows) {
  if (!rows || rows.length === 0) {
    return { valid: false, error: "Ficheiro CSV sem dados" };
  }
  if (!hasAnyCol(headers, IDENTIFIER_COLS)) {
    return { valid: false, error: `Coluna de identificador em falta. Esperado: ${IDENTIFIER_COLS.join(", ")}` };
  }
  if (!hasAnyCol(headers, NAME_COLS)) {
    return { valid: false, error: `Coluna de nome em falta. Esperado: ${NAME_COLS.join(", ")}` };
  }
  return { valid: true, error: null };
}

function validateGradesCsv(headers, rows) {
  if (!rows || rows.length === 0) {
    return { valid: false, error: "Ficheiro CSV sem dados" };
  }
  if (!hasAnyCol(headers, IDENTIFIER_COLS)) {
    return { valid: false, error: `Coluna de identificador em falta. Esperado: ${IDENTIFIER_COLS.join(", ")}` };
  }
  if (!hasAnyCol(headers, NAME_COLS)) {
    return { valid: false, error: `Coluna de nome em falta. Esperado: ${NAME_COLS.join(", ")}` };
  }
  return { valid: true, error: null };
}

function checkFileSize(fileSize) {
  if (fileSize > MAX_FILE_SIZE) {
    return { valid: false, error: `Ficheiro demasiado grande. Máximo: ${MAX_FILE_SIZE / 1024 / 1024} MB` };
  }
  return { valid: true, error: null };
}

module.exports = { validateStudentsCsv, validateGradesCsv, checkFileSize };
