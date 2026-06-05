const fs = require("fs/promises");
const path = require("path");
const request = require("supertest");

jest.mock("../../src/services/evolution-client", () => {
  const actual = jest.requireActual("../../src/services/evolution-client");
  return { ...actual, sendMessage: jest.fn() };
});

const { sendMessage } = require("../../src/services/evolution-client");
const app = require("../../src/app");

const dataDir = path.join(process.cwd(), "data");
const studentsPath = path.join(dataDir, "students.json");
const gradesPath = path.join(dataDir, "grades-last-upload.json");
const matchPath = path.join(dataDir, "match-last.json");

const studentsCsv = [
  "numero_estudante,nome,turma,whatsapp",
  "1001,Ana Silva,T1,244923456789",
].join("\n");

const gradesCsv = [
  "numero_estudante,nome,nota,turma",
  "1001,Ana Silva,17,T1",
].join("\n");

async function resetDataFiles() {
  await fs.mkdir(dataDir, { recursive: true });
  await fs.rm(studentsPath, { force: true });
  await fs.rm(gradesPath, { force: true });
  await fs.rm(matchPath, { force: true });
}

async function setupMatchData() {
  await request(app)
    .post("/api/students/upload")
    .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");
  await request(app)
    .post("/api/grades/upload")
    .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");
  await request(app).post("/api/match/generate");
}

describe("Evolution API error scenarios", () => {
  beforeEach(async () => {
    await resetDataFiles();
    jest.clearAllMocks();
    await setupMatchData();
  });

  it("handles network timeout / connection refused — records falhou and returns 200", async () => {
    sendMessage.mockRejectedValue(new Error("connect ECONNREFUSED 127.0.0.1:8080"));

    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: false });

    expect(res.status).toBe(200);
    expect(res.body.summary.falhas).toBe(1);
    expect(res.body.summary.enviados).toBe(0);
    expect(res.body.results[0].error).toContain("ECONNREFUSED");
  });

  it("handles API non-2xx server error — records error message in result", async () => {
    sendMessage.mockRejectedValue(new Error("Falha HTTP 500"));

    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: false });

    expect(res.status).toBe(200);
    expect(res.body.summary.falhas).toBe(1);
    expect(res.body.results[0].error).toBe("Falha HTTP 500");
  });

  it("handles rate limiting (HTTP 429) — records failure without crashing", async () => {
    sendMessage.mockRejectedValue(new Error("Falha HTTP 429"));

    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: false });

    expect(res.status).toBe(200);
    expect(res.body.summary.falhas).toBe(1);
    expect(res.body.results[0].error).toContain("429");
  });
});
