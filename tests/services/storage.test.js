const fs = require("fs/promises");
const path = require("path");

jest.mock("fs/promises");

const { saveStudents } = require("../../src/services/storage");

describe("writeJson (atomic write)", () => {
  const dataDir = path.join(process.cwd(), "data");
  const studentsPath = path.join(dataDir, "students.json");
  const tmpPath = `${studentsPath}.tmp`;

  beforeEach(() => {
    jest.clearAllMocks();
    fs.mkdir.mockResolvedValue(undefined);
    fs.writeFile.mockResolvedValue(undefined);
    fs.rename.mockResolvedValue(undefined);
    fs.rm.mockResolvedValue(undefined);
    fs.readFile.mockResolvedValue(JSON.stringify([]));
  });

  it("writes to a .tmp file then renames to the target", async () => {
    await saveStudents([{ numero_estudante: "1001", nome: "Ana" }]);

    expect(fs.writeFile).toHaveBeenCalledWith(
      tmpPath,
      expect.any(String),
      "utf8"
    );
    expect(fs.rename).toHaveBeenCalledWith(tmpPath, studentsPath);
  });

  it("calls rename after writeFile (correct order)", async () => {
    const callOrder = [];
    fs.writeFile.mockImplementation(() => {
      callOrder.push("writeFile");
      return Promise.resolve();
    });
    fs.rename.mockImplementation(() => {
      callOrder.push("rename");
      return Promise.resolve();
    });

    await saveStudents([]);

    expect(callOrder).toEqual(["writeFile", "rename"]);
  });

  it("cleans up .tmp file and rethrows when rename fails", async () => {
    const renameError = new Error("rename failed");
    fs.rename.mockRejectedValue(renameError);

    await expect(saveStudents([])).rejects.toThrow("rename failed");
    expect(fs.rm).toHaveBeenCalledWith(tmpPath, { force: true });
  });

  it("cleans up .tmp file and rethrows when writeFile fails", async () => {
    const writeError = new Error("disk full");
    fs.writeFile.mockRejectedValue(writeError);

    await expect(saveStudents([])).rejects.toThrow("disk full");
    expect(fs.rm).toHaveBeenCalledWith(tmpPath, { force: true });
  });

  it("does not leave a .tmp file after a successful write", async () => {
    await saveStudents([{ numero_estudante: "1001", nome: "Ana" }]);

    expect(fs.rm).not.toHaveBeenCalled();
  });
});
