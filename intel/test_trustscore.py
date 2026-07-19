#!/usr/bin/env python3
"""Unit test Trust Intelligence — jalankan: python3 -m unittest intel.test_trustscore -v"""

import unittest

from intel.trustscore import compute, economic_cv

NOW = 1_800_000_000
DAY = 86_400
ETH = 10**18


def entry(agent, cp, klass, tier, eth, outcome, days_ago=1, eid=0):
    return {
        "entryId": eid,
        "agentId": agent,
        "counterpartyId": cp,
        "actionClass": klass,
        "tier": tier,
        "valueWei": str(eth * ETH),
        "outcome": outcome,
        "timestamp": NOW - days_ago * DAY,
    }


class TrustScoreTest(unittest.TestCase):
    def test_empty_history_scores_low(self):
        c = compute([], agent_id=1, now=NOW)
        # tanpa history: cuma stress netral 0.5 * bobot 0.10 = 5.0
        self.assertLessEqual(c.score(), 5.0)

    def test_honest_agent_beats_farmer_despite_fewer_entries(self):
        # honest: 6 task sukses ke 6 counterparty berbeda
        honest = [
            entry(1, cp, 2, 2, 5, 0, days_ago=cp, eid=cp) for cp in range(2, 8)
        ]
        # farmer: 12 task sukses tapi SEMUA dengan 1 counterparty yang sama
        farmer = [
            entry(9, 10, 2, 2, 5, 0, days_ago=i + 1, eid=100 + i) for i in range(12)
        ]
        s_honest = compute(honest, 1, now=NOW).score()
        s_farmer = compute(farmer, 9, now=NOW).score()
        self.assertGreater(s_honest, s_farmer)
        # farming pattern → diversity mendekati nol
        self.assertLess(compute(farmer, 9, now=NOW).counterparty_diversity, 0.15)

    def test_lost_dispute_tanks_score(self):
        clean = [entry(1, c, 2, 2, 5, 0, days_ago=c, eid=c) for c in range(2, 7)]
        dirty = clean + [entry(1, 8, 3, 3, 5, 3, days_ago=1, eid=99)]
        self.assertGreater(
            compute(clean, 1, now=NOW).score(), compute(dirty, 1, now=NOW).score()
        )
        self.assertEqual(compute(dirty, 1, now=NOW).disputes_against, 1)

    def test_tier1_settlement_outweighs_tier4_attestation(self):
        # kegagalan di tier 4 (bukti lemah) harus lebih ringan daripada di tier 1
        base = [entry(1, c, 2, 2, 5, 0, days_ago=c, eid=c) for c in range(2, 6)]
        fail_t1 = base + [entry(1, 7, 1, 1, 5, 1, days_ago=1, eid=50)]
        fail_t4 = base + [entry(1, 0, 4, 4, 5, 1, days_ago=1, eid=51)]
        self.assertLess(
            compute(fail_t1, 1, now=NOW).success_rate,
            compute(fail_t4, 1, now=NOW).success_rate,
        )

    def test_recency_decay_old_failures_matter_less(self):
        recent_fail = [entry(1, 2, 2, 2, 5, 1, days_ago=1, eid=1)] + [
            entry(1, c, 2, 2, 5, 0, days_ago=300, eid=c) for c in range(3, 8)
        ]
        old_fail = [entry(1, 2, 2, 2, 5, 1, days_ago=300, eid=1)] + [
            entry(1, c, 2, 2, 5, 0, days_ago=1, eid=c) for c in range(3, 8)
        ]
        self.assertLess(
            compute(recent_fail, 1, now=NOW).success_rate,
            compute(old_fail, 1, now=NOW).success_rate,
        )

    def test_stress_behavior_from_class4(self):
        entries = [
            entry(1, 0, 4, 4, 1, 0, days_ago=2, eid=1),
            entry(1, 0, 4, 4, 1, 0, days_ago=3, eid=2),
            entry(1, 0, 4, 4, 1, 1, days_ago=4, eid=3),
        ]
        c = compute(entries, 1, now=NOW)
        self.assertGreater(c.stress_behavior, 0.6)
        self.assertLess(c.stress_behavior, 0.75)

    def test_volume_log_scaled_whale_cannot_dominate(self):
        small = [entry(1, 2, 1, 1, 10, 0, days_ago=1, eid=1)]
        whale = [entry(1, 2, 1, 1, 10_000, 0, days_ago=1, eid=1)]
        v_small = compute(small, 1, now=NOW).economic_volume
        v_whale = compute(whale, 1, now=NOW).economic_volume
        self.assertLess(v_whale, 1.0 + 1e-9)
        self.assertLess(v_whale / max(v_small, 1e-9), 4.0)  # 1000x nilai != 1000x skor

    def test_counterparty_sees_graph_entry(self):
        entries = [entry(1, 2, 1, 1, 5, 0, days_ago=1, eid=1)]
        c = compute(entries, 2, now=NOW)
        self.assertEqual(c.n_graph, 1)
        self.assertEqual(c.n_subject, 0)
        self.assertEqual(c.distinct_counterparties, 1)

    def test_economic_cv_renders(self):
        entries = [entry(1, 2, 1, 1, 5, 0, days_ago=1, eid=1)]
        cv = economic_cv(entries, 1, name="smc-bot", now=NOW)
        self.assertIn("Trust Score", cv)
        self.assertIn("smc-bot", cv)
        self.assertIn("Counterparty diversity", cv)


if __name__ == "__main__":
    unittest.main()
