# Implementation Plan: Pre-Match Prediction Reel

**Branch**: `001-prematch-prediction-reel` | **Date**: 2026-05-11 | **Spec**: `specs/001-prematch-prediction-reel/spec.md`

---

## Summary

Build a reusable HyperFrames HTML/CSS/JS composition that reads `inputs/match_prediction.json` and renders a 20-second 1080×1920 cricket prediction reel. The template is data-driven — only the JSON changes per match. An AI agent can operate the full pipeline end-to-end using `AGENTS.md`.

---

## Technical Context

**Language/Version**: HTML5 / CSS3 / Vanilla JS (HyperFrames composition)  
**Primary Dependencies**: HyperFrames (`npx skills add heygen-com/hyperframes`), Node.js scripts, FFmpeg/ffprobe  
**Storage**: Local filesystem (`inputs/`, `renders/`)  
**Testing**: JSON schema validation + MP4 metadata inspection + exact screenshot checkpoints  
**Target Platform**: HyperFrames renderer → MP4 → Instagram Reels / YouTube Shorts  
**Project Type**: Video template / agent-operated pipeline  
**Performance Goals**: Render in <5 minutes; output ≤50MB MP4  
**Constraints**: 1080×1920, 18–22 seconds, H.264, dark cinematic style  
**Scale/Scope**: MVP = 1 template; later expansion = 5 reusable templates

---

## Project Structure

```text
trueodds-video-studio/
│
├── specs/
│   └── 001-prematch-prediction-reel/
│       ├── spec.md          ← feature specification
│       ├── plan.md          ← this file
│       └── tasks.md         ← task breakdown
│
├── inputs/
│   ├── match_prediction.json       ← data input (changes per match)
│   └── match_prediction.schema.json ← locked input contract
│
├── compositions/
│   └── prematch-prediction.html    ← HyperFrames template (built in Phase 2)
│
├── scripts/
│   ├── validate-input.js           ← validates JSON before render
│   ├── render-prematch.js          ← renders MP4 through HyperFrames
│   ├── inspect-render.js           ← checks metadata + screenshots
│   └── compress-output.sh          ← optional FFmpeg compression
│
├── assets/
│   ├── logo/                       ← TrueOddsML logo files
│   ├── backgrounds/                ← dark cinematic BG images/videos
│   ├── sounds/                     ← optional audio stings
│   └── fonts/                      ← brand fonts
│
├── renders/
│   ├── prematch_prediction.mp4     ← output video
│   └── screenshots/                ← checkpoint screenshots
│
├── AGENTS.md                       ← agent operating instructions
├── DESIGN.md                       ← visual design decisions & style guide
└── README.md                       ← project overview and quickstart
```

---

## Phase Roadmap

### Phase 1 — Project Setup
Initialize repo, install HyperFrames, create sample JSON, write AGENTS.md skeleton.

### Phase 2 — Composition (Core Template)
Build `compositions/prematch-prediction.html` with all required sections:
- Dark cinematic background
- Match name header
- Public favourite vs Model pick split
- Animated probability meter
- 3 reason cards
- TrueOddsML watermark
- CTA footer

### Phase 3 — Data Binding
Wire all visual elements to JSON fields. Ensure template works with any valid `match_prediction.json`.

### Phase 4 — Render & Validate
Run HyperFrames render, inspect key frames, fix layout issues, confirm MP4 spec (1080×1920, H.264, 18–22s).

Screenshot checkpoints:

| Time | Expected Visible State |
|------|------------------------|
| 0s | Hook visible |
| 3s | Public favourite shown |
| 6s | Model pick revealed |
| 9s | Probability meter visible |
| 12s | Reason 1 and 2 visible |
| 15s | Reason 3 visible |
| 18s | CTA visible |
| 20s | End frame clean |

### Phase 5 — Agent Instructions
Complete `AGENTS.md` with full pipeline walkthrough so any AI agent can operate this without human guidance.

---

## Future Phases

| Phase | Addition |
|-------|----------|
| Phase 6 | Voiceover + subtitles |
| Phase 7 | Raw AI host video → video-use trim → HyperFrames |
| Phase 8 | Toss Shift template |
| Phase 9 | Fake Baba Roast template |
| Phase 10 | Post-Match Proof template |
| Phase 11 | Weekly Audit template |
