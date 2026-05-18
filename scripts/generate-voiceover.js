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

// ── Build ~38-word narration script ─────────────────────────────────────────
function buildScript(p) {
  const match = p.match
    .replace(/\bvs\b/ig, 'versus')
    .replace(/\b(MI|KKR|RCB|CSK|SRH|DC|PBKS|RR|GT|LSG)\b/g, m => TEAM_NAMES[m] || m);
  const probWords   = numToWords(p.probability);
  const publicTeam  = teamName(p.public_team);
  const modelPick   = teamName(p.model_pick);
  const sameFavorite = normalizeTeamName(publicTeam) === normalizeTeamName(modelPick);
  // Apply team name substitution to reasons text too
  const TEAM_RE     = /\b(MI|KKR|RCB|CSK|SRH|DC|PBKS|RR|GT|LSG)\b/g;
  const reasonsText = p.reasons.map(r => r.trim().replace(TEAM_RE, m => TEAM_NAMES[m] || m)).join('. ');
  // Use last 2 sentences of CTA to stay within 20s budget
  const ctaSentences = p.cta.split('.').map(s => s.trim()).filter(Boolean);
  const ctaLine     = ctaSentences.slice(-2).join('. ') + '.';

  if (sameFavorite) {
    return [
      `Toss update: ${match}.`,
      `${modelPick} was favourite before the toss, and stays favourite now.`,
      `TrueOddsML has ${modelPick} at ${probWords} percent.`,
      `${reasonsText}.`,
      ctaLine
    ].join('\n\n');
  }

  // Target: ~40 words → ~18-19s at 1.05x speed
  return [
    `The public is backing ${publicTeam}. Our model disagrees.`,
    `${match}. Market makes ${publicTeam} the favourite.`,
    `TrueOddsML picks ${modelPick}. ${probWords} percent probability.`,
    `${reasonsText}.`,
    ctaLine
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

// Generate TTS audio
run('hyperframes', ['tts', scriptPath, '-o', audioPath, '-v', 'bm_george', '-s', '1.05']);
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

// Build a synthetic word-level transcript from the known script text.
// TTS output is metrically consistent so proportional distribution is reliable.
// Longer words get proportionally more time; 3% end-padding for trailing silence.
function syntheticTranscript(scriptText, durationSeconds) {
  const tokens = scriptText
    .replace(/\n+/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 0);

  const activeDuration = durationSeconds * 0.97;
  const totalChars = tokens.reduce((s, w) => s + w.replace(/[^a-z]/gi, '').length || 1, 0);

  let cursor = 0;
  return tokens.map(token => {
    const charLen = token.replace(/[^a-z]/gi, '').length || 1;
    const dur = (charLen / totalChars) * activeDuration;
    const word = { text: token.replace(/[.,!?;:]+$/, ''), start: +cursor.toFixed(3), end: +(cursor + dur).toFixed(3) };
    cursor += dur;
    return word;
  });
}

const duration = getAudioDuration(audioPath);
console.log(`Audio duration: ${duration.toFixed(2)}s`);

const words = syntheticTranscript(script, duration);
console.log(`Synthetic transcript: ${words.length} words over ${duration.toFixed(2)}s`);

fs.writeFileSync(transcriptDest, JSON.stringify(words, null, 2), 'utf8');
console.log(`Transcript saved: ${transcriptDest} (${words.length} words)`);
