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

async function setupMatchData() {
  await request(app)
    .post("/api/students/upload")
    .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");
  await request(app)
    .post("/api/grades/upload")
    .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");
  await request(app).post("/api/match/generate");
}

describe("POST /api/send/bulk", () => {
  beforeEach(async () => {
    await resetDataFiles();
    jest.clearAllMocks();
  });

  it("returns 400 when template is missing", async () => {
    await setupMatchData();
    const res = await request(app).post("/api/send/bulk").send({});
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });

  it("returns 400 when template is blank string", async () => {
    await setupMatchData();
    const res = await request(app).post("/api/send/bulk").send({ template: "   " });
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });

  it("returns 400 when no match data exists", async () => {
    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: true });
    expect(res.status).toBe(400);
    expect(res.body.error).toBeDefined();
  });

  it("returns 200 with simulated results in dryRun mode", async () => {
    await setupMatchData();
    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}, nota {{nota}}", dryRun: true });

    expect(res.status).toBe(200);
    expect(res.body.summary).toEqual(
      expect.objectContaining({ total: 2, simulados: 2, enviados: 0, falhas: 0 })
    );
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it("calls sendMessage for each item and reports enviados", async () => {
    await setupMatchData();
    sendMessage.mockResolvedValue({ ok: true });

    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: false });

    expect(res.status).toBe(200);
    expect(res.body.summary.enviados).toBe(2);
    expect(res.body.summary.falhas).toBe(0);
    expect(sendMessage).toHaveBeenCalledTimes(2);
  });

  it("records falhou and continues when sendMessage rejects", async () => {
    await setupMatchData();
    sendMessage
      .mockResolvedValueOnce({ ok: true })
      .mockRejectedValueOnce(new Error("falha simulada"));

    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}", dryRun: false });

    expect(res.status).toBe(200);
    expect(res.body.summary.enviados).toBe(1);
    expect(res.body.summary.falhas).toBe(1);
  });

  it("interpolates all template placeholders correctly in dryRun", async () => {
    await setupMatchData();
    const res = await request(app)
      .post("/api/send/bulk")
      .send({ template: "{{nome}} - {{nota}} - {{turma}} - {{numero_estudante}}", dryRun: true });

    expect(res.status).toBe(200);
    expect(res.body.results[0].message).toBe("Ana Silva - 17 - T1 - 1001");
  });
});
