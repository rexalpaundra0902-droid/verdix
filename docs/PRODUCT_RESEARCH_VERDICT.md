# Verdict Produk Verdix — Sintesis Riset (2026-07-19)

*Metodologi & catatan jujur: deep-research workflow (79 agent: 6 sudut pencarian,
26 sumber di-fetch, 117 klaim diekstrak) dihentikan di fase verifikasi atas
permintaan founder (biaya token) — klaim di bawah TIDAK selesai diverifikasi
adversarial penuh; sumber dinilai dari kualitas outlet + konsistensi antar-sumber.
Digabung dengan filter internal (VERDIX_AI_COMPANY_VISION) + recon Unibase/Robinhood.*

---

## 1. Demand: SAKITNYA NYATA dan terdokumentasi — tapi ada warning

**Insiden 2025–2026 (masing-masing = iklan gratis untuk kategori ini):**
- **BasisOS / Virtuals (Nov 2025)**: "AI agent" yield vault ternyata dikendalikan
  manusia — rug ~$500k. Respons pasar yang PENTING: Virtuals **purge semua agent
  non-verified dan mewajibkan log keputusan on-chain**, kapital rotasi ke agent
  yang log-nya on-chain → *pasar sudah memilih on-chain verification sebagai obat*.
  Platform-nya yang menanggung reimbursement — platform punya liability nyata.
  (yahoo finance, 99bitcoins, coinjournal)
- **Bankrbot / Grok (Mei 2026)**: prompt-injection kode Morse → drain $174–200k.
  Artikel menyebut kontrol yang absen: **transaction caps, allow-list, verifikasi
  transfer besar** — persis primitif RiskGuardVault. (ccn)
- **Lobstar Wilde / OpenClaw (Feb 2026)**: salah parsing → buang seluruh holding
  (puncak ~$600k); dibingkai sebagai **kegagalan sistemik lingkungan eksekusi
  agent** → guardrail harus di LUAR agent, on-chain. (kucoin)
- **elizaOS (Apr 2026)**: class action — dituduh teknologi AI-nya tidak ada.
- Konteks makro: ~60% dana scam 2024 bermerek "AI/bot"; dashboard profit palsu =
  mekanik inti fraud; DeFi H1 2026 kehilangan ~$840M. (threesigma, thirdweb)
- **a16z (Jan 2026)** menamai gap ini "**KYA — Know Your Agent**": belum ada,
  jendela "berbulan-bulan bukan berdekade", dan **merchant mulai MEMBLOKIR agent**
  karena tidak bisa diverifikasi → demand datang juga dari sisi counterparty.

**Warning (jangan diabaikan):** boom-bust Virtuals (kreasi agent 1.000/hari → nol
dalam 4 bulan; revenue $500k/hari → <$500) + Gartner (>40% proyek agentic batal
sebelum 2028) = sebagian demand kategori ini spekulatif. Produk harus menempel ke
pain yang bertahan (dana hilang), bukan hype count agent.

## 2. Kompetisi: dua kandidat kita TERBANTAI, satu punya celah

- **Trust Directory / leaderboard → RAMAI, DITOLAK.** Recall (klaim 1,4jt user,
  175k agent, token live, arena kompetisi trading = track record agent SUDAH
  diproduktisasi), RNWY (150k+ agent, 12 chain), 8k4 (44k agent di BSC), Helixa
  (skor 11-faktor + staking) — selusin proyek trust-score di list awesome-erc8004.
  Solo founder masuk sini = perang melawan yang sudah punya distribusi.
  → `/web` kita tetap hidup sebagai *etalase*, bukan produk.
- **Escrow marketplace antar-agent → DITOLAK.** Prior art langsung (Theagora,
  AgentLux, Agent Arena 22k agent), pasar paling muda, dan dispute = ongoing
  judgment (gagal filter #3 dokumen company vision).
- **Guardrails/policy vault → CONTESTED TAPI ADA CELAH.** Incumbent: MetaMask
  Advanced Permissions (ERC-7715, live 12 chain termasuk BNB — caps/time-window),
  Brahma ConsoleKit ($200M+ secured, 3 audit, policy engine di Safe), Cobo/Safe/
  Privy. TAPI: mereka semua main di *execution rails*. **Tidak satu pun
  menggabungkan enforcement + track record terverifikasi + reputasi** — Brahma
  eksplisit TIDAK membingkai masalahnya sebagai trust/track-record; Recall punya
  reputasi tapi NOL enforcement; dan **spec ERC-8004 sendiri mengaku tidak
  menyelesaikan reputation-farming & tidak memverifikasi perilaku** — dua hal
  yang justru inti desain Verdix (recorder-gated writes, cost-of-forgery).
- **FundSeeder (prior art track record off-chain)**: pelajaran monetisasi krusial —
  **verifikasi GRATIS untuk trader; yang bayar adalah sisi kapital/alokator.**

## 3. Willingness to pay: SaaS langsung lemah; uang yang terbukti ada di 3 tempat

1. **Grant ekosistem**: BNB Chain Grants sampai **$200k/proyek**, kategori AI
   eligible, rolling tiap 2 bulan, ada wishlist publik (github community-contributions)
   yang harus dicek sebelum apply. Hackathon BNB $540k+ rolling — pemenang
   sebelumnya termasuk proyek adjacent (Kudo: verifiable commitments; Stitch AI:
   memory) → juri terbukti mendanai kategori ini.
2. **Sisi platform (B2B)**: platform agent menanggung reimbursement saat fraud
   (Virtuals bayar ~$500k) dan sudah MEWAJIBKAN verifikasi → platform adalah
   pembeli dengan liability nyata, bukan trader individual.
3. **Micropayment per-call (x402)**: Rug Munch jual risk-check $3/bln + $0,04/call
   via x402; transaksi x402 tumbuh >20x sebulan pasca launch → model "agent
   membayar API verifikasi per panggilan" sedang lahir.

## 4. VERDICT

**Bangun SATU produk: "Verdix Verified Agent" — vault berpolicy yang OTOMATIS
menghasilkan track record terverifikasi.**

Untuk operator/builder AI trading agent (bukan penjual sinyal — di-veto founder):
1. Spin vault RiskGuard self-serve (policy: caps/whitelist/floor — persis kontrol
   yang disebut hilang di insiden Bankr)
2. Setiap aksi agent → Economic Memory + Membase → **profil publik terverifikasi**
   (halaman /web yang sudah ada = muka produk)
3. Monetisasi mengikuti bukti, bukan harapan: **grant dulu** (BNB $200k track,
   apply dengan bukti insiden + deployment live), **B2B platform kedua**
   (BitAgent/Unibase = relasi yang sudah ada; precedent = mandat verifikasi
   Virtuals), **x402 per-call API ketiga**. Trader/operator individual: GRATIS
   (pelajaran FundSeeder) — mereka adalah sumber data, bukan revenue.

Positioning satu kalimat: *"MetaMask/Brahma membatasi apa yang agent boleh
lakukan; Recall menilai agent; **Verdix satu-satunya yang membuat batasan itu
MENGHASILKAN bukti** — enforcement yang jadi track record."*

**Ditolak eksplisit**: Trust Directory sebagai produk (kalah distribusi vs Recall
dkk), escrow marketplace (prior art + ongoing-judgment), TGE token (tetap
ditunda — tidak ada bukti WTP token baru selain spekulasi).

## 5. Rencana 90 hari

| Hari | Milestone |
|---|---|
| 1–14 | VaultFactory self-serve + auto-profil (semua komponen sudah ada); deploy BSC testnet; 3–5 operator agent beta (komunitas BitAgent/BNB dev) — gratis |
| 15–30 | **Apply BNB Grant** (cek wishlist repo dulu); deploy paralel ke Robinhood Chain testnet (chain trading AI-native tanpa trust layer, $1M builder pool, Open House) |
| 31–60 | Pitch B2B pertama: Unibase/BitAgent sebagai *verification layer* mereka (relasi ada, agent #1700 kita live di platformnya); kumpulkan data pemakaian beta utk tuning scorer |
| 61–90 | x402 paid API (per-call verification) kalau ada tanda pemakaian; evaluasi: ≥10 vault aktif & 1 percakapan B2B serius = lanjut; tidak = pivot dengan data |

## Sumber utama
threesigma.xyz (forensik scam AI-trading) · yahoo finance + 99bitcoins + coinjournal
(BasisOS/Virtuals) · kucoin news (OpenClaw) · ccn (Bankr hack) · a16zcrypto (KYA;
agent exploit research) · eips.ethereum.org/EIPS/eip-8004 · github ChaosChain 8004-ri ·
awesome-erc8004 (peta kompetitor) · recall.network · metamask.io (ERC-7715) ·
brahma.fi ConsoleKit · cobo.com · fundseeder.com · bnbchain.org/grants ·
blockeden.xyz · thirdweb blog (DeFi losses) · dev.to (Rug Munch x402) · coinmarketcap (elizaOS)
