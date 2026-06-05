const request = require("supertest");
const express = require("express");
const { rateLimit } = require("express-rate-limit");

function createLimitedApp(max = 3) {
  const app = express();
  const limiter = rateLimit({
    windowMs: 60 * 1000,
    max,
    standardHeaders: "draft-6",
    legacyHeaders: false,
    handler: (_req, res) => {
      res.status(429).json({ error: "Demasiadas requisições. Tente novamente em breve." });
    },
  });
  app.use("/api/", limiter);
  app.get("/api/test", (_req, res) => res.json({ ok: true }));
  app.get("/public/test", (_req, res) => res.json({ ok: true }));
  return app;
}

describe("Rate limiting middleware", () => {
  it("returns 429 after exceeding the configured limit", async () => {
    const app = createLimitedApp(3);

    for (let i = 0; i < 3; i++) {
      const res = await request(app).get("/api/test");
      expect(res.status).toBe(200);
    }

    const res = await request(app).get("/api/test");
    expect(res.status).toBe(429);
    expect(res.body.error).toBe("Demasiadas requisições. Tente novamente em breve.");
  });

  it("does not apply rate limiting to non-api routes", async () => {
    const app = createLimitedApp(2);

    for (let i = 0; i < 5; i++) {
      const res = await request(app).get("/public/test");
      expect(res.status).toBe(200);
    }
  });

  it("includes RateLimit headers on API responses", async () => {
    const app = createLimitedApp(100);
    const res = await request(app).get("/api/test");
    expect(res.status).toBe(200);
    expect(res.headers["ratelimit-limit"]).toBeDefined();
    expect(res.headers["ratelimit-remaining"]).toBeDefined();
    expect(res.headers["ratelimit-reset"]).toBeDefined();
  });
});
