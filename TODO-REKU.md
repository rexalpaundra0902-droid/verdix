# TODO REKU — Verdix (update 2026-07-20)

Urut prioritas baru yang disepakati: **beta operator DULU → baru mainnet.**
(Mainnet dgn 2 agent internal ga ngerubah cerita; 3–5 operator eksternal di
testnet bikin keputusan mainnet didukung data orang lain + proposal grant kuat.)

## 1. ⭐ OUTREACH BETA — target 3–5 operator agent (20 menit) — PRIORITAS #1
Kirim ke: Discord Unibase (#builders/#general), TG @unibase_ai, grup dev BNB yang lu ikuti.

Teks EN (copy-paste — versi baru, pakai semua upgrade 20 Jul):
> Give your AI agent an on-chain track record it can't fake.
> **Verdix** = policy-guarded, non-custodial vaults for AI agents: max tx, daily
> cap, cooldown, halt floor — enforced by the contract, not by promises.
> Every compliant action becomes verifiable reputation + a public profile.
>
> ✅ Self-serve: register agent + deploy vault from the browser in ~2 min
> ✅ Manage everything from the web app (no BscScan digging needed)
> ✅ Trust Score you can decompose yourself — every component is on the public API
> ✅ 9 verified contracts on BSC testnet — read the chain, not our claims
>
> Free for beta operators — looking for 3–5 agent builders; your feedback
> shapes the scoring weights. https://verdix.pages.dev — DM me!

Versi ID (grup lokal):
> Kasih AI agent-mu track record on-chain yang gak bisa dipalsuin.
> **Verdix** = vault non-custodial berpolicy (max tx, cap harian, cooldown, halt
> floor — dipaksa kontrak, bukan janji). Tiap aksi patuh = reputasi terverifikasi.
> Self-serve dari browser ±2 menit, kelola semua dari web app, skor bisa
> dibongkar sendiri lewat API publik, 9 kontrak verified di BSC testnet.
> Gratis buat beta — nyari 3–5 builder. https://verdix.pages.dev

Amunisi kalau ada yang skeptis (jawaban singkat):
- "Skornya bisa dipalsuin?" → formula open source (intel/trustscore.py) + tiap
  komponen bisa di-query API publik; bahkan agent kita sendiri keliatan
  diversity 0.0 karena baru 1 counterparty — sistemnya jujur ke diri sendiri.
- "Custodial?" → Tidak. Vault milik wallet lu, Verdix gak pernah pegang kunci.
- "Bukti policy jalan?" → tx yang diblokir policy kelihatan di BscScan:
  0xcb7e5d…e567d (status Fail) — permanen, bisa dicek siapa aja.

## 1b. ⭐ DM Unibase (5 menit) — bareng outreach beta, timing EMAS
BitAgent baru launch di Base 17 Jul — skor kita atas 63 agent mereka = proof
point pihak-ketiga buat launch week mereka. Kirim ke TG Dev Group
(t.me/+eLlBe3Q5P4NhZTQ9) atau DM X @Unibase_AI:

> Hi — I'm the builder of Verdix (verdix.pages.dev), submitted to your On-Chain
> Immortal AI Agent challenge in BNB Hack. Integration status: agent ERC-8004
> #1700 in your AIP registry, live answering gateway jobs, 12 payloads on
> Membase hub, and we publicly compute Trust Scores for 63 BitAgent agents.
> Congrats on the BitAgent Base launch — our independent scores over your agent
> population could be a third-party proof point for launch week; happy to
> co-publish a "state of BitAgent agents" thread. Two questions: (1) can Verdix
> be added to the integrations list in your docs? (2) Does the UB ecosystem/
> treasury allocation have a builder-support path for deep integrators — and
> does our agent's Membase contribution qualify for Knowledge Mining rewards?

## 1c. DappBay listing (10 menit) — gratis, sinyal buat grant reviewer
- https://dappbay.bnbchain.org/submit-dapp → connect wallet → isi form
  (logo ada di repo, deskripsi tinggal ambil dari README, kontrak: VaultFactory
  0x5883Bb4f6764D738304E9cc621e54b8B157775e4)
- Sekalian register Verdix di https://app.bitagent.io (Projects → connect existing)

## 📅 DEADLINE: 1–7 Agustus — BNB Chain Builder Grant ($50K, window bulanan)
- Form: dappbay.bnbchain.org/campaign/226-bnb-chain-builder-grant
- Gua yang draft aplikasinya (recycle GRANT_PROPOSAL) — lu tinggal review+submit.
- Odds naik kalau ada yang nyentuh mainnet dulu → nyambung ke keputusan lo.

## 2. Faucet Robinhood Chain (5 menit) — buka Phase 3
- http://faucet.testnet.chain.robinhood.com → paste `0xeB517e1ef8A282E8B5dd1f102cf61b76b02dBaCE`
- Claim → bilang "udah" → gua deploy full stack ke Robinhood testnet ±1 jam.

## 3. ~~Cek ronde Arbitrum Open House~~ — UDAH DICEK GUA (2026-07-20, riset verified)
- NYC & London SELESAI (London closed 25 Jun). Singapore next, BELUM buka.
- Gak usah ngapa-ngapain — gua yang pantau; fit-nya juga cuma 4/10 (wajib build di Arbitrum).

## 4. Tweet website (5 menit — build-in-public, penting buat jalur angel/hackathon)
> Reputation your AI agent can't fake — now with receipts.
> 🔐 policy-guarded vaults · 📊 trust scores you can decompose via public API ·
> ⛓ 9 verified contracts on BSC testnet · 🌐 7 languages
> https://verdix.pages.dev
> Built on @BNBCHAIN · integrated with @unibase_ai · #BNBHack

## 5. Verifikasi angka prize Unibase (5 menit)
- "$100K × top 5" BELUM terverifikasi dari kanal resmi — cek Discord/TG/form.

## 6. Keputusan grant BNB (nunggu lu, 5 poin — §6 GRANT_PROPOSAL.md)
angka buka $50K vs $60K · budget audit-prep · mainnet go/no-go (SESUDAH beta
operator, sesuai urutan baru) · commit 10–12 mgg · lisensi + entitas/KYC.

## 7. Opsional / kapan sempat
- WalletConnect Project ID (gratis, cloud.walletconnect.com) → gua integrasikan.
- Domain sendiri (verdix.xyz dll) → deploy tinggal satu perintah.

## Yang JALAN SENDIRI (nggak usah dipikirin)
- Bot testnet → daily pulse 07:10 → Economic Memory & Membase nambah tiap hari
- Watcher 30-menit → TG notif kalau ada job/star/juri/servis down
- Agent service polling gateway Unibase 24/7
- Riset funding (Unibase/BitAgent program, hackathon aktif, ChainGPT grant)
  lagi jalan — hasil + shortlist deadline nyusul dari gua
