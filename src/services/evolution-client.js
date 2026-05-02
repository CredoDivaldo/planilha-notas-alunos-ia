const { normalizePhone } = require("./matcher");

function getConfig() {
  const baseUrl = process.env.EVOLUTION_BASE_URL;
  const apiKey = process.env.EVOLUTION_API_KEY;
  const instance = process.env.EVOLUTION_INSTANCE;
  const integration = process.env.EVOLUTION_INTEGRATION || "WHATSAPP-BAILEYS";

  if (!baseUrl || !apiKey || !instance) {
    throw new Error("Configuração Evolution API incompleta no .env");
  }

  return { baseUrl, apiKey, instance, integration };
}

async function evolutionFetch(path, options = {}) {
  const { baseUrl, apiKey } = getConfig();
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      apikey: apiKey,
      ...(options.headers || {}),
    },
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.message || `Falha HTTP ${response.status}`);
  }

  return payload;
}

async function createInstance() {
  const { instance, integration } = getConfig();
  return evolutionFetch(`/instance/create`, {
    method: "POST",
    body: JSON.stringify({
      instanceName: instance,
      qrcode: true,
      integration,
    }),
  });
}

async function connectInstance() {
  const { instance } = getConfig();
  return evolutionFetch(`/instance/connect/${instance}`, {
    method: "GET",
  });
}

async function connectionState() {
  const { instance } = getConfig();
  return evolutionFetch(`/instance/connectionState/${instance}`, {
    method: "GET",
  });
}

function buildMessage(template, item) {
  return template
    .replaceAll("{{nome}}", item.nome)
    .replaceAll("{{numero_estudante}}", item.numero_estudante)
    .replaceAll("{{turma}}", item.turma)
    .replaceAll("{{nota}}", item.nota);
}

async function sendMessage({ phone, message }) {
  const { instance } = getConfig();
  const number = normalizePhone(phone);

  return evolutionFetch(`/message/sendText/${instance}`, {
    method: "POST",
    body: JSON.stringify({
      number,
      text: message,
    }),
  });
}

module.exports = {
  buildMessage,
  sendMessage,
  createInstance,
  connectInstance,
  connectionState,
};
