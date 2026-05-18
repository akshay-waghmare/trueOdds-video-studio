# Tasks: IPL Intelligence Products

**Input**: `specs/002-ipl-intelligence-products/spec.md` and `plan.md`  
**Feature**: `002-ipl-intelligence-products`  
**Scope**: Match Intelligence Card, Venue Intelligence Database, Player Role Intelligence, Prediction Tracker

---

## T001 - Create derived data directories

Create `data/intelligence/` and `inputs/cards/` for generated artifacts.

**Done when**: Both directories exist and are documented in the plan.

---

## T002 - Implement normalization rules

Add canonical team and venue alias handling and registry-backed player identity helpers.

**Done when**: Historical aliases collapse into consistent canonical keys.

---

## T003 - Build venue intelligence aggregation

Parse `data/ipl_json` and compute venue-level:
- average first-innings score
- historical second-innings win rate
- phase wicket mix
- pace vs spin wicket share where bowling style can be inferred
- behaviour label and confidence

**Done when**: `data/intelligence/venue_intelligence.json` is generated with metadata and sample sizes.

---

## T004 - Build player role intelligence aggregation

Compute player-level:
- best batting position
- powerplay / middle / death batting splits
- chase vs defend batting splits
- venue record
- opponent record
- descriptive role tags

**Done when**: `data/intelligence/player_role_intelligence.json` is generated with registry IDs and confidence metadata.

---

## T005 - Generate match intelligence card payload

Create a command that outputs one card JSON for a requested fixture using historical venue and player aggregates plus explicit probability-source metadata.

**Done when**: A fixture command writes `inputs/cards/match_intelligence_<fixture>.json`.

---

## T006 - Add prediction tracker commands

Implement commands to:
1. record a prediction
2. reconcile a result

**Done when**: `data/intelligence/prediction_tracker.json` stores pending and settled entries.

---

## T007 - Add tests for core aggregation rules

Cover:
- venue normalization
- player registry identity fallback
- phase classification
- Brier score calculation

**Done when**: The Python test file passes locally.

---

## T008 - Update README

Document the new commands, output artifacts, and product boundaries.

**Done when**: A new user can build intelligence outputs and track predictions from the README alone.

---

## T009 - Add Streamlit intelligence panel

Expose the intelligence workflow in `app.py`:
- build venue/player intelligence
- generate match intelligence card
- preview card metrics and player signals
- record prediction tracker entry

**Done when**: A user can operate the intelligence products from the Streamlit app without using CLI commands for the build and record steps.

---

## T010 - Filter low-confidence card signals

Remove broad low-confidence placeholder player signals from safe/risky/trump/avoid outputs.

**Done when**: Match cards surface only medium/high confidence player signals, and avoid picks require high confidence.
