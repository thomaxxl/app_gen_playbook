import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, "..");

const [, , scriptPath, ...args] = process.argv;

if (!scriptPath) {
  console.error("Expected a Node script path.");
  process.exit(1);
}

function buildEsbuildCandidates() {
  if (scriptPath.includes("/vitest/")) {
    return [
      path.resolve(frontendDir, "node_modules/vitest/node_modules/@esbuild/linux-x64/bin/esbuild"),
      path.resolve(frontendDir, "node_modules/vitest/node_modules/esbuild/bin/esbuild"),
      path.resolve(frontendDir, "node_modules/@esbuild/linux-x64/bin/esbuild"),
      path.resolve(frontendDir, "node_modules/esbuild/bin/esbuild"),
    ];
  }

  return [
    path.resolve(frontendDir, "node_modules/@esbuild/linux-x64/bin/esbuild"),
    path.resolve(frontendDir, "node_modules/esbuild/bin/esbuild"),
    path.resolve(frontendDir, "node_modules/vite-node/node_modules/@esbuild/linux-x64/bin/esbuild"),
    path.resolve(frontendDir, "node_modules/vite-node/node_modules/esbuild/bin/esbuild"),
  ];
}

async function resolveEsbuildBinary() {
  let lastError;
  for (const source of buildEsbuildCandidates()) {
    try {
      await fs.access(source);
      const target = path.join(
        os.tmpdir(),
        scriptPath.includes("/vitest/")
          ? `chess-tournament-esbuild-vitest-${process.platform}-${process.arch}-${process.pid}`
          : `chess-tournament-esbuild-vite-${process.platform}-${process.arch}-${process.pid}`,
      );
      await fs.rm(target, { force: true });
      await fs.copyFile(source, target);
      await fs.chmod(target, 0o755);
      return target;
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(
    `Unable to prepare an esbuild binary under node_modules.${lastError ? ` Last error: ${lastError}` : ""}`,
  );
}

const env = { ...process.env };
env.ESBUILD_BINARY_PATH = await resolveEsbuildBinary();

const child = spawn(process.execPath, [path.resolve(frontendDir, scriptPath), ...args], {
  cwd: frontendDir,
  env,
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
