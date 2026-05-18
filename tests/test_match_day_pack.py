from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_match_day_pack import build_pack_outputs, tracker_entry_to_pack  # noqa: E402


def sample_pack():
    return {
        "schema_version": "1.0.0",
        "match": "GT vs SRH",
        "public_team": "SRH",
        "model_pick": "GT",
        "probability": 61,
        "reasons": [
            "Historical blend stayed with GT",
            "Venue context was not one-sided",
            "Public confidence ran hotter than the model"
        ],
        "cta_mode": "join_telegram",
        "languages": ["english", "hinglish"],
        "turning_point": {
            "snapshot_label": "82/1 after 9 overs",
            "probability_before": 62,
            "probability_after": 48,
            "signals": ["Dot-ball pressure", "Required rate rise", "Set batter risk"],
            "lesson": "Pressure was visible before the wicket."
        },
        "market_edge_replay": {
            "snapshot_label": "Mid-chase divergence",
            "model_probability_before": 62,
            "model_probability_after": 48,
            "public_probability_before": 71,
            "public_probability_after": 56,
            "edge_reason": "Crowd stayed too confident while pressure built.",
            "risk_note": "Educational replay only."
        }
    }


def test_build_pack_outputs_writes_three_hooks_and_single_cta(tmp_path):
    manifest = build_pack_outputs(sample_pack(), tmp_path)
    assert manifest["cta_mode"] == "join_telegram"
    prematch = (tmp_path / "prematch_english.json").read_text(encoding="utf-8")
    assert '"hook_variants": [' in prematch
    assert "Join Telegram" in prematch


def test_tracker_entry_to_pack_only_adds_proof_when_settled():
    pending_entry = {
        "match": "GT vs SRH",
        "venue": "Ahmedabad",
        "prediction": {
            "model_pick": "GT",
            "probability": 71,
            "source": "historical_blend_v1",
            "method": "35% overall + 35% H2H + 30% venue"
        },
        "result": {"status": "pending"}
    }
    settled_entry = {
        **pending_entry,
        "result": {
            "status": "settled",
            "winner": "SRH",
            "hit": False,
            "notes": "Close call, but the model missed the finish."
        }
    }

    pending_pack = tracker_entry_to_pack(pending_entry)
    settled_pack = tracker_entry_to_pack(settled_entry)

    assert "post_match_proof" not in pending_pack
    assert settled_pack["post_match_proof"]["winner"] == "SRH"
    assert settled_pack["post_match_proof"]["result_label"] == "miss"
