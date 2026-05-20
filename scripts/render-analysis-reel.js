const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const compositionPath = path.join(root, "compositions", "prematch-analysis-reel.html");
const inputPath       = path.join(root, "inputs", "match_prediction.json");
const audioSrc        = path.join(root, "assets", "analysis-voiceover.wav");
const transcriptPath  = path.join(root, "assets", "analysis-transcript.json");
const cacheDir        = path.join(root, ".render-cache-analysis");
const renderCompositionPath = path.join(cacheDir, "index.html");
const outputPath = path.join(root, "renders", "prematch_analysis_reel.mp4");
const env = withFfmpegPath(process.env);

function withFfmpegPath(baseEnv) {
  const pathKey = Object.keys(baseEnv).find((key) => key.toLowerCase() === "path") || "PATH";
  const nextEnv = { ...baseEnv };
  const ffmpegBin = findWingetFfmpegBin();

  if (ffmpegBin) {
    nextEnv[pathKey] = `${ffmpegBin}${path.delimiter}${nextEnv[pathKey] || ""}`;
  }

  return nextEnv;
}

function findWingetFfmpegBin() {
  if (process.platform !== "win32") return null;

  const packagesRoot = path.join(
    process.env.LOCALAPPDATA || "",
    "Microsoft",
    "WinGet",
    "Packages"
  );

  if (!fs.existsSync(packagesRoot)) return null;

  const packageDirs = fs
    .readdirSync(packagesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("Gyan.FFmpeg"))
    .map((entry) => path.join(packagesRoot, entry.name));

  for (const packageDir of packageDirs) {
    const buildDir = fs
      .readdirSync(packageDir, { withFileTypes: true })
      .find((entry) => entry.isDirectory() && entry.name.startsWith("ffmpeg-"));

    if (!buildDir) continue;

    const binDir = path.join(packageDir, buildDir.name, "bin");
    if (fs.existsSync(path.join(binDir, "ffmpeg.exe"))) return binDir;
  }

  return null;
}

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    env,
    stdio: "inherit",
    shell: true
  });

  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

if (!fs.existsSync(compositionPath)) {
  console.error(`Missing composition: ${compositionPath}`);
  process.exit(1);
}

run("node", ["scripts/validate-input.js"]);
run("node", ["scripts/generate-analysis-voiceover.js"]);

const html       = fs.readFileSync(compositionPath, "utf8");
const prediction = fs.readFileSync(inputPath, "utf8");

const transcriptJson = fs.existsSync(transcriptPath)
  ? fs.readFileSync(transcriptPath, "utf8")
  : "[]";
const transcriptWords = JSON.parse(transcriptJson);
const safeTranscript  = JSON.stringify(transcriptWords).replace(/</g, "\\u003c");

const audioDuration = transcriptWords.length
  ? Math.ceil(transcriptWords[transcriptWords.length - 1].end + 0.5)
  : 32;
console.log(`Composition duration set to ${audioDuration}s (audio: ${
  transcriptWords.length ? transcriptWords[transcriptWords.length - 1].end.toFixed(2) : "?"
}s)`);

const injectedHtml = html
  .replace(/data-duration="\d+"/, `data-duration="${audioDuration}"`)
  .replace(
    "</head>",
    `<script>window.__MATCH_PREDICTION__ = ${prediction};</script>\n` +
    `<script>window.__TRANSCRIPT__ = ${safeTranscript};</script>\n</head>`
  );

fs.rmSync(cacheDir, { recursive: true, force: true });
fs.mkdirSync(cacheDir, { recursive: true });
fs.writeFileSync(renderCompositionPath, injectedHtml);

// Copy voiceover audio into render cache
if (fs.existsSync(audioSrc)) {
  const audioCacheDir = path.join(cacheDir, "assets");
  fs.mkdirSync(audioCacheDir, { recursive: true });
  fs.copyFileSync(audioSrc, path.join(audioCacheDir, "analysis-voiceover.wav"));
}

// Copy team logos into render cache
const logosDir = path.join(root, "assets", "logo");
if (fs.existsSync(logosDir)) {
  const logoCacheDir = path.join(cacheDir, "assets", "logo");
  fs.mkdirSync(logoCacheDir, { recursive: true });
  fs.readdirSync(logosDir).forEach(file => {
    fs.copyFileSync(path.join(logosDir, file), path.join(logoCacheDir, file));
  });
  console.log(`Copied ${fs.readdirSync(logosDir).length} logo(s) to render cache.`);
}

// Copy Lottie animations into render cache
const lottieDir = path.join(root, "assets", "lottie");
if (fs.existsSync(lottieDir)) {
  const lottieCacheDir = path.join(cacheDir, "assets", "lottie");
  fs.mkdirSync(lottieCacheDir, { recursive: true });
  fs.readdirSync(lottieDir).forEach(file => {
    fs.copyFileSync(path.join(lottieDir, file), path.join(lottieCacheDir, file));
  });
  console.log(`Copied ${fs.readdirSync(lottieDir).length} Lottie file(s) to render cache.`);
}

run("hyperframes", [
  "render",
  cacheDir,
  "--output",
  outputPath,
  "--fps",
  "30",
  "--quality",
  "standard"
]);

console.log(`Rendered: ${outputPath}`);
