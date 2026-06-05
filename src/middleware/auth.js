const crypto = require("crypto");

function authMiddleware(req, res, next) {
  if (process.env.NODE_ENV === "test") return next();

  const expected = process.env.API_KEY || "";
  const provided = req.headers["x-api-key"] || "";

  if (
    !expected ||
    provided.length !== expected.length ||
    !crypto.timingSafeEqual(Buffer.from(provided), Buffer.from(expected))
  ) {
    return res.status(401).json({ error: "Não autorizado" });
  }

  next();
}

module.exports = authMiddleware;
