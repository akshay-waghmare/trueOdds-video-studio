const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const outputPath = path.join(root, "renders", "prematch_prediction.mp4");
const screenshotsDir = path.join(root, "renders", "screenshots");
const maxBytes = 50 * 1024 * 1024;
const env = withFfmpegPath(process.env);

const checkpoints = [
  ["00_hook", 0],
  ["03_public_favourite", 3],
  ["06_model_pick", 6],
  ["09_probability_meter", 9],
  ["12_reasons_1_2", 12],
  ["15_reason_3", 15],
  ["18_cta", 18],
  ["20_end_frame", 19.9]
];

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: root,
    env,
    encoding: "utf8",
    shell: true,
    ...options
  });

  if (result.status !== 0) {
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(output || `${command} failed`);
  }

  return result.stdout;
}

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

function getMetadata() {
  const stdout = run("ffprobe", [
    "-v", "error",
    "-select_streams", "v:0",
    "-show_entries", "stream=width,height,codec_name,duration",
    "-of", "json",
    outputPath
  ]);
  const json = JSON.parse(stdout);
  return json.streams[0];
}

function assertRender() {
  if (!fs.existsSync(outputPath)) {
    throw new Error(`Missing render: ${outputPath}`);
  }

  const metadata = getMetadata();
  const stats = fs.statSync(outputPath);
  const duration = Number(metadata.duration);
  const failures = [];

  if (Number(metadata.width) !== 1080) failures.push(`width is ${metadata.width}, expected 1080`);
  if (Number(metadata.height) !== 1920) failures.push(`height is ${metadata.height}, expected 1920`);
  if (metadata.codec_name !== "h264") failures.push(`codec is ${metadata.codec_name}, expected h264`);
  if (duration < 18 || duration > 35) failures.push(`duration is ${duration}s, expected 18-35s`);
  if (stats.size > maxBytes) failures.push(`file size is ${(stats.size / 1024 / 1024).toFixed(2)}MB, expected <=50MB`);

  if (failures.length > 0) {
    console.error("Render inspection failed:");
    for (const failure of failures) console.error(`- ${failure}`);
    process.exit(1);
  }

  console.log("Render inspection passed.");
  console.log(`Metadata: ${metadata.width}x${metadata.height}, ${duration.toFixed(2)}s, ${metadata.codec_name}`);
  console.log(`File size: ${(stats.size / 1024 / 1024).toFixed(2)}MB`);
}

function captureScreenshots() {
  fs.mkdirSync(screenshotsDir, { recursive: true });

  for (const [name, seconds] of checkpoints) {
    const screenshotPath = path.join(screenshotsDir, `${name}.jpg`);
    run("ffmpeg", [
      "-y",
      "-ss", String(seconds),
      "-i", outputPath,
      "-frames:v", "1",
      screenshotPath
    ], { stdio: "pipe" });
    console.log(`Screenshot: ${screenshotPath}`);
  }
}

function captureThumbnail() {
  const thumbnailPath = path.join(root, "renders", "thumbnail.jpg");
  const tempPath = path.join(root, "renders", "prematch_prediction_tmp.mp4");

  // 11s frame: probability meter fully filled, reasons 1-2 visible — ideal for Instagram cover
  run("ffmpeg", [
    "-y", "-ss", "11", "-i", outputPath,
    "-frames:v", "1", "-update", "1", "-q:v", "2",
    thumbnailPath
  ], { stdio: "pipe" });
  console.log(`Thumbnail: ${thumbnailPath}`);

  // Embed thumbnail as MP4 cover art — Instagram and most players show this before playback
  run("ffmpeg", [
    "-y",
    "-i", outputPath,
    "-i", thumbnailPath,
    "-map", "0:v", "-map", "0:a", "-map", "1",
    "-c:v", "copy", "-c:a", "copy", "-c:v:1", "mjpeg",
    "-disposition:v:1", "attached_pic",
    "-movflags", "+faststart",
    tempPath
  ], { stdio: "pipe" });

  fs.renameSync(tempPath, outputPath);
  console.log(`Cover art embedded → ${outputPath}`);
}

try {
  assertRender();
  captureScreenshots();
  captureThumbnail();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
