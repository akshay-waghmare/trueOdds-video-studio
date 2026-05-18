# Implementation Plan: Traffic Content Engine

**Branch**: `003-traffic-content-engine` | **Date**: 2026-05-18 | **Spec**: `specs/003-traffic-content-engine/spec.md`

---

## Summary

Build a traffic-oriented content engine inside TrueOddsML Video Studio so one match source can produce multiple render-ready reel payloads, hook variants, language variants, and proof-oriented publishing assets. The first implementation focuses on data contracts, content-pack generation, and proof reuse. Visual composition expansion can layer on top of these payloads.

---

## Technical Context

**Language/Version**: Python 3, existing Node.js and HyperFrames pipeline  
**Primary Dependencies**: Standard library, existing tracker artifacts, existing Streamlit app  
**Storage**: Local filesystem under `inputs/`, `data/`, and `renders/`  
**Testing**: Python unit tests for pack normalization, hook generation, CTA normalization, tracker bootstrap  
**Target Platform**: Local CLI + Streamlit-assisted operations for Instagram / Telegram content production  
**Constraints**: No guaranteed-return or stake-sizing language; preserve single-source probability facts; deterministic outputs  
**Scale/Scope**: Content pack generation and payload scaffolding first; additional visual compositions follow

---

## Project Structure

```text
trueodds-video-studio/
│
├── specs/
│   └── 003-traffic-content-engine/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
│
├── inputs/
│   ├── match_day_pack.json
│   ├── match_day_pack.schema.json
│   └── packs/
│       └── <match-slug>/
│           ├── manifest.json
│           ├── prematch_english.json
│           ├── prematch_hinglish.json
│           └── ...
│
├── scripts/
│   └── build_match_day_pack.py
│
├── tests/
│   └── test_match_day_pack.py
│
├── README.md
└── app.py
```

---

## Phase Roadmap

### Phase 1 — Pack Contract

Define the source schema for match-day stages, CTA modes, language modes, and optional educational replay inputs.

### Phase 2 — Generator Core

Build a CLI generator that:
- validates source input
- bootstraps from tracker when requested
- writes per-stage, per-language payloads
- creates three hook variants per asset
- normalizes to a single CTA

### Phase 3 — Proof Reuse

Turn tracker-backed predictions into post-match proof payloads and reusable audit copy.

### Phase 4 — Replay Safety Layer

Support optional educational `market_edge_replay` payloads with explicit safety language and no guaranteed-return framing.

### Phase 5 — UX And Documentation

Document the workflow and optionally surface it in Streamlit once the generator contract is stable.

---

## Notes and Boundaries

- The first pass generates content payloads, not every final visual composition.
- The repo’s existing `prematch-prediction.html` remains the only full render template until the new compositions are built.
- `market_edge_replay` is intentionally framed as educational analysis of price-vs-probability divergence. It must not become a “how much we would have made” calculator.
- Traffic growth depends on repeatable content volume; therefore generator speed and copy consistency matter more than animation novelty in the first phase.
