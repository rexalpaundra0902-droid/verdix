# Verdix — Verifiable Economic Memory for the AI Agent Economy

> ERC-8004 tells you WHO an agent is.
> **Verdix tells you HOW that agent has actually behaved.**

Verdix is an **on-chain economic memory + trust intelligence layer** for AI
agents, dogfooded by a real trading bot — built for the
**BNB Hack × Unibase challenge: "On-Chain Immortal AI Agent"**.

An agent is *immortal* when its identity, memory, and track record outlive any
single platform:

- **Identity** — ERC-8004 NFT, registered in **two** registries (Verdix's own +
  Unibase AIP Registry, token **#1700**, BSC testnet)
- **Memory** — every economic action anchored on-chain as `dataHash`; full
  payloads stored on **Membase (Unibase DA)** — publicly verifiable, platform-independent
- **Track record** — Trust Score computed live from on-chain Economic Memory,
  not from self-reported claims
- **Constitution** — RiskGuardVault: an on-chain risk policy the agent
  *cannot* override, no matter how smart it gets

## Live deployments (BSC Testnet, chain 97)

All contracts are **verified on BscScan** — see `deployments/bsc-testnet.json`:

| Contract | Address |
|---|---|
| AgentRegistry (ERC-8004 surface) | `0x03E3701c98CFe457460BDe6b71d9b466CDC6cBe0` |
| **EconomicMemory** (core asset) | `0x8692F4Bbc7422139D4335AF01734bEbe99516900` |
| PaymentRouter (Tier-1 recorder) | `0x21Ec45c09BEFAbA63539fd1dCfA0ad2CeDcB8662` |
| TaskEscrow (Tier-2/3 recorder) | `0x1A51D8062f2C022bA12f46851411d87a47dF36D8` |
| StressOracle (Tier-4 recorder) | `0xb67b938F6e0592722aF87bc0e48A0DF7684FA6FD` |
| **RiskGuardVault** (first app) | `0x397170E0c1315654CfbB09902f564C1bd7B1358B` |
| VDX token (testnet, 500M fixed) | `0x85A78EDa8B300B7EEF196F876953Eb5b33Ea7984` |
| VDXStaking (skin in the game) | `0xf3294C1cC9308DD507aeB9E4D4acc9D2b4062ccB` |

**Reputation API (live):** `http://194.233.93.155:8600`
`/agents` · `/agent/1` · `/agent/1/cv` · `/memory/<dataHash>` · `/bitagent` · `/bitagent/<handle>`

**On-chain proof of policy enforcement** (RiskGuardVault):
- compliant action → [tx success](https://testnet.bscscan.com/tx/0x5ab22b5db269b3b2dd3679fa2af69404d6d0ed1c684f8df79d96a39b532fbc2f)
- oversized action → [tx **Fail**: `ExceedsMaxTx`](https://testnet.bscscan.com/tx/0xcb7e5dd10be44df82dfec34f7c49f2fd30be0cd3c57b31b2b6e0a908d34e567d)

## Architecture

```
                     ┌──────────────────────────────────────────────┐
                     │  smc-bot: live 4H trading engine (dogfood)   │
                     └──────────────┬───────────────────────────────┘
                                    │ closed trades, tasks, payments
                                    v
   ON-CHAIN (BSC testnet) ──────────────────────────── OFF-CHAIN
   AgentRegistry (ERC-8004)                            Membase / Unibase DA
   EconomicMemory: append-only,                        full payloads keyed by
     ONLY authorized recorders can        dataHash ──► dataHash, verifiable:
     write (self-report impossible                     sha256/keccak(payload)
     by construction):                                 == on-chain hash
       PaymentRouter  (Tier 1: settlement = proof)
       TaskEscrow     (Tier 2: two-sided bonds; Tier 3: arbitration)
       StressOracle   (Tier 4: observed behavior under stress)
   RiskGuardVault: on-chain risk constitution
     (maxTx / daily cap / cooldown / whitelist / halt floor)
                                    │
                                    v
   Trust Intelligence (intel/trustscore.py):
     f(success·tier·recency, log-volume, counterparty-diversity anti-farming,
       stress behavior, dispute record, control-change decay)
     → Trust Score + Economic CV, served by the Reputation API
```

Key design decisions (see `docs/MOAT_V9_ADDENDUM.md`):

- **Self-reports cannot enter memory** — only audited recorder contracts write,
  and each records only outcomes it witnessed (settlement, escrow release, ruling).
- **Anti-farming** — a fake Tier-2 entry requires locking payment + two bonds +
  gas; exclusive counterparty pairs are down-weighted (1-HHI diversity).
- **Anti reputation-buying** — ERC-8004 identity is a transferable NFT, so every
  control change (transfer / wallet rotation) is logged on-chain and the scorer
  decays pre-transfer history: a bought identity scores below a fresh one.
- **On-chain = proofs, off-chain = payloads** — the chain stores evidence and
  hashes (open, interoperable); full payloads live on Membase.

## Unibase integration (the "immortal" loop)

1. **Agent registered on AIP/BitAgent** — handle `verdix-smc-bot`, ERC-8004 NFT
   #1700 in `0x8004A818...BD9e` (chain 97), job offering `market_signal_4h`.
2. **Membase as the payload store** — every on-chain `dataHash` (12 backfilled:
   8 dogfood trades + escrow/payment/vault payloads) resolves to a verifiable
   payload: `GET /memory/<dataHash>` fetches from Membase and re-hashes.
3. **Live agent service** (`aip_agent/service.py`) — polls the Unibase Gateway,
   answers real 4H market-structure jobs (Binance data), attaches its live
   Trust Score, and writes each served job back to Membase (`memory_ref` in the
   result) — the agent's memory grows with every job, across platforms.
4. **Trust Intelligence for the whole BitAgent ecosystem** —
   `GET /bitagent` scores all chain-97 BitAgent agents (platform job stats +
   on-chain ERC-8004 identity verification via `ownerOf`). Unibase provides
   identity, memory, and payments; **Verdix adds the missing layer: verifiable
   reputation.**

## Run it yourself

```bash
# contracts
forge test                                   # 34 tests incl. attack scenarios + fuzz
bash demo/demo.sh                            # full local demo on anvil

# trust intelligence
python3 -m unittest intel.test_trustscore -v # 11 tests incl. bought-identity decay

# python env for Membase/AIP integrations
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# services (systemd units in deploy notes)
.venv/bin/python api/server.py               # Reputation API :8600
.venv/bin/python aip_agent/service.py        # AIP gateway agent

# end-to-end job through Unibase gateway
# submit {"agent_id":"verdix-smc-bot","offering_id":"market_signal_4h", ...}
# to POST gateway.aip.unibase.com/gateway/jobs/submit → result includes
# regime/bias/key-levels + trust score + verifiable memory_ref
```

Secrets (wallet keys, JWT) live outside the repo (`/root/.verdix-keys/`) and are
never committed. Testnet only — no real funds.

## Honest limitations

- Raw ERC-8183 event indexing is blocked today: every free BSC-testnet RPC
  rejects `eth_getLogs` and Etherscan free tier does not cover chain-97 logs.
  The BitAgent scorer therefore uses platform job stats + on-chain identity
  checks, with the same scoring shape ready to switch to raw events once a paid
  RPC is available.
- Trust Intelligence weights are a documented starting point, tuned on dogfood
  data — not a final formula.
- Single arbitrator and full entry storage on-chain are MVP choices
  (production path: arbitrator pool, event+merkle storage — documented).

## Design docs

- **$VDX (testnet)** — 500M fixed supply per protocol spec; live utility:
  stake-to-back-an-agent with a 7-day unstake cooldown (stake can't run away
  right before consequences land). Staked amount is surfaced by the Reputation
  API as `vdxStaked` — reputation backed by capital at risk. Mainnet TGE is
  deliberately deferred until the protocol has real external usage.
  ⚠️ Deliberate design, read before staking: third-party stake is a permanent
  *vouch* — only the agent's controller can ever withdraw it; and each new
  unstake request re-locks the whole pending amount (cooldown extends).

- `docs/MOAT_V9_ADDENDUM.md` — moat repositioning & identity-transfer mitigation
- `docs/UNIBASE_RECON.md` — integration recon + reverse-engineered auth path
- `deployments/bsc-testnet.json` — all live addresses + demo tx hashes
