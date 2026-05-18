# Feature Specification: Pre-Match Prediction Reel

**Feature Branch**: `001-prematch-prediction-reel`  
**Created**: 2026-05-11  
**Status**: Draft  
**Project**: TrueOddsML Video Studio

---

## Overview

TrueOddsML is a cricket prediction brand built on probability, not baba-style guesses. The first content unit is a **Pre-Match Prediction Reel** — a 20-second vertical short-form video (9:16 / 1080×1920) generated entirely from a JSON prediction file using HyperFrames. No raw footage required in Phase 1.

Pipeline:
```
Model output → match_prediction.json → HyperFrames → prematch_prediction.mp4
```

---

## User Scenarios & Testing

### User Story 1 — Generate a Reel from JSON (Priority: P1)

A content operator drops a `match_prediction.json` file into `inputs/`, runs the agent, and receives a rendered `prematch_prediction.mp4` in `renders/`.

**Why this priority**: Core value proposition. Everything else depends on this working.

**Independent Test**: Drop the example JSON, run the composition, confirm MP4 is produced at 1080×1920.

**Acceptance Scenarios**:

1. **Given** a valid `match_prediction.json` in `inputs/`, **When** the agent runs HyperFrames on `compositions/prematch-prediction.html`, **Then** a 18–22 second MP4 is rendered to `renders/`.
2. **Given** the rendered video, **When** inspected at 0s, 3s, 6s, 9s, 12s, 15s, 18s, and 20s, **Then** hook, public favourite, model pick, probability meter, reason cards, CTA, and clean end frame are visible at the expected moments.
3. **Given** a different JSON file (new match), **When** re-rendered with the same template, **Then** all content updates correctly with zero template edits.

---

### User Story 2 — Reusable Template for Any Match (Priority: P2)

The HTML/CSS/JS composition is fully data-driven. Changing only the JSON file produces a completely different reel without touching the template.

**Why this priority**: Without reusability, every reel is a one-off — kills the whole factory model.

**Independent Test**: Render two different JSONs with the same template and confirm both produce correct, distinct outputs.

**Acceptance Scenarios**:

1. **Given** Template `prematch-prediction.html`, **When** `match` field changes from "MI vs KKR" to "CSK vs RCB", **Then** new render shows correct team names throughout.
2. **Given** `probability` changes from 62 to 78, **When** rendered, **Then** probability meter animates to the correct position.
3. **Given** `reasons` array is updated, **When** rendered, **Then** all three reason cards display the new text.

---

### User Story 3 — Agent-Operable Workflow (Priority: P3)

An AI agent (Copilot / Claude / Codex) can operate the full pipeline end-to-end: read JSON, invoke HyperFrames, confirm output, report key-frame screenshots.

**Why this priority**: Manual operation is fine for now; agent automation unlocks scale.

**Independent Test**: Paste the agent prompt into Copilot, confirm it produces MP4 without human intervention beyond the initial prompt.

**Acceptance Scenarios**:

1. **Given** the `AGENTS.md` instructions, **When** an agent reads them, **Then** it knows exactly which commands to run and in what order.
2. **Given** agent runs the pipeline, **When** render completes, **Then** agent captures screenshots of at least 3 key frames (opening, probability moment, CTA).

---

### Edge Cases

- What if `probability` is outside 0–100? → Clamp to valid range, do not crash.
- What if `reasons` has fewer than 3 items? → Show available cards, hide extras gracefully.
- What if HyperFrames is not installed? → `AGENTS.md` must include install instructions.
- What if the JSON has missing keys? → `scripts/validate-input.js` fails before render with explicit field errors.
- What if a team name resembles a protected brand? → Use text badges only; do not use official IPL or team logos in v1.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST read prediction data exclusively from `inputs/match_prediction.json`.
- **FR-001A**: System MUST validate `inputs/match_prediction.json` against `inputs/match_prediction.schema.json` before rendering.
- **FR-002**: Template MUST render a 1080×1920 (9:16) video, 18–22 seconds long.
- **FR-003**: Video MUST include: match name, public favourite, model pick, probability meter (animated), 3 reason cards, TrueOddsML watermark, CTA text.
- **FR-004**: Probability meter MUST animate from 0 to the given probability value.
- **FR-005**: Template MUST be fully data-driven — only JSON changes between renders.
- **FR-006**: Output MP4 MUST be saved to `renders/prematch_prediction.mp4`.
- **FR-007**: `AGENTS.md` MUST contain complete agent instructions for operating the pipeline.
- **FR-008**: Style MUST be dark cinematic — dark background, bold white/yellow typography, no light/pastel themes.
- **FR-009**: Version 1 MUST use text-based team badges only; official IPL/team logos MUST NOT be used.
- **FR-010**: Screenshot verification MUST capture frames at 0s, 3s, 6s, 9s, 12s, 15s, 18s, and 20s.

### Key Entities

- **MatchPrediction**: `template`, `match`, `public_team`, `model_pick`, `probability` (0–100), `reasons` (array, exactly 3 for ideal output), `cta` (string).
- **Composition**: The `prematch-prediction.html` HyperFrames template file.
- **Render**: The output MP4 at a fixed path in `renders/`.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A new reel can be generated from a fresh JSON in under 5 minutes (agent-operated).
- **SC-002**: The same template produces correct output for at least 5 different match JSONs without modification.
- **SC-003**: Output video plays correctly on Instagram Reels / YouTube Shorts (1080×1920, H.264, ≤50MB).
- **SC-004**: An AI agent following `AGENTS.md` completes validation, render, metadata inspection, screenshot capture, and compression decision with zero human interventions beyond the initial prompt.

---

## Assumptions

- Phase 1 does not use raw talking-head footage — HyperFrames only.
- HyperFrames is installed via `npx skills add heygen-com/hyperframes` or equivalent.
- FFmpeg is available for any post-render compression.
- Mobile/web upload of renders is out of scope for Phase 1.
- Brand assets (logo, fonts) will be added to `assets/` manually before first render.
- Team visuals in v1 are text badges such as `MI`, `KKR`, and `RCB`, not official IPL or team marks.
