const express = require("express");
const {
  createInstance,
  connectInstance,
  connectionState,
} = require("../services/evolution-client");
const { asyncHandler } = require("../utils/async-handler");

const router = express.Router();

function withEvolutionErrorHandling(handler) {
  return asyncHandler(async (req, res) => {
    try {
      await handler(req, res);
    } catch (error) {
      error.status = 400;
      throw error;
    }
  });
}

router.post(
  "/instance/create",
  withEvolutionErrorHandling(async (_req, res) => {
    const payload = await createInstance();
    res.json(payload);
  })
);

router.get(
  "/instance/connect",
  withEvolutionErrorHandling(async (_req, res) => {
    const payload = await connectInstance();
    res.json(payload);
  })
);

router.get(
  "/instance/state",
  withEvolutionErrorHandling(async (_req, res) => {
    const payload = await connectionState();
    res.json(payload);
  })
);

module.exports = router;
