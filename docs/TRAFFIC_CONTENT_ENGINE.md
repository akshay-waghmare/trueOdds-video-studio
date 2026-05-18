# Traffic Content Engine

## What Was Added

This repo now has a traffic-oriented content layer on top of the original pre-match reel pipeline.

The first pass added:

- a new feature spec set in `specs/003-traffic-content-engine/`
- a source contract in `inputs/match_day_pack.json`
- a schema in `inputs/match_day_pack.schema.json`
- a generator CLI in `scripts/build_match_day_pack.py`
- tests in `tests/test_match_day_pack.py`
- Streamlit scaffolding in `app.py`
- an npm shortcut in `package.json`

The purpose is to turn one match input into multiple content assets for traffic growth, instead of producing only one pre-match reel.

## Supported Content Stages

The generator currently supports these payload types:

- `prematch`
- `toss_update`
- `turning_point`
- `probability_swing`
- `post_match_proof`
- `market_edge_replay`

Important boundary:

- `market_edge_replay` is educational only.
- It is for showing where model probability diverged from crowd or price perception.
- It must not be used for guaranteed-profit or “we made money” claims.

## What The Generator Produces

For every emitted stage, the generator writes:

- exactly 3 hook variants
- exactly 1 CTA mode
- English and/or Hinglish variants
- voiceover copy
- caption copy

It also writes a `manifest.json` that lists which assets were generated and which stages were skipped.

## Source File

Main source file:

- `inputs/match_day_pack.json`

Key fields:

- `match`
- `venue`
- `public_team`
- `model_pick`
- `probability`
- `reasons`
- `cta_mode`
- `languages`

Optional blocks:

- `toss_update`
- `turning_point`
- `probability_swing`
- `post_match_proof`
- `market_edge_replay`

## Usage

### 1. Build from the sample pack

```bash
python scripts/build_match_day_pack.py --input inputs/match_day_pack.json
```

or

```bash
npm run build:pack
```

Output goes to:

```text
inputs/packs/<match-slug>/
```

Typical files:

- `manifest.json`
- `prematch_english.json`
- `prematch_hinglish.json`
- `turning_point_english.json`
- `post_match_proof_english.json`

### 2. Bootstrap proof content from the tracker

If a prediction has already been recorded in `data/intelligence/prediction_tracker.json`, you can build a pack from the tracker entry:

```bash
python scripts/build_match_day_pack.py --tracker-match-id gt-vs-srh-narendra-modi-stadium
```

Behavior:

- pending tracker entries do not fabricate settled proof
- settled tracker entries can produce `post_match_proof`

### 3. Use from Streamlit

Run:

```bash
streamlit run app.py
```

In the app:

1. Generate or load a normal prediction first.
2. Go to `Traffic Content Pack`.
3. Choose languages.
4. Choose one CTA mode.
5. Click `Scaffold pack JSON`.
6. Add optional live/proof/replay blocks into `inputs/match_day_pack.json`.
7. Click `Build content pack`.

The app will show the current pack JSON and the last built manifest.

## CTA Modes

Only one CTA mode is allowed per asset.

Supported values:

- `join_telegram`
- `follow`
- `comment_match`
- `check_live_score`

This is intentional. The content pack normalizes every asset to a single action so the funnel stays clear.

## Recommended Workflow

For a normal match day:

1. Start with `prematch`.
2. Add `toss_update` after toss.
3. Add `turning_point` during the match.
4. Add `probability_swing` for a sharp move.
5. Add `post_match_proof` after settlement.

Use `market_edge_replay` only when you have explicit probability or price snapshots and want to explain divergence safely.

## Files To Extend Next

The content payload layer is now in place. The next build step is visual composition coverage for the new stages.

Most likely next files:

- `compositions/turning-point.html`
- `compositions/post-match-proof.html`
- `scripts/render-<stage>.js`

Right now, the original full HyperFrames render path still exists only for:

- `compositions/prematch-prediction.html`

So the generator currently creates content payloads for the new stages first, and full rendered visuals for those stages still need to be added.

## Validation Done

Validated in this repo with:

```bash
python -m py_compile app.py scripts/build_match_day_pack.py
pytest tests/test_match_day_pack.py
python scripts/build_match_day_pack.py --input inputs/match_day_pack.json
```
