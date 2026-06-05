const { validateStudentsCsv, validateGradesCsv, checkFileSize } = require("../../src/services/csv-validator");

const MAX_FILE_SIZE = 2 * 1024 * 1024;

describe("validateStudentsCsv", () => {
  it("returns invalid when identifier column is missing", () => {
    const result = validateStudentsCsv(["nome", "turma"], [{ nome: "Ana" }]);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/identificador/i);
  });

  it("returns invalid when name column is missing", () => {
    const result = validateStudentsCsv(["numero_estudante", "turma"], [{ numero_estudante: "1" }]);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/nome/i);
  });

  it("returns invalid when rows array is empty", () => {
    const result = validateStudentsCsv(["numero_estudante", "nome"], []);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/sem dados/i);
  });

  it("accepts numero_estudante as identifier column", () => {
    const result = validateStudentsCsv(["numero_estudante", "nome"], [{ numero_estudante: "1", nome: "Ana" }]);
    expect(result.valid).toBe(true);
  });

  it("accepts alias columns (numero, aluno)", () => {
    const result = validateStudentsCsv(["numero", "aluno"], [{ numero: "1", aluno: "Ana" }]);
    expect(result.valid).toBe(true);
  });

  it("accepts id + nome as valid headers", () => {
    const result = validateStudentsCsv(["id", "nome"], [{ id: "1", nome: "Ana" }]);
    expect(result.valid).toBe(true);
  });
});

describe("validateGradesCsv", () => {
  it("returns invalid when identifier column is missing", () => {
    const result = validateGradesCsv(["nome", "nota"], [{ nome: "Ana", nota: "17" }]);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/identificador/i);
  });

  it("returns invalid when name column is missing", () => {
    const result = validateGradesCsv(["numero_estudante", "nota"], [{ numero_estudante: "1" }]);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/nome/i);
  });

  it("returns invalid when rows array is empty", () => {
    const result = validateGradesCsv(["numero_estudante", "nome"], []);
    expect(result.valid).toBe(false);
  });

  it("accepts valid grades headers", () => {
    const result = validateGradesCsv(["numero_estudante", "nome", "nota"], [{ numero_estudante: "1", nome: "Ana", nota: "17" }]);
    expect(result.valid).toBe(true);
  });
});

describe("checkFileSize", () => {
  it("returns invalid when file exceeds 2 MB", () => {
    const result = checkFileSize(MAX_FILE_SIZE + 1);
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/demasiado grande/i);
  });

  it("returns valid when file is exactly 2 MB", () => {
    const result = checkFileSize(MAX_FILE_SIZE);
    expect(result.valid).toBe(true);
  });

  it("returns valid when file is below limit", () => {
    const result = checkFileSize(1024);
    expect(result.valid).toBe(true);
  });
});
