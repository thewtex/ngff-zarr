#!/usr/bin/env node

import { spawn } from "child_process";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import process from "node:process";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Function to run a command with proper error handling
function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: "inherit",
      shell: true,
      ...options,
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve(code);
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on("error", (err) => {
      reject(err);
    });
  });
}

async function main() {
  try {
    console.log("📦 Installing Playwright dependencies...");

    // Check if we need to install dependencies
    const testDir = join(__dirname, "../test/browser-npm");
    const projectRoot = join(__dirname, "..");

    // Ensure npm package is copied to test directory
    console.log("📋 Copying npm package to test directory...");
    await runCommand("cp", ["-r", "npm", "test/browser-npm/"], {
      cwd: projectRoot,
    });

    // Install npm dependencies first
    await runCommand("npm", ["install"], { cwd: testDir });

    // Install Playwright browsers
    await runCommand("npx", ["playwright", "install"], { cwd: testDir });

    console.log("🎭 Running Playwright tests...");

    // Run Playwright tests
    const playwrightArgs = process.argv.slice(2);
    await runCommand("npx", ["playwright", "test", ...playwrightArgs], {
      cwd: testDir,
    });

    console.log("✅ All tests completed successfully!");
  } catch (error) {
    console.error("❌ Test execution failed:", error.message);
    process.exit(1);
  }
}

main();
