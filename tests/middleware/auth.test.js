const authMiddleware = require("../../src/middleware/auth");

function mockReqRes(headers = {}) {
  const req = { headers };
  const res = {
    status: jest.fn().mockReturnThis(),
    json: jest.fn().mockReturnThis(),
  };
  const next = jest.fn();
  return { req, res, next };
}

describe("authMiddleware (production mode)", () => {
  const savedNodeEnv = process.env.NODE_ENV;
  const savedApiKey = process.env.API_KEY;

  beforeEach(() => {
    process.env.NODE_ENV = "production";
    process.env.API_KEY = "secret-key-123";
  });

  afterEach(() => {
    process.env.NODE_ENV = savedNodeEnv;
    if (savedApiKey !== undefined) {
      process.env.API_KEY = savedApiKey;
    } else {
      delete process.env.API_KEY;
    }
  });

  it("returns 401 when X-API-Key header is missing", () => {
    const { req, res, next } = mockReqRes({});
    authMiddleware(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
    expect(res.json).toHaveBeenCalledWith({ error: "Não autorizado" });
    expect(next).not.toHaveBeenCalled();
  });

  it("returns 401 when X-API-Key is incorrect", () => {
    const { req, res, next } = mockReqRes({ "x-api-key": "wrong-key" });
    authMiddleware(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
    expect(next).not.toHaveBeenCalled();
  });

  it("calls next() when X-API-Key is correct", () => {
    const { req, res, next } = mockReqRes({ "x-api-key": "secret-key-123" });
    authMiddleware(req, res, next);
    expect(next).toHaveBeenCalled();
    expect(res.status).not.toHaveBeenCalled();
  });

  it("returns 401 when API_KEY env var is not set", () => {
    delete process.env.API_KEY;
    const { req, res, next } = mockReqRes({ "x-api-key": "" });
    authMiddleware(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
  });
});

describe("authMiddleware (test mode)", () => {
  it("calls next() without checking key when NODE_ENV=test", () => {
    const savedEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "test";
    const { req, res, next } = mockReqRes({});
    authMiddleware(req, res, next);
    expect(next).toHaveBeenCalled();
    process.env.NODE_ENV = savedEnv;
  });
});
