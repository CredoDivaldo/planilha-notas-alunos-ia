const fs = require("fs/promises");
const path = require("path");
const request = require("supertest");
const app = require("../../src/app");

const dataDir = path.join(process.cwd(), "data");
const studentsPath = path.join(dataDir, "students.json");
const gradesPath = path.join(dataDir, "grades-last-upload.json");
const matchPath = path.join(dataDir, "match-last.json");

const studentsCsv = [
  "numero_estudante,nome,turma,whatsapp",
  "1001,Ana Silva,T1,244923456789",
  "1002,Bruno Costa,T1,244934567890",
].join("\n");

const gradesCsv = [
  "numero_estudante,nome,nota,turma",
  "1001,Ana Silva,17,T1",
  "1002,Bruno Costa,13,T1",
].join("\n");

async function resetDataFiles() {
  await fs.mkdir(dataDir, { recursive: true });
  await fs.rm(studentsPath, { force: true });
  await fs.rm(gradesPath, { force: true });
  await fs.rm(matchPath, { force: true });
}

describe("GET /api/match", () => {
  beforeEach(resetDataFiles);

  it("returns empty match structure when no data exists", async () => {
    const res = await request(app).get("/api/match");
    expect(res.status).toBe(200);
    expect(res.body.matched).toEqual([]);
    expect(res.body.unmatched).toEqual([]);
  });
});

describe("POST /api/match/generate", () => {
  beforeEach(resetDataFiles);

  it("returns matched results with correct stats when data exists", async () => {
    await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");
    await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");

    const res = await request(app).post("/api/match/generate");

    expect(res.status).toBe(200);
    expect(res.body.stats).toEqual(
      expect.objectContaining({ total_grades: 2, matched: 2, unmatched: 0 })
    );
    expect(res.body.matched).toHaveLength(2);
  });

  it("returns all unmatched when grades have no matching students", async () => {
    await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");

    const res = await request(app).post("/api/match/generate");

    expect(res.status).toBe(200);
    expect(res.body.stats.matched).toBe(0);
    expect(res.body.stats.unmatched).toBe(2);
  });

  it("returns empty stats when no grades exist", async () => {
    const res = await request(app).post("/api/match/generate");

    expect(res.status).toBe(200);
    expect(res.body.stats).toEqual(
      expect.objectContaining({ total_grades: 0, matched: 0, unmatched: 0 })
    );
  });

  it("persists result so GET /api/match reflects the generated match", async () => {
    await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");
    await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");
    await request(app).post("/api/match/generate");

    const res = await request(app).get("/api/match");
    expect(res.status).toBe(200);
    expect(res.body.matched).toHaveLength(2);
  });
});
