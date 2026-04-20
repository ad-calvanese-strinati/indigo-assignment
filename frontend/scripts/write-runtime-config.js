import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const distDir = join(process.cwd(), "dist");
const targetFile = join(distDir, "runtime-config.js");

mkdirSync(distDir, { recursive: true });

const config = {
  API_BASE_URL:
    process.env.API_BASE_URL ||
    process.env.VITE_API_BASE_URL ||
    "http://localhost:8000/api",
  API_TOKEN:
    process.env.API_TOKEN ||
    process.env.VITE_API_TOKEN ||
    "change-me",
};

writeFileSync(
  targetFile,
  `window.__APP_CONFIG__ = ${JSON.stringify(config, null, 2)};\n`,
  "utf-8",
);
