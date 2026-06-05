const { buildMatch, normalizePhone } = require("../../src/services/matcher");

const students = [
  { numero_estudante: "1001", nome: "Ana Silva", turma: "T1", whatsapp: "244923456789" },
  { numero_estudante: "1002", nome: "Bruno Costa", turma: "T1", whatsapp: "244934567890" },
];

const grades = [
  { numero_estudante: "1001", nome: "Ana Silva", nota: "17" },
  { numero_estudante: "1002", nome: "Bruno Costa", nota: "13" },
];

describe("buildMatch", () => {
  it("matches all grades by numero_estudante", () => {
    const result = buildMatch(students, grades);
    expect(result.matched).toHaveLength(2);
    expect(result.stats.matched).toBe(2);
    expect(result.stats.unmatched).toBe(0);
  });

  it("falls back to name matching when numero_estudante is absent in grade", () => {
    const gradesNoNum = [{ nome: "Ana Silva", nota: "17" }];
    const result = buildMatch(students, gradesNoNum);
    expect(result.matched).toHaveLength(1);
    expect(result.matched[0].nome).toBe("Ana Silva");
  });

  it("adds to unmatched when grade has no matching student", () => {
    const unknownGrades = [{ numero_estudante: "9999", nome: "Desconhecido", nota: "10" }];
    const result = buildMatch(students, unknownGrades);
    expect(result.unmatched).toHaveLength(1);
    expect(result.stats.unmatched).toBe(1);
  });

  it("adds to invalidPhones when matched student has a short phone number", () => {
    const studentsWithBadPhone = [
      { numero_estudante: "1001", nome: "Ana Silva", turma: "T1", whatsapp: "123" },
    ];
    const result = buildMatch(studentsWithBadPhone, [grades[0]]);
    expect(result.invalidPhones).toHaveLength(1);
    expect(result.stats.invalidPhones).toBe(1);
  });

  it("returns all unmatched when students array is empty", () => {
    const result = buildMatch([], grades);
    expect(result.matched).toHaveLength(0);
    expect(result.unmatched).toHaveLength(2);
  });

  it("returns empty result when grades array is empty", () => {
    const result = buildMatch(students, []);
    expect(result.matched).toHaveLength(0);
    expect(result.unmatched).toHaveLength(0);
    expect(result.stats.total_grades).toBe(0);
  });

  it("counts all three buckets correctly in a mixed dataset", () => {
    const mixedStudents = [
      { numero_estudante: "1001", nome: "Ana", turma: "T1", whatsapp: "244923456789" },
      { numero_estudante: "1002", nome: "Bruno", turma: "T1", whatsapp: "123" },
    ];
    const mixedGrades = [
      { numero_estudante: "1001", nota: "17" },
      { numero_estudante: "1002", nota: "13" },
      { numero_estudante: "9999", nota: "10" },
    ];
    const result = buildMatch(mixedStudents, mixedGrades);
    expect(result.stats.total_grades).toBe(3);
    expect(result.stats.matched).toBe(1);
    expect(result.stats.unmatched).toBe(1);
    expect(result.stats.invalidPhones).toBe(1);
  });

  it("is case-insensitive and accent-insensitive for name matching", () => {
    const studentsWithAccent = [
      { numero_estudante: "2001", nome: "João Ferreira", turma: "T2", whatsapp: "244956789012" },
    ];
    const gradesNoAccent = [{ nome: "joao ferreira", nota: "15" }];
    const result = buildMatch(studentsWithAccent, gradesNoAccent);
    expect(result.matched).toHaveLength(1);
  });
});

describe("normalizePhone", () => {
  it("strips spaces and country code prefix symbols", () => {
    expect(normalizePhone("+244 923 456 789")).toBe("244923456789");
  });

  it("strips dashes and parentheses", () => {
    expect(normalizePhone("(244) 923-456-789")).toBe("244923456789");
  });

  it("returns empty string for null", () => {
    expect(normalizePhone(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(normalizePhone(undefined)).toBe("");
  });

  it("returns pure digit string unchanged", () => {
    expect(normalizePhone("244923456789")).toBe("244923456789");
  });
});
