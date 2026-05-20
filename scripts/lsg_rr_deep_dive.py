"""
Deep-dive: LSG vs RR May 19 2026 — innings 2 over-by-over.
Show: score, wickets, runs_needed, RRR, bat_prob, bowl_prob per ball.
"""
import json
from pathlib import Path

DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")

d = json.loads((DATA / "ipl_live_ml_1_history.json").read_text())
history = d["history"]

TARGET = 221
TOTAL_BALLS = 120

inn2 = [e for e in history if e.get("innings") == 2]
print(f"LSG vs RR — May 19 2026 — RR chasing {TARGET}")
print(f"  Total inn2 entries: {len(inn2)}")
print()

# Show key entries — one per over
prev_ov = -1
print(f"{'Overs':>6}  {'Score':>8}  {'Need':>5}  {'Balls':>5}  {'RRR':>5}  {'BatProb':>8}  {'BowlProb':>9}  {'Note'}")
print("-" * 72)
for e in inn2:
    ov = e.get("overs", 0)
    sc = e.get("score", 0)
    wk = e.get("wickets", 0)
    bp = e.get("bat_prob", 0)
    boP = e.get("bowl_prob", 0)
    balls_done = int(ov * 6)
    balls_left = TOTAL_BALLS - balls_done
    needed = TARGET - sc
    rrr = needed / balls_left * 6 if balls_left > 0 else 0

    if int(ov) != prev_ov:
        note = ""
        if int(ov) == 6:
            note = "← POWERPLAY END"
        elif int(ov) == 8:
            note = "← BIG OVER"
        elif int(ov) == 11:
            note = "← MODEL 99%"
        print(f"  {ov:>5.1f}  {sc}/{wk:>4}  {needed:>5}  {balls_left:>5}  {rrr:>5.1f}  {bp:>7.1%}  {boP:>8.1%}  {note}")
        prev_ov = int(ov)

# Also show the final few entries
print()
print("Last 5 entries:")
for e in inn2[-5:]:
    ov = e.get("overs", 0)
    sc = e.get("score", 0)
    wk = e.get("wickets", 0)
    bp = e.get("bat_prob", 0)
    ts = e.get("timestamp", "")[:16]
    print(f"  {ov:.1f}  {sc}/{wk}  bat_prob={bp:.1%}  {ts}")
