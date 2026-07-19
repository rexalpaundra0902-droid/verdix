#!/usr/bin/env python3
"""Unit test scorer BitAgent — offline (tanpa network).
Jalankan: python3 -m unittest bitagent.test_indexer -v"""

import unittest

from bitagent.indexer import leaderboard, score_agent


def agent(handle, total=0, done=0, rev=0.0, onchain=True, online=True):
    return {
        "handle": handle, "agent_id": f"97:0xreg:{hash(handle) % 1000}",
        "display_name": handle, "registered_onchain": onchain, "online": online,
        "stats": {"total_jobs": total, "completed_jobs": done, "total_revenue": rev},
    }


class IndexerTest(unittest.TestCase):
    def test_empty_stats_scores_identity_only(self):
        s = score_agent(agent("fresh"))
        self.assertEqual(s["components"]["success_rate"], 0.0)
        self.assertEqual(s["components"]["activity"], 0.0)
        # registered_onchain tanpa cek langsung → identity 0.5 (klaim platform)
        self.assertEqual(s["components"]["identity"], 0.5)
        self.assertLessEqual(s["trustScore"], 10.0)

    def test_reliable_beats_spammy(self):
        # 5/5 jobs selesai vs 283 jobs cuma 5 selesai (pola flaptest asli)
        reliable = score_agent(agent("reliable", total=5, done=5, rev=0.01))
        spammy = score_agent(agent("spammy", total=283, done=5, rev=0.5))
        self.assertGreater(reliable["trustScore"], spammy["trustScore"])

    def test_revenue_log_scaled(self):
        small = score_agent(agent("s", total=10, done=10, rev=1.0))
        whale = score_agent(agent("w", total=10, done=10, rev=1000.0))
        ratio = whale["components"]["economic_volume"] / max(
            small["components"]["economic_volume"], 1e-9)
        self.assertLess(ratio, 12)  # 1000x revenue != 1000x komponen

    def test_no_stats_key_safe(self):
        a = agent("nostats")
        a["stats"] = None
        s = score_agent(a)
        self.assertEqual(s["raw_stats"]["total_jobs"], 0.0)

    def test_leaderboard_sorted_desc(self):
        agents = [agent("a", 5, 5, 0.1), agent("b"), agent("c", 100, 90, 5.0)]
        lb = leaderboard(agents=agents, top=3)
        scores = [x["trustScore"] for x in lb]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(lb[0]["handle"], "c")


if __name__ == "__main__":
    unittest.main()
