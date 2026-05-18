# AGENTS.md - TrueOddsML Video Studio

## What This Project Is

TrueOddsML Video Studio is a cricket prediction reel factory. It takes a JSON prediction file and produces a 20-second 9:16 vertical video using HyperFrames.

MVP pipeline:

```text
match_prediction.json -> validate -> HyperFrames -> MP4 -> inspect -> screenshots
```

No raw footage. No AI host. No video-use in v1.

---

## Stack

| Tool | Role |
|------|------|
| HyperFrames | HTML/CSS/JS -> MP4 renderer |
| Node.js | Pipeline scripts |
| FFmpeg | Screenshots and compression |
| ffprobe | MP4 metadata inspection |
| Python 3 | Probability agent + Streamlit UI |
| GitHub Copilot SDK | AI narrative generation (no API key — `gh auth login`) |
| OpenAI / GitHub Models | Fallback AI when Copilot SDK unavailable |

---

## Project Layout

```text
trueodds-video-studio/
├── specs/001-prematch-prediction-reel/
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
├── inputs/
│   ├── match_prediction.json
│   └── match_prediction.schema.json
├── compositions/
│   └── prematch-prediction.html
├── scripts/
│   ├── validate-input.js
│   ├── render-prematch.js
│   ├── inspect-render.js
│   ├── compress-output.sh
│   └── probability_agent.py
├── assets/
├── renders/
│   ├── prematch_prediction.mp4
│   └── screenshots/
├── AGENTS.md
├── DESIGN.md
└── README.md
```

---

## Pipeline

### Step 1 - Install HyperFrames once

```bash
npx skills add heygen-com/hyperframes
```

### Step 2 - AI Probability Agent (optional but recommended)

Instead of manually filling in the prediction JSON, run the agent:

```bash
# CLI
python scripts/probability_agent.py "GT vs SRH" --venue "Ahmedabad"

# Or click "🤖 Analyse Match" in the Streamlit app
streamlit run app.py
```

**What it does:**
1. Mines `CRICSHEET_IPL_PATH` (Cricsheet IPL JSON files) for overall, H2H, and venue stats
2. Applies a blended Bradley-Terry formula: `35% overall + 35% H2H + 30% venue` (clamped 50–85%)
3. Calls GitHub Copilot SDK to generate: `public_team`, `model_pick`, 3 reasons, explanation

**Output JSON:**
```json
{
  "match":           "GT vs SRH",
  "model_pick":      "GT",
  "public_team":     "SRH",
  "probability":     63,
  "reasons":         ["...", "...", "..."],
  "explanation":     "One sentence.",
  "stats":           { ... },
  "stats_available": true
}
```

**Auth (one-time):**
```bash
gh auth login          # Copilot SDK — recommended, no API key
# OR
export GITHUB_TOKEN=ghp_...   # GitHub Models fallback
```

**Cricsheet data path:**
Set `CRICSHEET_IPL_PATH` in a `.env` file at the project root:
```
CRICSHEET_IPL_PATH=C:\path\to\ipl_json
```
Default: `C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\ipl_json`

**Blended formula:**
- When ≥ 3 venue H2H games: `prob = overall×0.35 + h2h×0.35 + venue×0.30`
- When < 3 venue games: `prob = overall×0.50 + h2h×0.50`
- Clamped to 50–85% (never predicts a certainty)

### Step 3 - Edit the JSON

Edit `inputs/match_prediction.json`. Do not invent extra fields unless `inputs/match_prediction.schema.json` is updated first.

Required fields:
- `match`
- `public_team`
- `model_pick`
- `probability`
- `reasons`
- `cta`

### Step 4 - Validate input

```bash
node scripts/validate-input.js
```

### Step 5 - Render

```bash
node scripts/render-prematch.js
```

### Step 6 - Inspect video and capture screenshots

```bash
node scripts/inspect-render.js
```

This must verify:
- 1080x1920
- 18-35 seconds (duration matches TTS audio length dynamically)
- H.264
- under 50MB

It must capture screenshots at:

| Time | Expected state |
|------|----------------|
| 0s | Hook visible |
| 3s | Public favourite shown |
| 6s | Model pick revealed |
| 9s | Probability meter visible |
| 12s | Reason 1 and 2 visible |
| 15s | Reason 3 visible |
| 18s | CTA visible |
| 20s | End frame clean |

### Step 7 - Compress if needed

Only compress if `prematch_prediction.mp4` is over 50MB.

```bash
bash scripts/compress-output.sh
```

---

## Design / Legal Rules

- Use dark cinematic backgrounds.
- Use bold white/yellow typography.
- Position TrueOddsML as probability-first and anti-baba.
- Do not use official IPL or team logos in v1.
- Use text badges like `MI`, `KKR`, and `RCB`.
- The brand focus is TrueOddsML, not IPL/team-dependent visuals.

---

## Agent Operating Prompt

```text
You are operating the TrueOddsML Video Studio pipeline.

1. Read AGENTS.md, DESIGN.md, and specs/001-prematch-prediction-reel/tasks.md.
2. (Optional) Run probability agent: python scripts/probability_agent.py "TEAM1 vs TEAM2" --venue "VenueName"
3. Edit inputs/match_prediction.json with model_pick, public_team, probability, reasons, cta.
4. Validate it with: node scripts/validate-input.js
5. Render with: node scripts/render-prematch.js
6. Inspect with: node scripts/inspect-render.js
7. If output is over 50MB, compress with: bash scripts/compress-output.sh
8. Report the final MP4 path, file size, metadata result, and screenshot checkpoint paths.
9. Do not use official IPL/team logos.
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| HyperFrames not found | Run `npx skills add heygen-com/hyperframes` |
| JSON validation fails | Fix `inputs/match_prediction.json`; do not bypass validation |
| Render command fails | Check `scripts/render-prematch.js` and HyperFrames CLI availability |
| ffprobe missing | Install FFmpeg and ensure `ffprobe` is in PATH |
| Screenshots missing | Confirm `renders/prematch_prediction.mp4` exists before inspection |
| File over 50MB | Run `bash scripts/compress-output.sh` |
| Copilot SDK missing | `pip install "git+https://github.com/github/copilot-sdk.git#subdirectory=python"` then `gh auth login` |
| Agent returns no JSON | Check Copilot auth, or set `GITHUB_TOKEN` in `.env` for GitHub Models fallback |
| No Cricsheet data | Set `CRICSHEET_IPL_PATH` in `.env`; agent falls back to AI-only mode |
