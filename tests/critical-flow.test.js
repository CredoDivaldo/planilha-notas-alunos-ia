const fs = require("fs/promises");
const path = require("path");
const request = require("supertest");

jest.mock("../src/services/evolution-client", () => {
  const actual = jest.requireActual("../src/services/evolution-client");
  return {
    ...actual,
    sendMessage: jest.fn(),
  };
});

const { sendMessage } = require("../src/services/evolution-client");
const app = require("../src/app");

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

describe("Fluxo crítico upload -> match -> send", () => {
  beforeEach(async () => {
    await resetDataFiles();
    jest.clearAllMocks();
  });

  it("cobre upload de estudantes, upload de notas, geração de match e envio dryRun", async () => {
    const studentsResponse = await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");

    expect(studentsResponse.status).toBe(200);
    expect(studentsResponse.body.total).toBe(2);

    const gradesResponse = await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");

    expect(gradesResponse.status).toBe(200);
    expect(gradesResponse.body.total).toBe(2);

    const matchResponse = await request(app).post("/api/match/generate");

    expect(matchResponse.status).toBe(200);
    expect(matchResponse.body.stats).toEqual(
      expect.objectContaining({
        total_grades: 2,
        matched: 2,
      })
    );

    const dryRunResponse = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}, nota {{nota}}", dryRun: true });

    expect(dryRunResponse.status).toBe(200);
    expect(dryRunResponse.body.summary).toEqual(
      expect.objectContaining({
        total: 2,
        simulados: 2,
        enviados: 0,
        falhas: 0,
      })
    );
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it("cobre envio real com falha simulada", async () => {
    await request(app)
      .post("/api/students/upload")
      .attach("file", Buffer.from(studentsCsv, "utf8"), "students.csv");

    await request(app)
      .post("/api/grades/upload")
      .attach("file", Buffer.from(gradesCsv, "utf8"), "grades.csv");

    await request(app).post("/api/match/generate");

    sendMessage
      .mockResolvedValueOnce({ ok: true })
      .mockRejectedValueOnce(new Error("falha simulada"));

    const response = await request(app)
      .post("/api/send/bulk")
      .send({ template: "Olá {{nome}}, nota {{nota}}", dryRun: false });

    expect(response.status).toBe(200);
    expect(response.body.summary).toEqual(
      expect.objectContaining({
        total: 2,
        enviados: 1,
        falhas: 1,
        simulados: 0,
      })
    );

    expect(sendMessage).toHaveBeenCalledTimes(2);
  });
});
