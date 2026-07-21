# Verdix — Beta Operator Quickstart

For anyone running an **AI agent that touches funds**. Give your agent a
verifiable, portable track record + an on-chain risk policy it can't override.
**Free. Testnet. ~5 minutes.** No signup, non-custodial (Verdix never holds your keys or funds).

---

## Why bother (the 30-second version)

Right now an AI agent's track record is self-reported — unverifiable and fakeable —
and its wallet has no guardrails. Verdix fixes both:

1. **Policy-guarded vault** — deposit funds, set hard limits (max per action, daily
   cap, allowed destinations, a balance floor). Your agent operates *inside* those
   limits; the contract rejects anything that exceeds them. No prompt can override it.
2. **Verifiable Economic Memory** — every compliant action becomes an on-chain,
   independently-verifiable track record. Your agent earns a **Trust Score** computed
   only from real economic outcomes, not claims — a public profile anyone can check.

You keep custody the whole time. If Verdix disappeared tomorrow, your funds are still
yours (owner can always withdraw).

## Prerequisites

- **MetaMask** (or any EVM wallet).
- **BSC Testnet** network added (chainId **97**, RPC `https://bsc-testnet.bnbchain.org`).
- A little **testnet BNB** from a faucet (e.g. Chainlink / BNB faucet) — for gas only, no real money.

## 5-minute quickstart

Open **https://verdix.pages.dev/web/create** and:

1. **Register your agent (ERC-8004).** Connect wallet → Register. The registering
   wallet becomes your agent's *controller*; your `agentId` appears automatically.
   (URI is optional — a URL describing your agent, can stay empty.)
2. **Create a vault + policy.** Pick your agent, set the risk constitution — every
   field is a hard rule the contract enforces:
   - `maxTxValue` — max per single action
   - `dailyCap` — max total per 24h
   - `cooldown` — min gap between actions
   - `haltFloor` — balance floor that can never be crossed
   Deposit some testnet BNB. Add your venue/target address to the allowlist.
3. **Run your agent.** Point it at the vault's `act(target, value, memo)`. Every
   compliant action auto-records to Economic Memory and feeds your Trust Score.
   Non-compliant actions revert on-chain (that's the point).

## What you get back

- A public profile + Trust Score: `https://verdix.pages.dev/web/agent/<agentId>`
- Machine-readable API (no key, read-only):
  - `GET /agents` — all agents + scores
  - `GET /agent/<id>` — one agent detail
  - `GET /agent/<id>/cv` — full Trust Score breakdown ("economic CV")
  - `GET /memory/<dataHash>` — verify the payload behind any recorded action
  - Base URL: `https://verdix-api.kilatlab.com`

## Live deployment (BSC Testnet, chain 97) — all verified on BscScan

- VaultFactory (start here): `0x564339644325dc147BF6F944f4253Dc59d268D7B`
- AgentRegistry: `0x23dd8707AE4159A39303B3d193308AfBcAaf865F`
- EconomicMemory: `0x9913A072915EF382b680bb4a0ff3CD8373490C4D`
- Full list: `deployments/bsc-testnet.json`. Contracts audited (internal multi-agent +
  Slither, see `docs/AUDIT_2026-07-21.md` / `docs/REAUDIT_2026-07-21.md`).

## The one ask

Try it with a real (even tiny) agent action on testnet, then tell us **where it
breaks** — DM the builder. Beta operator feedback is what shapes what's built next
(and gates the mainnet decision — see `docs/MAINNET_READINESS.md`).

> Note: this is early testnet software. Known residual (documented, not hidden): a
> reputation-fabrication path via two colluding self-owned agents is still
> theoretically possible; single-operator self-dealing is blocked. Stake-gated
> settlement is on the roadmap. Use testnet funds only.
