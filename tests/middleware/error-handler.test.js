const request = require("supertest");
const express = require("express");
const { requestIdMiddleware } = require("../../src/middleware/request-id");

function createTestApp(routeHandler) {
  const app = express();
  app.use(requestIdMiddleware);
  app.get("/test", routeHandler);
  app.use((error, req, res, _next) => {
    console.error(`[${req.id || "unknown"}] Erro na API:`, error);
    const status = Number(error?.status) || 500;
    const message = status >= 500 ? "Erro interno" : error.message || "Erro na requisição";
    res.status(status).json({ error: message });
  });
  return app;
}

describe("Global error handler", () => {
  it("returns { error: 'Erro interno' } for unhandled 500 errors — no stack trace", async () => {
    const app = createTestApp((_req, _res, next) => {
      const err = new Error("internal details that should not leak");
      next(err);
    });

    const res = await request(app).get("/test");
    expect(res.status).toBe(500);
    expect(res.body).toEqual({ error: "Erro interno" });
    expect(JSON.stringify(res.body)).not.toContain("internal details");
  });

  it("returns explicit user-facing message for 4xx errors", async () => {
    const app = createTestApp((_req, _res, next) => {
      const err = new Error("Ficheiro CSV é obrigatório");
      err.status = 400;
      next(err);
    });

    const res = await request(app).get("/test");
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("Ficheiro CSV é obrigatório");
  });

  it("includes X-Request-Id header in every response", async () => {
    const app = createTestApp((_req, res) => {
      res.json({ ok: true });
    });

    const res = await request(app).get("/test");
    expect(res.headers["x-request-id"]).toBeDefined();
    expect(res.headers["x-request-id"]).toHaveLength(8);
  });

  it("includes X-Request-Id header in error responses", async () => {
    const app = createTestApp((_req, _res, next) => {
      next(new Error("crash"));
    });

    const res = await request(app).get("/test");
    expect(res.status).toBe(500);
    expect(res.headers["x-request-id"]).toBeDefined();
  });
});
