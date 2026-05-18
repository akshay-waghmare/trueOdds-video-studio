from __future__ import annotations

import argparse
import json
from pathlib import Path

from ipl_intelligence import record_prediction, reconcile_prediction


def main() -> None:
    parser = argparse.ArgumentParser(description="Record and reconcile TrueOddsML predictions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Record a prediction from a card JSON or a fixture string.")
    record_parser.add_argument("--card", type=Path, help="Path to a generated match intelligence card JSON")
    record_parser.add_argument("--match", help="Fixture string like 'GT vs SRH'")
    record_parser.add_argument("--venue", help="Optional venue")

    reconcile_parser = subparsers.add_parser("reconcile", help="Reconcile a recorded prediction with the final winner.")
    reconcile_parser.add_argument("--match-id", required=True, help="Tracker match_id")
    reconcile_parser.add_argument("--winner", required=True, help="Winner abbreviation or full name")
    reconcile_parser.add_argument("--notes", help="Optional notes for what went right or wrong")

    args = parser.parse_args()

    if args.command == "record":
        entry, path = record_prediction(card_path=args.card, match=args.match, venue=args.venue)
        print(json.dumps({"tracker": str(path), "entry": entry}, indent=2))
        return

    entry, path = reconcile_prediction(args.match_id, args.winner, args.notes)
    print(json.dumps({"tracker": str(path), "entry": entry}, indent=2))


if __name__ == "__main__":
    main()
