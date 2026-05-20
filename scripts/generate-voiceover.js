'use strict';
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const inputPath    = path.join(root, 'inputs', 'match_prediction.json');
const scriptPath   = path.join(root, 'assets', 'voiceover-script.txt');
const audioPath    = path.join(root, 'assets', 'voiceover.wav');
const transcriptDest = path.join(root, 'assets', 'transcript.json');

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

// Map team abbreviations → full city names for natural TTS pronunciation
const TEAM_NAMES = {
  MI:   'Mumbai',   KKR:  'Kolkata',  RCB:  'Bangalore',
  CSK:  'Chennai',  SRH:  'Hyderabad', DC:  'Delhi',
  PBKS: 'Punjab',  RR:   'Rajasthan', GT:  'Gujarat',
  LSG:  'Lucknow',
};

function teamName(abbr) {
  return TEAM_NAMES[abbr] || abbr;
}

function normalizeTeamName(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '');
}

// ── Build narration script aligned to video beat timeline ───────────────────
//
// Video beat timeline:
//   t=0–5s   hook   — hook lines (public vs model) animate on screen
//   t=5–9s   prob   — probability panel + counter animates
//   t=9–15s  reasons— reason cards 1, 2, 3 slide in
//   t=15s+   cta    — CTA card appears
//
// Script is split into 4 paragraphs with \n\n between each.
// The TTS engine inserts a natural ~0.5s pause at each paragraph break,
// which paces the narration to match the video's scene timing.
//
// Speed 0.85x gives ~2.2 words/second — slow enough to sound natural,
// fast enough to stay within the 20–25s composition window.
//
// Rough word budget per beat at 0.85x:
//   hook   (~5s):  8–10 words
//   prob   (~4s):  6–7 words (says the model pick + probability number)
//   reasons(~6s):  12–15 words (3 short reasons, period-separated)
//   cta    (~2s):  4–6 words
function buildScript(p) {
  const TEAM_RE   = /\b(MI|KKR|RCB|CSK|SRH|DC|PBKS|RR|GT|LSG)\b/g;
  const match     = p.match
    .replace(/\bvs\b/ig, 'versus')
    .replace(TEAM_RE, m => TEAM_NAMES[m] || m);
  const probWords = numToWords(p.probability);
  const pub       = teamName(p.public_team);
  const pick      = teamName(p.model_pick);
  const sameFav   = normalizeTeamName(pub) === normalizeTeamName(pick);
  const reasons   = p.reasons.map(r =>
    r.trim()
     .replace(TEAM_RE, m => TEAM_NAMES[m] || m)
     .replace(/\bH2H\b/gi, 'head to head')  // TTS reads "H2H" as letters, not words
     .replace(/[.!?]+$/, '')                 // strip trailing punctuation — re-added when joining
  );
  const ctaSents  = p.cta.split('.').map(s => s.trim()).filter(Boolean);
  const cta       = ctaSents.slice(-2).join('. ') + '.';

  if (sameFav) {
    return [
      /* beat 1 – hook */    `${match}. ${pick} is the clear market favourite.`,
      /* beat 2 – prob  */   `TrueOddsML agrees. ${probWords} percent win probability.`,
      /* beat 3 – reasons */ reasons.join('. ') + '.',
      /* beat 4 – cta   */   cta,
    ].join('\n\n');
  }

  return [
    /* beat 1 – hook */    `The public is backing ${pub}. Our model disagrees.`,
    /* beat 2 – prob  */   `TrueOddsML picks ${pick}. ${probWords} percent probability.`,
    /* beat 3 – reasons */ reasons.join('. ') + '.',
    /* beat 4 – cta   */   cta,
  ].join('\n\n');
}


function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: 'inherit',
    shell: true
  });
  if (result.status !== 0) {
    console.error(`Command failed: ${command} ${args.join(' ')}`);
    process.exit(result.status || 1);
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
const prediction = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const script     = buildScript(prediction);

fs.mkdirSync(path.join(root, 'assets'), { recursive: true });
fs.writeFileSync(scriptPath, script, 'utf8');

console.log('Voiceover script written to assets/voiceover-script.txt');
console.log('--- Script ---');
console.log(script);
console.log('--------------');

// Generate TTS audio at 0.85x speed — natural pacing, clear inter-sentence pauses
run('hyperframes', ['tts', scriptPath, '-o', audioPath, '-v', 'bm_george', '-s', '0.85']);
console.log(`Audio generated: ${audioPath}`);

// Get audio duration via ffprobe (already required for the render pipeline)
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

// Paragraph-aware synthetic transcript.
//
// Problem with the old character-proportional approach: it distributed ALL words
// evenly over the total audio duration, ignoring the ~0.5s silence the TTS engine
// inserts between paragraph breaks (\n\n). This caused captions to appear *before*
// the corresponding word was actually spoken (because the pauses shift real timing).
//
// Fix: detect paragraph boundaries, insert a 0.50s gap between them in the
// transcript, then distribute each paragraph's words proportionally *within*
// that paragraph's speech window only.
const PARA_PAUSE_SECS = 0.50;  // seconds TTS inserts at each \n\n boundary

function syntheticTranscript(scriptText, durationSeconds) {
  const paragraphs = scriptText.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  const pauseTotal = (paragraphs.length - 1) * PARA_PAUSE_SECS;
  const trailSilence = durationSeconds * 0.03; // 3% trailing fade
  const speechTime = Math.max(durationSeconds - pauseTotal - trailSilence, 1);

  // Total char count (letters only) across every word — used for proportional weighting
  const allTokens = paragraphs.flatMap(p => p.split(/\s+/).filter(w => w.length > 0));
  const totalChars = allTokens.reduce((s, w) => s + (w.replace(/[^a-z]/gi, '').length || 1), 0);

  let cursor = 0;
  const words = [];

  for (let pi = 0; pi < paragraphs.length; pi++) {
    const tokens = paragraphs[pi].split(/\s+/).filter(w => w.length > 0);
    for (const token of tokens) {
      const charLen = token.replace(/[^a-z]/gi, '').length || 1;
      const dur = (charLen / totalChars) * speechTime;
      words.push({
        text: token.replace(/[.,!?;:]+$/, ''),
        start: +cursor.toFixed(3),
        end:   +(cursor + dur).toFixed(3),
      });
      cursor += dur;
    }
    // Advance cursor by the paragraph pause (skip after last paragraph)
    if (pi < paragraphs.length - 1) {
      cursor += PARA_PAUSE_SECS;
    }
  }

  return words;
}

const duration = getAudioDuration(audioPath);
console.log(`Audio duration: ${duration.toFixed(2)}s`);

const words = syntheticTranscript(script, duration);
console.log(`Synthetic transcript: ${words.length} words over ${duration.toFixed(2)}s`);

fs.writeFileSync(transcriptDest, JSON.stringify(words, null, 2), 'utf8');
console.log(`Transcript saved: ${transcriptDest} (${words.length} words)`);
