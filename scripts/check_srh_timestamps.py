"""Check SRH ODM history timestamps to identify which innings/match."""
import json
from pathlib import Path

ML_DATA = Path(r"C:\Users\ADMINS\Documents\projects\machine_learning_bbl_009-odi-mc-predictor\data")

d = json.loads((ML_DATA / "ipl_live_ml_1_odm_history.json").read_text())
srh = [e for e in d if "Sunrisers" in e.get("batting_team", "")]

print("SRH batting rows with timestamps:")
for e in srh:
    ts = e.get("timestamp", "?")
    sc = e["score"]
    wk = e["wickets"]
    ov = e["over"]
    bp = e["bat_prob"]
    print(f"  Inn{e['innings']} Ov{ov:>2} | {sc}/{wk} | prob={bp:.1%} | ts={ts}")
