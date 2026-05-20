const { spawnSync } = require("node:child_process");
const fs   = require("node:fs");
const path = require("node:path");

const root            = path.resolve(__dirname, "..");
const compositionPath = path.join(root, "compositions", "powerplay-signal.html");
const cacheDir        = path.join(root, ".render-cache-powerplay");
const renderHtmlPath  = path.join(cacheDir, "index.html");
const outputPath      = path.join(root, "renders", "powerplay-signal.mp4");

function withFfmpegPath(baseEnv) {
  const pathKey = Object.keys(baseEnv).find((k) => k.toLowerCase() === "path") || "PATH";
  const next = { ...baseEnv };
  const bin  = findWingetFfmpegBin();
  if (bin) next[pathKey] = `${bin}${path.delimiter}${next[pathKey] || ""}`;
  return next;
}

function findWingetFfmpegBin() {
  if (process.platform !== "win32") return null;
  const packagesRoot = path.join(process.env.LOCALAPPDATA || "", "Microsoft", "WinGet", "Packages");
  if (!fs.existsSync(packagesRoot)) return null;
  const dirs = fs.readdirSync(packagesRoot, { withFileTypes: true })
    .filter((e) => e.isDirectory() && e.name.startsWith("Gyan.FFmpeg"))
    .map((e) => path.join(packagesRoot, e.name));
  for (const d of dirs) {
    const build = fs.readdirSync(d, { withFileTypes: true }).find((e) => e.isDirectory() && e.name.startsWith("ffmpeg-"));
    if (!build) continue;
    const bin = path.join(d, build.name, "bin");
    if (fs.existsSync(path.join(bin, "ffmpeg.exe"))) return bin;
  }
  return null;
}

const env = withFfmpegPath(process.env);

function run(command, args) {
  const r = spawnSync(command, args, { cwd: root, env, stdio: "inherit", shell: true });
  if (r.status !== 0) process.exit(r.status || 1);
}

if (!fs.existsSync(compositionPath)) {
  console.error(`Missing composition: ${compositionPath}`);
  process.exit(1);
}

// Prepare cache directory
fs.rmSync(cacheDir, { recursive: true, force: true });
fs.mkdirSync(cacheDir, { recursive: true });
fs.copyFileSync(compositionPath, renderHtmlPath);

// Lint first
console.log("Linting…");
run("hyperframes", ["lint", cacheDir]);

// Render
console.log(`Rendering → ${outputPath}`);
run("hyperframes", ["render", cacheDir, "--output", outputPath, "--fps", "30", "--quality", "standard"]);

console.log(`Done: ${outputPath}`);
