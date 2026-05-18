from __future__ import annotations

import json
import hashlib
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IPL_JSON_DIR = ROOT / "data" / "ipl_json"
INTELLIGENCE_DIR = ROOT / "data" / "intelligence"
CARDS_DIR = ROOT / "inputs" / "cards"

SCHEMA_VERSION = "1.0.0"
BOWLER_WICKET_KINDS = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}
EXCLUDED_MATCH_METHODS = {"D/L"}

TEAM_ABBR_TO_NAME = {
    "MI": "Mumbai Indians",
    "KKR": "Kolkata Knight Riders",
    "RCB": "Royal Challengers Bangalore",
    "CSK": "Chennai Super Kings",
    "SRH": "Sunrisers Hyderabad",
    "DC": "Delhi Capitals",
    "PBKS": "Punjab Kings",
    "RR": "Rajasthan Royals",
    "GT": "Gujarat Titans",
    "LSG": "Lucknow Super Giants",
}
TEAM_NAME_ALIASES = {
    "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
}
TEAM_INPUT_LOOKUP = {
    **{abbr: name for abbr, name in TEAM_ABBR_TO_NAME.items()},
    **{name: name for name in TEAM_ABBR_TO_NAME.values()},
    **TEAM_NAME_ALIASES,
}
CURRENT_TEAMS = set(TEAM_ABBR_TO_NAME.values())

VENUE_CANONICAL_ALIASES = {
    "ahmedabad": "Narendra Modi Stadium",
    "bangalore": "M Chinnaswamy Stadium",
    "bengaluru": "M Chinnaswamy Stadium",
    "chennai": "MA Chidambaram Stadium",
    "hyderabad": "Rajiv Gandhi International Stadium, Uppal",
    "delhi": "Arun Jaitley Stadium",
    "jaipur": "Sawai Mansingh Stadium",
    "kolkata": "Eden Gardens",
    "mumbai": "Wankhede Stadium",
    "lucknow": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
    "mohali": "Punjab Cricket Association Stadium",
    "m chinnaswamy stadium": "M Chinnaswamy Stadium",
    "mchinnaswamy stadium": "M Chinnaswamy Stadium",
    "m chinnaswamy stadium bangalore": "M Chinnaswamy Stadium",
    "rajiv gandhi international stadium uppal": "Rajiv Gandhi International Stadium, Uppal",
    "rajiv gandhi international stadium": "Rajiv Gandhi International Stadium, Uppal",
    "ma chidambaram stadium chepauk": "MA Chidambaram Stadium",
    "ma chidambaram stadium": "MA Chidambaram Stadium",
    "arun jaitley stadium delhi": "Arun Jaitley Stadium",
    "feroz shah kotla": "Arun Jaitley Stadium",
    "wankhede stadium mumbai": "Wankhede Stadium",
    "wankhede stadium": "Wankhede Stadium",
    "narendra modi stadium ahmedabad": "Narendra Modi Stadium",
    "narendra modi stadium": "Narendra Modi Stadium",
    "brsabv ekana cricket stadium": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
    "ekana cricket stadium": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
    "dr y s rajasekhara reddy aca vdca cricket stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "dr ys rajasekhara reddy aca vdca cricket stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium",
    "sawai mansingh stadium jaipur": "Sawai Mansingh Stadium",
    "himachal pradesh cricket association stadium": "Himachal Pradesh Cricket Association Stadium, Dharamsala",
    "himachal pradesh cricket association stadium dharamsala": "Himachal Pradesh Cricket Association Stadium, Dharamsala",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_output_dirs() -> None:
    INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def canonical_team_name(raw_name: str) -> str:
    clean = " ".join(str(raw_name or "").strip().split())
    if not clean:
        return "Unknown"
    return TEAM_NAME_ALIASES.get(clean, clean)


def team_abbreviation(name_or_abbr: str) -> str:
    token = " ".join(str(name_or_abbr or "").strip().split())
    if token in TEAM_ABBR_TO_NAME:
        return token
    canonical = canonical_team_name(token)
    for abbr, full_name in TEAM_ABBR_TO_NAME.items():
        if full_name == canonical:
            return abbr
    return token.upper()


def canonical_venue_name(raw_venue: str) -> str:
    clean = " ".join(str(raw_venue or "").strip().split())
    if not clean:
        return "Unknown Venue"
    normalized = normalize_key(clean)
    return VENUE_CANONICAL_ALIASES.get(normalized, clean)


def canonical_player_id(player_name: str, people_registry: dict[str, str]) -> str:
    player_id = people_registry.get(player_name)
    if player_id:
        return player_id
    return f"name:{slugify(player_name)}"


def is_legal_delivery(delivery: dict[str, Any]) -> bool:
    extras = delivery.get("extras", {})
    return "wides" not in extras and "noballs" not in extras


def phase_for_legal_ball(legal_ball_number: int) -> str:
    if legal_ball_number <= 36:
        return "powerplay"
    if legal_ball_number <= 90:
        return "middle"
    return "death"


def confidence_label(sample_size: int, high: int = 20, medium: int = 8) -> str:
    if sample_size >= high:
        return "high"
    if sample_size >= medium:
        return "medium"
    return "low"


def safe_divide(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def round_if_number(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def compute_brier_score(probability: float, predicted_team_won: bool) -> float:
    actual = 1.0 if predicted_team_won else 0.0
    return (probability - actual) ** 2


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def dataset_source_hash(dataset_dir: Path) -> str:
    digest = hashlib.sha1()
    for path in sorted(dataset_dir.glob("*.json")):
        stat = path.stat()
        digest.update(f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}".encode("utf-8"))
    return digest.hexdigest()


def build_match_id(match: str, venue: str | None = None) -> str:
    suffix = slugify(venue) if venue else "unknown-venue"
    return f"{slugify(match)}-{suffix}"


def infer_venue_behaviour(avg_score: float | None, wickets: float | None, chase_rate: float | None) -> str:
    if avg_score is None or wickets is None:
        return "insufficient data"
    if avg_score >= 180 and (chase_rate or 0) >= 0.5:
        return "batting-friendly and chaseable"
    if avg_score >= 170 and wickets <= 6.5:
        return "batting-friendly"
    if avg_score <= 155 and wickets >= 7.0:
        return "bowler-friendly"
    if (chase_rate or 0) >= 0.58:
        return "chase-friendly"
    if (chase_rate or 0) <= 0.42:
        return "defend-friendly"
    return "balanced"


def top_player_types_for_venue(metrics: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    avg_score = metrics.get("avg_first_innings_score") or 0
    chase_rate = metrics.get("historical_second_innings_win_rate") or 0
    death_econ = metrics.get("death_over_economy") or 0
    pp_wkts = metrics.get("powerplay_wickets_per_innings") or 0
    if avg_score >= 175:
        tags.append("top-order hitters")
    if pp_wkts >= 2.0:
        tags.append("powerplay bowlers")
    if death_econ >= 10.0:
        tags.append("death hitters")
    if death_econ <= 8.4 and death_econ > 0:
        tags.append("death bowlers")
    if chase_rate >= 0.56:
        tags.append("chase anchors")
    if not tags:
        tags.append("balanced all-rounders")
    return tags[:3]


def player_display_name(player_name_counter: Counter[str]) -> str:
    return player_name_counter.most_common(1)[0][0] if player_name_counter else "Unknown Player"


def player_current_team(team_counter: Counter[str]) -> str | None:
    if not team_counter:
        return None
    team, _ = team_counter.most_common(1)[0]
    return team


def update_latest_team(profile: dict[str, Any], team_name: str, match_date: str) -> None:
    latest_seen = profile.get("latest_seen")
    if latest_seen is None or match_date >= latest_seen:
        profile["latest_seen"] = match_date
        profile["latest_team"] = team_name


def player_tags(profile: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    batting = profile["batting"]
    bowling = profile["bowling"]
    overall_sr = batting.get("strike_rate") or 0
    avg_runs = batting.get("average_runs") or 0
    death_sr = batting["phases"]["death"].get("strike_rate") or 0
    pp_sr = batting["phases"]["powerplay"].get("strike_rate") or 0
    pp_bowling_wickets = bowling["phases"]["powerplay"].get("wickets") or 0
    death_bowling_wickets = bowling["phases"]["death"].get("wickets") or 0
    death_bowling_balls = bowling["phases"]["death"].get("balls") or 0
    overall_economy = bowling.get("economy") or 99

    if batting.get("innings", 0) >= 10 and avg_runs >= 28 and 115 <= overall_sr <= 138:
        tags.append("anchor")
    if batting.get("innings", 0) >= 10 and overall_sr >= 145:
        tags.append("aggressor")
    if batting["phases"]["death"].get("balls", 0) >= 40 and death_sr >= 155:
        tags.append("finisher")
    if batting["phases"]["powerplay"].get("balls", 0) >= 50 and pp_sr >= 138:
        tags.append("powerplay aggressor")
    if pp_bowling_wickets >= 5 and bowling["phases"]["powerplay"].get("balls", 0) >= 60:
        tags.append("powerplay bowler")
    if death_bowling_balls >= 48 and death_bowling_wickets >= 4:
        tags.append("death specialist")
    if bowling.get("balls", 0) >= 120 and overall_economy <= 7.5:
        tags.append("economical")

    form_delta = profile.get("recent_form_delta") or 0
    if form_delta >= 0.2:
        tags.append("form hot")
    elif form_delta <= -0.2:
        tags.append("form cold")

    return tags[:4]


def build_intelligence(dataset_dir: Path = IPL_JSON_DIR) -> dict[str, Any]:
    ensure_output_dirs()

    venue_acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "matches": 0,
            "completed_matches": 0,
            "innings1_runs": 0,
            "innings1_wickets": 0,
            "second_innings_wins": 0,
            "batting_first_wins": 0,
            "toss_winner_wins": 0,
            "toss_decision_chase": 0,
            "toss_decision_bat": 0,
            "toss_count": 0,
            "phase_runs": {"powerplay": 0, "middle": 0, "death": 0},
            "phase_balls": {"powerplay": 0, "middle": 0, "death": 0},
            "phase_wickets": {"powerplay": 0, "middle": 0, "death": 0},
            "top_teams": Counter(),
        }
    )
    player_acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "display_names": Counter(),
            "teams": Counter(),
            "latest_seen": None,
            "latest_team": None,
            "batting": {
                "innings": 0,
                "runs": 0,
                "balls": 0,
                "dismissals": 0,
                "boundaries": 0,
                "sixes": 0,
                "positions": Counter(),
                "phases": {
                    "powerplay": {"runs": 0, "balls": 0},
                    "middle": {"runs": 0, "balls": 0},
                    "death": {"runs": 0, "balls": 0},
                },
                "chase": {"innings": 0, "runs": 0, "balls": 0},
                "defend": {"innings": 0, "runs": 0, "balls": 0},
                "venues": defaultdict(lambda: {"innings": 0, "runs": 0, "balls": 0}),
                "opponents": defaultdict(lambda: {"innings": 0, "runs": 0, "balls": 0}),
                "innings_records": [],
            },
            "bowling": {
                "innings": 0,
                "runs": 0,
                "balls": 0,
                "wickets": 0,
                "phases": {
                    "powerplay": {"runs": 0, "balls": 0, "wickets": 0},
                    "middle": {"runs": 0, "balls": 0, "wickets": 0},
                    "death": {"runs": 0, "balls": 0, "wickets": 0},
                },
                "venues": defaultdict(lambda: {"innings": 0, "runs": 0, "balls": 0, "wickets": 0}),
                "opponents": defaultdict(lambda: {"innings": 0, "runs": 0, "balls": 0, "wickets": 0}),
                "innings_records": [],
            },
        }
    )

    files = sorted(dataset_dir.glob("*.json"))
    latest_dataset_year = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        info = data.get("info", {})
        innings = data.get("innings", [])
        teams_raw = info.get("teams", [])
        if len(teams_raw) != 2 or len(innings) < 2:
            continue

        teams = [canonical_team_name(team) for team in teams_raw]
        people_registry = info.get("registry", {}).get("people", {})
        venue = canonical_venue_name(info.get("venue", "Unknown Venue"))
        match_date = str((info.get("dates") or ["0000-00-00"])[0])
        if match_date[:4].isdigit():
            latest_dataset_year = max(latest_dataset_year, int(match_date[:4]))
        venue_row = venue_acc[venue]
        venue_row["matches"] += 1
        venue_row["top_teams"].update(teams)

        outcome = info.get("outcome", {})
        result = outcome.get("result")
        method = outcome.get("method")
        winner = canonical_team_name(outcome.get("winner", "")) if outcome.get("winner") else None
        is_standard_result = result != "no result" and method not in EXCLUDED_MATCH_METHODS and len(innings) >= 2

        toss = info.get("toss", {})
        toss_winner = canonical_team_name(toss.get("winner", "")) if toss.get("winner") else None
        toss_decision = toss.get("decision")
        if toss_winner:
            venue_row["toss_count"] += 1
            if toss_decision == "field":
                venue_row["toss_decision_chase"] += 1
            elif toss_decision == "bat":
                venue_row["toss_decision_bat"] += 1
            if winner and toss_winner == winner:
                venue_row["toss_winner_wins"] += 1

        innings_summaries: list[dict[str, Any]] = []
        for innings_index, innings_data in enumerate(innings[:2], start=1):
            batting_team = canonical_team_name(innings_data.get("team", "Unknown"))
            bowling_team = teams[0] if batting_team == teams[1] else teams[1]
            batting_innings_players: dict[str, dict[str, Any]] = {}
            bowling_innings_players: dict[str, dict[str, Any]] = {}
            batting_order: dict[str, int] = {}
            innings_summary = {
                "team": batting_team,
                "runs": 0,
                "wickets": 0,
                "legal_balls": 0,
                "phase_runs": {"powerplay": 0, "middle": 0, "death": 0},
                "phase_balls": {"powerplay": 0, "middle": 0, "death": 0},
                "phase_wickets": {"powerplay": 0, "middle": 0, "death": 0},
            }

            for over_data in innings_data.get("overs", []):
                for delivery in over_data.get("deliveries", []):
                    current_ball_number = min(innings_summary["legal_balls"] + 1, 120)
                    phase = phase_for_legal_ball(current_ball_number)
                    legal = is_legal_delivery(delivery)
                    if legal:
                        innings_summary["legal_balls"] += 1

                    runs = delivery.get("runs", {})
                    total_runs = int(runs.get("total", 0))
                    batter_runs = int(runs.get("batter", 0))
                    extras = delivery.get("extras", {})
                    byes = int(extras.get("byes", 0))
                    legbyes = int(extras.get("legbyes", 0))
                    bowler_runs = total_runs - byes - legbyes

                    batter_name = delivery.get("batter")
                    bowler_name = delivery.get("bowler")
                    if not batter_name or not bowler_name:
                        continue
                    batter_id = canonical_player_id(batter_name, people_registry)
                    bowler_id = canonical_player_id(bowler_name, people_registry)

                    if batter_id not in batting_order:
                        batting_order[batter_id] = len(batting_order) + 1

                    innings_summary["runs"] += total_runs
                    innings_summary["phase_runs"][phase] += total_runs
                    if legal:
                        innings_summary["phase_balls"][phase] += 1

                    batter_row = batting_innings_players.setdefault(
                        batter_id,
                        {
                            "player_name": batter_name,
                            "runs": 0,
                            "balls": 0,
                            "dismissed": 0,
                            "boundaries": 0,
                            "sixes": 0,
                            "position": batting_order[batter_id],
                            "phase_runs": {"powerplay": 0, "middle": 0, "death": 0},
                            "phase_balls": {"powerplay": 0, "middle": 0, "death": 0},
                        },
                    )
                    batter_row["runs"] += batter_runs
                    batter_row["phase_runs"][phase] += batter_runs
                    if legal:
                        batter_row["balls"] += 1
                        batter_row["phase_balls"][phase] += 1
                    if batter_runs == 4:
                        batter_row["boundaries"] += 1
                    elif batter_runs == 6:
                        batter_row["boundaries"] += 1
                        batter_row["sixes"] += 1

                    bowler_row = bowling_innings_players.setdefault(
                        bowler_id,
                        {
                            "player_name": bowler_name,
                            "runs": 0,
                            "balls": 0,
                            "wickets": 0,
                            "phase_runs": {"powerplay": 0, "middle": 0, "death": 0},
                            "phase_balls": {"powerplay": 0, "middle": 0, "death": 0},
                            "phase_wickets": {"powerplay": 0, "middle": 0, "death": 0},
                        },
                    )
                    bowler_row["runs"] += bowler_runs
                    bowler_row["phase_runs"][phase] += bowler_runs
                    if legal:
                        bowler_row["balls"] += 1
                        bowler_row["phase_balls"][phase] += 1

                    for wicket in delivery.get("wickets", []):
                        wicket_kind = wicket.get("kind", "")
                        player_out = wicket.get("player_out")
                        if wicket_kind != "retired hurt":
                            innings_summary["wickets"] += 1
                            innings_summary["phase_wickets"][phase] += 1
                        if player_out:
                            player_out_id = canonical_player_id(player_out, people_registry)
                            dismissal_row = batting_innings_players.setdefault(
                                player_out_id,
                                {
                                    "player_name": player_out,
                                    "runs": 0,
                                    "balls": 0,
                                    "dismissed": 0,
                                    "boundaries": 0,
                                    "sixes": 0,
                                    "position": batting_order.get(player_out_id, len(batting_order) + 1),
                                    "phase_runs": {"powerplay": 0, "middle": 0, "death": 0},
                                    "phase_balls": {"powerplay": 0, "middle": 0, "death": 0},
                                },
                            )
                            if wicket_kind != "retired hurt":
                                dismissal_row["dismissed"] += 1
                        if wicket_kind in BOWLER_WICKET_KINDS:
                            bowler_row["wickets"] += 1
                            bowler_row["phase_wickets"][phase] += 1

            innings_summaries.append(innings_summary)

            chase_context = innings_index == 2
            for player_id, summary in batting_innings_players.items():
                profile = player_acc[player_id]
                profile["display_names"][summary["player_name"]] += 1
                profile["teams"][batting_team] += 1
                update_latest_team(profile, batting_team, match_date)
                batting = profile["batting"]
                batting["innings"] += 1
                batting["runs"] += summary["runs"]
                batting["balls"] += summary["balls"]
                batting["dismissals"] += summary["dismissed"]
                batting["boundaries"] += summary["boundaries"]
                batting["sixes"] += summary["sixes"]
                batting["positions"][summary["position"]] += 1
                for phase_name in ("powerplay", "middle", "death"):
                    batting["phases"][phase_name]["runs"] += summary["phase_runs"][phase_name]
                    batting["phases"][phase_name]["balls"] += summary["phase_balls"][phase_name]
                target_bucket = batting["chase"] if chase_context else batting["defend"]
                target_bucket["innings"] += 1
                target_bucket["runs"] += summary["runs"]
                target_bucket["balls"] += summary["balls"]
                batting["venues"][venue]["innings"] += 1
                batting["venues"][venue]["runs"] += summary["runs"]
                batting["venues"][venue]["balls"] += summary["balls"]
                batting["opponents"][bowling_team]["innings"] += 1
                batting["opponents"][bowling_team]["runs"] += summary["runs"]
                batting["opponents"][bowling_team]["balls"] += summary["balls"]
                batting["innings_records"].append(summary["runs"])

            for player_id, summary in bowling_innings_players.items():
                profile = player_acc[player_id]
                profile["display_names"][summary["player_name"]] += 1
                profile["teams"][bowling_team] += 1
                update_latest_team(profile, bowling_team, match_date)
                bowling = profile["bowling"]
                bowling["innings"] += 1
                bowling["runs"] += summary["runs"]
                bowling["balls"] += summary["balls"]
                bowling["wickets"] += summary["wickets"]
                for phase_name in ("powerplay", "middle", "death"):
                    bowling["phases"][phase_name]["runs"] += summary["phase_runs"][phase_name]
                    bowling["phases"][phase_name]["balls"] += summary["phase_balls"][phase_name]
                    bowling["phases"][phase_name]["wickets"] += summary["phase_wickets"][phase_name]
                bowling["venues"][venue]["innings"] += 1
                bowling["venues"][venue]["runs"] += summary["runs"]
                bowling["venues"][venue]["balls"] += summary["balls"]
                bowling["venues"][venue]["wickets"] += summary["wickets"]
                bowling["opponents"][batting_team]["innings"] += 1
                bowling["opponents"][batting_team]["runs"] += summary["runs"]
                bowling["opponents"][batting_team]["balls"] += summary["balls"]
                bowling["opponents"][batting_team]["wickets"] += summary["wickets"]
                bowling["innings_records"].append(summary["wickets"])

        if len(innings_summaries) < 2:
            continue

        innings1 = innings_summaries[0]
        innings2 = innings_summaries[1]
        venue_row["innings1_runs"] += innings1["runs"]
        venue_row["innings1_wickets"] += innings1["wickets"]
        for phase_name in ("powerplay", "middle", "death"):
            venue_row["phase_runs"][phase_name] += innings1["phase_runs"][phase_name] + innings2["phase_runs"][phase_name]
            venue_row["phase_balls"][phase_name] += innings1["phase_balls"][phase_name] + innings2["phase_balls"][phase_name]
            venue_row["phase_wickets"][phase_name] += innings1["phase_wickets"][phase_name] + innings2["phase_wickets"][phase_name]

        if is_standard_result:
            venue_row["completed_matches"] += 1
            if winner == innings2["team"]:
                venue_row["second_innings_wins"] += 1
            elif winner == innings1["team"]:
                venue_row["batting_first_wins"] += 1

    venue_output: list[dict[str, Any]] = []
    for venue_name, stats in sorted(venue_acc.items()):
        completed = stats["completed_matches"]
        avg_score = safe_divide(stats["innings1_runs"], stats["matches"])
        avg_wickets = safe_divide(stats["innings1_wickets"], stats["matches"])
        chase_rate = safe_divide(stats["second_innings_wins"], completed)
        toss_winner_rate = safe_divide(stats["toss_winner_wins"], stats["toss_count"])
        death_econ = safe_divide(stats["phase_runs"]["death"] * 6, stats["phase_balls"]["death"])
        total_phase_wickets = sum(stats["phase_wickets"].values())
        venue_metrics = {
            "venue": venue_name,
            "matches": stats["matches"],
            "completed_matches": completed,
            "avg_first_innings_score": round_if_number(avg_score),
            "avg_first_innings_wickets": round_if_number(avg_wickets),
            "historical_second_innings_win_rate": round_if_number(chase_rate),
            "batting_first_win_rate": round_if_number(safe_divide(stats["batting_first_wins"], completed)),
            "toss_winner_win_rate": round_if_number(toss_winner_rate),
            "choose_to_bowl_rate_after_winning_toss": round_if_number(safe_divide(stats["toss_decision_chase"], stats["toss_count"])),
            "powerplay_wickets_per_innings": round_if_number(safe_divide(stats["phase_wickets"]["powerplay"], stats["matches"] * 2)),
            "powerplay_wicket_pct": round_if_number(safe_divide(stats["phase_wickets"]["powerplay"], total_phase_wickets)),
            "middle_wicket_pct": round_if_number(safe_divide(stats["phase_wickets"]["middle"], total_phase_wickets)),
            "death_wicket_pct": round_if_number(safe_divide(stats["phase_wickets"]["death"], total_phase_wickets)),
            "death_over_economy": round_if_number(death_econ),
            "venue_behaviour": infer_venue_behaviour(avg_score, avg_wickets, chase_rate),
            "best_player_types": top_player_types_for_venue(
                {
                    "avg_first_innings_score": avg_score,
                    "historical_second_innings_win_rate": chase_rate,
                    "death_over_economy": death_econ,
                    "powerplay_wickets_per_innings": safe_divide(stats["phase_wickets"]["powerplay"], stats["matches"] * 2) or 0,
                }
            ),
            "confidence": confidence_label(completed),
            "pace_wicket_pct": None,
            "spin_wicket_pct": None,
        }
        venue_output.append(venue_metrics)

    player_output: list[dict[str, Any]] = []
    for player_id, stats in player_acc.items():
        display_name = player_display_name(stats["display_names"])
        batting = stats["batting"]
        bowling = stats["bowling"]
        batting_average_runs = safe_divide(batting["runs"], batting["innings"])
        batting_average = safe_divide(batting["runs"], batting["dismissals"])
        batting_sr = safe_divide(batting["runs"] * 100, batting["balls"])
        boundary_rate = safe_divide(batting["boundaries"], batting["balls"])
        bowling_economy = safe_divide(bowling["runs"] * 6, bowling["balls"])
        wickets_per_innings = safe_divide(bowling["wickets"], bowling["innings"])
        best_position = batting["positions"].most_common(1)[0][0] if batting["positions"] else None
        recent_records = batting["innings_records"][-5:]
        recent_avg = safe_divide(sum(recent_records), len(recent_records))
        recent_form_delta = 0.0
        if batting_average_runs:
            recent_form_delta = ((recent_avg or 0) - batting_average_runs) / batting_average_runs

        profile = {
            "player_id": player_id,
            "display_name": display_name,
            "current_team": stats.get("latest_team") or player_current_team(stats["teams"]),
            "latest_seen": stats.get("latest_seen"),
            "latest_year": int(str(stats.get("latest_seen"))[:4]) if str(stats.get("latest_seen"))[:4].isdigit() else None,
            "sample_size": {
                "batting_innings": batting["innings"],
                "bowling_innings": bowling["innings"],
            },
            "best_batting_position": best_position,
            "batting": {
                "innings": batting["innings"],
                "runs": batting["runs"],
                "balls": batting["balls"],
                "average_runs": round_if_number(batting_average_runs),
                "average": round_if_number(batting_average),
                "strike_rate": round_if_number(batting_sr),
                "boundary_rate": round_if_number(boundary_rate),
                "phases": {
                    phase_name: {
                        "runs": phase_stats["runs"],
                        "balls": phase_stats["balls"],
                        "strike_rate": round_if_number(safe_divide(phase_stats["runs"] * 100, phase_stats["balls"])),
                    }
                    for phase_name, phase_stats in batting["phases"].items()
                },
                "chase": {
                    "innings": batting["chase"]["innings"],
                    "runs": batting["chase"]["runs"],
                    "balls": batting["chase"]["balls"],
                    "strike_rate": round_if_number(safe_divide(batting["chase"]["runs"] * 100, batting["chase"]["balls"])),
                },
                "defend": {
                    "innings": batting["defend"]["innings"],
                    "runs": batting["defend"]["runs"],
                    "balls": batting["defend"]["balls"],
                    "strike_rate": round_if_number(safe_divide(batting["defend"]["runs"] * 100, batting["defend"]["balls"])),
                },
                "top_venues": [
                    {
                        "venue": venue_name,
                        "innings": venue_stats["innings"],
                        "runs": venue_stats["runs"],
                        "strike_rate": round_if_number(safe_divide(venue_stats["runs"] * 100, venue_stats["balls"])),
                    }
                    for venue_name, venue_stats in sorted(
                        batting["venues"].items(),
                        key=lambda item: (item[1]["runs"], item[1]["innings"]),
                        reverse=True,
                    )[:5]
                ],
                "top_opponents": [
                    {
                        "opponent": opponent_name,
                        "innings": opponent_stats["innings"],
                        "runs": opponent_stats["runs"],
                        "strike_rate": round_if_number(safe_divide(opponent_stats["runs"] * 100, opponent_stats["balls"])),
                    }
                    for opponent_name, opponent_stats in sorted(
                        batting["opponents"].items(),
                        key=lambda item: (item[1]["runs"], item[1]["innings"]),
                        reverse=True,
                    )[:5]
                ],
            },
            "bowling": {
                "innings": bowling["innings"],
                "balls": bowling["balls"],
                "runs": bowling["runs"],
                "wickets": bowling["wickets"],
                "economy": round_if_number(bowling_economy),
                "wickets_per_innings": round_if_number(wickets_per_innings),
                "phases": {
                    phase_name: {
                        "balls": phase_stats["balls"],
                        "runs": phase_stats["runs"],
                        "wickets": phase_stats["wickets"],
                        "economy": round_if_number(safe_divide(phase_stats["runs"] * 6, phase_stats["balls"])),
                    }
                    for phase_name, phase_stats in bowling["phases"].items()
                },
                "top_venues": [
                    {
                        "venue": venue_name,
                        "innings": venue_stats["innings"],
                        "wickets": venue_stats["wickets"],
                        "economy": round_if_number(safe_divide(venue_stats["runs"] * 6, venue_stats["balls"])),
                    }
                    for venue_name, venue_stats in sorted(
                        bowling["venues"].items(),
                        key=lambda item: (item[1]["wickets"], item[1]["innings"]),
                        reverse=True,
                    )[:5]
                ],
                "top_opponents": [
                    {
                        "opponent": opponent_name,
                        "innings": opponent_stats["innings"],
                        "wickets": opponent_stats["wickets"],
                        "economy": round_if_number(safe_divide(opponent_stats["runs"] * 6, opponent_stats["balls"])),
                    }
                    for opponent_name, opponent_stats in sorted(
                        bowling["opponents"].items(),
                        key=lambda item: (item[1]["wickets"], item[1]["innings"]),
                        reverse=True,
                    )[:5]
                ],
            },
            "recent_form_delta": round_if_number(recent_form_delta),
            "confidence": confidence_label(max(batting["innings"], bowling["innings"])),
        }
        profile["tags"] = player_tags(profile)
        player_output.append(profile)

    player_output.sort(
        key=lambda item: (
            item["current_team"] or "",
            -(item["sample_size"]["batting_innings"] + item["sample_size"]["bowling_innings"]),
            item["display_name"],
        )
    )

    return {
        "venue_intelligence": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "source_hash": dataset_source_hash(dataset_dir),
            "source_matches": len(files),
            "venues": venue_output,
        },
        "player_role_intelligence": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now_iso(),
            "source_hash": dataset_source_hash(dataset_dir),
            "source_matches": len(files),
            "latest_dataset_year": latest_dataset_year,
            "players": player_output,
        },
    }


def write_intelligence_artifacts(artifacts: dict[str, Any]) -> dict[str, Path]:
    ensure_output_dirs()
    venue_path = INTELLIGENCE_DIR / "venue_intelligence.json"
    player_path = INTELLIGENCE_DIR / "player_role_intelligence.json"
    venue_path.write_text(json.dumps(artifacts["venue_intelligence"], indent=2), encoding="utf-8")
    player_path.write_text(json.dumps(artifacts["player_role_intelligence"], indent=2), encoding="utf-8")
    return {
        "venue_intelligence": venue_path,
        "player_role_intelligence": player_path,
    }


def load_json_file(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_or_build_intelligence() -> tuple[dict[str, Any], dict[str, Any]]:
    venue_path = INTELLIGENCE_DIR / "venue_intelligence.json"
    player_path = INTELLIGENCE_DIR / "player_role_intelligence.json"
    if venue_path.exists() and player_path.exists():
        return load_json_file(venue_path), load_json_file(player_path)
    artifacts = build_intelligence()
    write_intelligence_artifacts(artifacts)
    return artifacts["venue_intelligence"], artifacts["player_role_intelligence"]


def parse_matchup(match: str) -> tuple[str, str]:
    parts = re.split(r"\s+vs\.?\s+|\s+v\s+|\s+versus\s+", match.strip(), flags=re.IGNORECASE)
    if len(parts) != 2:
        raise ValueError("Match must look like 'GT vs SRH'")
    left = TEAM_INPUT_LOOKUP.get(parts[0].strip(), parts[0].strip())
    right = TEAM_INPUT_LOOKUP.get(parts[1].strip(), parts[1].strip())
    return canonical_team_name(left), canonical_team_name(right)


def historical_probability(match: str, venue: str | None = None) -> dict[str, Any]:
    team1, team2 = parse_matchup(match)
    team1_abbr = team_abbreviation(team1)
    team2_abbr = team_abbreviation(team2)
    venue_keywords = [venue] if venue else []

    team1_played = team1_wins = team2_played = team2_wins = 0
    h2h_total = h2h_t1 = h2h_t2 = 0
    venue_total = venue_t1 = venue_t2 = 0

    for path in sorted(IPL_JSON_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        info = data.get("info", {})
        teams = [canonical_team_name(team) for team in info.get("teams", [])]
        if len(teams) != 2:
            continue
        winner = canonical_team_name(info.get("outcome", {}).get("winner", "")) if info.get("outcome", {}).get("winner") else ""
        raw_venue = info.get("venue", "")
        if team1 in teams:
            team1_played += 1
            if winner == team1:
                team1_wins += 1
        if team2 in teams:
            team2_played += 1
            if winner == team2:
                team2_wins += 1
        if team1 in teams and team2 in teams:
            h2h_total += 1
            if winner == team1:
                h2h_t1 += 1
            elif winner == team2:
                h2h_t2 += 1
            if venue_keywords and any(
                keyword.lower() in raw_venue.lower()
                or canonical_venue_name(raw_venue) == canonical_venue_name(keyword)
                for keyword in venue_keywords
            ):
                venue_total += 1
                if winner == team1:
                    venue_t1 += 1
                elif winner == team2:
                    venue_t2 += 1

    combined_total = team1_wins + team2_wins
    overall_wr = team1_wins / combined_total if combined_total else 0.5
    h2h_wr = h2h_t1 / h2h_total if h2h_total else 0.5
    venue_wr = venue_t1 / venue_total if venue_total else 0.5

    if venue_total >= 3:
        probability = overall_wr * 0.35 + h2h_wr * 0.35 + venue_wr * 0.30
        method = "35% overall + 35% H2H + 30% venue"
    else:
        probability = overall_wr * 0.50 + h2h_wr * 0.50
        method = "50% overall + 50% H2H"
    probability = max(0.50, min(0.85, probability))
    model_pick = team1_abbr if probability >= 0.5 else team2_abbr
    return {
        "source": "historical_blend_v1",
        "method": method,
        "team1": team1_abbr,
        "team2": team2_abbr,
        "model_pick": model_pick,
        "probability": round(probability * 100),
        "inputs": {
            "overall_team1_win_rate": round_if_number(overall_wr, 4),
            "h2h_team1_win_rate": round_if_number(h2h_wr, 4),
            "venue_team1_win_rate": round_if_number(venue_wr, 4),
            "venue_sample": venue_total,
            "h2h_sample": h2h_total,
        },
    }


def player_card_reason(profile: dict[str, Any], venue_name: str | None, opponent_name: str) -> str:
    tags = profile.get("tags", [])
    if venue_name:
        for row in profile["batting"]["top_venues"]:
            if row["venue"] == venue_name and row["innings"] >= 3:
                return f"{row['runs']} runs in {row['innings']} innings at {venue_name}"
        for row in profile["bowling"]["top_venues"]:
            if row["venue"] == venue_name and row["innings"] >= 3:
                return f"{row['wickets']} wickets in {row['innings']} innings at {venue_name}"
    for row in profile["batting"]["top_opponents"]:
        if row["opponent"] == opponent_name and row["innings"] >= 3:
            return f"{row['runs']} runs in {row['innings']} innings vs {opponent_name}"
    for row in profile["bowling"]["top_opponents"]:
        if row["opponent"] == opponent_name and row["innings"] >= 3:
            return f"{row['wickets']} wickets in {row['innings']} innings vs {opponent_name}"
    if tags:
        return f"Profile tags: {', '.join(tags[:2])}"
    return "Broad historical sample only"


def avoid_player_reason(profile: dict[str, Any]) -> str:
    tags = profile.get("tags", [])
    if "form cold" in tags:
        return "Recent form flag is cold against the model context"
    batting_sr = profile["batting"].get("strike_rate") or 0
    economy = profile["bowling"].get("economy") or 0
    if batting_sr and batting_sr < 120:
        return f"Lower scoring-rate profile: career SR {batting_sr}"
    if economy and economy > 9.5:
        return f"Expensive bowling profile: economy {economy}"
    return "High-variance profile; use caution"


def confidence_rank(confidence: str | None) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(confidence or "low", 0)


def has_specific_signal(profile: dict[str, Any], reason: str) -> bool:
    if reason != "Broad historical sample only":
        return True
    return bool(profile.get("tags"))


def player_signal_scores(profile: dict[str, Any], venue_name: str | None, opponent_name: str) -> dict[str, float]:
    batting_sr = profile["batting"].get("strike_rate") or 0
    batting_avg_runs = profile["batting"].get("average_runs") or 0
    wickets_per_innings = profile["bowling"].get("wickets_per_innings") or 0
    economy = profile["bowling"].get("economy") or 12
    sample = profile["sample_size"]["batting_innings"] + profile["sample_size"]["bowling_innings"]
    recent_delta = profile.get("recent_form_delta") or 0
    safe_score = batting_avg_runs + wickets_per_innings * 12 + max(recent_delta, 0) * 10 + min(sample, 20) * 0.8
    risky_score = max(batting_sr - 135, 0) * 0.12 + abs(recent_delta) * 12 + max(9.0 - economy, 0) * 0.4

    venue_bonus = 0.0
    if venue_name:
        for row in profile["batting"]["top_venues"]:
            if row["venue"] == venue_name:
                venue_bonus += (row["strike_rate"] or 0) * 0.02 + row["innings"]
        for row in profile["bowling"]["top_venues"]:
            if row["venue"] == venue_name:
                venue_bonus += row["wickets"] * 0.8
    opponent_bonus = 0.0
    for row in profile["batting"]["top_opponents"]:
        if row["opponent"] == opponent_name:
            opponent_bonus += (row["strike_rate"] or 0) * 0.015 + row["innings"]
    for row in profile["bowling"]["top_opponents"]:
        if row["opponent"] == opponent_name:
            opponent_bonus += row["wickets"] * 0.7

    return {
        "safe": safe_score + venue_bonus + opponent_bonus,
        "risky": risky_score + max(venue_bonus, 0) * 0.2,
        "value": venue_bonus + opponent_bonus + max(recent_delta, 0) * 6,
        "avoid": max(-recent_delta, 0) * 8 + max(economy - 9.5, 0) + max(120 - batting_sr, 0) * 0.03,
    }


def generate_match_card(match: str, venue: str | None = None) -> tuple[dict[str, Any], Path]:
    ensure_output_dirs()
    venue_data, player_data = load_or_build_intelligence()
    team1, team2 = parse_matchup(match)
    canonical_venue = canonical_venue_name(venue) if venue else None
    venue_row = None
    if canonical_venue:
        venue_row = next((row for row in venue_data["venues"] if row["venue"] == canonical_venue), None)

    probability = historical_probability(match, canonical_venue)
    latest_dataset_year = player_data.get("latest_dataset_year") or max(
        (profile.get("latest_year") or 0 for profile in player_data["players"]),
        default=0,
    )
    active_cutoff_year = max(latest_dataset_year - 1, 0)
    team_candidates = [
        profile
        for profile in player_data["players"]
        if profile.get("current_team") in {team1, team2}
        and (profile.get("latest_year") or 0) >= active_cutoff_year
    ]

    safe_candidates: list[tuple[float, dict[str, Any], str]] = []
    risky_candidates: list[tuple[float, dict[str, Any], str]] = []
    value_candidates: list[tuple[float, dict[str, Any], str]] = []
    avoid_candidates: list[tuple[float, dict[str, Any], str]] = []
    for profile in team_candidates:
        opponent = team2 if profile.get("current_team") == team1 else team1
        scores = player_signal_scores(profile, canonical_venue, opponent)
        reason = player_card_reason(profile, canonical_venue, opponent)
        safe_candidates.append((scores["safe"], profile, reason))
        risky_candidates.append((scores["risky"], profile, reason))
        value_candidates.append((scores["value"], profile, reason))
        avoid_candidates.append((scores["avoid"], profile, avoid_player_reason(profile)))

    def build_player_signal(
        rows: list[tuple[float, dict[str, Any], str]],
        count: int,
        min_confidence: str = "medium",
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        output: list[dict[str, Any]] = []
        for score, profile, reason in sorted(rows, key=lambda item: item[0], reverse=True):
            if profile["player_id"] in seen:
                continue
            if confidence_rank(profile.get("confidence")) < confidence_rank(min_confidence):
                continue
            if not has_specific_signal(profile, reason):
                continue
            seen.add(profile["player_id"])
            output.append(
                {
                    "player_id": profile["player_id"],
                    "display_name": profile["display_name"],
                    "team": profile.get("current_team"),
                    "tags": profile.get("tags", []),
                    "confidence": profile.get("confidence"),
                    "reason": reason,
                }
            )
            if len(output) == count:
                break
        return output

    safe_players = build_player_signal(safe_candidates, 3)
    safe_ids = {row["player_id"] for row in safe_players}
    risky_players = build_player_signal(
        [row for row in risky_candidates if row[1]["player_id"] not in safe_ids],
        3,
    )
    trump_pick = build_player_signal(
        [row for row in value_candidates if row[1]["player_id"] not in safe_ids],
        1,
    )
    used_signal_ids = safe_ids | {row["player_id"] for row in risky_players}
    used_signal_ids |= {trump_pick[0]["player_id"]} if trump_pick else set()
    avoid_pick = build_player_signal(
        [row for row in avoid_candidates if row[1]["player_id"] not in used_signal_ids],
        1,
        min_confidence="high",
    )

    card = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "match": f"{team_abbreviation(team1)} vs {team_abbreviation(team2)}",
        "teams": {
            "team1": {"abbr": team_abbreviation(team1), "name": team1},
            "team2": {"abbr": team_abbreviation(team2), "name": team2},
        },
        "venue": {
            "requested": venue,
            "canonical": canonical_venue,
            "summary": venue_row,
        },
        "prediction": probability,
        "player_signal_filter": {
            "active_cutoff_year": active_cutoff_year,
            "latest_dataset_year": latest_dataset_year,
            "rule": "only players seen for their current team in the latest two IPL seasons in the local dataset",
        },
        "toss_impact": {
            "historical_second_innings_win_rate": venue_row.get("historical_second_innings_win_rate") if venue_row else None,
            "toss_winner_win_rate": venue_row.get("toss_winner_win_rate") if venue_row else None,
            "choose_to_bowl_rate_after_winning_toss": venue_row.get("choose_to_bowl_rate_after_winning_toss") if venue_row else None,
            "confidence": venue_row.get("confidence") if venue_row else "low",
        },
        "expected_score": {
            "first_innings_average": venue_row.get("avg_first_innings_score") if venue_row else None,
            "confidence": venue_row.get("confidence") if venue_row else "low",
        },
        "expected_wickets": {
            "first_innings_average": venue_row.get("avg_first_innings_wickets") if venue_row else None,
            "powerplay_wickets_per_innings": venue_row.get("powerplay_wickets_per_innings") if venue_row else None,
            "confidence": venue_row.get("confidence") if venue_row else "low",
        },
        "venue_behaviour": venue_row.get("venue_behaviour") if venue_row else "insufficient data",
        "safe_players": safe_players,
        "risky_players": risky_players,
        "trump_pick": trump_pick[0] if trump_pick else None,
        "avoid_pick": avoid_pick[0] if avoid_pick else None,
        "notes": [
            "This output is descriptive intelligence, not a fantasy optimizer.",
            "Venue behaviour is inferred from historical scoring and wicket patterns.",
        ],
    }

    output_path = CARDS_DIR / f"match_intelligence_{slugify(card['match'])}.json"
    output_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card, output_path


def default_tracker() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": utc_now_iso(),
        "predictions": [],
    }


def load_tracker() -> dict[str, Any]:
    ensure_output_dirs()
    tracker_path = INTELLIGENCE_DIR / "prediction_tracker.json"
    if tracker_path.exists():
        return json.loads(tracker_path.read_text(encoding="utf-8"))
    tracker = default_tracker()
    tracker_path.write_text(json.dumps(tracker, indent=2), encoding="utf-8")
    return tracker


def save_tracker(tracker: dict[str, Any]) -> Path:
    tracker["updated_at"] = utc_now_iso()
    tracker_path = INTELLIGENCE_DIR / "prediction_tracker.json"
    tracker_path.write_text(json.dumps(tracker, indent=2), encoding="utf-8")
    return tracker_path


def record_prediction(card_path: Path | None = None, match: str | None = None, venue: str | None = None) -> tuple[dict[str, Any], Path]:
    if card_path:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    elif match:
        card, _ = generate_match_card(match, venue)
    else:
        raise ValueError("Provide either card_path or match")

    tracker = load_tracker()
    match_id = build_match_id(card["match"], card["venue"].get("canonical"))
    tracker["predictions"] = [row for row in tracker["predictions"] if row["match_id"] != match_id]
    entry = {
        "match_id": match_id,
        "match": card["match"],
        "venue": card["venue"].get("canonical"),
        "recorded_at": utc_now_iso(),
        "prediction": {
            "model_pick": card["prediction"]["model_pick"],
            "probability": card["prediction"]["probability"],
            "source": card["prediction"]["source"],
            "method": card["prediction"]["method"],
        },
        "result": {
            "status": "pending",
            "winner": None,
            "hit": None,
            "brier_score": None,
            "notes": None,
        },
    }
    tracker["predictions"].append(entry)
    tracker_path = save_tracker(tracker)
    return entry, tracker_path


def reconcile_prediction(match_id: str, winner: str, notes: str | None = None) -> tuple[dict[str, Any], Path]:
    tracker = load_tracker()
    canonical_winner = TEAM_INPUT_LOOKUP.get(winner, winner)
    canonical_winner = canonical_team_name(canonical_winner)
    for entry in tracker["predictions"]:
        if entry["match_id"] != match_id:
            continue
        model_pick_name = TEAM_INPUT_LOOKUP.get(entry["prediction"]["model_pick"], entry["prediction"]["model_pick"])
        model_pick_name = canonical_team_name(model_pick_name)
        probability = float(entry["prediction"]["probability"]) / 100.0
        hit = canonical_winner == model_pick_name
        entry["result"] = {
            "status": "settled",
            "winner": team_abbreviation(canonical_winner),
            "hit": hit,
            "brier_score": round_if_number(compute_brier_score(probability, hit), 4),
            "notes": notes,
        }
        tracker_path = save_tracker(tracker)
        return entry, tracker_path
    raise KeyError(f"Prediction not found: {match_id}")
