# TODO REKU — Verdix (update 2026-07-21 malam)

## ☀️ BESOK PAGI (sisa dari 2026-07-21, ±10 menit total)
1. Cek balasan 3 thread: Lucas (Discord Unibase) · DM X @Unibase_AI ·
   pertanyaan form di Discord BNB. Ada balasan → paste ke Claude, dibantu draft.
2. Cek komen di post outreach grup TG BNB → bales yang nyaut.
3. Register di app.bitagent.io (Projects → connect existing → Verdix).
4. Tweet (teks di §4 bawah).

Urut prioritas baru yang disepakati: **beta operator DULU → baru mainnet.**
(Mainnet dgn 2 agent internal ga ngerubah cerita; 3–5 operator eksternal di
testnet bikin keputusan mainnet didukung data orang lain + proposal grant kuat.)

## 1. ⭐ OUTREACH BETA — STATUS 2026-07-20 MALAM: BERGERAK
- ❌ Post di General Unibase: kena auto-delete bot 2× (akun aman) — jangan ulangi jalur ini
- ✅ DM admin Lucas (Unibase) TERKIRIM 2026-07-20 — sampai 2026-07-21 belum ada balasan
- ✅ DM X @Unibase_AI TERKIRIM 2026-07-21 (2 pesan, DM kebuka) — nunggu balasan.
  Dua jalur aktif: Lucas (Discord) + X. JANGAN post ulang di Discord General
  (auto-delete bot 2x).
- Sisa target: grup dev BNB lain yang lu ikuti (teks di bawah masih valid)
- 2026-07-21: Reku join TG BNB (grup BNB Hack). Form utama BNB Hack
  (forms.gle/UVvuEGPZ) KETUTUP — blog resmi konfirmasi "may close submissions
  at any time". Reku udah nanya di Discord BNB soal reopen + apakah submission
  19 Jul (Unibase) masuk pipeline utama — NUNGGU JAWABAN.
- ✅ Outreach EN KEPOST di grup TG BNB (BNB Hack) 2026-07-21 — standby bales
  yang nyaut; jangan repost di grup yang sama.
Kirim ke: Discord Unibase (#builders/#general), TG @unibase_ai, grup dev BNB yang lu ikuti.

Teks EN (copy-paste — v3, direview auditor: buka soal MEREKA, satu ask, faucet link):
> Running an AI agent that touches funds? Then you know the problem: nobody
> fully believes your track record, because you're the one reporting it.
>
> I built **Verdix** so the chain reports it instead. Give your agent a
> non-custodial vault with hard rules — max tx, daily cap, cooldown, halt
> floor, enforced by the contract, not by promises — and every compliant
> action becomes a public, verifiable track record + Trust Score.
> Scores are decomposable via the public API: nobody can pump a score here,
> including us.
>
> There's a live tx on the site where the contract refused an overspend —
> the chain said no.
>
> Self-serve on BSC testnet, ~2 min from your browser (register agent →
> deploy vault → act). Need gas? Faucet: https://www.bnbchain.org/en/testnet-faucet
>
> First 5 get permanent founding-operator status on the registry — agent
> #1–7 slots don't come back.
> **One ask: try it and tell me where it breaks. DM me.** https://verdix.pages.dev

Versi ID (grup lokal):
> Jalanin AI agent yang pegang dana? Berarti lu tau masalahnya: track record
> lu gak sepenuhnya dipercaya orang, karena yang lapor ya lu sendiri.
>
> Gua bikin **Verdix** biar chain yang lapor. Kasih agent-mu vault
> non-custodial dengan aturan keras (max tx, cap harian, cooldown, halt floor
> — dipaksa kontrak, bukan janji) — tiap aksi patuh jadi track record publik
> terverifikasi + Trust Score. Skor bisa dibongkar siapa aja via API publik:
> gak ada yang bisa mompa skor di sini, termasuk kami.
>
> Di situsnya ada tx live di mana kontrak nolak overspend — chain-nya bilang
> tidak.
>
> Self-serve di BSC testnet, ±2 menit dari browser. Butuh gas? Faucet:
> https://www.bnbchain.org/en/testnet-faucet
>
> 5 pertama dapet status founding operator permanen di registry — slot agent
> awal gak bakal balik lagi.
> **Satu ask: cobain, kasih tau di mana rusaknya. DM gua.** https://verdix.pages.dev

⚠️ JEBAKAN FAUCET (diverifikasi 2026-07-21): faucet resmi bnbchain.org WAJIB
punya 0.002 BNB MAINNET — wallet fresh bakal ditolak. Kalau ada calon operator
ngeluh gak dapet gas:
1. Suruh coba faucet Chainlink: https://faucets.chain.link/bnb-chain-testnet
   (login GitHub, tanpa syarat saldo — jalur yang dulu kita pakai), ATAU
2. Langsung tawarin: "DM me your address, I'll send you testnet gas" →
   kasih tau Claude alamatnya, dikirim 0.02 tBNB dari deployer (stok 0.108,
   cukup ±5 operator). Friksi ilang = operator gak kabur di langkah pertama.

Amunisi kalau ada yang skeptis (jawaban singkat):
- "Skornya bisa dipalsuin?" → formula open source (intel/trustscore.py) + tiap
  komponen bisa di-query API publik. Contoh kejujurannya: agent kami sendiri
  kelihatan diversity 0.0 (baru 1 counterparty) dan itu kami biarkan tampil —
  artinya skor lu di sini gak bisa dipompa siapa pun, termasuk kami.
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

## 1b-X. ⭐ DM X @Unibase_AI — versi pendek buat X (copy-paste per blok)
X DM ke non-mutual masuk "message requests" → harus pendek & langsung nilai.
Kirim sebagai 2 pesan terpisah:

> Hey — builder of Verdix here (BNB Hack, your On-Chain Immortal Agent
> challenge). We publicly compute Trust Scores for 63 BitAgent agents +
> our agent runs live in your AIP registry (#1700, Membase payloads).
> Congrats on the Base launch 🎉

> Our independent scores over your agent population = third-party proof
> point for launch week. Happy to co-publish a "state of BitAgent agents"
> thread. Also: any builder-support path for deep integrators?
> Live: verdix.pages.dev

Fallback kalau DM ketutup — reply publik ke tweet Base launch mereka:
> Independent Trust Scores for 63 BitAgent agents, live since launch week —
> decomposable via public API. verdix.pages.dev 🤝

## ⛔ BLOCKED — DappBay listing (nunggu jawaban support / mainnet)
- Status 2026-07-20: submit ke-blok (form mainnet-oriented; BSC/opBNB/Greenfield).
  Nunggu jawaban support BNB Chain (Discord) ATAU deployment mainnet.
- Persiapan DONE dari sisi gua: README udah listing-ready (blok "Listing info"
  copy-paste: one-liner, kategori, logo URL, kontrak; IP mentah dibersihkan) +
  logo publik https://verdix.pages.dev/img/verdix-logo-512.png
- Begitu kebuka: semua bahan tinggal comot dari blok Listing info di README.
- Yang MASIH bisa jalan sekarang: register Verdix di https://app.bitagent.io
  (Projects → connect existing) — gak tergantung DappBay.

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

## 6. ✅ Keputusan grant BNB — TERKUNCI 2026-07-20
$60K buka · security review $9K line item (M3) · mainnet GO sbg M5 (sesudah
review) · 16 minggu front-loaded · MIT · penandatangan individu (+tanya BNB
eligibility). Draft final di docs/GRANT_PROPOSAL.md.
⚠️ CATATAN INTERNAL (jangan masuk proposal): mainnet M5 = komitmen BERSYARAT —
dieksekusi kalau grant cair; kalau pas M5 tiba belum ada satu pun operator
eksternal, re-evaluasi dulu sebelum deploy.

## 6b. 💴 PAJAK — sebelum milestone pertama cair
Cek perlakuan pajak grant crypto utk residen Jepang (grant USD/token = income?
timing pengakuan? NTA Jepang ketat soal crypto) — konsul akuntan/pajak lokal
SEBELUM pencairan pertama, jangan pas telat.

## 🗓 AGENDA 8 AGUSTUS — bedah penuh Robinhood Chain (setelah grant BNB masuk)
KEPUTUSAN 2026-07-20 (opsi c dieksekusi): wording roadmap publik dilunakkan jadi
"Robinhood Chain (RWA trading L2) — under evaluation" — nama tetap (ambisi+SEO),
verb jujur, utang janji lunas. Evaluasi naik-turunnya wording = sesi 8 Agu.

Kenapa fit-nya nyata (jangan dibuang): chain trading buatan broker, sebentar
lagi ada agent trading tokenized stocks 24/7 pegang duit riil = persis profil
pengguna Verdix; angle unik Reku = trader yang bangun trust infra; mainnet umur
seminggu = first-mover kebuka; $1jt dev pool = jalur funding nyata.

Agenda sesi 8 Agu (SATU sesi khusus):
1. Apa yang dibutuhin buat deploy penuh (bytecode sama; API/scorer perlu param
   multi-chain — sekarang hardcode chain 97; faucet nunggu klik Reku)
2. Jalur masuk $1jt dev pool (via Arbitrum Open House? langsung?)
3. Muat gak di 16 minggu TANPA ganggu milestone BNB
→ Kalau "ya" semua: wording naik jadi komitmen DENGAN rencana di belakangnya.

## 7. Domain sendiri — RENCANA REKU minggu depan (±27 Jul)
- **Daftar via Cloudflare Registrar** (dash.cloudflare.com → Domain Registration):
  harga at-cost tanpa markup, dan DNS langsung nyatu sama akun CF yang udah
  dipakai deploy Pages — nol migrasi.
- Kandidat dicek ketersediaan pas beli: verdix.xyz / verdix.io / verdix.ai
  (.ai paling mahal ±$70-90/thn; .xyz paling murah ±$10; .io ±$40).
  ⚠️ verdix.com kemungkinan kepakai/premium — cek dulu, jangan dipaksa.
- Begitu kebeli, bilang gua — sisanya gua yang kerjain (±30 mnt):
  (1) custom domain di Pages project verdix → website jadi verdix.xyz,
  (2) subdomain api.verdix.xyz → ganti verdix-api.kilatlab.com (lepas total
      dari kilatlab) + TLS + update proxy functions & nginx,
  (3) update semua link internal (landing, /web, README, TODO teks outreach),
  (4) redirect verdix.pages.dev tetap hidup (link lama gak mati).
- Kalau outreach udah kekirim SEBELUM domain ada: gak masalah, pages.dev
  tetap jalan selamanya — domain tinggal nambah di atasnya.

## 8. Opsional / kapan sempat
- WalletConnect Project ID (gratis, cloud.walletconnect.com) → gua integrasikan.

## Yang JALAN SENDIRI (nggak usah dipikirin)
- Bot testnet → daily pulse 07:10 → Economic Memory & Membase nambah tiap hari
- Watcher 30-menit → TG notif kalau ada job/star/juri/servis down
- Agent service polling gateway Unibase 24/7
- Riset funding (Unibase/BitAgent program, hackathon aktif, ChainGPT grant)
  lagi jalan — hasil + shortlist deadline nyusul dari gua
