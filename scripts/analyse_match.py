"""Analyse specific match file over-by-over and print chase probability."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def chase_prob(runs_needed, balls_left, wickets_left):
    if balls_left <= 0:
        return 0.0
    if runs_needed <= 0:
        return 1.0
    rrr = (runs_needed / balls_left) * 6
    wkt_factor = (wickets_left / 10) ** 0.5
    rr_score = math.exp(-0.28 * max(0, rrr - 8.5))
    return round(min(0.92, max(0.08, rr_score * wkt_factor * 0.93 + 0.07)), 3)


def analyse(fname):
    d = json.loads((ROOT / "data" / "ipl_json" / fname).read_text())
    teams   = d["info"]["teams"]
    date    = d["info"]["dates"][0]
    venue   = d["info"]["venue"]
    toss    = d["info"]["toss"]
    outcome = d["info"]["outcome"]

    print(f"Match : {teams[0]} vs {teams[1]}")
    print(f"Date  : {date}")
    print(f"Venue : {venue}")
    print(f"Toss  : {toss['winner']} chose to {toss['decision']}")
    print(f"Result: {outcome}")
    print()

    inn1, inn2 = d["innings"][0], d["innings"][1]
    runs1 = sum(b["runs"]["total"] for ov in inn1["overs"] for b in ov["deliveries"])
    target = runs1 + 1

    print(f"1st innings ({inn1['team']}): {runs1}  |  Target for {inn2['team']}: {target}")
    print()
    print(f"{'Over':>4}  {'Score':>7}  {'Needed':>7}  {'Balls':>5}  {'Prob':>5}  Balls")
    print("-" * 65)

    runs = wkts = balls = 0
    for ov in inn2["overs"]:
        ball_str = []
        for ball in ov["deliveries"]:
            balls += 1
            runs += ball["runs"]["total"]
            if ball.get("wickets"):
                wkts += 1
            suffix = "W" if ball.get("wickets") else ""
            ball_str.append(str(ball["runs"]["total"]) + suffix)
        bl     = 120 - balls
        needed = target - runs
        if bl > 0 and needed > 0:
            p = chase_prob(needed, bl, 10 - wkts)
        else:
            p = 1.0 if needed <= 0 else 0.0
        print(f"{ov['over']+1:>4}  {runs:>3}/{wkts:<3}  {needed:>7}  {bl:>5}  {p:>4.0%}  {' '.join(ball_str)}")


if __name__ == "__main__":
    fname = sys.argv[1] if len(sys.argv) > 1 else "1216523.json"
    analyse(fname)
