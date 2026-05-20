"""
Mine Cricsheet IPL JSON files to find the best real-match "entry window" examples.
An entry window = score looks fine (<=2 wkts) but win probability drops >15% in 3 overs.
This powers Reel 2: "The Entry Window"
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IPL_DIR = ROOT / "data" / "ipl_json"


def chase_prob(runs_needed, balls_left, wickets_left):
    """Simple win probability model for a T20 chase."""
    if balls_left <= 0:
        return 0.0
    if runs_needed <= 0:
        return 1.0
    rrr = (runs_needed / balls_left) * 6
    wkt_factor = (wickets_left / 10) ** 0.5
    rr_score = math.exp(-0.28 * max(0, rrr - 8.5))
    return round(min(0.92, max(0.08, rr_score * wkt_factor * 0.93 + 0.07)), 3)


def simulate_chase(inn2, target):
    runs = 0
    wkts = 0
    balls = 0
    snapshots = []
    for ov in inn2.get("overs", []):
        for ball in ov["deliveries"]:
            balls += 1
            runs += ball["runs"]["total"]
            if ball.get("wickets"):
                wkts += 1
        ov_num = ov["over"] + 1
        balls_left = 120 - balls
        needed = target - runs
        if balls_left > 0 and needed > 0:
            p = chase_prob(needed, balls_left, 10 - wkts)
            snapshots.append({
                "over": ov_num,
                "score": f"{runs}/{wkts}",
                "runs": runs,
                "wkts": wkts,
                "needed": needed,
                "balls_left": balls_left,
                "prob": p,
            })
    return snapshots


def find_entry_windows(files, min_drop=0.15, max_wkts=2, prob_min=0.55):
    results = []
    for f in files:
        try:
            d = json.loads(f.read_text())
            innings = d.get("innings", [])
            if len(innings) < 2:
                continue
            inn1, inn2 = innings[0], innings[1]
            runs1 = sum(
                b["runs"]["total"]
                for ov in inn1.get("overs", [])
                for b in ov["deliveries"]
            )
            target = runs1 + 1
            teams = d["info"].get("teams", [])
            chasing = inn2["team"]
            batting = next((t for t in teams if t != chasing), "?")
            winner = d["info"].get("outcome", {}).get("winner", "?")
            date = d["info"].get("dates", ["?"])[0]
            venue = d["info"].get("venue", "?")

            snaps = simulate_chase(inn2, target)

            # Find biggest prob drop in 3-over window where score still looks fine
            for i in range(len(snaps) - 3):
                s1 = snaps[i]
                s2 = snaps[i + 3]
                if s1["prob"] >= prob_min and s1["wkts"] <= max_wkts:
                    drop = s1["prob"] - s2["prob"]
                    if drop >= min_drop:
                        results.append({
                            "drop": drop,
                            "date": date,
                            "venue": venue,
                            "batting": batting,
                            "chasing": chasing,
                            "target": target,
                            "winner": winner,
                            "file": f.name,
                            "before": s1,
                            "after": s2,
                        })
        except Exception:
            pass
    results.sort(key=lambda x: x["drop"], reverse=True)
    return results


if __name__ == "__main__":
    # Use only 2020+ files (modern IPL era)
    files = [f for f in sorted(IPL_DIR.glob("*.json")) if int(f.stem) >= 1200000]
    if not files:
        files = sorted(IPL_DIR.glob("*.json"))[-300:]

    print(f"Scanning {len(files)} matches...\n")
    windows = find_entry_windows(files, min_drop=0.15, max_wkts=2)

    print(f"Found {len(windows)} entry window moments.\nTop 8:\n")
    for w in windows[:8]:
        b = w["before"]
        a = w["after"]
        chaser_won = w["winner"] == w["chasing"]
        result_tag = "CHASER WON" if chaser_won else "CHASER LOST"
        print(f"  {w['date']} | {w['batting']} vs {w['chasing']}")
        print(f"  Venue: {w['venue']}")
        print(f"  Target: {w['target']} | {result_tag}")
        print(f"  Over {b['over']}: {b['score']} — needed {b['needed']} off {b['balls_left']}b"
              f" | Prob: {b['prob']:.0%}")
        print(f"  Over {a['over']}: {a['score']} — needed {a['needed']} off {a['balls_left']}b"
              f" | Prob: {a['prob']:.0%}")
        print(f"  DROP: {w['drop']:.0%}  (file: {w['file']})")
        print()
