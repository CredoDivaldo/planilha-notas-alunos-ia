const crypto = require("crypto");

function requestIdMiddleware(req, res, next) {
  req.id = crypto.randomUUID().slice(0, 8);
  res.setHeader("X-Request-Id", req.id);
  next();
}

module.exports = { requestIdMiddleware };
