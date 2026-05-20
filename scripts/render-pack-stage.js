/**
 * render-pack-stage.js
 *
 * Renders a single pack stage composition to MP4.
 *
 * Usage:
 *   node scripts/render-pack-stage.js \
 *     --composition post-match-proof \
 *     --input inputs/packs/mumbai-indians-vs-punjab-kings/post_match_proof_english.json \
 *     [--output renders/post_match_proof_mi_pbks.mp4]
 *
 * Supported compositions: post-match-proof, turning-point
 */

const { spawnSync } = require("node:child_process");
const fs   = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");

// ── CLI args ──────────────────────────────────────────────────────────────────
const args         = process.argv.slice(2);
const KNOWN_COMPS  = ["post-match-proof", "turning-point"];

function getArg(flag) {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : null;
}

const compositionName = getArg("--composition");
const inputPath       = getArg("--input");
let   outputPath      = getArg("--output");

if (!compositionName || !KNOWN_COMPS.includes(compositionName)) {
  console.error(`Usage: --composition <${KNOWN_COMPS.join("|")}> --input <path> [--output <path>]`);
  process.exit(1);
}

if (!inputPath) {
  console.error("Error: --input <path> is required.");
  process.exit(1);
}

const absInput = path.resolve(root, inputPath);
if (!fs.existsSync(absInput)) {
  console.error(`Input not found: ${absInput}`);
  process.exit(1);
}

const compositionPath = path.join(root, "compositions", `${compositionName}.html`);
if (!fs.existsSync(compositionPath)) {
  console.error(`Composition not found: ${compositionPath}`);
  process.exit(1);
}

// Default output path derived from composition + match slug
if (!outputPath) {
  const payload   = JSON.parse(fs.readFileSync(absInput, "utf8"));
  const matchSlug = (payload.match || "unknown")
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  const stageName = (payload.template || compositionName).replace(/-/g, "_");
  outputPath = path.join(root, "renders", `${stageName}_${matchSlug}.mp4`);
}

const cacheDir              = path.join(root, ".render-cache");
const renderCompositionPath = path.join(cacheDir, "index.html");
const audioSrc              = path.join(root, "assets", "voiceover.wav");
const transcriptPath        = path.join(root, "assets", "transcript.json");
const env                   = withFfmpegPath(process.env);

function withFfmpegPath(baseEnv) {
  const pathKey = Object.keys(baseEnv).find(k => k.toLowerCase() === "path") || "PATH";
  const nextEnv = { ...baseEnv };
  const bin     = findWingetFfmpegBin();
  if (bin) nextEnv[pathKey] = `${bin}${path.delimiter}${nextEnv[pathKey] || ""}`;
  return nextEnv;
}

function findWingetFfmpegBin() {
  if (process.platform !== "win32") return null;
  const packagesRoot = path.join(process.env.LOCALAPPDATA || "", "Microsoft", "WinGet", "Packages");
  if (!fs.existsSync(packagesRoot)) return null;
  const packageDirs = fs.readdirSync(packagesRoot, { withFileTypes: true })
    .filter(e => e.isDirectory() && e.name.startsWith("Gyan.FFmpeg"))
    .map(e => path.join(packagesRoot, e.name));
  for (const packageDir of packageDirs) {
    const buildDir = fs.readdirSync(packageDir, { withFileTypes: true })
      .find(e => e.isDirectory() && e.name.startsWith("ffmpeg-"));
    if (!buildDir) continue;
    const binDir = path.join(packageDir, buildDir.name, "bin");
    if (fs.existsSync(path.join(binDir, "ffmpeg.exe"))) return binDir;
  }
  return null;
}

function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, env, stdio: "inherit", shell: true });
  if (result.status !== 0) process.exit(result.status || 1);
}

// ── Validate payload has required template field ──────────────────────────────
const payload = JSON.parse(fs.readFileSync(absInput, "utf8"));
const expectedTemplate = compositionName.replace(/-/g, "_");
if (payload.template && payload.template !== expectedTemplate) {
  console.warn(
    `Warning: payload template "${payload.template}" does not match composition "${compositionName}". Proceeding anyway.`
  );
}

// ── Build render cache ────────────────────────────────────────────────────────
const html           = fs.readFileSync(compositionPath, "utf8");
const payloadJson    = fs.readFileSync(absInput, "utf8");
// Pack stages have their own voiceover text; do not reuse the prematch transcript
// as its word-timing will not align and captions will bleed at wrong times.
const transcriptJson = "[]";

const transcriptWords = JSON.parse(transcriptJson);
const safeTranscript  = JSON.stringify(transcriptWords).replace(/</g, "\\u003c");

const audioDuration = transcriptWords.length
  ? Math.ceil(transcriptWords[transcriptWords.length - 1].end + 0.5)
  : 20;

console.log(`Composition : ${compositionName}`);
console.log(`Input       : ${absInput}`);
console.log(`Output      : ${outputPath}`);
console.log(`Duration    : ${audioDuration}s`);

const injectedHtml = html
  .replace(/data-duration="\d+"/, `data-duration="${audioDuration}"`)
  .replace(
    "</head>",
    `<script>window.__MATCH_PREDICTION__ = ${payloadJson};</script>\n` +
    `<script>window.__TRANSCRIPT__ = ${safeTranscript};</script>\n</head>`
  );

fs.rmSync(cacheDir, { recursive: true, force: true });
fs.mkdirSync(cacheDir, { recursive: true });
fs.writeFileSync(renderCompositionPath, injectedHtml);

// Copy voiceover audio
if (fs.existsSync(audioSrc)) {
  const audioCacheDir = path.join(cacheDir, "assets");
  fs.mkdirSync(audioCacheDir, { recursive: true });
  fs.copyFileSync(audioSrc, path.join(audioCacheDir, "voiceover.wav"));
}

// Copy team logos
const logosDir = path.join(root, "assets", "logo");
if (fs.existsSync(logosDir)) {
  const logoCacheDir = path.join(cacheDir, "assets", "logo");
  fs.mkdirSync(logoCacheDir, { recursive: true });
  fs.readdirSync(logosDir).forEach(file =>
    fs.copyFileSync(path.join(logosDir, file), path.join(logoCacheDir, file))
  );
}

// Ensure output directory exists
fs.mkdirSync(path.dirname(path.resolve(root, outputPath)), { recursive: true });

// ── Render ────────────────────────────────────────────────────────────────────
run("hyperframes", ["render", cacheDir, "--output", outputPath, "--fps", "30", "--quality", "standard"]);

console.log(`\nRendered: ${outputPath}`);
