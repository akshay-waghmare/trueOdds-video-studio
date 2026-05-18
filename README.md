# TrueOddsML Video Studio

Spec-first video factory for TrueOddsML prediction reels.

MVP pipeline:

```text
JSON -> validate -> HyperFrames -> MP4 -> inspect -> screenshots
```

## Quickstart

Install HyperFrames once:

```bash
npx skills add heygen-com/hyperframes
```

1. Edit `inputs/match_prediction.json`.
2. Validate:

```bash
node scripts/validate-input.js
```

3. Render:

```bash
node scripts/render-prematch.js
```

4. Inspect and capture screenshots:

```bash
node scripts/inspect-render.js
```

## Traffic Content Engine

This repo can also generate multi-stage reel payloads for traffic growth, not just a single pre-match reel.

Detailed documentation:

- `docs/TRAFFIC_CONTENT_ENGINE.md`

### Build a match-day pack

```bash
python scripts/build_match_day_pack.py --input inputs/match_day_pack.json
```

Outputs:

- `inputs/packs/<match-slug>/manifest.json`
- `inputs/packs/<match-slug>/prematch_english.json`
- `inputs/packs/<match-slug>/prematch_hinglish.json`
- additional per-stage files for any supplied `toss_update`, `turning_point`, `probability_swing`, `post_match_proof`, or `market_edge_replay`

What it does:

- generates exactly 3 hook variants per asset
- writes English and Hinglish variants
- enforces a single CTA mode per asset
- turns tracker-backed predictions into proof content when reconciled

### Bootstrap proof content from the tracker

```bash
python scripts/build_match_day_pack.py --tracker-match-id gt-vs-srh-narendra-modi-stadium
```

Notes:

- pending tracker entries generate pack data without fake settled proof
- `market_edge_replay` is intentionally educational and must not be used for guaranteed-return claims

## Rules

- First template only: `prematch-prediction`.
- Use JSON-only changes per match.
- Do not use official IPL or team logos in v1.
- Keep output 1080x1920, H.264, 18-22 seconds, under 50MB.

## IPL intelligence products

This repo can now build local IPL intelligence artifacts from `data/ipl_json` for:

- Match Intelligence Card
- Venue Intelligence Database
- Player Role Intelligence
- Prediction Tracker

The separate Fantasy Decision Engine is **not** included in this feature.

### Build venue and player intelligence

```bash
python scripts/build_ipl_intelligence.py build-all
```

Outputs:

- `data/intelligence/venue_intelligence.json`
- `data/intelligence/player_role_intelligence.json`

Notes:

- `venue_behaviour` is inferred from historical scoring and wicket patterns
- `pace_wicket_pct` / `spin_wicket_pct` remain `null` until bowling-style metadata is added
- every venue and player summary includes sample-size context or confidence

### Generate a match intelligence card payload

```bash
python scripts/build_ipl_intelligence.py build-card --match "GT vs SRH" --venue "Ahmedabad"
```

Output:

- `inputs/cards/match_intelligence_gt-vs-srh.json`

The card includes:

- labeled probability source (`historical_blend_v1`)
- toss-impact context
- expected first-innings score and wickets
- venue behaviour summary
- descriptive player signals such as safe/risky, trump pick, and avoid pick

### Prediction tracker

Record a prediction from a generated card:

```bash
python scripts/track_prediction.py record --card inputs/cards/match_intelligence_gt-vs-srh.json
```

Reconcile the final result later:

```bash
python scripts/track_prediction.py reconcile --match-id gt-vs-srh-narendra-modi-stadium --winner GT --notes "Venue trend and top-order edge held."
```

Tracker output:

- `data/intelligence/prediction_tracker.json`

It stores the original prediction, settlement status, final winner, and Brier score.

### Streamlit intelligence panel

```bash
streamlit run app.py
```

Use **IPL Intelligence Products** to:

1. Build venue/player intelligence from `data/ipl_json`
2. Generate a match intelligence card for a fixture
3. Preview expected score, toss context, venue behaviour, and player signals
4. Record the card into the prediction tracker

Settlement is still handled by the CLI reconcile command so the final winner is explicit and auditable.
