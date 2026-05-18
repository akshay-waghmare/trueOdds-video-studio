# Implementation Plan: IPL Intelligence Products

**Branch**: `002-ipl-intelligence-products` | **Date**: 2026-05-14 | **Spec**: `specs/002-ipl-intelligence-products/spec.md`

---

## Summary

Build a local IPL analytics layer inside TrueOddsML Video Studio that mines `data/ipl_json`, normalizes historical records, and emits reusable JSON outputs for venue intelligence, player role intelligence, match intelligence cards, and prediction tracking. The implementation stays inside this repo and does not modify the external predictor repository.

---

## Technical Context

**Language/Version**: Python 3, Node.js for existing pipeline scripts  
**Primary Dependencies**: Standard library, Streamlit app, existing `scripts/probability_agent.py`  
**Storage**: Local filesystem (`data/`, `inputs/`, `renders/`)  
**Testing**: Python unit tests for normalization and aggregation rules, existing repo commands where applicable  
**Target Platform**: Local CLI + JSON outputs for website, image, reel, Telegram, and future app surfaces  
**Constraints**: No fantasy engine in this feature; no unsupported “pitch type” claims; confidence metadata required  
**Scale/Scope**: Products 1, 3, 4, and 5 only

---

## Project Structure

```text
trueodds-video-studio/
│
├── specs/
│   └── 002-ipl-intelligence-products/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
│
├── data/
│   ├── ipl_json/
│   └── intelligence/
│       ├── venue_intelligence.json
│       ├── player_role_intelligence.json
│       └── prediction_tracker.json
│
├── inputs/
│   └── cards/
│       └── match_intelligence_*.json
│
├── scripts/
│   ├── build_ipl_intelligence.py
│   └── track_prediction.py
│
├── tests/
│   └── test_ipl_intelligence.py
│
├── app.py
├── README.md
└── AGENTS.md
```

---

## Phase Roadmap

### Phase 1 — Data Contract and Normalization

Define canonical team and venue normalization, registry-based player identity, and minimum-sample confidence rules.

### Phase 2 — Aggregation Engine

Build the IPL analytics script that parses `data/ipl_json` and computes:
- venue scoring and chase aggregates
- wicket mix and phase metrics
- player batting/bowling phase splits
- chase vs defend and venue/opponent splits

### Phase 3 — Product Outputs

Emit:
- `data/intelligence/venue_intelligence.json`
- `data/intelligence/player_role_intelligence.json`
- `inputs/cards/match_intelligence_<fixture>.json`
- `data/intelligence/prediction_tracker.json`

### Phase 4 — Tracker Workflow

Add commands to record a pre-match prediction and later reconcile a final result with Brier score and outcome notes.

### Phase 5 — Documentation and Usability

Document the commands, output files, and product boundaries in `README.md`.

---

## Notes and Boundaries

- `pitch_type` will be represented as inferred `venue_behaviour`.
- Player tags on the match card remain descriptive, not fantasy recommendations.
- Probability output may reuse the existing historical blend agent; the source must be labeled in the output.
- Rain-affected and malformed matches should be excluded from baselines where standard innings assumptions break.
