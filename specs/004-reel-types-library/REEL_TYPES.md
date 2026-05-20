# Crickzen TrueOdds — Reel Types Library

> **Reference doc for all repeatable reel formats.**
> For each new match, pick the applicable reel types from this library and generate the input JSON.

---

## Who We're Talking To

| Audience | Pain Point | What They Get |
|---|---|---|
| **Casual fan** | "I watch the score and still get surprised" | Pre-match read + turning point = feel smarter |
| **Analytics lover** | "I read stats but can't combine them" | Probability = unified output of all their stats |
| **Serious trader** | "I don't know WHEN to enter" | Model vs market divergence = entry window signal |

---

## Core Philosophy Lines (use in every reel)

- **"The score is visible. The probability is hidden."**
- **"Don't guess the match. Read the probability."**
- **"Casual fans watch the score. Smart fans watch probability."**
- **"Every over changes the match."**

---

## Reel Type 1 — PRE-MATCH READ
**When:** Before every match (30–60 mins before toss)
**Audience:** Both (casual + analytics)
**Goal:** Build identity, position app as intelligence layer

**Template fields:**
- Public pick vs Model pick
- Win probability %
- 3 data reasons (venue, H2H, historical blend)
- Hook: "The public thinks X. The data says Y."

**Real example:** MI vs PBKS (Dharamsala, May 2026) — Public: PBKS, Model: MI 52%

**Script skeleton:**
```
HOOK:    "The public backs [TEAM A]. Our model says [TEAM B] at [X]%."
MIDDLE:  [3 reasons — venue, H2H, phase risk]
CLOSE:   "Not a baba call. A probability read."
CTA:     "Join Telegram for pre-match drops."
```

---

## Reel Type 2 — THE ENTRY WINDOW (Market Edge)
**When:** Post-match (within 24h) when model diverged from market mid-chase
**Audience:** Serious traders + analytics lovers
**Goal:** Show WHEN the gap opened between model and market

**Template fields:**
- Timeline: 3–4 over snapshots with model_prob + public_prob_est
- Entry window over (where gap was largest)
- Signals that drove the gap (required rate, dots, venue)
- Result (chaser won or lost — both work)

**Real example (BEST):** RCB vs SRH, Chepauk, April 14 2021
- Over 14: SRH 102/2, model 79%, market ~82%
- Over 16: SRH 115/2, model 55%, market ~65% ← ENTRY WINDOW (10% gap)
- Over 17: SRH 116/5, model 19% — 3 wickets, 1 run
- Result: RCB won by 6 runs
- Key line: "Score went up. Wickets stayed 2. Probability fell silently."

**Other candidates from real data:**
| Match | Date | Venue | Entry Over | Prob Drop | Result |
|---|---|---|---|---|---|
| KKR vs KXIP | 2020-10-10 | Sheikh Zayed Stadium | 17→19 | 92%→22% | KKR won (KXIP lost by 2) |
| GT vs LSG | 2023-04-22 | Ekana Stadium, Lucknow | 16→19 | 90%→22% | GT won |
| DC vs LSG | 2022-04-07 | DY Patil, Mumbai | 15→18 | 86%→23% | DC won |
| LSG vs RR | 2023-04-19 | Sawai Mansingh, Jaipur | 13→16 | 79%→24% | LSG won |

**Script skeleton:**
```
HOOK:    "[SCORE] after [OVER] overs. Looked comfortable."
         "The model was already warning."
MIDDLE:  Over-by-over timeline (3 snapshots)
         "Score: going up. Wickets: same. Probability: falling."
REVEAL:  "Over [X]: 3 wickets. Match done."
         "The model saw it [Y] overs earlier."
CLOSE:   "This is the entry window. Model vs market gap."
CTA:     "Educational replay. Read the probability."
```

---

## Reel Type 3 — THE SCORE LIED (Turning Point)
**When:** Post-match when score looked fine but collapse was predictable
**Audience:** Casual fans (highest reach reel)
**Goal:** Stop-the-scroll hook, build identity

**Template fields:**
- The "looks fine" snapshot (score / wickets)
- The hidden pressure signals (3 bullet points)
- The collapse moment
- Philosophy line

**Real example:** RCB vs SRH 2021 — "102/2 looked fine. Required rate was quietly at 9 and rising."

**Script skeleton:**
```
HOOK:    "[SCORE]. [OVERS] gone. Looked comfortable."
         "Every fan thought the chase was on."
PROBLEM: "The scoreboard said COMFORTABLE."
         "The model said PRESSURE BUILDING."
REVEAL:  [3 signals that score missed]
CLOSER:  "Casual fans watched the score."
         "Crickzen users watched the probability drop."
CTA:     "The score is visible. The probability is hidden."
```

---

## Reel Type 4 — ANALYTICS DECODER
**When:** Once a week (educational / authority content)
**Audience:** Analytics lovers (highest share potential)
**Goal:** Position app as "unified layer above all other stats"

**Template fields:**
- 4–5 stats a fan already reads (run rate, wagon wheel, etc.)
- Show each stat alone = partial picture
- Show probability = combined output
- Feature showcase (6 model inputs)

**Script skeleton:**
```
HOOK:    "You already read: run rate, wagon wheel, phase splits."
         "But what do they all MEAN together?"
MIDDLE:  [Each stat → one thing. Prob → everything combined.]
         [Show the 6 model inputs]
CLOSER:  "You're not replacing your analytics."
         "You're adding the layer that unifies them."
CTA:     "One number. Every phase. Every over."
```

---

## Reel Type 5 — POST-MATCH PROOF (Audit)
**When:** After every match result
**Audience:** New/skeptical audience (trust builder)
**Goal:** Credibility without hype — "we publish every result"

**Template fields:**
- Pre-match call (public pick / model pick / probability)
- Actual result
- Result label: `correct_pick` / `tight_read` / `miss_acknowledged`
- Honest audit note

**Real example:** MI vs PBKS — Model: MI 52%, Winner: PBKS
- Result label: `tight_read` — "We didn't call a one-sided match. It was close. That was right."

**Script skeleton:**
```
HOOK:    "Before [MATCH] we published this:"
         [Show the pre-match card]
MIDDLE:  "Here's what happened."
         "[WINNER] won. Here's the audit."
HONEST:  "We [got it right / called it tight / missed]."
         "Not hype. Honest probability."
CLOSE:   "Every result audited. Every call published."
CTA:     "Audit page on Telegram. Every match."
```

---

## Reel Type 6 (NEW) — THE POWERPLAY SIGNAL
**When:** Post-match when chasing team had 0 wickets at powerplay end despite a tough target
**Audience:** Casual fans + analytics lovers (high reach — counterintuitive insight)
**Goal:** Show that wickets in hand > run rate at powerplay. Build "model sees what score can't" identity.

**Template fields:**
- Inn1 final score (target set)
- Powerplay score + wickets + required rate at over 6
- Model probability at powerplay end vs public estimate
- First wicket impact (model drop)
- Chain to model 90%+ moment

**Real example (REAL PROD DATA — May 19 2026, YESTERDAY):**
**LSG vs RR, IPL 2026 — 64th Match**
- LSG set 220/5. RR chasing 221.
- Over 6 (powerplay end): 71/0, RRR=10.7 — public: RR ~35%. **Model: 72%.**
- Over 7: first wicket falls → model drops to 44% (28% in one ball)
- Over 11: 137/1, model 90%. Over 12: 166/1, model 99%.
- Result: RR won.
- Data source: `ipl_live_ml_1_history.json` (live prediction recording, 933 rows)
- Input JSON: `inputs/packs/lsg-vs-rr-may19-2026/powerplay_signal_english.json`

**Key line:** "Score said 71 off 221 = behind. Model said: 0 wickets = 10 wickets × 84 balls = 72%."
**Wicket impact proof:** One wicket changed probability by 28%. Score didn't change. Resource did.

**Script skeleton:**
```
HOOK:    "Yesterday. Chasing [TARGET]. Over 6. Score: [X]/0."
         "You thought: too far behind."
         "Model thought: [Y]%."
REVEAL:  "Why?"
         "0 wickets at powerplay = [N] wickets × [B] balls remaining."
         "The score was showing the past. Model was reading the resources."
PROOF:   "Over [A]: 1 wicket fell → model dropped [D]% in one ball."
         "Over [B]: [SCORE] → model [Z]%. Match done."
RESULT:  "[TEAM] won. Model called it at over 6."
CTA:     "Don't watch the score. Read the probability."
```

---

## Reel Type 8 — TOSS INTELLIGENCE
**When:** Right after toss (live / near-live)
**Audience:** Both
**Goal:** Show toss impact is often smaller than crowd reaction

**Template fields:**
- Pre-toss probability
- Post-toss probability
- Did toss swing the model? (usually: not much)
- Why or why not (venue, pitch, team depth)

**Script skeleton:**
```
HOOK:    "Toss is in. [TEAM] chose to [bat/field]."
         "The crowd just reacted. The model stayed calm."
MIDDLE:  "Probability before toss: [X]%"
         "Probability after toss: [Y]%"
         "Swing: [+Z%] / [barely moved]"
CLOSE:   "Toss matters. But not as much as the market thinks."
CTA:     "Pre-match read drops before every toss."
```

---

## Recurring Content Engine

| Timing | Reel Type | Trigger |
|---|---|---|
| 60 min before match | Type 1 — Pre-match read | Every match |
| Right after toss | Type 6 — Toss intelligence | Every match |
| Mid-match (optional) | Type 3 — Score Lied (live) | If turning point happens |
| Within 24h post-match | Type 2 — Entry Window | If model-market gap was >8% |
| Within 24h post-match | Type 6 — Powerplay Signal | If 0-wicket powerplay AND target 180+ |
| Within 24h post-match | Type 5 — Post-match proof | Every match |
| Once per week | Type 4 — Analytics Decoder | Best example from the week |
| Once per week | Type 2 — Entry Window replay | Best divergence of the week |

---

## Input JSON Schema per Reel Type

Each reel needs an input JSON in `inputs/packs/[match-slug]/[stage]_[language].json`.

Stages map to templates:
- `prematch` → Type 1
- `powerplay_signal` → Type 6
- `toss_update` → Type 8
- `turning_point` → Type 3
- `probability_swing` → Type 3 variant
- `market_edge_replay` → Type 2
- `post_match_proof` → Type 5

Type 4 (Analytics Decoder) uses a separate `analysis_reel` template.

---

## File Naming Convention

```
inputs/packs/[team-a-slug]-vs-[team-b-slug]-[venue-city]-[year]/
  prematch_english.json
  prematch_hinglish.json
  toss_update_english.json
  turning_point_english.json
  probability_swing_english.json
  market_edge_replay_english.json
  post_match_proof_english.json
  manifest.json
```

---

## Notes for Future Matches

1. **Run `find_entry_window.py`** after each match to score the probability drop
2. **Entry window threshold**: use if model-market gap was ≥8% for ≥2 overs
3. **Hinglish versions**: same data, voiceover rewritten in Hinglish (mix)
4. **Both outcomes work**: chaser winning or losing can both tell the story
5. **Safe framing always**: never claim guaranteed returns — frame as "educational replay" and "probability reading"
