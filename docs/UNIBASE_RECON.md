# RECON — Unibase Challenge (BNB Hack): "On-Chain Immortal AI Agent"

*2026-07-19. Recon only, belum ada kode. Verdict di bawah.*

## Stack mereka (hasil baca docs + GitHub)

| Komponen | Fakta | Maturity |
|---|---|---|
| **Membase** | Memory layer terdesentralisasi; Python SDK (`pip install` dari git); `MultiMemory`/`Message`, auto-upload ke Hub; LTM summarization + Chroma KB; auth wallet Ethereum via env (`MEMBASE_ID/ACCOUNT/SECRET_KEY`); hub testnet: `https://testnet.hub.membase.io` | 11★, no releases, early |
| **membase-mcp** | Gateway MCP (save_message/get_messages per conversation) | 24★, 6 commit, pre-release |
| **BitAgent / AIP** | Platform multi-agent: identity **ERC-8004** + payment X402 + commerce **ERC-8183**; SDK `unibase-aip-sdk` (Python/uv); register via JWT (`UNIBASE_PROXY_AUTH`) → `POST api.aip.unibase.com/agents/register`; job offering harga USDC; polling gateway | docs bolong (nggak ada alamat kontrak di page register; fee/gas nggak dijelasin) |
| **Kontrak (BSC TESTNET chain 97!)** | AIP Registry `0x8004A818BFB912233c491871b3d84c89A494BD9e`; Agentic Commerce (8183) `0x770a741AB71d1A75a124133098f2da11F893488C`; test USDC `0x6454...8930` | mainnet BSC juga ada |

**Fakta kunci: mereka pakai ERC-8004 di BSC testnet chain 97 — standard yang sama dengan AgentRegistry kita, chain yang sama dengan deployment Verdix yang sudah live.**

## Mapping Verdix → challenge

| Verdix | Sambungan | Nilai buat juri |
|---|---|---|
| **EconomicMemory (on-chain proof + dataHash)** | Payload di balik tiap `dataHash` disimpan ke **Membase** (sekarang cuma file lokal — slot "payload store" moat v9 memang masih kosong) | Pakai Membase secara ARSITEKTURAL, bukan tempelan: "proof di BSC, payload verifiable di Membase/Unibase DA" |
| **AgentRegistry (ERC-8004)** | Register smc-bot juga ke **AIP Registry mereka** via SDK → muncul di marketplace BitAgent | "Cross-platform interoperability" literal: satu agent, dua registry 8004 |
| **Reputation API + scorer** | Indexer baca event settlement **ERC-8183 mereka** di chain 97 → jadi entry Class 1/Tier 1 Verdix → Trust Score untuk SEMUA agent BitAgent | Celah terbesar: mereka punya identity+memory+payment, **belum punya reputation layer** — itu persis Verdix |
| **RiskGuardVault** | Konstitusi on-chain si immortal agent (demo failed-tx sudah live) | "Immortal" yang tetap accountable |
| **Dogfood bot SMC** | Trade journal → Membase (payload) + attestation on-chain (sudah jalan) | Data hidup, bukan mock |

Narasi submission: **"Immortal = memory yang persist (Membase) + reputasi yang portable & verifiable (Verdix) + konstitusi yang tidak bisa dilanggar (RiskGuard)"** — agent-nya mati platform pun, identity+memory+track record tetap hidup on-chain.

## Estimasi effort (jujur, jam kerja fokus)

| Item | Jam |
|---|---|
| Gate 0: smoke test SDK (dapat JWT, tulis/baca Membase hub, register test agent) | 2–4 |
| Membase payload store (dogfood + task spec → hub, link dataHash, verifikasi retrieval) | 4–6 |
| Register smc-bot ke AIP + job offering | 3–6 |
| Indexer ERC-8183 → entry Verdix + extend Reputation API | 4–8 |
| GitHub publik + docs EN + diagram (keys sudah di luar repo ✓) | 2–3 |
| Video demo + deck (rekam = Reku) + X post + form | 4–5 |
| **Total** | **~19–32 jam** (~3–5 hari; core 2 hari) |

## Risiko

1. **JWT auth gate (risiko #1)** — cara dapat `UNIBASE_PROXY_AUTH` nggak dijelasin di docs; mungkin harus login dashboard BitAgent/kontak tim. Bisa memblokir registrasi AIP. Mitigasi: jalur manual API, tanya via X/Discord mereka, atau demo tanpa listing marketplace.
2. **SDK bayi** — no releases, belasan stars, API bisa berubah, hub testnet bisa mati kapan pun. Mitigasi: pin commit, cache payload lokal (selaras moat v9 — payload copy tetap milik kita), MCP sebagai fallback.
3. **Angka prize belum terverifikasi** — "$100K × top 5" dari info Reku; halaman BNB Hack cuma bilang total sponsored $526k semua track, tanpa rincian Unibase. Jangan pasang ekspektasi sebelum cek form/kanal resmi. (Kemungkinan juga prize dalam token UB, bukan USD cash.)
4. **ABI ERC-8183 belum tentu tersedia** — kalau kontrak commerce mereka nggak verified, effort indexer naik.
5. **Docs bolong-bolong** — page registrasi tanpa alamat kontrak/fee → siapkan buffer trial-and-error.
6. **Strategis**: jangan biarkan Verdix terframe jadi "plugin Unibase" — posisi tetap: reputation layer platform-agnostic di atas ERC-8004 mana pun (punya kita DAN punya mereka).
7. Syarat umum BNB Hack: repo **GitHub publik** (repo kita masih lokal — harus publish), ≥2 tx sukses (sudah ~30 ✓), deploy BSC testnet (✓), tweet tag @BNBChain #BNBHack + @unibase_ai (butuh akun X Reku).

## VERDICT: **GO — dengan gate**

Kecocokan arsitektur langka bagusnya: chain sama, standard identity sama, dan slot yang mereka kosong (reputation) persis yang Verdix isi, sementara slot yang kita kosong (payload store) persis yang Membase isi. Effort ~20–30 jam, sebagian besar bisa gua kerjain sendiri.

**Syarat GO**: eksekusi mulai dari **Gate 0 (2–4 jam smoke test)** — kalau JWT nggak bisa didapat DAN hub testnet nggak bisa ditulis, turun jadi "submit tanpa listing AIP" (Membase saja) atau NO-GO; keputusan di titik itu, bukan sesudah 20 jam.

*Sumber: unibaseio.gitbook.io (unibase-docs, bitagent-docs), github.com/unibaseio/{membase,membase-mcp,unibase-aip-sdk}, bnbchain.org/en/hackathons/bnb-ai-hack.*

---

## GATE 0 — HASIL (2026-07-19): LOLOS SEMUA ✅

1. **Membase Hub roundtrip OK** — payload Verdix upload+download utuh di `testnet.hub.membase.io`, auth = signature wallet sendiri (key: `/root/.verdix-keys/membase-agent.key`).
2. **Membase on-chain register OK** — `verdix-smc-bot` di kontrak `0x100E3F8c5285df46A8B9edF6b38B8f90F1C32B7b` (BSC testnet); `getAgent` = wallet kita. Awas: RPC rotasi mereka suka lag read.
3. **AIP registration OK** — agent **`verdix-smc-bot`** terdaftar, **agent_id `97:0x8004a818...bd9e:1700`** = NFT ERC-8004 tokenId 1700 di AIP Registry mereka, card full Verdix publik di `api.aip.unibase.com/agents/handle/verdix-smc-bot`.

### Jalur auth yang BENAR (docs-nya nggak lengkap, hasil reverse-engineer):
- JWT dari `POST api.pay.unibase.com/v1/init` → user approve → token. TAPI token itu 403 di register ("Master wallet not found") meski user sudah di-`/accounts/users/register`.
- **Jalur yang jalan**: (1) bikin key lokal dedicated (`/root/.verdix-keys/aip-master.key`, wallet `0x82eFB7A48D31382A90A1A916f570571c0237c3A6`, funded 0.03 tBNB), (2) `POST /accounts/users/register-with-key` (custodial, makanya key dedicated), (3) register dengan body + `user_id`=address polos TANPA prefix `user:` + `wallet_type:"local"` + `message:"Create an AIP agent"` + `signature`=personal_sign message itu (`cast wallet sign`). Prefix `user:` → 401 mismatch.
- SDK: `pip install -e` gagal (a2a-sdk incompatible) → pin `a2a-sdk==0.3.24` (versi uv.lock mereka).
- Registrasi ulang dgn `agent_id` yang sama = update card (status `already_registered`).
- ownerOf(1700) = `0xE8bF...916f` (agentic wallet yang di-provision platform, bukan master kita).
