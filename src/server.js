require("dotenv").config();

const { validateEnv } = require("./config/validate-env");
validateEnv();

const app = require("./app");

const port = Number(process.env.APP_PORT || 3000);

app.listen(port, () => {
  console.log(`MVP em execução em http://localhost:${port}`);
});
