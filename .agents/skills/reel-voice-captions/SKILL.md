---
name: reel-voice-captions
description: Add TTS voiceover and synced word-level captions to any TrueOddsML HyperFrames reel. Use when asked to add voice, narration, audio, captions, subtitles, or talking text to a cricket prediction reel. Covers script writing, TTS generation, transcription, audio element wiring, and the full TrueOddsML caption style (bold bottom-third, yellow accents, word-by-word pop).
---

# Reel Voice + Captions

## When to Use

Invoke this skill when asked to:
- Add voice / narration / voiceover to a reel
- Add captions / subtitles / synced text to a reel
- Redo the voiceover with a different script or voice
- Change caption style or timing

---

## Full Workflow

```
1. Write script (match scene timing)
2. Generate TTS → assets/vo-<reel>.wav
3. Transcribe → assets/vo-<reel>.json
4. Inspect transcript quality
5. Add <audio> element to composition
6. Update data-duration to match audio length
7. Add caption container CSS + HTML
8. Build GSAP caption timeline from transcript groups
9. Lint + render + verify
```

---

## Step 1 — Write the Script

### Scene timing reference (read from composition)

Before writing, read the composition's JS for scene start variables:
- `var S1`, `var T12`, `var S2`, `var T23` … `var S6`
- Scene duration = next transition time − scene start
- Leave 0.2–0.4s breathing room at end of each scene

### Script rules

- **One idea per scene.** Match the visual's hero element.
- **Target 2.5–3.0 words/second** at normal speech pace.
- **Numbers**: spell out for natural TTS — `"two twenty one"` not `"221"`.
- **Team names**: use full name once, then "they/them/the team" after.
- **Brand CTA**: always end with a line containing "probability" — `"Don't guess the match. Read the probability."`
- Never mention betting, guaranteed tips, or sure-shot predictions.

### Template script (20-second reel, 6 scenes)

```
Scene 1 (~2.5s, ~6 words):    "[Context]. [Team] was chasing [target]."
Scene 2 (~3s,   ~8 words):    "[Score] for none after six overs."
Scene 3 (~3.5s, ~9 words):    "Our model gave them [X] percent. Here's why."
Scene 4 (~3s,   ~8 words):    "[Key signal]. The edge others missed."
Scene 5 (~2.8s, ~7 words):    "Watch how probability shifted every over."
Scene 6 (~2.8s, ~7 words):    "[Team] won. Called [N] overs early. Read the probability."
```

---

## Step 2 — Generate TTS

```bash
npx hyperframes tts "YOUR SCRIPT TEXT HERE" \
  -o assets/vo-<reel-name>.wav \
  -v bm_george \
  -s 1.0
```

### Voice recommendations

| Voice ID    | Character                        | Best for                     |
|-------------|----------------------------------|------------------------------|
| `bm_george` | British male, authoritative      | Match analysis, probability  |
| `am_michael`| American male, confident         | Hype/launch reels            |
| `af_nova`   | American female, clear           | Explanation/tutorial reels   |
| `bf_emma`   | British female, warm             | Storytelling reels           |
| `af_heart`  | American female, energetic       | CTA/social reels             |

**Default for TrueOddsML cricket reels: `bm_george`** — authoritative, probability-analyst feel.

### Speed guide

- `0.9` — slower, dramatic pauses (good for data reveals)
- `1.0` — natural pace (default)
- `1.1` — snappier, more energetic

### Check audio duration

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/vo-<reel>.wav
```

The composition `data-duration` must be ≥ audio duration. Update it if needed.

---

## Step 3 — Transcribe

```bash
npx hyperframes transcribe assets/vo-<reel>.wav \
  --model small.en \
  -o assets/vo-<reel>.json
```

Always use `small.en` for TTS-generated speech (clean audio, English only).  
Use `medium.en` only if `small.en` produces garbled output.

### Quality check (mandatory)

Read the transcript JSON. Reject and retry if:
- More than 20% entries are `♪`, `♩`, `♫`, or `♬` symbols
- Words are clearly wrong (garbled, repeated nonsense)
- Any `end - start < 0.05` (unreliable timestamp)

Clean filter before building captions:
```js
var words = raw.filter(function(w) {
  if (!w.text || w.text.trim().length === 0) return false;
  if (/^[♪♩♫♬\u266a-\u266f]+$/.test(w.text)) return false;
  return true;
});
```

---

## Step 4 — Add Audio to Composition

Place **before** the closing `</div>` of the root composition element, on its own `data-track-index` (use an index not already taken — typically 1 or 2):

```html
<audio
  id="vo-audio"
  src="../assets/vo-<reel>.wav"
  data-start="0"
  data-duration="AUDIO_DURATION_HERE"
  data-track-index="1"
  data-volume="1"
></audio>
```

**Never** embed audio inside a scene div. It must be a direct child of the root composition element.

---

## Step 5 — Update Composition Duration

If audio is longer than the current `data-duration`:
```html
<!-- change this: -->
data-duration="20"
<!-- to: -->
data-duration="ROUNDED_UP_AUDIO_DURATION"
```

Also update the JS `data-duration` comment if present, and the inspect script's duration check range.

---

## Step 6 — Caption CSS (TrueOddsML Style)

Add inside `<style>` before the closing `</style>` tag.  
This is the **brand caption style** — bold bottom-third, yellow number accents, dark backdrop:

```css
/* ══════════════════ CAPTIONS ══════════════════ */
#caption-layer {
  position: absolute;
  left: 0; right: 0;
  bottom: 420px;           /* bottom-third of 1920px portrait canvas */
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  z-index: 20;
}

.caption-group {
  position: absolute;
  left: 0; right: 0;
  bottom: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 0 80px;
  max-width: 1080px;
  overflow: visible;
  visibility: hidden;
  opacity: 0;
}

.caption-word {
  display: inline-block;
  font-family: "Bebas Neue", Impact, "Arial Narrow", sans-serif;
  font-size: 68px;
  font-weight: 900;
  line-height: 1.0;
  letter-spacing: 0.04em;
  color: #ffffff;
  text-shadow:
    0 2px 18px rgba(0,0,0,0.90),
    0 0 40px rgba(0,0,0,0.70);
  opacity: 0;
}

/* Yellow accent — numbers, brand name, key stats */
.caption-word.accent {
  color: #f5c518;
  text-shadow:
    0 2px 18px rgba(0,0,0,0.90),
    0 0 40px rgba(245,197,24,0.35);
}

/* Teal accent — probability values */
.caption-word.teal {
  color: #00c9a7;
  text-shadow:
    0 2px 18px rgba(0,0,0,0.90),
    0 0 40px rgba(0,201,167,0.35);
}
```

---

## Step 7 — Caption HTML

Add this **inside** the root composition div, after the last scene and before any `<script>` tags:

```html
<!-- ══════════════════ CAPTION LAYER ══════════════════ -->
<div id="caption-layer">
  <!-- Groups injected by JS -->
</div>
```

---

## Step 8 — Caption JavaScript Pattern

Read the transcript JSON inline (paste the `assets/vo-<reel>.json` contents as a JS literal), group words into 3–5 word chunks, then build the GSAP timeline.

### Full pattern

```js
// ── CAPTIONS ─────────────────────────────────────────
var WORDS = [
  // PASTE TRANSCRIPT ARRAY HERE — array of {text, start, end}
  // e.g.: { "text": "Yesterday.", "start": 0.00, "end": 0.44 },
];

// Group into 3-word chunks (social/hype style)
var GROUPS = (function() {
  var groups = [];
  var i = 0;
  while (i < WORDS.length) {
    var chunk = WORDS.slice(i, i + 3);
    groups.push({
      text: chunk.map(function(w) { return w.text; }).join(" "),
      words: chunk,
      start: chunk[0].start,
      end: chunk[chunk.length - 1].end + 0.10  // 100ms tail
    });
    i += 3;
  }
  return groups;
})();

// Build caption DOM
var capLayer = document.getElementById("caption-layer");
GROUPS.forEach(function(group, gi) {
  var div = document.createElement("div");
  div.className = "caption-group";
  div.id = "cg-" + gi;
  group.words.forEach(function(w, wi) {
    var span = document.createElement("span");
    span.id = "cw-" + gi + "-" + wi;
    span.className = "caption-word" + accentClass(w.text);
    span.textContent = w.text;
    div.appendChild(span);
  });
  capLayer.appendChild(div);
});

// Accent classifier — customize for your reel's key words
function accentClass(word) {
  var w = word.replace(/[^a-z0-9%]/gi, "").toLowerCase();
  // Numbers and percentages → yellow
  if (/^\d+$/.test(w) || w.indexOf("%") > -1) return " accent";
  // Probability-related → teal
  if (/^(probability|percent|model)$/.test(w)) return " teal";
  // Brand names → yellow
  if (/^(crickzen|trueodds)$/i.test(w)) return " accent";
  return "";
}

// Timeline — entrance + word-by-word + exit
GROUPS.forEach(function(group, gi) {
  var groupEl = document.getElementById("cg-" + gi);

  // Group entrance: make visible
  tl.set(groupEl, { visibility: "visible", opacity: 1 }, group.start);

  // Each word pops in
  group.words.forEach(function(w, wi) {
    var wordEl = document.getElementById("cw-" + gi + "-" + wi);
    tl.fromTo(wordEl,
      { opacity: 0, scale: 0.72, y: 14 },
      { opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.2)" },
      w.start
    );
  });

  // Group exit — hard kill (non-negotiable)
  tl.to(groupEl,   { opacity: 0, scale: 0.95, duration: 0.12, ease: "power2.in" }, group.end - 0.12);
  tl.set(groupEl,  { opacity: 0, visibility: "hidden" }, group.end);
});

// Self-lint (runs at init — remove after verified)
GROUPS.forEach(function(group, gi) {
  var el = document.getElementById("cg-" + gi);
  if (!el) return;
  tl.seek(group.end + 0.01);
  var cs = window.getComputedStyle(el);
  if (cs.opacity !== "0" && cs.visibility !== "hidden") {
    console.warn("[caption-lint] group " + gi + " still visible at t=" + (group.end + 0.01).toFixed(2));
  }
});
tl.seek(0);
```

### Key accent words to mark yellow for cricket reels

- All numbers: `71`, `221`, `72`, `10`, `44`, `90`, `99`
- Percentages: any word ending in `%`
- Brand: `Crickzen`, `TrueOdds`

Adjust `accentClass()` per reel.

---

## Step 9 — Quality Checklist

After render, verify:

- [ ] Audio plays from T=0 (no silence gap at start)
- [ ] Captions appear at the right moment for each word
- [ ] Yellow on numbers and brand names
- [ ] No caption group lingers past its `group.end`
- [ ] No caption covers the hero element of its scene (reposition `bottom` value if needed)
- [ ] `npx hyperframes lint` passes (0 errors)
- [ ] Total duration matches audio length ± 0.5s
- [ ] File size under 50MB (run `compress-output.sh` if needed)

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Audio starts late | Check `data-start="0"` on `<audio>` element |
| Captions overlap scene content | Increase `bottom` in `#caption-layer` (try `560px` or `680px`) |
| Words mis-transcribed | Manually correct WORDS array timestamps |
| `small.en` garbled output | Retry with `--model medium.en` |
| Data-duration mismatch | Set `data-duration` to audio duration + 0.5s buffer |
| Caption group still visible | Ensure hard `tl.set` kill exists at `group.end` |
| TTS too fast / robotic | Add commas and periods in script for natural pauses |

---

## Reuse Checklist (Each New Reel)

1. [ ] Copy script template → fill in match details
2. [ ] Run `npx hyperframes tts "..." -o assets/vo-<name>.wav -v bm_george`
3. [ ] Run `npx hyperframes transcribe assets/vo-<name>.wav --model small.en -o assets/vo-<name>.json`
4. [ ] Quality-check transcript
5. [ ] Paste WORDS array into composition JS
6. [ ] Update `accent` classifier for this reel's numbers
7. [ ] Update `data-duration` on composition root
8. [ ] Update `<audio>` src and data-duration
9. [ ] Lint → Render → Screenshot → Check captions visible
