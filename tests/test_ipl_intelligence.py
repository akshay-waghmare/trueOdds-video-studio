from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ipl_intelligence import canonical_player_id, canonical_venue_name, compute_brier_score, phase_for_legal_ball


class IPLIntelligenceTests(unittest.TestCase):
    def test_canonical_venue_name_merges_aliases(self) -> None:
        self.assertEqual(canonical_venue_name("M.Chinnaswamy Stadium"), "M Chinnaswamy Stadium")
        self.assertEqual(canonical_venue_name("M Chinnaswamy Stadium"), "M Chinnaswamy Stadium")

    def test_canonical_player_id_prefers_registry(self) -> None:
        self.assertEqual(canonical_player_id("DA Warner", {"DA Warner": "20291"}), "20291")
        self.assertEqual(canonical_player_id("Unknown Player", {}), "name:unknown-player")

    def test_phase_boundaries_follow_legal_ball_counts(self) -> None:
        self.assertEqual(phase_for_legal_ball(1), "powerplay")
        self.assertEqual(phase_for_legal_ball(36), "powerplay")
        self.assertEqual(phase_for_legal_ball(37), "middle")
        self.assertEqual(phase_for_legal_ball(90), "middle")
        self.assertEqual(phase_for_legal_ball(91), "death")

    def test_brier_score(self) -> None:
        self.assertAlmostEqual(compute_brier_score(0.63, True), 0.1369, places=4)
        self.assertAlmostEqual(compute_brier_score(0.63, False), 0.3969, places=4)


if __name__ == "__main__":
    unittest.main()
