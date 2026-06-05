const { validateEnv, REQUIRED_VARS } = require("../../src/config/validate-env");

describe("validateEnv", () => {
  const originalEnv = {};

  beforeEach(() => {
    REQUIRED_VARS.forEach((v) => {
      originalEnv[v] = process.env[v];
      delete process.env[v];
    });
    jest.spyOn(process, "exit").mockImplementation(() => {
      throw new Error("process.exit called");
    });
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    REQUIRED_VARS.forEach((v) => {
      if (originalEnv[v] !== undefined) {
        process.env[v] = originalEnv[v];
      } else {
        delete process.env[v];
      }
    });
    jest.restoreAllMocks();
  });

  it("exits with code 1 when all required vars are missing", () => {
    expect(() => validateEnv()).toThrow("process.exit called");
    expect(process.exit).toHaveBeenCalledWith(1);
  });

  it("logs all missing vars in a single error message", () => {
    expect(() => validateEnv()).toThrow();
    const errorMessage = console.error.mock.calls[0][0];
    REQUIRED_VARS.forEach((v) => {
      expect(errorMessage).toContain(v);
    });
  });

  it("exits with code 1 when one var is missing", () => {
    process.env.EVOLUTION_BASE_URL = "http://localhost:8080";
    process.env.EVOLUTION_API_KEY = "test-key";

    expect(() => validateEnv()).toThrow("process.exit called");
    expect(process.exit).toHaveBeenCalledWith(1);
    expect(console.error.mock.calls[0][0]).toContain("EVOLUTION_INSTANCE");
  });

  it("does not exit when all required vars are set", () => {
    process.env.EVOLUTION_BASE_URL = "http://localhost:8080";
    process.env.EVOLUTION_API_KEY = "test-key";
    process.env.EVOLUTION_INSTANCE = "test-instance";
    process.env.API_KEY = "secret";

    expect(() => validateEnv()).not.toThrow();
    expect(process.exit).not.toHaveBeenCalled();
  });
});
