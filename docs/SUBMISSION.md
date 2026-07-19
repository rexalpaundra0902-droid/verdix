# BNB Hack Submission — Unibase Challenge

**Project:** Verdix — On-Chain Immortal AI Agent with Verifiable Economic Memory
**Challenge:** Unibase — "Build an On-Chain Immortal AI Agent with Decentralized
Memory and Cross-Platform Interoperability on BNB Chain"
**Chain:** BSC Testnet (97) — 6 verified contracts, 30+ successful transactions

## One-liner

An AI trading agent whose identity (ERC-8004, dual-registry), memory
(on-chain proofs + Membase payloads), reputation (Trust Score from verified
economic actions only), and risk constitution (RiskGuardVault) all live
on-chain — so the agent outlives any platform, and its track record can be
verified by anyone.

## What makes it "immortal"

| Layer | Where it lives | Survives platform death? |
|---|---|---|
| Identity | ERC-8004 NFT #1700 (Unibase AIP Registry) + Verdix AgentRegistry | ✅ on-chain |
| Memory | dataHash on BSC + payloads on Membase (Unibase DA) | ✅ decentralized |
| Reputation | EconomicMemory contract + open scoring | ✅ recomputable by anyone |
| Constitution | RiskGuardVault policy | ✅ enforced by chain, not by ops |

## Requirement checklist

- [x] Deployed on BSC testnet — 6 contracts, all verified on BscScan
- [x] ≥ 2 successful contract transactions (30+: registrations, escrow cycle,
      payments, 8 dogfood attestations, vault actions incl. an intentionally
      blocked one)
- [x] Uses **Membase**: payload store for all on-chain dataHashes + agent
      memory of every served job (`memory_ref`), hub `testnet.hub.membase.io`,
      on-chain Membase registration `verdix-smc-bot`
- [x] Uses **BitAgent/AIP**: agent registered (ERC-8004 #1700), job offering
      `market_signal_4h`, live gateway polling service, E2E job completed
      through Unibase Gateway
- [x] Open source repo + docs (this repo)
- [ ] Demo video (Reku)
- [ ] X post tagging @BNBChain #BNBHack @unibase_ai (Reku)
- [ ] Submission form: https://forms.gle/6jDbA1xrbtxHu2W87 (Reku)

## Demo script (for the video, ±3 minutes)

1. **Identity** — open `api.aip.unibase.com/agents/handle/verdix-smc-bot`
   (agent card) + BscScan AIP Registry token #1700: "one agent, two ERC-8004
   registries."
2. **Constitution** — open the two RiskGuardVault txs side by side:
   compliant = success, oversized = `Fail (ExceedsMaxTx)`. "The agent cannot
   break its own risk policy — the chain rejects it."
3. **Memory** — pick any entry from `194.233.93.155:8600/agent/1/cv`, take its
   dataHash, open `/memory/<hash>`: payload fetched from Membase, hash matches
   on-chain. "Proofs on BNB Chain, payloads on Membase — verifiable by anyone."
4. **Live job** — submit a job to the Unibase gateway (`jobs/submit`), show the
   result: real 4H analysis + trust score + fresh `memory_ref`, then open its
   `/memory/<ref>` URL. "Every job served becomes permanent, verifiable memory."
5. **Ecosystem reputation** — open `/bitagent`: "63 BitAgent agents scored;
   Unibase gives agents identity, memory, payments — Verdix adds the layer they
   still need: verifiable reputation."

## Draft X post (for Reku)

> Meet verdix-smc-bot — an on-chain immortal AI trading agent on @BNBChain.
> 🪪 ERC-8004 identity (@unibase_ai AIP Registry #1700)
> 🧠 memory: proofs on BSC + payloads on Membase
> ⚖️ on-chain risk constitution it cannot override
> 📊 live trust score from verified actions only
> #BNBHack — repo: <GITHUB_URL>

## Links

- Reputation API: http://194.233.93.155:8600
- EconomicMemory: https://testnet.bscscan.com/address/0x8692F4Bbc7422139D4335AF01734bEbe99516900
- RiskGuardVault blocked tx: https://testnet.bscscan.com/tx/0xcb7e5dd10be44df82dfec34f7c49f2fd30be0cd3c57b31b2b6e0a908d34e567d
- Agent card: https://api.aip.unibase.com/agents/handle/verdix-smc-bot
