"""
Scan all live history JSON files in the ml predictor data folder.
Find recent matches with biggest model vs market divergence gaps.
"""
import json
import glob
import os
from pathlib import Path
from collections import defaultdict

DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")
BETX21 = DATA / "betx21_live"

# Find all *_history.json files
history_files = sorted(DATA.glob("*_history.json")) + sorted(DATA.glob("**/*_history.json"))

print(f"Found {len(history_files)} history files\n")

summaries = []
for hf in history_files:
    try:
        data = json.loads(hf.read_text())
        if not isinstance(data, list) or len(data) < 10:
            continue
        # Get match metadata from first entry
        first = data[0]
        teams = (first.get("batting_team", "?"), first.get("bowling_team", "?"))
        timestamps = [e.get("timestamp", "") for e in data if e.get("timestamp")]
        last_ts = max(timestamps) if timestamps else "?"
        first_ts = min(timestamps) if timestamps else "?"

        # Only innings 2 entries for divergence analysis
        inn2 = [e for e in data if e.get("innings") == 2]
        if len(inn2) < 5:
            continue

        # Find biggest gap between model prob and market prob (if available)
        gaps = []
        for e in inn2:
            mp = e.get("bat_prob") or e.get("model_prob")
            mkt = e.get("market_prob") or e.get("market_bat_prob") or e.get("odm_prob")
            if mp is not None and mkt is not None:
                gaps.append(abs(mp - mkt))

        max_gap = max(gaps) if gaps else None

        # Unique overs covered
        overs = sorted(set(round(e.get("overs", 0), 1) for e in inn2))

        summaries.append({
            "file": hf.name,
            "teams": teams,
            "first_ts": first_ts[:10],
            "last_ts": last_ts[:10],
            "inn2_rows": len(inn2),
            "has_market": max_gap is not None,
            "max_gap": max_gap,
            "over_range": f"{min(overs):.1f}–{max(overs):.1f}" if overs else "?"
        })
    except Exception as e:
        pass

# Sort by date desc
summaries.sort(key=lambda x: x["last_ts"], reverse=True)

print("Recent matches with live model data:\n")
for s in summaries[:15]:
    gap_str = f"  max_gap={s['max_gap']:.2f}" if s["max_gap"] else "  (no market col)"
    print(f"  {s['last_ts']}  {s['teams'][0]} vs {s['teams'][1]}")
    print(f"    file={s['file']}  inn2_rows={s['inn2_rows']}  overs={s['over_range']}{gap_str}")
    print()
