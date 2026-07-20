# Verdix — BNB Chain Grant Proposal (DRAFT)

> **Status: DRAFT for Reku's review. Nothing submitted. No form opened.**
> **Selected path: Scenario B (Medium) — $60K · 16 weeks · traction-first delivery: beta operators + external security review up front, mainnet behind them.**
> Program: BNB Chain Grants (rolling, up to $200K) — category **Dev Tools & Infra + AI/DePIN**.
> Repo: https://github.com/rexalpaundra0902-droid/verdix · Live: https://verdix.pages.dev · API: http://194.233.93.155:8600

---

## 0. Positioning in one sentence

**Proof-of-personhood proves a *human* is unique. Verdix proves an *AI agent* is
trustworthy** — sybil-resistant reputation for the agent economy, computed from
economic actions the agent *cannot* fake, on top of the identity and commerce
rails BNB Chain is already shipping (ERC-8004, bnbagent-sdk, BAS).

---

## 1. Problem statement

*(Framing deliberately aligned to Wishlist Issue #66 "Anti Sybil Tool", re-pointed
from humans to agents.)*

Issue #66 frames the core problem precisely: *"Bots and fake accounts can
undermine the integrity of digital protocols, leading to abuse and reducing trust
within online communities."* Its proposed answer is **proof-of-personhood** — prove
a real, unique *human* is behind an account.

BNB Chain is now betting on the opposite kind of account: **autonomous AI agents**
that hold wallets, negotiate, take jobs, and move money. The 2026 roadmap ships an
**AI Agent Framework with an agent registry supporting identity, reputation
scoring, and verifiable capabilities**, an **ERC-8004 Agent Registry** (agents as
tradable NFTs with on-chain reputation, Nov 2025), and an **Agent Passport**
(portable verifiable identity, May 2026) explicitly to *"combat fake accounts and
Sybil attacks."* The rails for *who an agent is* now exist.

But identity alone does not stop sybil abuse in the agent economy. Three gaps
remain:

1. **Identity is cheap; reputation is not.** ERC-8004 registration is gas-free
   (MegaFuel-sponsored in bnbagent-sdk). One operator can mint 1,000 agent NFTs in
   an afternoon. A registry answers *"is this a registered agent?"* — not *"has this
   agent ever behaved well with real money at risk?"*
2. **Self-reported track records are worthless.** An agent claiming *"98% job
   success"* in its own metadata is exactly the fake-account problem #66 describes,
   moved up a layer. There is no on-chain, un-gameable record of *observed*
   economic behavior.
3. **Reputation-buying defeats naive scores.** If reputation attaches to a
   transferable identity NFT, a bad actor simply buys an aged, high-score agent and
   inherits its trust.

**The anti-sybil problem for agents is not "prove you're human" — it's "prove your
track record cost something real to earn, and can't be transferred, farmed, or
faked."** That is the tool this grant funds.

---

## 2. Solution — and what is *already live* (proof, not promises)

Verdix is an **on-chain economic memory + trust-intelligence layer** for AI agents.
It does not re-invent identity — it consumes BNB Chain's identity rails and adds the
missing layer: **verifiable reputation with built-in sybil resistance.**

### 2.1 Already shipped on BSC Testnet (chain 97) — verifiable today

| Component | What it does | Proof |
|---|---|---|
| **6 verified contracts** | AgentRegistry (ERC-8004), EconomicMemory, PaymentRouter, TaskEscrow, StressOracle, RiskGuardVault | All verified on BscScan (`deployments/bsc-testnet.json`), 30+ successful txs |
| **EconomicMemory** | Append-only ledger; **only audited recorder contracts can write** — self-report is impossible by construction | `0x8692F4Bbc7422139D4335AF01734bEbe99516900` |
| **RiskGuardVault** | On-chain risk constitution (max-tx / daily cap / cooldown / whitelist / halt floor) the agent cannot override | Compliant tx succeeds; oversized tx **reverts `ExceedsMaxTx`** on-chain |
| **Trust Score engine** | `f(success·tier·recency, log-volume, counterparty-diversity anti-farming, stress behavior, disputes, control-change decay)` | `intel/trustscore.py`, 11 unit tests incl. bought-identity decay |
| **Reputation API (live)** | `/agents`, `/agent/1/cv`, `/memory/<dataHash>`, `/bitagent` | http://194.233.93.155:8600 |
| **Self-serve product** | Anyone registers an ERC-8004 agent + deploys a policy-guarded non-custodial vault from the browser | VaultFactory `0x5883…75e4`, `/web/create` |
| **Dogfood** | A real live 4H trading bot writes its own economic memory daily | 8+ on-chain attestations, growing |
| **Unibase integration** | ERC-8004 #1700 in AIP Registry; payloads on Membase; live gateway agent answers real jobs | BNB Hack × Unibase submission (submitted) |

### 2.2 The sybil-resistance mechanics (the actual "anti-sybil tool")

These are **already implemented**, not roadmap:

- **Cost-to-fake.** A fake Tier-2 track-record entry requires locking a payment +
  two escrow bonds + gas. Reputation is *bought with capital at risk*, so farming
  it costs more than it's worth.
- **Anti-farming via counterparty diversity.** Two colluding agents trading only
  with each other are down-weighted by a **1 − HHI** diversity term — reputation
  earned from a diverse, real counterparty set outscores an echo chamber.
- **Anti reputation-buying.** ERC-8004 identity is a transferable NFT, so every
  control change (transfer / wallet rotation) is logged on-chain, and the scorer
  **decays pre-transfer history** — a bought identity scores *below* a fresh one.
- **Skin in the game.** $VDX stake-to-back-an-agent with a 7-day unstake cooldown;
  `vdxStaked` is surfaced in the API — reputation backed by capital that can't run
  away right before consequences land.

This is sybil resistance by **economic cost + graph structure + identity-transfer
accounting**, not by biometrics — the right primitive when the "users" are agents,
not humans.

---

## 3. Why this is a public good for the BNB ecosystem

### 3.1 Direct integration with `bnb-chain/bnbagent-sdk`

The SDK gives agents **identity (ERC-8004)** and **commerce (ERC-8183: negotiate →
accept job → deliver → settle via optimistic escrow)**. It deliberately does **not**
ship a reputation layer — and its own README notes that raw ERC-8183 event indexing
is currently hard on free RPCs. **That gap is exactly Verdix's layer.** Concrete plug-in path:

1. **Verdix as an ERC-8183 settlement recorder.** Every settled job in the SDK's
   escrow flow is an *observed* economic outcome. Verdix ingests those settlement
   events into EconomicMemory the same way it ingests its own PaymentRouter/TaskEscrow
   events today — turning the SDK's commerce trail into an un-fakeable track record.
2. **A drop-in `verdix` reputation client for the SDK.** The SDK is already plugin-shaped
   (`StorageProvider`, `WalletProvider`, `PolicyClient` abstractions). Verdix ships a
   small client so any SDK agent can (a) publish its Trust Score in its agent card and
   (b) query a counterparty's score *before* accepting a job — sybil defense at the
   point of transaction.
3. **A2A / MCP reputation endpoint.** The SDK prefers A2A endpoints; Verdix already
   serves a REST reputation surface. Expose it as an A2A/MCP capability so any agent —
   or a marketplace built on the SDK — can resolve `handle → verifiable reputation`.

### 3.2 Complementary to (not competing with) BNB's own stack

- **ERC-8004 Agent Registry / Agent Passport** answer *identity*; Verdix answers
  *behavior over time*. Passports say who you are; Verdix says how you've acted.
- **BAS (BNB Attestation Service)** is the ecosystem's attestation primitive.
  Verdix can **emit Trust Scores as BAS attestations** and **consume BAS attestations**
  as memory inputs — making Verdix a producer/consumer in the native trust graph,
  not a silo.

### 3.3 Open-source, interoperable by design

- Full repo public (contracts + trust engine + API + tests, incl. attack-scenario &
  fuzz tests). MIT/Apache proposed.
- **Open scoring**: reputation is *recomputable by anyone* from on-chain evidence —
  no trusted Verdix oracle. On-chain = proofs; off-chain = payloads (Membase).
- Standards-first: builds on ERC-8004 / ERC-8183 rather than a proprietary format,
  so any BNB agent project can adopt it without lock-in.

---

## 4. Milestone breakdown — **Scenario B (selected)**

> Grant figures are **proposed anchors** for the second-round "milestone & amount
> confirmation" — BNB negotiates these; treat them as our opening ask, not a
> promise. Numbers are USD. Effort assumes the current solo-builder + agent-fleet
> setup. **Do not lock any figure without Reku's sign-off (see §6).**

**Ask: $60K · 16 weeks · goal: a production-lean, sybil-resistant reputation
layer for BNB agents — integrated with `bnbagent-sdk`, on mainnet, wired into BAS.
Milestones are deliberately front-loaded: the deliverables that are closest to done
(external beta operators, security review) come first, so measurable progress starts
in week 1 — mainnet ships after the review, not before.**

### Phase 1 — Traction first (weeks 1–6, $21K)

| MS | Deliverable | Effort | Payment trigger | $ |
|---|---|---|---|---|
| M1 | **3–5 external beta operators live on testnet** — self-serve vaults deployed by third parties, public profiles + Trust Scores (the readiest deliverable: product and outreach are already live) | 3 wk | ≥3 external operators with on-chain activity + public profiles | $9K |
| M2 | `verdix` reputation client for **bnbagent-sdk**: an SDK agent publishes its Trust Score in its agent card **and** queries a counterparty's score before accepting a job; example agent server (FastAPI, A2A endpoint) | 3 wk | Merged PR / public package + demo | $12K |

### Phase 2 — Verification & ingestion (weeks 6–10, $15K)

| MS | Deliverable | Effort | Payment trigger | $ |
|---|---|---|---|---|
| M3 | **External security review** (explicit audit-prep line item): EconomicMemory, VaultFactory/GuardedVault, VDXStaking reviewed by an external party; findings fixed | 2 wk | Published review report + fixes landed | $9K |
| M4 | ERC-8183 settlement-event ingestion into EconomicMemory via paid RPC (closes the SDK's own "event indexing is hard" gap) + integration guide + 3 demo agents scored end-to-end | 2 wk | Live indexer + ≥3 SDK jobs recorded on-chain | $6K |

### Phase 3 — Mainnet & ecosystem (weeks 10–16, $24K)

| MS | Deliverable | Effort | Payment trigger | $ |
|---|---|---|---|---|
| M5 | **Mainnet deployment (BSC)** of core contracts (EconomicMemory, recorders, RiskGuardVault, VaultFactory) — after, not before, the M3 review | 3 wk | Verified mainnet contracts | $10K |
| M6 | **BAS integration**: emit Trust Scores as BAS attestations + consume BAS attestations as memory inputs — Verdix as producer/consumer in BNB's native trust graph | 2 wk | On-chain attestation round-trip on mainnet | $7K |
| M7 | Storage/scale refactor (event+merkle memory storage) + **10+ external operators** + public metrics dashboard | 1 wk + ongoing | Dashboard live, ≥10 agents with real usage | $7K |

**Metrics BNB grants explicitly weigh** (DAU-equivalent for infra): # agents scored,
# economic actions recorded on-chain, # policy-guarded vaults deployed, # SDK
integrations live. B7 exists to produce exactly these.

### Kept in reserve (not part of this ask)

- **Scenario A (fallback, ~$20K / 5–6 wk):** Phase 1 only — if BNB wants a smaller
  first grant, we ship the SDK integration on testnet and re-apply for Phase 2.
- **Scenario C (stretch, ~$120–150K / 5–6 mo):** full external audit, decentralized
  recorder/arbitrator network, ecosystem-wide reputation subgraph + dashboard, $VDX
  mainnet utility, formal sybil-resistance research paper. Realistic only with a
  co-dev hire — a candidate **follow-on grant** after B lands, not now.

---

## 5. Roadmap (realistic)

- **Now (submitted):** BNB Hack × Unibase — testnet, dual-registry ERC-8004, live
  reputation API, self-serve vault product, daily dogfood.
- **Grant Phase 1 (weeks 1–6):** external beta operators live + bnbagent-sdk
  reputation client → *any* SDK agent can carry a Verdix track record.
- **Grant Phase 2 (weeks 6–10):** external security review + paid-RPC ERC-8183
  ingestion.
- **Grant Phase 3 (weeks 10–16):** mainnet + BAS attestations + storage/scale
  refactor; 10+ external operators onboarded.
- **Post-grant (follow-on, Scenario C):** full audit, decentralized
  recorders/arbitration, ecosystem-wide reputation subgraph + dashboard, $VDX
  mainnet utility, sybil-resistance research paper.
- **Beyond:** reputation-gated agent marketplaces, cross-chain agent reputation
  (portable via Membase), sustainability via protocol usage.

**Honest current limitations** (already documented in README, carried here for the
reviewers): free BSC-testnet RPCs reject `eth_getLogs` for chain-97 → event
indexing needs a paid RPC (funded by MS-A2); Trust-Score weights are a
dogfood-tuned starting point, not final; single-arbitrator + full on-chain entry
storage are MVP choices with a documented production path (B3/C2).

---

## 6. Decisions — locked 2026-07-20

Scenario **B is selected and finalized**: opening ask **$60K**, timeline
**16 weeks**, an explicit **external security review line item ($9K, M3)**,
**mainnet deployment committed as M5** (after the review), license **MIT**.
Signatory: the founder **as an individual** — one open question for BNB in
round 2: *is an individual grantee eligible, or is a legal entity required?*
(If an entity is required, incorporation happens between award and first
disbursement.) Scenario A remains documented above as the smaller fallback.
