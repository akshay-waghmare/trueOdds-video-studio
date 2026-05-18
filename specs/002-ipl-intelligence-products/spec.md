# Feature Specification: IPL Intelligence Products

**Feature Branch**: `002-ipl-intelligence-products`  
**Created**: 2026-05-14  
**Status**: Draft  
**Project**: TrueOddsML Video Studio

---

## Overview

TrueOddsML needs reusable IPL intelligence outputs derived from historical Cricsheet data in `data/ipl_json` and aligned with the current production predictor context from `machine_learning_bbl_009-odi-mc-predictor`. This feature adds a local analytics layer for four products:

1. Match Intelligence Card
2. Venue Intelligence Database
3. Player Role Intelligence
4. Prediction Tracker

The separate Fantasy Decision Engine is explicitly out of scope for this feature.

Pipeline:
```
Cricsheet IPL JSON -> normalize -> aggregate -> derived intelligence JSON -> CLI outputs / tracker records
```

---

## User Scenarios & Testing

### User Story 1 — Build Venue Intelligence (Priority: P1)

A content operator runs one command and gets venue-level summaries with first-innings scoring, chase tendency, wicket mix, and behaviour labels.

**Why this priority**: Venue context is reusable across multiple products and does not require external live feeds.

**Independent Test**: Run the venue build command and confirm a JSON artifact is created with canonical venue keys, counts, averages, and confidence labels.

**Acceptance Scenarios**:

1. **Given** valid Cricsheet IPL files in `data/ipl_json`, **When** the venue build command runs, **Then** it writes a venue intelligence JSON artifact with per-venue aggregates and metadata.
2. **Given** the same venue appears under multiple raw names, **When** the artifact is built, **Then** those rows are normalized into one canonical venue entry.
3. **Given** a venue has a small sample, **When** the artifact is built, **Then** the output includes sample size and a low-confidence label instead of an unqualified claim.

---

### User Story 2 — Build Player Role Intelligence (Priority: P1)

A content operator can inspect player-level phase and role summaries keyed by stable player IDs rather than ambiguous names.

**Why this priority**: Player intelligence is required for match cards and future premium products.

**Independent Test**: Run the player build command and confirm a JSON artifact exists with registry-backed player IDs, display names, phase splits, batting position summaries, and opponent/venue aggregates.

**Acceptance Scenarios**:

1. **Given** a player appears under name variants across seasons, **When** the artifact is built, **Then** their records remain grouped under one registry ID.
2. **Given** player batting records span multiple positions, **When** the artifact is built, **Then** the output reports the most common batting slot and supporting counts.
3. **Given** a player has too few balls or innings in a slice, **When** the artifact is built, **Then** the output includes low confidence and does not overstate the split.

---

### User Story 3 — Generate Match Intelligence Card Input (Priority: P1)

A content operator supplies two teams and an optional venue and receives a ready-to-use match intelligence JSON payload with prediction context and descriptive player tags.

**Why this priority**: This converts raw analytics into the closest thing to a production content unit.

**Independent Test**: Run the card generation command for a fixture and confirm it produces one JSON file containing probability, venue behaviour, expected score, expected wickets, toss context, and player tags.

**Acceptance Scenarios**:

1. **Given** a fixture like `GT vs SRH`, **When** the card generator runs, **Then** it outputs a card JSON with the teams, probability source, expected score, expected wickets, and venue chase context.
2. **Given** limited venue or player samples, **When** the card generator runs, **Then** the card flags low-confidence sections instead of silently fabricating precision.
3. **Given** player tag output, **When** the card is produced, **Then** labels are descriptive (`anchor`, `aggressor`, `death specialist`, `form hot`, `form cold`) rather than pretending to be a full fantasy optimizer.

---

### User Story 4 — Track Predictions Publicly (Priority: P2)

A content operator records a pre-match prediction and later reconciles the outcome for accountability reporting.

**Why this priority**: Public tracking is a differentiator and supports trust.

**Independent Test**: Record a prediction row, reconcile it with a final result, and confirm the tracker artifact stores both the original prediction and the settled outcome.

**Acceptance Scenarios**:

1. **Given** a generated match card or prediction JSON, **When** the record command runs, **Then** a tracker entry is appended with model pick, probability, source, and timestamp.
2. **Given** a completed match result, **When** the reconcile command runs, **Then** the tracker entry is updated with the winner, hit/miss result, and Brier score.
3. **Given** a match has not yet been reconciled, **When** tracker data is viewed, **Then** the entry remains pending rather than showing a fake result.

---

### Edge Cases

- What if venue names differ between seasons? -> Normalize with an alias map before aggregation.
- What if player names differ or collide? -> Use `info.registry.people` IDs as the primary key.
- What if a match is rain-affected or not a standard two-innings result? -> Exclude it from venue and player baselines that depend on normal innings completion.
- What if sample sizes are tiny? -> Output `sample_size` and `confidence` for every aggregate that feeds a product.
- What if the probability source is simple historical blend rather than the full live predictor? -> Label the source explicitly in the card output.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST read historical IPL data from `data/ipl_json`.
- **FR-002**: System MUST normalize team and venue aliases before producing aggregates.
- **FR-003**: System MUST key player intelligence on Cricsheet registry IDs where available.
- **FR-004**: System MUST generate a venue intelligence artifact with canonical venue entries, averages, rates, sample sizes, and confidence labels.
- **FR-005**: System MUST generate a player role intelligence artifact with batting position summaries, phase splits, chase vs defend splits, venue record, and opponent record.
- **FR-006**: System MUST generate a match intelligence card JSON for a requested fixture using historical venue and player aggregates plus an explicit probability source.
- **FR-007**: System MUST NOT implement or claim a full fantasy decision engine in this feature.
- **FR-008**: System MUST generate or maintain a prediction tracker artifact that supports recording predictions and reconciling outcomes later.
- **FR-009**: System MUST include schema metadata such as `schema_version`, `generated_at`, and source summary in each derived artifact.
- **FR-010**: System MUST expose confidence or sample-size context for every user-facing aggregate used in products.

### Key Entities

- **VenueIntelligence**: canonical venue record with run, wicket, chase, and behaviour metrics.
- **PlayerRoleProfile**: player record keyed by registry ID with role and split summaries.
- **MatchIntelligenceCard**: fixture-specific output with venue context, prediction context, and descriptive player tags.
- **PredictionTrackerEntry**: persisted pre-match prediction and later result reconciliation.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: One command builds venue intelligence and player intelligence artifacts from the local IPL dataset without manual editing.
- **SC-002**: A fixture command produces a match intelligence card JSON with no missing required fields for a standard IPL matchup.
- **SC-003**: Tracker commands can record and reconcile at least one prediction end-to-end using local files only.
- **SC-004**: Derived artifacts preserve explicit sample size and confidence metadata rather than emitting unsupported certainty.

---

## Assumptions

- `data/ipl_json` is the local historical source of truth for this feature.
- The external predictor repo remains read-only context for model-feature alignment; this feature does not modify it.
- Venue behaviour labels are inferred from historical scoring and wicket patterns, not direct pitch labels supplied by the source data.
- Player tags are descriptive intelligence labels, not fantasy-team recommendations.
