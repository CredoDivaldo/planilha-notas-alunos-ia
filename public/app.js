const studentsForm = document.getElementById("studentsForm");
const gradesForm = document.getElementById("gradesForm");
const matchBtn = document.getElementById("matchBtn");
const sendBtn = document.getElementById("sendBtn");

const studentsStatus = document.getElementById("studentsStatus");
const gradesStatus = document.getElementById("gradesStatus");
const matchStats = document.getElementById("matchStats");
const matchTableBody = document.querySelector("#matchTable tbody");
const sendResult = document.getElementById("sendResult");

const createInstanceBtn = document.getElementById("createInstanceBtn");
const connectInstanceBtn = document.getElementById("connectInstanceBtn");
const stateInstanceBtn = document.getElementById("stateInstanceBtn");
const evolutionStatus = document.getElementById("evolutionStatus");
const evolutionResult = document.getElementById("evolutionResult");
const qrImage = document.getElementById("qrImage");

async function uploadCsv(inputId, endpoint) {
  const fileInput = document.getElementById(inputId);
  if (!fileInput.files.length) {
    throw new Error("Selecciona um ficheiro CSV");
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const response = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Falha no upload");
  }

  return payload;
}

studentsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  studentsStatus.textContent = "A importar...";

  try {
    const payload = await uploadCsv("studentsFile", "/api/students/upload");
    studentsStatus.textContent = `Estudantes importados: ${payload.total}`;
  } catch (error) {
    studentsStatus.textContent = `Erro: ${error.message}`;
  }
});

gradesForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  gradesStatus.textContent = "A importar...";

  try {
    const payload = await uploadCsv("gradesFile", "/api/grades/upload");
    gradesStatus.textContent = `Notas importadas: ${payload.total}`;
  } catch (error) {
    gradesStatus.textContent = `Erro: ${error.message}`;
  }
});

matchBtn.addEventListener("click", async () => {
  matchStats.textContent = "A gerar match...";
  matchTableBody.innerHTML = "";

  const response = await fetch("/api/match/generate", { method: "POST" });
  const payload = await response.json();

  if (!response.ok) {
    matchStats.textContent = payload.error || "Erro ao gerar match";
    return;
  }

  matchStats.textContent = `Total notas: ${payload.stats.total_grades} | Matched: ${payload.stats.matched} | Sem match: ${payload.stats.unmatched} | WhatsApp inválido: ${payload.stats.invalidPhones}`;

  payload.matched.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.numero_estudante}</td>
      <td>${item.nome}</td>
      <td>${item.turma}</td>
      <td>${item.whatsapp}</td>
      <td>${item.nota}</td>
    `;
    matchTableBody.appendChild(tr);
  });
});

async function callEvolution(endpoint, method = "GET") {
  const response = await fetch(endpoint, { method });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Falha na Evolution API");
  }

  evolutionResult.textContent = JSON.stringify(payload, null, 2);
  return payload;
}

function setQrFromPayload(payload) {
  const qrcode = payload?.qrcode?.base64 || payload?.base64;
  if (qrcode) {
    qrImage.src = qrcode;
    qrImage.style.display = "block";
    return true;
  }
  return false;
}

async function waitForQr(maxAttempts = 20, delayMs = 1500) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    evolutionStatus.textContent = `A aguardar QR... tentativa ${attempt}/${maxAttempts}`;

    const statePayload = await callEvolution("/api/evolution/instance/state", "GET");
    const state = statePayload?.instance?.state;

    if (state === "open") {
      evolutionStatus.textContent = "Instância conectada (estado open).";
      return;
    }

    const connectPayload = await callEvolution("/api/evolution/instance/connect", "GET");
    if (setQrFromPayload(connectPayload)) {
      evolutionStatus.textContent = "QR gerado. Escaneia no WhatsApp.";
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  evolutionStatus.textContent = "Sem QR após várias tentativas. Verifica logs da Evolution e tenta novamente.";
}

createInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A criar instância...";
    const payload = await callEvolution("/api/evolution/instance/create", "POST");
    if (setQrFromPayload(payload)) {
      evolutionStatus.textContent = "QR gerado no create. Escaneia no WhatsApp.";
      return;
    }
    await waitForQr();
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

connectInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A solicitar QR...";
    const payload = await callEvolution("/api/evolution/instance/connect", "GET");
    if (setQrFromPayload(payload)) {
      evolutionStatus.textContent = "QR gerado. Escaneia no WhatsApp.";
      return;
    }
    await waitForQr();
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

stateInstanceBtn.addEventListener("click", async () => {
  try {
    evolutionStatus.textContent = "A consultar estado...";
    const payload = await callEvolution("/api/evolution/instance/state", "GET");
    const state = payload?.instance?.state || "desconhecido";
    evolutionStatus.textContent = `Estado actual: ${state}`;
  } catch (error) {
    evolutionStatus.textContent = `Erro: ${error.message}`;
  }
});

sendBtn.addEventListener("click", async () => {
  const dryRun = document.getElementById("dryRun").checked;
  const confirmReal = document.getElementById("confirmReal").checked;
  const template = document.getElementById("template").value;

  if (!dryRun && !confirmReal) {
    alert("Marca a confirmação para envio real ou usa simulação.");
    return;
  }

  sendResult.textContent = "A enviar...";

  const response = await fetch("/api/send/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template, dryRun }),
  });

  const payload = await response.json();
  sendResult.textContent = JSON.stringify(payload, null, 2);
});
