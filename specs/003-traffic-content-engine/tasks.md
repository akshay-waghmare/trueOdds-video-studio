# Tasks: Traffic Content Engine

**Input**: `specs/003-traffic-content-engine/spec.md` and `plan.md`  
**Feature**: `003-traffic-content-engine`  
**Scope**: Multi-stage reel payloads, hooks, language variants, tracker proof reuse, educational replay contract

---

## T001 - Create match-day pack contract

Create `inputs/match_day_pack.json` and `inputs/match_day_pack.schema.json`.

**Done when**: The source format supports pre-match, toss, turning point, swing, proof, CTA mode, and language selection.

---

## T002 - Implement pack generator CLI

Create `scripts/build_match_day_pack.py`.

**Done when**: One command reads a match-day pack and writes a manifest plus per-stage output files.

---

## T003 - Add hook variant generation

Generate exactly three hooks per asset tailored to each template type.

**Done when**: Every output JSON contains `hook_variants` with three distinct lines.

---

## T004 - Add English and Hinglish outputs

Generate language-specific caption and voiceover copy from the same source data.

**Done when**: At least `english` and `hinglish` variants are created for emitted assets.

---

## T005 - Enforce one CTA per asset

Normalize output to a single CTA mode and rewrite copy accordingly.

**Done when**: No generated asset contains mixed CTA intents such as follow + Telegram + comment together.

---

## T006 - Bootstrap proof assets from tracker

Allow the generator to derive post-match proof content from `data/intelligence/prediction_tracker.json`.

**Done when**: A reconciled tracker entry can be turned into a proof asset without manual copy writing.

---

## T007 - Add educational replay contract

Support an optional `market_edge_replay` payload that uses explicit probability or price snapshots.

**Done when**: Replay outputs stay educational and include risk-aware language instead of profit claims.

---

## T008 - Add generator tests

Cover:
- CTA normalization
- hook count
- tracker bootstrap
- replay safety wording

**Done when**: The new Python tests pass locally.

---

## T009 - Update README

Document the traffic content engine workflow and commands.

**Done when**: A repo user can generate a match-day pack and inspect the outputs from the README alone.
