from __future__ import annotations

import argparse
import json

from ipl_intelligence import build_intelligence, generate_match_card, write_intelligence_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IPL intelligence artifacts and match cards.")
    parser.add_argument(
        "command",
        choices=["build-all", "build-card"],
        help="build-all writes venue/player intelligence; build-card writes one fixture card JSON.",
    )
    parser.add_argument("--match", help="Fixture string like 'GT vs SRH'")
    parser.add_argument("--venue", help="Optional venue name")
    args = parser.parse_args()

    if args.command == "build-all":
        artifacts = build_intelligence()
        written = write_intelligence_artifacts(artifacts)
        print(json.dumps({name: str(path) for name, path in written.items()}, indent=2))
        return

    if not args.match:
        raise SystemExit("--match is required for build-card")
    card, output_path = generate_match_card(args.match, args.venue)
    print(json.dumps({"output": str(output_path), "model_pick": card["prediction"]["model_pick"], "probability": card["prediction"]["probability"]}, indent=2))


if __name__ == "__main__":
    main()
