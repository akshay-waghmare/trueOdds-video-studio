"""
Extract over-by-over summary from a live history JSON file.
Shows model probability, score, wickets, and market probability per over.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")


def summarise_match(fname, innings_filter=None):
    d = json.loads((DATA / fname).read_text())
    history = d["history"] if isinstance(d, dict) else d

    # Group by over, take last entry per over
    by_over = defaultdict(list)
    for e in history:
        inn = e.get("innings", 1)
        ov  = e.get("overs", 0)
        if innings_filter and inn != innings_filter:
            continue
        by_over[(inn, int(ov))].append(e)

    url = d.get("match_url", fname) if isinstance(d, dict) else fname
    print(f"Match: {url}")
    print()

    prev_prob = None
    for (inn, ov), entries in sorted(by_over.items()):
        e = entries[-1]
        bp   = e.get("bat_prob", 0)
        mkt  = e.get("market_stack_bat_prob")
        sc   = e.get("score", "?")
        wk   = e.get("wickets", "?")
        bat  = e.get("batting_team", "?")
        bowl = e.get("bowling_team", "?")

        prob_str  = f"{bp:.0%}"
        mkt_str   = f"{mkt:.0%}" if mkt is not None else "  n/a"
        gap_str   = f"  GAP={abs(bp - mkt):.0%}" if mkt is not None else ""

        swing = ""
        if prev_prob is not None:
            delta = bp - prev_prob
            if abs(delta) >= 0.05:
                swing = f"  {'▲' if delta > 0 else '▼'}{abs(delta):.0%}"

        print(f"  Inn{inn} Ov{ov:>2}: {str(sc):>5}/{wk}  model={prob_str}  mkt={mkt_str}{gap_str}{swing}  [{bat[:3]}]")
        prev_prob = bp


if __name__ == "__main__":
    fname = sys.argv[1] if len(sys.argv) > 1 else "ipl_live_ml_1_history.json"
    summarise_match(fname)
