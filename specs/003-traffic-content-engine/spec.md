# Feature Specification: Traffic Content Engine

**Feature Branch**: `003-traffic-content-engine`  
**Created**: 2026-05-18  
**Status**: Draft  
**Project**: TrueOddsML Video Studio

---

## Overview

TrueOddsML needs to evolve from a single pre-match reel generator into a reusable match-day content engine that can publish multiple reel formats from the same source-of-truth data. The goal is traffic growth first: more original match-day content, faster iteration on hooks, clearer CTAs, and stronger proof that the model reads matches better than generic score apps or fake certainty pages.

This feature adds five traffic-oriented content formats plus an optional post-match educational replay:

1. Pre-match reel
2. Toss update reel
3. Turning-point reel
4. Probability swing reel
5. Post-match proof reel
6. Optional `market_edge_replay` asset for educational price-vs-probability analysis

Pipeline:
```text
match source + tracker + optional live snapshots
-> normalized match-day pack
-> hook variants + language variants + single CTA
-> render-ready reel payloads
-> captions / voiceover / publishing copy
```

---

## User Scenarios & Testing

### User Story 1 — Generate A Match-Day Pack (Priority: P1)

A content operator supplies one structured match-day input and gets multiple content-ready payloads for the same match.

**Why this priority**: The repo currently produces one pre-match reel at a time, which is too narrow for traffic growth.

**Independent Test**: Run the pack generator and confirm it emits a manifest plus per-template JSON assets for every supplied stage.

**Acceptance Scenarios**:

1. **Given** one valid match-day pack input, **When** the generator runs, **Then** it writes render-ready payloads for each declared content stage.
2. **Given** a stage is missing from the source input, **When** the generator runs, **Then** it skips that stage rather than fabricating unsupported content.
3. **Given** the same match is generated twice, **When** the generator runs, **Then** outputs are deterministic except for timestamps.

---

### User Story 2 — Produce Hook Variants Automatically (Priority: P1)

A content operator wants multiple first-two-second hook options from one source narrative so they can test non-follower reach and retention.

**Why this priority**: Hook quality directly affects scroll-stop rate and is more important to traffic growth than minor rendering polish.

**Independent Test**: Generate a content pack and confirm each asset contains exactly three distinct hook variants matched to its template.

**Acceptance Scenarios**:

1. **Given** a pre-match or turning-point payload, **When** hook generation runs, **Then** three template-appropriate hook variants are included.
2. **Given** a post-match proof payload, **When** hook generation runs, **Then** at least one hook emphasizes accountability or audit rather than hype.
3. **Given** a template has a required score or probability shift field, **When** the hook generator runs, **Then** those fields can be referenced without manual rewriting.

---

### User Story 3 — Support English And Hinglish Variants (Priority: P1)

A content operator wants both English and Hinglish publishing copy from the same source asset.

**Why this priority**: The audience is India-first and regional language adaptation is a traffic lever, not just formatting.

**Independent Test**: Generate a pack with two languages and confirm each asset writes one English and one Hinglish payload with language-appropriate captions and voiceover copy.

**Acceptance Scenarios**:

1. **Given** `languages=["english","hinglish"]`, **When** the generator runs, **Then** both language variants are created for every emitted asset.
2. **Given** a CTA mode such as `join_telegram`, **When** language variants are created, **Then** the CTA stays single-purpose while adapting the copy per language.
3. **Given** score or probability values, **When** Hinglish copy is generated, **Then** numeric data stays precise even if the surrounding sentence structure changes.

---

### User Story 4 — Turn Tracker Data Into Public Proof Content (Priority: P1)

A content operator wants prediction history to become reusable proof content rather than staying buried in a tracker JSON file.

**Why this priority**: Public accountability is a core differentiator for the brand.

**Independent Test**: Generate a proof asset from a reconciled tracker entry and confirm the payload includes model pick, probability, result, and audit framing.

**Acceptance Scenarios**:

1. **Given** a reconciled tracker entry, **When** proof generation runs, **Then** it creates a post-match proof payload with the original probability and final outcome.
2. **Given** a pending tracker entry, **When** proof generation runs, **Then** it must not pretend the final result exists.
3. **Given** a close-loss or close-win scenario, **When** proof copy is generated, **Then** it can frame “tight match / honest uncertainty” instead of forcing a fake victory narrative.

---

### User Story 5 — Educational Replay Of Model Edge (Priority: P2)

A content operator wants to show when the model’s read diverged from public reaction or market pricing during a past match without promising gambling profits.

**Why this priority**: This can create strong curiosity and proof content, but it must remain educational and probability-first.

**Independent Test**: Generate a `market_edge_replay` payload from supplied probability and price snapshots and confirm it produces an educational replay with explicit risk language.

**Acceptance Scenarios**:

1. **Given** model probability and public or market probability snapshots, **When** replay generation runs, **Then** it outputs “edge opened here / edge closed here” framing rather than guaranteed return claims.
2. **Given** missing price or probability snapshots, **When** replay generation runs, **Then** it skips the replay rather than inventing an edge.
3. **Given** a replay payload is generated, **When** copy is rendered, **Then** it includes an educational or risk-aware note and must not claim “we would have made X money.”

---

### Edge Cases

- What if only pre-match data exists? -> Generate pre-match only and skip live/post-match assets.
- What if tracker data is pending? -> Allow pre-match or audit teaser content, but not settled proof.
- What if CTA copy already includes multiple actions? -> Normalize to one CTA mode and rewrite output accordingly.
- What if a stage lacks required inputs such as score snapshot or probability delta? -> Skip that stage with a clear manifest note.
- What if a replay suggests a profitable betting path? -> Present it as an educational `market_edge_replay` only, never a guaranteed or promised return narrative.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept one structured match-day pack input and emit per-stage content payloads.
- **FR-002**: System MUST support at least these template IDs: `prematch`, `toss_update`, `turning_point`, `probability_swing`, `post_match_proof`.
- **FR-003**: System MUST generate exactly three hook variants for every emitted asset.
- **FR-004**: System MUST support at least `english` and `hinglish` language variants.
- **FR-005**: System MUST normalize every asset to one CTA mode only.
- **FR-006**: System MUST be able to bootstrap pack data from the local prediction tracker for proof-oriented assets.
- **FR-007**: System MUST write a manifest artifact that explains which assets were generated and which stages were skipped.
- **FR-008**: System MUST preserve the same model probability and match facts across every derived asset for that stage.
- **FR-009**: System MUST support an optional `market_edge_replay` asset only when explicit probability or price snapshots are provided.
- **FR-010**: System MUST NOT generate guaranteed-profit, stake-sizing, or “made money” claims in replay outputs.

### Key Entities

- **MatchDayPack**: source-of-truth input for one match and its optional stages.
- **ReelAssetPayload**: render-ready JSON for one template and one language.
- **HookVariantSet**: exactly three short hook options tied to one asset.
- **TrackerProofSource**: normalized tracker-backed record for proof content.
- **MarketEdgeReplay**: optional educational replay payload using model and public/price snapshots.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: One command can generate a manifest plus per-stage reel payloads for a match-day pack without manual copy rewriting.
- **SC-002**: Every emitted asset has exactly one CTA and exactly three hook variants.
- **SC-003**: A reconciled tracker entry can be converted into a post-match proof payload using local files only.
- **SC-004**: Educational replay outputs never contain guaranteed-profit or fixed-return language.

---

## Assumptions

- The current pre-match reel remains the first production-ready visual template.
- New stage payloads can ship before every new visual composition is fully implemented.
- Post-match proof is only trustworthy when sourced from reconciled tracker data or explicit manual result input.
- The optional replay feature is for educational “edge reading” content, not betting automation or profit promises.
