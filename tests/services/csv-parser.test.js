const { parseCsv, normalizeStudent, normalizeGrade } = require("../../src/services/csv-parser");

describe("parseCsv", () => {
  it("parses a well-formed CSV into an array of objects", () => {
    const csv = [
      "numero_estudante,nome,turma",
      "1001,Ana Silva,T1",
      "1002,Bruno Costa,T1",
    ].join("\n");

    const result = parseCsv(Buffer.from(csv, "utf8"));
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ numero_estudante: "1001", nome: "Ana Silva", turma: "T1" });
  });

  it("returns empty array when CSV has only headers", () => {
    const csv = "numero_estudante,nome,turma\n";
    const result = parseCsv(Buffer.from(csv, "utf8"));
    expect(result).toHaveLength(0);
  });

  it("trims leading and trailing whitespace from values", () => {
    const csv = ["numero_estudante,nome", "  1001  ,  Ana Silva  "].join("\n");
    const result = parseCsv(Buffer.from(csv, "utf8"));
    expect(result[0].numero_estudante).toBe("1001");
    expect(result[0].nome).toBe("Ana Silva");
  });

  it("skips empty lines", () => {
    const csv = ["numero_estudante,nome,turma", "", "1001,Ana,T1", ""].join("\n");
    const result = parseCsv(Buffer.from(csv, "utf8"));
    expect(result).toHaveLength(1);
  });
});

describe("normalizeStudent", () => {
  it("maps direct column names to canonical fields", () => {
    const raw = { numero_estudante: "1001", nome: "Ana", turma: "T1", whatsapp: "244923456789" };
    expect(normalizeStudent(raw)).toEqual({
      numero_estudante: "1001",
      nome: "Ana",
      turma: "T1",
      whatsapp: "244923456789",
    });
  });

  it("maps alias: numero → numero_estudante, aluno → nome, telefone → whatsapp", () => {
    const raw = { numero: "2001", aluno: "Carlos", turma: "T2", telefone: "244945678901" };
    const result = normalizeStudent(raw);
    expect(result.numero_estudante).toBe("2001");
    expect(result.nome).toBe("Carlos");
    expect(result.whatsapp).toBe("244945678901");
  });

  it("maps alias: phone → whatsapp", () => {
    const raw = { numero_estudante: "1001", nome: "Ana", turma: "T1", phone: "244923456789" };
    expect(normalizeStudent(raw).whatsapp).toBe("244923456789");
  });

  it("returns empty strings for missing optional fields", () => {
    const raw = { numero_estudante: "1001", nome: "Ana" };
    const result = normalizeStudent(raw);
    expect(result.turma).toBe("");
    expect(result.whatsapp).toBe("");
  });
});

describe("normalizeGrade", () => {
  it("maps direct column names to canonical fields", () => {
    const raw = { numero_estudante: "1001", nome: "Ana", nota: "17", turma: "T1" };
    expect(normalizeGrade(raw)).toEqual({
      numero_estudante: "1001",
      nome: "Ana",
      nota: "17",
      turma: "T1",
    });
  });

  it("maps alias: aluno → nome, media → nota", () => {
    const raw = { numero_estudante: "1001", aluno: "Bruno", media: "15", turma: "T1" };
    const result = normalizeGrade(raw);
    expect(result.nome).toBe("Bruno");
    expect(result.nota).toBe("15");
  });

  it("maps alias: valor → nota", () => {
    const raw = { numero_estudante: "1001", nome: "Ana", valor: "18", turma: "T1" };
    expect(normalizeGrade(raw).nota).toBe("18");
  });

  it("returns empty string for missing nota", () => {
    const raw = { numero_estudante: "1001", nome: "Ana" };
    expect(normalizeGrade(raw).nota).toBe("");
  });
});
