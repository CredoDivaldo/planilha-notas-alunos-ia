const fs = require("fs/promises");
const path = require("path");
const request = require("supertest");
const app = require("../../src/app");

const dataDir = path.join(process.cwd(), "data");
const studentsPath = path.join(dataDir, "students.json");
const gradesPath = path.join(dataDir, "grades-last-upload.json");
const matchPath = path.join(dataDir, "match-last.json");

async function resetDataFiles() {
  await fs.mkdir(dataDir, { recursive: true });
  await fs.rm(studentsPath, { force: true });
  await fs.rm(gradesPath, { force: true });
  await fs.rm(matchPath, { force: true });
}

const validCsv = [
  "numero_estudante,nome,turma,whatsapp",
  "1001,Ana Silva,T1,244923456789",
  "1002,Bruno Costa,T1,244934567890",
].join("\n");

describe("GET /api/students", () => {
  beforeEach(resetDataFiles);

  it("returns empty list when no students file exists", async () => {
    const res = await request(app).get("/api/students");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ students: [], total: 0 });
  });

  it("returns stored students after upload", async () => {
    await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(validCsv, "utf8"), "students.csv");

    const res = await request(app).get("/api/students");
    expect(res.status).toBe(200);
    expect(res.body.total).toBe(2);
    expect(res.body.students[0].numero_estudante).toBe("1001");
  });
});

describe("POST /api/students/upload", () => {
  beforeEach(resetDataFiles);

  it("returns 400 when no file is attached", async () => {
    const res = await request(app).post("/api/students/upload");
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });

  it("parses valid CSV and returns correct total", async () => {
    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(validCsv, "utf8"), "students.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(2);
    expect(res.body.students).toHaveLength(2);
  });

  it("returns student with correct normalized fields", async () => {
    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(validCsv, "utf8"), "students.csv");

    expect(res.status).toBe(200);
    expect(res.body.students[0]).toMatchObject({
      numero_estudante: "1001",
      nome: "Ana Silva",
      turma: "T1",
      whatsapp: "244923456789",
    });
  });

  it("filters out rows missing both numero_estudante and nome", async () => {
    const csv = [
      "numero_estudante,nome,turma,whatsapp",
      ",,,",
      "1001,Ana Silva,T1,244923456789",
    ].join("\n");

    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(csv, "utf8"), "students.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(1);
  });

  it("accepts alias column names (numero, aluno, telefone)", async () => {
    const csv = [
      "numero,aluno,turma,telefone",
      "2001,Carlos Dias,T2,244945678901",
    ].join("\n");

    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(csv, "utf8"), "students.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(1);
    expect(res.body.students[0].numero_estudante).toBe("2001");
    expect(res.body.students[0].nome).toBe("Carlos Dias");
  });

  it("returns 400 when CSV is missing identifier column", async () => {
    const csv = ["nome,turma", "Ana Silva,T1"].join("\n");

    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(csv, "utf8"), "students.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/identificador/i);
  });

  it("returns 400 when CSV is missing name column", async () => {
    const csv = ["numero_estudante,turma", "1001,T1"].join("\n");

    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(csv, "utf8"), "students.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/nome/i);
  });

  it("returns 400 when CSV has headers only (no data rows)", async () => {
    const csv = "numero_estudante,nome";

    const res = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(csv, "utf8"), "students.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/sem dados/i);
  });
});
