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

const validGradesCsv = [
  "numero_estudante,nome,nota,turma",
  "1001,Ana Silva,17,T1",
  "1002,Bruno Costa,13,T1",
].join("\n");

describe("GET /api/grades", () => {
  beforeEach(resetDataFiles);

  it("returns empty list when no grades file exists", async () => {
    const res = await request(app).get("/api/grades");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ grades: [], total: 0 });
  });

  it("returns stored grades after upload", async () => {
    await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(validGradesCsv, "utf8"), "grades.csv");

    const res = await request(app).get("/api/grades");
    expect(res.status).toBe(200);
    expect(res.body.total).toBe(2);
  });
});

describe("POST /api/grades/upload", () => {
  beforeEach(resetDataFiles);

  it("returns 400 when no file is attached", async () => {
    const res = await request(app).post("/api/grades/upload");
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });

  it("parses valid grades CSV and returns correct total", async () => {
    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(validGradesCsv, "utf8"), "grades.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(2);
    expect(res.body.grades).toHaveLength(2);
  });

  it("returns grade with correct normalized fields", async () => {
    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(validGradesCsv, "utf8"), "grades.csv");

    expect(res.status).toBe(200);
    expect(res.body.grades[0]).toMatchObject({
      numero_estudante: "1001",
      nome: "Ana Silva",
      nota: "17",
      turma: "T1",
    });
  });

  it("accepts alias column names (aluno, media)", async () => {
    const csv = [
      "numero_estudante,aluno,media,turma",
      "1001,Ana Silva,18,T1",
    ].join("\n");

    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(csv, "utf8"), "grades.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(1);
    expect(res.body.grades[0].nota).toBe("18");
    expect(res.body.grades[0].nome).toBe("Ana Silva");
  });

  it("filters out rows missing both numero_estudante and nome", async () => {
    const csv = [
      "numero_estudante,nome,nota,turma",
      ",,15,T1",
      "1001,Ana Silva,17,T1",
    ].join("\n");

    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(csv, "utf8"), "grades.csv");

    expect(res.status).toBe(200);
    expect(res.body.total).toBe(1);
  });

  it("returns 400 when CSV is missing identifier column", async () => {
    const csv = ["nome,nota", "Ana Silva,17"].join("\n");

    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(csv, "utf8"), "grades.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/identificador/i);
  });

  it("returns 400 when CSV is missing name column", async () => {
    const csv = ["numero_estudante,nota", "1001,17"].join("\n");

    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(csv, "utf8"), "grades.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/nome/i);
  });

  it("returns 400 when CSV has headers only (no data rows)", async () => {
    const csv = "numero_estudante,nome";

    const res = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(csv, "utf8"), "grades.csv");

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/sem dados/i);
  });
});
