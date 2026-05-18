from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "inputs" / "match_day_pack.json"
DEFAULT_TRACKER = ROOT / "data" / "intelligence" / "prediction_tracker.json"
DEFAULT_PACKS_DIR = ROOT / "inputs" / "packs"

LANGUAGES = {"english", "hinglish"}
CTA_MODES = {"follow", "comment_match", "join_telegram", "check_live_score"}

FULL_NAMES = {
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


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def full_team_name(team: str) -> str:
    return FULL_NAMES.get(team, team)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def validate_pack(pack: dict[str, Any]) -> None:
    required = ["schema_version", "match", "public_team", "model_pick", "probability", "reasons", "cta_mode", "languages"]
    missing = [key for key in required if key not in pack]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    if not isinstance(pack["probability"], int) or not 0 <= pack["probability"] <= 100:
        raise ValueError("probability must be an integer from 0 to 100")

    reasons = pack["reasons"]
    if not isinstance(reasons, list) or not reasons or any(not str(item).strip() for item in reasons):
        raise ValueError("reasons must be a non-empty list of strings")

    cta_mode = pack["cta_mode"]
    if cta_mode not in CTA_MODES:
        raise ValueError(f"cta_mode must be one of: {', '.join(sorted(CTA_MODES))}")

    languages = pack["languages"]
    if not isinstance(languages, list) or not languages:
        raise ValueError("languages must be a non-empty list")
    invalid_languages = sorted(set(languages) - LANGUAGES)
    if invalid_languages:
        raise ValueError(f"Unsupported languages: {', '.join(invalid_languages)}")


def cta_text(mode: str, language: str) -> str:
    copy = {
        "follow": {
            "english": "Follow TrueOddsML for live probability reads.",
            "hinglish": "Live probability reads ke liye TrueOddsML follow karo.",
        },
        "comment_match": {
            "english": "Comment MATCH if you want the full breakdown.",
            "hinglish": "Full breakdown chahiye to MATCH comment karo.",
        },
        "join_telegram": {
            "english": "Join Telegram before toss for full match reads.",
            "hinglish": "Full match reads ke liye toss se pehle Telegram join karo.",
        },
        "check_live_score": {
            "english": "Check Crickzen live score and probability now.",
            "hinglish": "Abhi Crickzen live score aur probability check karo.",
        },
    }
    return copy[mode][language]


def stage_title(stage: str, language: str) -> str:
    titles = {
        "prematch": {
            "english": "Pre-match read",
            "hinglish": "Pre-match read",
        },
        "toss_update": {
            "english": "Toss update",
            "hinglish": "Toss update",
        },
        "turning_point": {
            "english": "Turning point",
            "hinglish": "Turning point",
        },
        "probability_swing": {
            "english": "Probability swing",
            "hinglish": "Probability swing",
        },
        "post_match_proof": {
            "english": "Post-match proof",
            "hinglish": "Post-match proof",
        },
        "market_edge_replay": {
            "english": "Market edge replay",
            "hinglish": "Market edge replay",
        },
    }
    return titles[stage][language]


def hooks_for_stage(stage: str, pack: dict[str, Any], language: str) -> list[str]:
    public_team = full_team_name(pack["public_team"])
    model_pick = full_team_name(pack["model_pick"])
    probability = pack["probability"]

    if stage == "prematch":
        if language == "english":
            return [
                "Casual fans saw a normal pre-match call.",
                f"The public backed {public_team}. The model leaned {model_pick}.",
                f"This was never a safe {probability}-plus certainty match."
            ]
        return [
            "Casual fans ne is match ko simple samjha.",
            f"Public {public_team} ke saath thi. Model {model_pick} ki side tha.",
            f"Yeh kabhi bhi safe one-sided {probability} plus call nahi tha."
        ]

    if stage == "toss_update":
        if language == "english":
            return [
                "Toss is in. The model still stayed calm.",
                "The crowd reacted harder than the numbers did.",
                "Toss happened. The real edge barely moved."
            ]
        return [
            "Toss aa gaya. Model phir bhi calm raha.",
            "Crowd zyada react hui, numbers utne nahi hile.",
            "Toss hua, par real edge zyada shift nahi hui."
        ]

    if stage == "turning_point":
        label = pack["turning_point"]["snapshot_label"]
        if language == "english":
            return [
                "This was the real turning point.",
                f"The scoreboard looked fine at {label}. The pressure did not.",
                "The wicket was late. The warning signs were early."
            ]
        return [
            "Yahi asli turning point tha.",
            f"{label} par scoreboard theek lag raha tha. Pressure nahi.",
            "Wicket baad mein aayi. Warning pehle se thi."
        ]

    if stage == "probability_swing":
        before = pack["probability_swing"]["probability_before"]
        after = pack["probability_swing"]["probability_after"]
        if language == "english":
            return [
                "One over changed the match.",
                f"Probability moved from {before}% to {after}%.",
                "Normal score apps miss this kind of swing."
            ]
        return [
            "Ek over ne match badal diya.",
            f"Probability {before}% se {after}% par aa gayi.",
            "Aise swing normal score apps miss kar dete hain."
        ]

    if stage == "post_match_proof":
        result_label = pack["post_match_proof"]["result_label"]
        if language == "english":
            return [
                "Here is the audit, not the hype.",
                f"We called it {pack['probability']}-{100 - pack['probability']}, not a fake sure-shot.",
                "Proof matters more than loud prediction pages." if result_label != "hit" else "The point is the process, not fake certainty."
            ]
        return [
            "Yeh audit hai, hype nahi.",
            f"Humne ise {pack['probability']}-{100 - pack['probability']} bola tha, sure-shot nahi.",
            "Proof fake prediction pages se zyada matter karta hai." if result_label != "hit" else "Point process ka hai, fake certainty ka nahi."
        ]

    if language == "english":
        return [
            "The edge opened before the crowd saw it.",
            "Probability and public reaction were not saying the same thing.",
            "This is an educational replay, not a guaranteed return story."
        ]
    return [
        "Edge crowd se pehle open hui thi.",
        "Probability aur public reaction same story nahi bol rahe the.",
        "Yeh educational replay hai, guaranteed return story nahi."
    ]


def build_voiceover(stage: str, pack: dict[str, Any], language: str) -> str:
    public_team = full_team_name(pack["public_team"])
    model_pick = full_team_name(pack["model_pick"])
    probability = pack["probability"]
    reasons = ". ".join(str(item).strip() for item in pack["reasons"][:3])
    cta = cta_text(pack["cta_mode"], language)

    if stage == "prematch":
        if language == "english":
            return (
                f"The public is backing {public_team}. "
                f"Our model leans {model_pick} at {probability} percent. "
                f"{reasons}. {cta}"
            )
        return (
            f"Public {public_team} ke saath hai. "
            f"Hamara model {model_pick} ko {probability} percent par lean karta hai. "
            f"{reasons}. {cta}"
        )

    if stage in {"toss_update", "turning_point", "probability_swing"}:
        stage_payload = pack[stage]
        signals = ". ".join(stage_payload["signals"][:3])
        lesson = stage_payload["lesson"]
        if language == "english":
            return f"{stage_payload['snapshot_label']}. {signals}. {lesson} {cta}"
        return f"{stage_payload['snapshot_label']}. {signals}. {lesson} {cta}"

    if stage == "post_match_proof":
        proof = pack["post_match_proof"]
        if language == "english":
            return (
                f"We originally had {model_pick} at {probability} percent. "
                f"Final winner: {proof['winner']}. {proof['audit_note']} {cta}"
            )
        return (
            f"Hamare model ne {model_pick} ko {probability} percent diya tha. "
            f"Final winner: {proof['winner']}. {proof['audit_note']} {cta}"
        )

    replay = pack["market_edge_replay"]
    if language == "english":
        return (
            f"{replay['snapshot_label']}. "
            f"Model probability moved from {replay['model_probability_before']} to {replay['model_probability_after']}. "
            f"Public pricing moved from {replay['public_probability_before']} to {replay['public_probability_after']}. "
            f"{replay['edge_reason']} {replay.get('risk_note') or 'Educational replay only.'}"
        )
    return (
        f"{replay['snapshot_label']}. "
        f"Model probability {replay['model_probability_before']} se {replay['model_probability_after']} par aayi. "
        f"Public pricing {replay['public_probability_before']} se {replay['public_probability_after']} par aayi. "
        f"{replay['edge_reason']} {replay.get('risk_note') or 'Educational replay only.'}"
    )


def build_caption(stage: str, pack: dict[str, Any], language: str) -> str:
    cta = cta_text(pack["cta_mode"], language)
    if stage == "post_match_proof":
        proof = pack["post_match_proof"]
        if language == "english":
            return (
                f"Post-match audit for {pack['match']}.\n"
                f"Model pick: {full_team_name(pack['model_pick'])} at {pack['probability']}%.\n"
                f"Winner: {proof['winner']}.\n"
                f"{proof['audit_note']}\n\n"
                f"{cta}"
            )
        return (
            f"{pack['match']} ka post-match audit.\n"
            f"Model pick: {full_team_name(pack['model_pick'])} at {pack['probability']}%.\n"
            f"Winner: {proof['winner']}.\n"
            f"{proof['audit_note']}\n\n"
            f"{cta}"
        )

    if stage == "market_edge_replay":
        replay = pack["market_edge_replay"]
        risk = replay.get("risk_note") or "Educational replay only."
        if language == "english":
            return (
                f"{pack['match']} educational replay.\n"
                f"Model: {replay['model_probability_before']}% -> {replay['model_probability_after']}%.\n"
                f"Public or price view: {replay['public_probability_before']}% -> {replay['public_probability_after']}%.\n"
                f"{replay['edge_reason']}\n\n"
                f"{risk}"
            )
        return (
            f"{pack['match']} educational replay.\n"
            f"Model: {replay['model_probability_before']}% -> {replay['model_probability_after']}%.\n"
            f"Public ya price view: {replay['public_probability_before']}% -> {replay['public_probability_after']}%.\n"
            f"{replay['edge_reason']}\n\n"
            f"{risk}"
        )

    if stage == "prematch":
        if language == "english":
            return (
                f"{pack['match']} pre-match read.\n"
                f"Public side: {full_team_name(pack['public_team'])}.\n"
                f"Model side: {full_team_name(pack['model_pick'])} at {pack['probability']}%.\n"
                + "\n".join(f"-> {reason}" for reason in pack["reasons"][:3])
                + f"\n\n{cta}"
            )
        return (
            f"{pack['match']} pre-match read.\n"
            f"Public side: {full_team_name(pack['public_team'])}.\n"
            f"Model side: {full_team_name(pack['model_pick'])} at {pack['probability']}%.\n"
            + "\n".join(f"-> {reason}" for reason in pack["reasons"][:3])
            + f"\n\n{cta}"
        )

    stage_payload = pack[stage]
    if language == "english":
        return (
            f"{pack['match']} {stage.replace('_', ' ')}.\n"
            f"{stage_payload['snapshot_label']}.\n"
            f"Probability: {stage_payload['probability_before']}% -> {stage_payload['probability_after']}%.\n"
            + "\n".join(f"-> {signal}" for signal in stage_payload["signals"][:3])
            + f"\n\nLesson: {stage_payload['lesson']}\n\n{cta}"
        )
    return (
        f"{pack['match']} {stage.replace('_', ' ')}.\n"
        f"{stage_payload['snapshot_label']}.\n"
        f"Probability: {stage_payload['probability_before']}% -> {stage_payload['probability_after']}%.\n"
        + "\n".join(f"-> {signal}" for signal in stage_payload["signals"][:3])
        + f"\n\nLesson: {stage_payload['lesson']}\n\n{cta}"
    )


def build_asset(stage: str, pack: dict[str, Any], language: str) -> dict[str, Any]:
    asset = {
        "template": stage,
        "language": language,
        "title": stage_title(stage, language),
        "match": pack["match"],
        "venue": pack.get("venue"),
        "public_team": pack["public_team"],
        "model_pick": pack["model_pick"],
        "probability": pack["probability"],
        "hook_variants": hooks_for_stage(stage, pack, language),
        "cta_mode": pack["cta_mode"],
        "cta_text": cta_text(pack["cta_mode"], language),
        "voiceover": build_voiceover(stage, pack, language),
        "caption": build_caption(stage, pack, language),
        "generated_at": now_iso(),
    }

    if stage == "prematch":
        asset["reasons"] = pack["reasons"][:3]
    elif stage == "post_match_proof":
        asset["proof"] = pack["post_match_proof"]
    elif stage == "market_edge_replay":
        asset["replay"] = {
            **pack["market_edge_replay"],
            "safe_framing": "Educational replay only. No guaranteed return claims."
        }
    else:
        asset["snapshot"] = pack[stage]

    return asset


def tracker_entry_to_pack(entry: dict[str, Any]) -> dict[str, Any]:
    pack: dict[str, Any] = {
        "schema_version": "1.0.0",
        "match": entry["match"],
        "venue": entry.get("venue"),
        "public_team": entry["prediction"]["model_pick"],
        "model_pick": entry["prediction"]["model_pick"],
        "probability": int(entry["prediction"]["probability"]),
        "reasons": [
            f"Tracker source: {entry['prediction']['source']}",
            f"Method: {entry['prediction']['method']}",
            "This audit comes from the recorded prediction history."
        ],
        "cta_mode": "follow",
        "languages": ["english", "hinglish"],
    }

    result = entry.get("result") or {}
    if result.get("status") == "settled":
        hit = result.get("hit")
        label = "hit" if hit is True else "miss"
        pack["post_match_proof"] = {
            "winner": result.get("winner") or "Unknown",
            "result_label": label,
            "audit_note": result.get("notes") or "Recorded result reconciled from the prediction tracker."
        }
    return pack


def load_tracker_entry(tracker_path: Path, match_id: str) -> dict[str, Any]:
    tracker = load_json(tracker_path)
    for entry in tracker.get("predictions", []):
        if entry.get("match_id") == match_id:
            return entry
    raise ValueError(f"Tracker entry not found for match_id: {match_id}")


def has_unsafe_replay_claim(text: str) -> bool:
    lowered = text.lower()
    banned_phrases = [
        "made money",
        "guaranteed profit",
        "guaranteed profits",
        "sure-shot profit",
        "sure shot profit",
    ]
    return any(phrase in lowered for phrase in banned_phrases)


def stages_to_generate(pack: dict[str, Any]) -> list[str]:
    ordered = [
        "prematch",
        "toss_update",
        "turning_point",
        "probability_swing",
        "post_match_proof",
        "market_edge_replay",
    ]
    present = []
    for stage in ordered:
        if stage == "prematch" or stage in pack:
            present.append(stage)
    return present


def build_pack_outputs(pack: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    validate_pack(pack)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at": now_iso(),
        "match": pack["match"],
        "output_dir": str(output_dir),
        "cta_mode": pack["cta_mode"],
        "languages": pack["languages"],
        "assets": [],
        "skipped_stages": [],
    }

    for stage in ["toss_update", "turning_point", "probability_swing", "post_match_proof", "market_edge_replay"]:
        if stage not in pack:
            manifest["skipped_stages"].append({"stage": stage, "reason": "not provided in source pack"})

    for stage in stages_to_generate(pack):
        if stage == "market_edge_replay":
            replay_note = pack[stage].get("risk_note") or ""
            if has_unsafe_replay_claim(replay_note):
                raise ValueError("market_edge_replay risk_note contains unsafe profit language")
        for language in pack["languages"]:
            asset = build_asset(stage, pack, language)
            filename = f"{stage}_{language}.json"
            path = output_dir / filename
            write_json(path, asset)
            manifest["assets"].append({
                "stage": stage,
                "language": language,
                "path": str(path),
            })

    manifest_path = output_dir / "manifest.json"
    write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a TrueOddsML match-day traffic content pack.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to match-day pack JSON")
    parser.add_argument("--tracker-match-id", help="Bootstrap pack from a tracker match_id instead of manual input")
    parser.add_argument("--tracker", type=Path, default=DEFAULT_TRACKER, help="Path to prediction_tracker.json")
    parser.add_argument("--output-dir", type=Path, help="Directory for generated assets")
    args = parser.parse_args()

    if args.tracker_match_id:
        entry = load_tracker_entry(args.tracker, args.tracker_match_id)
        pack = tracker_entry_to_pack(entry)
    else:
        if not args.input.exists():
            raise SystemExit(f"Input file not found: {args.input}")
        pack = load_json(args.input)

    match_slug = slugify(pack["match"])
    output_dir = args.output_dir or (DEFAULT_PACKS_DIR / match_slug)
    manifest = build_pack_outputs(pack, output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
