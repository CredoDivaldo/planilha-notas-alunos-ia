const REQUIRED_VARS = ["EVOLUTION_BASE_URL", "EVOLUTION_API_KEY", "EVOLUTION_INSTANCE", "API_KEY"];

function validateEnv() {
  const missing = REQUIRED_VARS.filter((v) => !process.env[v]);
  if (missing.length > 0) {
    console.error(`[startup] Variáveis de ambiente obrigatórias em falta: ${missing.join(", ")}`);
    process.exit(1);
  }
}

module.exports = { validateEnv, REQUIRED_VARS };
