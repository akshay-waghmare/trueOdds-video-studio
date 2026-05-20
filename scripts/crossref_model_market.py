"""Cross-reference betx21 market odds with ML model probability for CSK vs SRH May 18 2026."""
import gzip, json
from pathlib import Path
from datetime import datetime, timezone

BETX21 = Path(r"C:\Users\ADMINS\Documents\projects\betx21.live\ipl_matches_download\2026-05-18")
ML_DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")

# ── 1. Load scores ─────────────────────────────────────────────────────────────
score_lines = []
with gzip.open(BETX21 / "35612043_scores.jsonl.gz", "rb") as f:
    for line in f:
        try:
            score_lines.append(json.loads(line))
        except Exception:
            pass

# Build over → timestamp map for innings 2
ov_to_time = {}
for r in score_lines:
    s2 = r.get("s2", "")
    if not s2:
        continue
    try:
        ov = int(float(s2.split("(")[1].rstrip(")")))
        ts = r["t"]
        if ov not in ov_to_time:
            ov_to_time[ov] = ts
    except Exception:
        pass

print("Innings 2 over → timestamp:")
for ov, ts in sorted(ov_to_time.items()):
    print(f"  Over {ov:>2}: {ts}")

# ── 2. Load market odds ─────────────────────────────────────────────────────────
odds_lines = []
with gzip.open(BETX21 / "35612043_odds.jsonl.gz", "rb") as f:
    for line in f:
        try:
            odds_lines.append(json.loads(line))
        except Exception:
            pass

# Build timestamp → (srh_back_price, srh_implied_prob)
# Runner order from first active record: runner[0]=CSK(t1), runner[1]=SRH(t2)
odds_map = {}
for r in odds_lines:
    if r.get("mt") != "matchOdds":
        continue
    runners = r.get("r", [])
    if len(runners) < 2:
        continue
    srh_runner = runners[1]  # t2 = SRH
    backs = srh_runner.get("b", [])
    if backs:
        best_back = backs[0][0]  # best back price
        implied = 1.0 / best_back if best_back > 0 else 0
        odds_map[r["t"]] = (best_back, implied)

# ── 3. Load ML model data (ODM history – all innings 1, but SRH batting = chase)
ml_raw = json.loads((ML_DATA / "ipl_live_ml_1_odm_history.json").read_text())
srh_bat = [e for e in ml_raw if "Sunrisers" in e.get("batting_team", "")]

# Group by over, take last entry
ml_by_over = {}
for e in srh_bat:
    ov = e["over"]
    ml_by_over[ov] = e  # overwrite = last entry per over

# ── 4. Cross-reference ─────────────────────────────────────────────────────────
print()
print("Cross-reference: Model prob vs Market implied (SRH win%)")
print(f"{'Over':>5}  {'Score':>10}  {'ModelProb':>9}  {'MktBestBack':>11}  {'MktImplied':>10}  {'Gap':>6}")
print("-" * 65)

sorted_ts = sorted(odds_map.keys())

for ov in sorted(ml_by_over.keys()):
    e = ml_by_over[ov]
    model_prob = e["bat_prob"]
    sc = e["score"]
    wk = e["wickets"]
    score_str = f"{sc}/{wk}"

    # Find closest market odds just before this over's timestamp
    ov_ts = ov_to_time.get(ov)
    mkt_prob = None
    mkt_back = None
    if ov_ts:
        # Find the last odds record before this timestamp
        for ts in reversed(sorted_ts):
            if ts <= ov_ts:
                mkt_back, mkt_prob = odds_map[ts]
                break

    if mkt_prob is not None:
        gap = model_prob - mkt_prob
        gap_str = f"{gap:+.0%}"
    else:
        mkt_prob_str = "  n/a"
        mkt_back_str = "   n/a"
        gap_str = "   n/a"

    if mkt_prob is not None:
        print(f"  {ov:>3}  {score_str:>10}  {model_prob:>8.1%}  {mkt_back:>10.2f}  {mkt_prob:>9.1%}  {gap_str:>6}")
    else:
        print(f"  {ov:>3}  {score_str:>10}  {model_prob:>8.1%}  {'n/a':>10}  {'n/a':>9}  {gap_str:>6}")
