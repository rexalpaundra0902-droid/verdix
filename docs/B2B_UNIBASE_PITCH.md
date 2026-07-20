# Verdix × Unibase/BitAgent — Partnership Pitch (B2B draft v1)

*Draft 2026-07-20. Audience: Unibase/BitAgent core team (Discord/TG/X DM or
call). Ask at the bottom. Keep to ~2 min read. Bahasa: EN (tim internasional).
Status: DRAFT — belum dikirim, nunggu review Reku.*

---

## One-liner

**BitAgent gives agents identity, memory, and payments. Verdix gives them a
track record they can't fake.** We'd like to be the verification/reputation
layer for the BitAgent marketplace — starting free, on your stack, where we
already run live.

## The gap (why now)

- Your stack ships **ERC-8004 identity + Membase memory + x402/ERC-8183
  commerce** — but no reputation layer. Buyers on the marketplace pick agents
  by claims, not evidence. (Your own bnbagent-sdk README notes indexing 8183
  settlement events on free RPCs is painful — that's exactly the layer we run.)
- The market has already voted on what happens without verification:
  **BasisOS/Virtuals — $500k lost, then Virtuals *mandated* on-chain logging**;
  Bankr ($200k) and OpenClaw ($600k) hit the same wall. a16z now calls the gap
  "KYA" (Know Your Agent). Platforms end up holding the reimbursement bag.
- Every marketplace that matured (eBay, Upwork, app stores) won on the same
  primitive: **verified track record**. Agent marketplaces won't be different.

## What we already built — on YOUR stack, live today

| Piece | Status |
|---|---|
| Agent registered in **your AIP Registry (ERC-8004 #1700**, BSC testnet 97) — same agent also in our registry: one agent, two 8004 registries, interoperable | live |
| **Membase as payload store**: every on-chain `dataHash` in our EconomicMemory resolves to a verifiable payload on your hub | live (hackathon submission) |
| **RiskGuardVault**: non-custodial vault whose policy (max tx / daily cap / halt floor) is enforced by the chain — violating tx *reverts*, and the revert is part of the record | live, 9 verified contracts, 47 tests |
| **Trust Score + public agent profiles** (open formula, open source) | live — verdix.pages.dev |
| Dogfood: our own trading agent writing real entries daily | live |

No slideware: `api.aip.unibase.com/agents/handle/verdix-smc-bot` is our agent
on your platform; its track record is at `verdix.pages.dev` (profile #1).

## The proposal — pilot, free, 4–6 weeks

1. **Badge in the marketplace**: BitAgent listings can show a "Verdix
   verified" score (API/embed we provide; formula stays open source).
2. **8183 settlements → reputation**: our indexer ingests your commerce
   settlement events on chain 97 as first-class evidence — every completed
   job on BitAgent builds the agent's portable track record automatically.
3. **Vaults for your operators**: any BitAgent operator can deploy a
   policy-guarded vault self-serve (already live at /web/create) — the
   platform's fraud/reimbursement exposure drops because limits are enforced
   on-chain, not by promises.

**Cost to Unibase: zero.** Beta is free for operators; we want usage data and
feedback on scoring weights. If the badge drives marketplace trust, we talk
about a paid platform tier later (x402 per-verification is on our roadmap —
your own payment rail).

## Why us, honestly

- Small team, but the stack is **live and dogfooded**, not a deck.
- Standard-native: ERC-8004 both sides, BAS-compatible attestations planned,
  BSC testnet 97 where you already are.
- We deliberately did NOT build a competing directory/marketplace — Verdix is
  the neutral evidence layer; BitAgent stays the venue.

## The ask

1. 30-min call (or async thread) with whoever owns marketplace/trust.
2. Blessing to run the 8183-settlement indexer against your testnet contracts
   (ABI/addresses for the commerce contract if unverified).
3. One pilot cohort: 3–5 operators from your community try vaults + profiles;
   we tune scoring on real usage.

Contact: @<REKU_X_HANDLE> · repo: github.com/rexalpaundra0902-droid/verdix ·
live: verdix.pages.dev

---

*Catatan internal (jangan ikut kekirim):*
- *Angka insiden (BasisOS $500k, Bankr $200k, OpenClaw $600k, mandat Virtuals)
  = dari PRODUCT_RESEARCH_VERDICT.md — riset dihentikan sebelum verifikasi
  adversarial penuh; sebelum kirim, cek ulang 3 link sumber utama ATAU
  lunakkan jadi "publicly reported incidents".*
- *Agent #1700 & handle: verifikasi masih resolve sebelum kirim (SDK mereka
  pre-release, hub bisa berubah).*
- *Placeholder `<REKU_X_HANDLE>` — isi akun X Reku.*
- *Jalur kirim (urutan): DM X @unibase_ai → Discord #builders → form kontak.
  JANGAN kirim sebelum Reku approve teks.*
