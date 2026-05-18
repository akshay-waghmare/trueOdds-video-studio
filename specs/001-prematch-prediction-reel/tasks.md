# Tasks: Pre-Match Prediction Reel

**Input**: `specs/001-prematch-prediction-reel/spec.md` and `plan.md`  
**Feature**: `001-prematch-prediction-reel`  
**MVP Pipeline**: `JSON -> validate -> HyperFrames -> MP4 -> inspect -> screenshots`
**Implementation Status**: T001-T014 completed for the MVP pass. T015-T019 added for Phase 6 (Voiceover + Subtitles).

---

## T001 - Initialize project structure

Create folders: `specs/`, `inputs/`, `compositions/`, `scripts/`, `assets/`, `renders/`, and `renders/screenshots/`.

**Done when**: Folder tree matches the project structure in `plan.md`.

---

## T002 - Create sample input JSON

Create `inputs/match_prediction.json` with dummy MI vs KKR data.

**Done when**: JSON includes `match`, `public_team`, `model_pick`, `probability`, `reasons`, and `cta`.

---

## T003 - Create JSON schema

Create `inputs/match_prediction.schema.json` and define required fields.

**Done when**: Schema rejects missing required fields, invalid probability values, and malformed `reasons`.

---

## T004 - Write DESIGN.md

Define visual style:
- dark cinematic background
- bold typography
- anti-baba probability positioning
- yellow/white accent
- no official team logos in v1

**Done when**: Design rules are explicit enough for an agent to build the first composition.

---

## T005 - Write AGENTS.md skeleton

Explain agent pipeline:
1. Read JSON
2. Validate input
3. Render HyperFrames composition
4. Take screenshots
5. Inspect video metadata
6. Save MP4 in `renders/`

**Done when**: A fresh agent knows the exact scripts and file paths to use.

---

## T006 - Build basic HyperFrames composition

Create `compositions/prematch-prediction.html` with static dummy data.

**Done when**: The composition opens with a 1080x1920 layout and visible hook, matchup, pick, probability, reasons, watermark, and CTA.

---

## T007 - Add timeline animation

Implement 20-second sequence:
- 0-3s hook
- 3-6s model disagreement
- 6-9s prediction reveal
- 9-16s reason cards
- 16-20s CTA

**Done when**: Timeline has clear state changes at each checkpoint.

---

## T008 - Bind composition to JSON

Replace hardcoded values with `inputs/match_prediction.json` data.

**Done when**: Changing only JSON produces different text and probability output.

---

## T009 - Add probability meter

Animate probability number and circular/bar meter.

**Done when**: Meter animates from 0 to the JSON probability value and clamps invalid values safely.

---

## T010 - Add render script

Create `scripts/render-prematch.js` that renders `renders/prematch_prediction.mp4`.

**Done when**: A single command can render the MP4 from the current JSON and composition.

---

## T011 - Add validation script

Create `scripts/validate-input.js` to check required JSON fields before render.

**Done when**: Invalid JSON stops the pipeline before HyperFrames is called.

---

## T012 - Add screenshot verification

Capture frames at 0, 3, 6, 9, 12, 15, 18, and 20 seconds.

**Done when**: Screenshots are saved in `renders/screenshots/` with clear names.

---

## T013 - Inspect final MP4

Verify:
- 1080x1920
- 18-22 seconds
- H.264
- file size under 50MB

**Done when**: `scripts/inspect-render.js` reports pass/fail for each requirement.

---

## T014 - Final agent dry run

Give the agent a new `match_prediction.json` and confirm it can produce a new reel without editing template code.

**Done when**: Same template renders a second match successfully from JSON-only changes.

---

## T015 - Write voiceover script generator

Create `scripts/generate-voiceover.js` that reads `inputs/match_prediction.json` and builds a ~38-word narration script dynamically. Converts probabilities to English words, spells team acronyms letter by letter for TTS.

**Done when**: Running the script produces `assets/voiceover-script.txt` with a natural narration script.

---

## T016 - Generate TTS voiceover

`generate-voiceover.js` runs `npx hyperframes tts` with `bm_george` voice at 0.95x speed to produce `assets/voiceover.wav`.

**Done when**: `assets/voiceover.wav` exists and is under 20 seconds.

---

## T017 - Transcribe voiceover to word-level timestamps

`generate-voiceover.js` runs `npx hyperframes transcribe` and outputs a cleaned `assets/transcript.json` with per-word `{ text, start, end }` entries. Validates transcript quality (rejects >20% music tokens).

**Done when**: `assets/transcript.json` exists with ≥5 word entries.

---

## T018 - Wire voiceover + captions into composition

Update `compositions/prematch-prediction.html`:
- `<audio>` element referencing `assets/voiceover.wav`
- `#caption-layer` div at bottom of stage
- `buildCaptionLayer()` builds DOM from `window.__TRANSCRIPT__`
- `buildTimeline()` adds karaoke tweens (yellow active word, 3 words per group)

**Done when**: Rendered video plays voiceover in sync with karaoke captions.

---

## T019 - Update render pipeline for voiceover

Update `scripts/render-prematch.js` to call `generate-voiceover.js`, inject `window.__TRANSCRIPT__` into HTML, and copy `assets/voiceover.wav` to `.render-cache/assets/`.

**Done when**: `node scripts/render-prematch.js` produces an MP4 with voiceover and captions end-to-end.
