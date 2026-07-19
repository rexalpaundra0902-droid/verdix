#!/usr/bin/env python3
"""Verdix Layer 3 — Trust Intelligence (off-chain).

Menghitung Trust Score dari Economic Memory entries sesuai bentuk fungsional
VERDIX_PROTOCOL v8:

    Trust Score = f(success_rate, economic_volume, counterparty_diversity,
                    stress_behavior, recency, dispute_rate)

Prinsip desain v8 yang dipegang:
- Input HANYA entry yang lolos verification tier on-chain (scorer tidak pernah
  mengkonsumsi klaim tak terverifikasi — by construction, karena EconomicMemory
  cuma bisa ditulis recorder resmi).
- Transparan di input: output selalu menyertakan breakdown komponen
  (gaya "Economic CV"), walau bobot bisa dituning.
- Tier 4 statistical screening: pasangan counterparty yang eksklusif
  (farming pattern) menurunkan diversity — entry-nya tidak dihapus,
  tapi bobot graph-nya rendah.

Entry format (JSON list):
    {"entryId": 0, "agentId": 1, "counterpartyId": 2, "actionClass": 1..4,
     "tier": 1..4, "valueWei": "2000000000000000000", "outcome": 0..3,
     "timestamp": 1780000000}

Outcome: 0 Success, 1 Failed, 2 DisputedFor, 3 DisputedAgainst
Class:   1 Settlement, 2 Agreement, 3 Adjudicated, 4 Stress

Bobot di bawah adalah STARTING POINT — v8 eksplisit bilang bobot pasti salah
saat launch dan harus dituning pakai data dogfooding.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import defaultdict
from dataclasses import dataclass

WEI = 10**18

# Bobot bukti per verification tier (tier 1 = settlement, paling kuat)
TIER_WEIGHT = {1: 1.00, 2: 0.75, 3: 0.90, 4: 0.30}

# Bobot komponen di skor akhir
W_SUCCESS = 0.40
W_VOLUME = 0.15
W_DIVERSITY = 0.20
W_STRESS = 0.10
W_DISPUTE = 0.15

RECENCY_HALF_LIFE_DAYS = 90.0
VOLUME_SATURATION_ETH = 1000.0  # volume yang dianggap "penuh" di komponen volume

# Identity ERC-8004 = NFT transferable → reputasi bisa DIBELI. Mitigasi:
# history yang diperoleh SEBELUM perpindahan kontrol (ownership transfer /
# ganti operational wallet) hanya dibawa sebagian — skor mengikuti perilaku
# controller sekarang, bukan token-nya.
CONTROL_CHANGE_CARRYOVER = 0.4  # multiplier per perpindahan kontrol sesudah entry
# Evidence yang hilang karena perpindahan kontrol tidak dibuang begitu saja —
# ia berubah jadi KETIDAKPASTIAN: separuhnya masuk penyebut success rate sebagai
# "outcome tak diketahui". Ini yang bikin identity hasil beli < identity fresh.
CONTROL_CHANGE_UNCERTAINTY = 0.5

OUTCOME_SUCCESS = 0
OUTCOME_FAILED = 1
OUTCOME_DISPUTED_FOR = 2
OUTCOME_DISPUTED_AGAINST = 3

CLASS_STRESS = 4


@dataclass
class Components:
    success_rate: float
    economic_volume: float  # 0..1 (log-scaled)
    counterparty_diversity: float
    stress_behavior: float
    dispute_component: float
    n_subject: int
    n_graph: int
    volume_eth: float
    distinct_counterparties: int
    disputes_against: int
    n_control_changes: int

    def score(self) -> float:
        raw = (
            W_SUCCESS * self.success_rate
            + W_VOLUME * self.economic_volume
            + W_DIVERSITY * self.counterparty_diversity
            + W_STRESS * self.stress_behavior
            + W_DISPUTE * self.dispute_component
        )
        return round(100.0 * raw, 1)


def _recency_weight(ts: int, now: int) -> float:
    age_days = max(0.0, (now - ts) / 86400.0)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def _is_success(outcome: int) -> bool:
    return outcome in (OUTCOME_SUCCESS, OUTCOME_DISPUTED_FOR)


def _carryover(ts: int, control_changes: list[int]) -> float:
    """Multiplier bukti untuk entry di timestamp ts: tiap perpindahan kontrol
    SESUDAH entry memotong bobotnya (history itu milik controller lama)."""
    n_after = sum(1 for c in control_changes if c > ts)
    return CONTROL_CHANGE_CARRYOVER**n_after


def compute(
    entries: list[dict],
    agent_id: int,
    now: int | None = None,
    control_changes: list[int] | None = None,
) -> Components:
    now = int(now if now is not None else time.time())
    control_changes = [int(c) for c in (control_changes or [])]
    subject = [e for e in entries if int(e["agentId"]) == agent_id]
    graph = [
        e
        for e in entries
        if int(e["agentId"]) == agent_id or int(e.get("counterpartyId", 0)) == agent_id
    ]

    # --- success_rate: tier-, recency- & carryover-weighted, subjek saja ---
    num = den = den_raw = 0.0
    for e in subject:
        w_raw = TIER_WEIGHT[int(e["tier"])] * _recency_weight(int(e["timestamp"]), now)
        w = w_raw * _carryover(int(e["timestamp"]), control_changes)
        den_raw += w_raw
        den += w
        if _is_success(int(e["outcome"])):
            num += w
    # evidence yang gugur karena kontrol pindah → sebagian jadi "unknown" di penyebut
    lost = den_raw - den
    success_rate = (num / (den + CONTROL_CHANGE_UNCERTAINTY * lost)) if den > 0 else 0.0
    # fraksi evidence yang selamat — dipakai men-discount komponen graph
    evidence_f = (den / den_raw) if den_raw > 0 else 1.0

    # --- economic_volume: log-scaled, carryover-adjusted ---
    volume_eth = (
        sum(int(e["valueWei"]) * _carryover(int(e["timestamp"]), control_changes) for e in graph)
        / WEI
    )
    economic_volume = min(
        1.0, math.log10(1.0 + volume_eth) / math.log10(1.0 + VOLUME_SATURATION_ETH)
    )

    # --- counterparty_diversity: 1 - HHI konsentrasi (anti-farming Tier 4) ---
    per_cp: dict[int, float] = defaultdict(float)
    for e in graph:
        cp = (
            int(e.get("counterpartyId", 0))
            if int(e["agentId"]) == agent_id
            else int(e["agentId"])
        )
        if cp and cp != agent_id:
            per_cp[cp] += _carryover(int(e["timestamp"]), control_changes)
    total = sum(per_cp.values())
    if total > 0:
        hhi = sum((c / total) ** 2 for c in per_cp.values())
        # >1 counterparty mulai dapat kredit; 1 counterparty eksklusif = 0
        counterparty_diversity = 1.0 - hhi
        # saturasi: dengan k counterparty seimbang, 1-HHI = 1-1/k; normalisasi ke target k=10
        counterparty_diversity = min(1.0, counterparty_diversity / (1.0 - 1.0 / 10.0))
        # relasi graph dibangun controller lama → ikut ter-discount saat kontrol pindah
        counterparty_diversity *= evidence_f
    else:
        counterparty_diversity = 0.0

    # --- stress_behavior: Class 4 saja; tanpa data = 0.5 netral ---
    stress = [e for e in subject if int(e["actionClass"]) == CLASS_STRESS]
    if stress:
        s_num = s_den = 0.0
        for e in stress:
            w = _recency_weight(int(e["timestamp"]), now) * _carryover(
                int(e["timestamp"]), control_changes
            )
            s_den += w
            if _is_success(int(e["outcome"])):
                s_num += w
        stress_behavior = s_num / s_den
    else:
        stress_behavior = 0.5

    # --- dispute_rate: porsi subjek yang berakhir di arbitrase & hasilnya ---
    disputes_against = sum(
        1 for e in subject if int(e["outcome"]) == OUTCOME_DISPUTED_AGAINST
    )
    disputed = sum(
        1
        for e in subject
        if int(e["outcome"]) in (OUTCOME_DISPUTED_FOR, OUTCOME_DISPUTED_AGAINST)
    )
    if subject:
        lost_rate = disputes_against / len(subject)
        friction_rate = disputed / len(subject)
        # kalah dispute jauh lebih berat daripada sekadar sering ke arbitrase
        dispute_component = max(0.0, 1.0 - 3.0 * lost_rate - 0.5 * friction_rate)
    else:
        dispute_component = 0.0

    return Components(
        success_rate=success_rate,
        economic_volume=economic_volume,
        counterparty_diversity=counterparty_diversity,
        stress_behavior=stress_behavior,
        dispute_component=dispute_component,
        n_subject=len(subject),
        n_graph=len(graph),
        volume_eth=volume_eth,
        distinct_counterparties=len(per_cp),
        disputes_against=disputes_against,
        n_control_changes=len(control_changes),
    )


def economic_cv(
    entries: list[dict],
    agent_id: int,
    name: str = "",
    now: int | None = None,
    control_changes: list[int] | None = None,
) -> str:
    c = compute(entries, agent_id, now=now, control_changes=control_changes)
    label = name or f"Agent #{agent_id}"
    lines = [
        f"# Economic CV — {label}",
        "",
        f"**Trust Score: {c.score():.1f} / 100**",
        "",
        f"- Verified economic actions (subjek): {c.n_subject}",
        f"- Keterlibatan graph total: {c.n_graph}",
        f"- Volume terverifikasi: {c.volume_eth:.4f} ETH",
        f"- Counterparty unik: {c.distinct_counterparties}",
        f"- Kalah dispute: {c.disputes_against}",
        f"- Perpindahan kontrol identity: {c.n_control_changes}"
        + (" ⚠ history lama di-discount" if c.n_control_changes else ""),
        "",
        "| Komponen | Nilai | Bobot |",
        "|---|---|---|",
        f"| Success rate (tier+recency weighted) | {c.success_rate:.3f} | {W_SUCCESS} |",
        f"| Economic volume (log-scaled) | {c.economic_volume:.3f} | {W_VOLUME} |",
        f"| Counterparty diversity (anti-farming) | {c.counterparty_diversity:.3f} | {W_DIVERSITY} |",
        f"| Stress behavior (Class 4) | {c.stress_behavior:.3f} | {W_STRESS} |",
        f"| Dispute record | {c.dispute_component:.3f} | {W_DISPUTE} |",
        "",
        "*Semua input berasal dari Economic Memory on-chain yang lolos verification",
        "tier — tidak ada self-report. Bobot = starting point, dituning via dogfooding.*",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Verdix Trust Intelligence scorer")
    ap.add_argument("entries_json", help="file JSON list of entries, atau '-' utk stdin")
    ap.add_argument("--agent", type=int, required=True, help="agentId subjek")
    ap.add_argument("--name", default="", help="nama tampilan agent")
    ap.add_argument("--now", type=int, default=None, help="override waktu skor (unix)")
    ap.add_argument("--json", action="store_true", help="output JSON, bukan Economic CV")
    ap.add_argument(
        "--rotations",
        default=None,
        help="file JSON {agentId: [timestamp perpindahan kontrol, ...]} dari registry",
    )
    args = ap.parse_args()

    raw = (
        sys.stdin.read()
        if args.entries_json == "-"
        else open(args.entries_json).read()
    )
    entries = json.loads(raw)
    rotations: list[int] = []
    if args.rotations:
        rotations = json.load(open(args.rotations)).get(str(args.agent), [])

    if args.json:
        c = compute(entries, args.agent, now=args.now, control_changes=rotations)
        print(json.dumps({"agentId": args.agent, "trustScore": c.score(), **c.__dict__}, indent=2))
    else:
        print(
            economic_cv(
                entries, args.agent, name=args.name, now=args.now, control_changes=rotations
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
