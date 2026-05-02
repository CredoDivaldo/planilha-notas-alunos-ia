const express = require("express");
const path = require("path");
const cors = require("cors");

const studentsRoutes = require("./routes/students");
const gradesRoutes = require("./routes/grades");
const matchRoutes = require("./routes/match");
const sendRoutes = require("./routes/send");
const evolutionRoutes = require("./routes/evolution");

const app = express();

app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(process.cwd(), "public")));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "planilha-notas-mvp" });
});

app.use("/api/students", studentsRoutes);
app.use("/api/grades", gradesRoutes);
app.use("/api/match", matchRoutes);
app.use("/api/send", sendRoutes);
app.use("/api/evolution", evolutionRoutes);

app.use((error, _req, res, _next) => {
  console.error("Erro na API:", error);
  const status = Number(error?.status) || 500;
  const message = status >= 500 ? "Erro interno" : error.message || "Erro na requisição";
  res.status(status).json({ error: message });
});

module.exports = app;
