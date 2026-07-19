# Verdix — Economic Memory untuk AI Agent Economy

> ERC-8004 tells you WHO an agent is.
> **Verdix tells you HOW that agent has actually behaved.**

Phase 1 implementation dari VERDIX_PROTOCOL v8: identity + economic memory +
verification tiers + trust intelligence, dogfooded oleh trading bot sendiri.

## Arsitektur

```
Layer 0  AgentRegistry    — ERC-8004 draft surface: agent = NFT ERC-721,
                            register(agentURI), metadata k/v, operational wallet
                            (signature consent). SETIAP perpindahan kontrol
                            (transfer/wallet) tercatat → scorer men-discount
                            history lama (anti "beli reputasi")
Layer 2  EconomicMemory   — CORE ASSET: append-only log, HANYA recorder resmi
                            yang bisa menulis (self-report tidak mungkin masuk,
                            by construction)
         Recorders:
           PaymentRouter  — Tier 1: settlement adalah bukti (Class 1)
           TaskEscrow     — Tier 2: escrow + bond 10% DUA SISI; dispute →
                            arbitrator = Tier 3 (Class 2/3)
           StressOracle   — Tier 4: observed behavior under stress (Class 4),
                            bukti terlemah, bobot terendah
Layer 3  intel/trustscore.py — Trust Intelligence off-chain:
           f(success_rate·tier·recency, log-volume, counterparty-diversity
             anti-farming (1-HHI), stress, dispute record) → Trust Score
             + Economic CV
```

Anti-farming (cost-of-forgery principle v8): satu entry Tier-2 palsu butuh
lock payment + 2 bond + gas, dan pasangan counterparty eksklusif otomatis
kena penalti diversity di scorer — biaya memalsukan selalu > Trust Score
yang didapat.

## Jalankan

```bash
forge test                      # 22 test, termasuk skenario attack + fuzz
python3 -m unittest intel.test_trustscore -v   # 11 test scorer
bash demo/demo.sh [journal.db]  # end-to-end di anvil lokal:
                                # deploy → register 2 agent → escrow task →
                                # payment → dogfood trade bot SMC (read-only)
                                # → export → Trust Score + Economic CV
```

## Status

- [x] Kontrak Phase 1 + test (lokal, anvil)
- [x] Trust Intelligence v0 (bobot = starting point, dituning via dogfooding)
- [x] Dogfood: closed trades bot SMC → Class 4 attestations
- [ ] Deploy testnet (BSC/Base — nunggu wallet, Gate 1 w3lab)
- [ ] Indexer streaming (eth_getLogs) + API
- [ ] ZK privacy layer, HumanID, $VDX — Phase 2+

Dokumen desain: `/root/FORVERDIX/` (protocol v8, grand vision, arsitektur) +
`docs/MOAT_V9_ADDENDUM.md` (reposisi moat: on-chain = bukti publik, payload
off-chain + graph intelligence = aset proprietary; mitigasi identity transferable).
