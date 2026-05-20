"""
Build precise cross-reference for CSK vs SRH May 18 2026.
Find exact market odds at key overs (7-9 entry window, over 13 exit).
"""
import gzip, json
from pathlib import Path
from datetime import datetime, timedelta

BETX21 = Path(r"C:\Users\ADMINS\Documents\projects\betx21.live\ipl_matches_download\2026-05-18")
ML_DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")
IST_OFFSET = timedelta(hours=5, minutes=30)

# ── Load scores ────────────────────────────────────────────────────────────────
score_lines = []
with gzip.open(BETX21 / "35612043_scores.jsonl.gz", "rb") as f:
    for line in f:
        try:
            score_lines.append(json.loads(line))
        except Exception:
            pass

# Over → first UTC timestamp for innings 2
ov_to_utc = {}
for r in score_lines:
    s2 = r.get("s2", "")
    if not s2:
        continue
    try:
        ov = int(float(s2.split("(")[1].rstrip(")")))
        ts = r["t"]
        if ov not in ov_to_utc:
            ov_to_utc[ov] = ts
    except Exception:
        pass

# ── Load ML history ─────────────────────────────────────────────────────────────
ml_raw = json.loads((ML_DATA / "ipl_live_ml_1_odm_history.json").read_text())
srh_bat = [e for e in ml_raw if "Sunrisers" in e.get("batting_team", "")]

# Per-over: last ML entry (highest confidence)
ml_by_ov = {}
for e in srh_bat:
    ov = e["over"]
    ml_by_ov[ov] = e  # overwrite = latest

# ── Load market odds ────────────────────────────────────────────────────────────
odds_lines = []
with gzip.open(BETX21 / "35612043_odds.jsonl.gz", "rb") as f:
    for line in f:
        try:
            odds_lines.append(json.loads(line))
        except Exception:
            pass

match_odds = [(r["t"], r) for r in odds_lines if r.get("mt") == "matchOdds" and r.get("ms") != "suspended"]
match_odds.sort(key=lambda x: x[0])

def get_mkt_at(utc_ts):
    """Return (csk_back, srh_back, csk_implied, srh_implied) for the last active odds record before utc_ts."""
    last = None
    for ts, r in match_odds:
        if ts <= utc_ts:
            last = r
        else:
            break
    if not last:
        return None
    runners = last.get("r", [])
    if len(runners) < 2:
        return None
    csk = runners[0]
    srh = runners[1]
    csk_back = csk.get("b", [[0]])[0][0] if csk.get("b") else None
    srh_back = srh.get("b", [[0]])[0][0] if srh.get("b") else None
    csk_imp  = 1 / csk_back if csk_back else None
    srh_imp  = 1 / srh_back if srh_back else None
    return csk_back, srh_back, csk_imp, srh_imp

# ── Print full over table ───────────────────────────────────────────────────────
print("CSK vs SRH — May 18 2026 — Innings 2 (SRH chasing 181)")
print(f"{'Ov':>3}  {'Score':>8}  {'ModelSRH%':>10}  {'MktSRHBack':>10}  {'MktSRH%':>8}  {'ModelCSH%':>10}  {'GapCSK':>7}")
print("-" * 72)

for ov in sorted(set(ml_by_ov.keys()) | set(ov_to_utc.keys())):
    e = ml_by_ov.get(ov)
    if not e:
        continue
    sc  = e["score"]
    wk  = e["wickets"]
    srh_model = e["bat_prob"]
    csk_model = 1 - srh_model

    utc_ts = ov_to_utc.get(ov)
    mkt = get_mkt_at(utc_ts) if utc_ts else None

    if mkt:
        csk_back, srh_back, csk_imp, srh_imp = mkt
        gap_csk = csk_model - csk_imp
        flag = " ◄ ENTRY" if gap_csk > 0.35 else ("  EXIT?" if -0.15 < gap_csk < 0 and ov >= 12 else "")
        print(f"  {ov:>2}  {sc}/{wk:>4}  {srh_model:>9.1%}  {srh_back:>10.2f}  {srh_imp:>7.1%}  {csk_model:>9.1%}  {gap_csk:>+6.0%}{flag}")
    else:
        print(f"  {ov:>2}  {sc}/{wk:>4}  {srh_model:>9.1%}  {'n/a':>10}  {'n/a':>7}  {csk_model:>9.1%}  {'n/a':>6}")

print()
print("KEY TRADE LOGIC:")
print("  ENTRY: Back CSK when ModelCSK% >> MktCSK% (large positive gap)")
print("  EXIT:  Lay CSK (= back SRH) when model flips toward SRH")
print()
print("RESULT: SRH won by 1 wicket (181/5 in 19 overs)")
