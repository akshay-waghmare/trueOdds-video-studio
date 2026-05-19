'use strict';
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root           = path.resolve(__dirname, '..');
const inputPath      = path.join(root, 'inputs', 'match_prediction.json');
const scriptPath     = path.join(root, 'assets', 'analysis-voiceover-script.txt');
const audioPath      = path.join(root, 'assets', 'analysis-voiceover.wav');
const transcriptDest = path.join(root, 'assets', 'analysis-transcript.json');

// ── Number to English words (0-100) ─────────────────────────────────────────
const ONES = [
  'zero','one','two','three','four','five','six','seven','eight','nine',
  'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen',
  'seventeen','eighteen','nineteen'
];
const TENS = ['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety'];

function numToWords(n) {
  n = Math.round(n);
  if (n === 100) return 'one hundred';
  if (n < 20)    return ONES[n];
  if (n % 10 === 0) return TENS[Math.floor(n / 10)];
  return TENS[Math.floor(n / 10)] + '-' + ONES[n % 10];
}

const TEAM_NAMES = {
  MI:   'Mumbai',   KKR:  'Kolkata',  RCB:  'Bangalore',
  CSK:  'Chennai',  SRH:  'Hyderabad', DC:  'Delhi',
  PBKS: 'Punjab',  RR:   'Rajasthan', GT:  'Gujarat',
  LSG:  'Lucknow',
};

function teamName(abbr) { return TEAM_NAMES[abbr] || abbr; }

function norm(v) { return String(v || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, ''); }

// ── 5-beat persuasion script ─────────────────────────────────────────────────
//
// Beat timeline (approximate):
//   0–3s   Hook scene     — "Stop guessing cricket"
//   3–8s   Problem scene  — crowd picks, emotion vs data pivot
//   8–22s  Demo scene     — full prediction reveal
//   22–27s Proof scene    — how we analyse
//   27–32s CTA scene      — free prediction, follow
//
// Split into 5 paragraphs so TTS paragraph-pause pacing aligns to scene cuts.
//
function buildScript(p) {
  const TEAM_RE = /\b(MI|KKR|RCB|CSK|SRH|DC|PBKS|RR|GT|LSG)\b/g;
  const pub      = teamName(p.public_team);
  const pick     = teamName(p.model_pick);
  const prob     = numToWords(p.probability);
  const sameTeam = norm(pub) === norm(pick);

  const reasons = (p.reasons || []).map(r =>
    r.trim()
     .replace(TEAM_RE, m => TEAM_NAMES[m] || m)
     .replace(/\bH2H\b/gi, 'head to head')
     .replace(/\b(\d+)W\b/g, (_, n) => n + (n === '1' ? ' win' : ' wins'))
     .replace(/\bvs\b/gi, 'versus')
     .replace(/[.!?]+$/, '')
  );

  const ctaLine = p.cta
    ? p.cta.replace(/Follow TrueOddsML\.?/gi, '').trim().replace(/\.$/, '') + '.'
    : 'Try one free prediction today.';

  if (sameTeam) {
    return [
      `Still guessing cricket? Stop. Your emotions are not a strategy.`,
      `Even the crowd agrees with the data today — both are backing ${pub}. But the reason matters.`,
      `TrueOddsML confirms ${pick} at ${prob} percent win probability. ${reasons.join('. ')}.`,
      `Powered by Machine Learning and Monte Carlo simulation. We run thousands of IPL match scenarios — team form, venue history, head to head. Cutting edge cricket science.`,
      `${ctaLine} Follow TrueOddsML.`,
    ].join('\n\n');
  }

  return [
    `Still guessing cricket? Stop. Your emotions are not a strategy.`,
    `Right now the crowd is picking ${pub}. Home ground. Favourite team. Pure emotion. No data.`,
    `TrueOddsML model picks ${pick}. ${prob} percent win probability. ${reasons.join('. ')}.`,
    `Powered by Machine Learning and Monte Carlo simulation. We run thousands of IPL match scenarios — team form, venue history, head to head. Cutting edge cricket science.`,
    `${ctaLine} Follow TrueOddsML.`,
  ].join('\n\n');
}

function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit', shell: true });
  if (result.status !== 0) {
    console.error(`Command failed: ${command} ${args.join(' ')}`);
    process.exit(result.status || 1);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────
const prediction = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const script     = buildScript(prediction);

fs.mkdirSync(path.join(root, 'assets'), { recursive: true });
fs.writeFileSync(scriptPath, script, 'utf8');

console.log('Analysis voiceover script written to assets/analysis-voiceover-script.txt');
console.log('--- Script ---');
console.log(script);
console.log('--------------');

run('hyperframes', ['tts', scriptPath, '-o', audioPath, '-v', 'bm_george', '-s', '0.85']);
console.log(`Audio generated: ${audioPath}`);

function getAudioDuration(filePath) {
  const r = spawnSync('ffprobe', [
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'csv=p=0',
    filePath
  ], { encoding: 'utf8', shell: true });
  const d = parseFloat(r.stdout.trim());
  if (isNaN(d) || d <= 0) throw new Error(`ffprobe could not read duration of ${filePath}`);
  return d;
}

const PARA_PAUSE_SECS = 0.50;

function syntheticTranscript(scriptText, durationSeconds) {
  const paragraphs  = scriptText.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  const pauseTotal  = (paragraphs.length - 1) * PARA_PAUSE_SECS;
  const trailSilence = durationSeconds * 0.03;
  const speechTime  = Math.max(durationSeconds - pauseTotal - trailSilence, 1);
  const allTokens   = paragraphs.flatMap(p => p.split(/\s+/).filter(w => w.length > 0));
  const totalChars  = allTokens.reduce((s, w) => s + (w.replace(/[^a-z]/gi, '').length || 1), 0);

  let cursor = 0;
  const words = [];

  for (let pi = 0; pi < paragraphs.length; pi++) {
    const tokens = paragraphs[pi].split(/\s+/).filter(w => w.length > 0);
    for (const token of tokens) {
      const charLen = token.replace(/[^a-z]/gi, '').length || 1;
      const dur = (charLen / totalChars) * speechTime;
      words.push({
        text:  token.replace(/[.,!?;:]+$/, ''),
        start: +cursor.toFixed(3),
        end:   +(cursor + dur).toFixed(3),
      });
      cursor += dur;
    }
    if (pi < paragraphs.length - 1) cursor += PARA_PAUSE_SECS;
  }

  return words;
}

const duration = getAudioDuration(audioPath);
console.log(`Audio duration: ${duration.toFixed(2)}s`);

const words = syntheticTranscript(script, duration);
console.log(`Synthetic transcript: ${words.length} words over ${duration.toFixed(2)}s`);

fs.writeFileSync(transcriptDest, JSON.stringify(words, null, 2), 'utf8');
console.log(`Transcript saved: ${transcriptDest} (${words.length} words)`);
