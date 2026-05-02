const { parse } = require("csv-parse/sync");

function parseCsv(buffer) {
  const text = buffer.toString("utf8");
  const records = parse(text, {
    columns: true,
    skip_empty_lines: true,
    trim: true,
  });
  return records;
}

function normalizeStudent(raw) {
  return {
    numero_estudante: String(
      raw.numero_estudante || raw.numero || raw.numeroAluno || raw.id || ""
    ).trim(),
    nome: String(raw.nome || raw.aluno || "").trim(),
    turma: String(raw.turma || "").trim(),
    whatsapp: String(raw.whatsapp || raw.telefone || raw.phone || "").trim(),
  };
}

function normalizeGrade(raw) {
  return {
    numero_estudante: String(
      raw.numero_estudante || raw.numero || raw.numeroAluno || raw.id || ""
    ).trim(),
    nome: String(raw.nome || raw.aluno || "").trim(),
    nota: String(raw.nota || raw.media || raw.valor || "").trim(),
    turma: String(raw.turma || "").trim(),
  };
}

module.exports = {
  parseCsv,
  normalizeStudent,
  normalizeGrade,
};
