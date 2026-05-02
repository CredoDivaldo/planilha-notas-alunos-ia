function normalizeName(name) {
  return String(name || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

function normalizePhone(phone) {
  return String(phone || "").replace(/\D/g, "");
}

function isValidPhone(phone) {
  const cleaned = normalizePhone(phone);
  return cleaned.length >= 10 && cleaned.length <= 15;
}

function buildMatch(students, grades) {
  const byNumber = new Map();
  const byName = new Map();

  students.forEach((student) => {
    byNumber.set(student.numero_estudante, student);
    byName.set(normalizeName(student.nome), student);
  });

  const matched = [];
  const unmatched = [];
  const invalidPhones = [];

  for (const grade of grades) {
    let student = null;

    if (grade.numero_estudante && byNumber.has(grade.numero_estudante)) {
      student = byNumber.get(grade.numero_estudante);
    } else if (grade.nome && byName.has(normalizeName(grade.nome))) {
      student = byName.get(normalizeName(grade.nome));
    }

    if (!student) {
      unmatched.push(grade);
      continue;
    }

    const item = {
      numero_estudante: student.numero_estudante,
      nome: student.nome,
      turma: student.turma,
      whatsapp: student.whatsapp,
      nota: grade.nota,
    };

    if (!isValidPhone(student.whatsapp)) {
      invalidPhones.push(item);
      continue;
    }

    matched.push(item);
  }

  return {
    matched,
    unmatched,
    invalidPhones,
    stats: {
      total_grades: grades.length,
      matched: matched.length,
      unmatched: unmatched.length,
      invalidPhones: invalidPhones.length,
    },
  };
}

module.exports = {
  buildMatch,
  normalizePhone,
};
