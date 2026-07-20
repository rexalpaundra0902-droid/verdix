# Verdix × ERC-8004 — Positioning (ditetapkan 2026-07-20)

## Fakta yang tidak boleh diabaikan
ERC-8004 "Trustless Agents" = standar resmi Ethereum, **mainnet sejak akhir
Januari 2026**, ribuan–puluhan ribu agent identity on-chain (orde terkonfirmasi;
angka 45K belum diverifikasi independen). Spec-nya mencakup TIGA registry:
**identity, reputation, validation** — artinya 2/3 kategori Verdix sudah punya
standar resmi yang jalan, sementara Verdix di testnet dengan 2 agent internal.

Diabaikan = dalam 12 bulan setiap investor/juri bertanya "kenapa nggak pakai
8004 aja?" dan kita tidak punya jawaban.

## Posisi resmi: LAYER DI ATAS 8004, BUKAN ALTERNATIF

**"ERC-8004 gives agents an identity. Verdix gives that identity teeth —
enforced policy and a computed, decomposable score."**

Yang 8004 TIDAK punya (dan tidak akan — dia standar registry, bukan produk):
1. **Enforcement.** 8004 mencatat; dia tidak bisa MEMBLOKIR transaksi.
   RiskGuardVault = policy on-chain yang bikin pelanggaran revert. Registry
   tanpa enforcement = rapor tanpa rem.
2. **Scoring engine.** Reputation registry 8004 = wadah entri mentah; tidak
   ada formula, tidak ada skor. Verdix = f() terbuka + decomposable via API +
   anti-farming/anti-beli-reputasi (controlChangesOf, carryover discount).
3. **Vault non-custodial self-serve** — produk, bukan spec.

Dengan framing ini, populasi agent 8004 berubah dari ancaman jadi **TAM**:
setiap agent 8004 adalah calon pemilik vault + subjek skor.

## Konsekuensi roadmap (prioritas strategis #2 setelah beta operator)
- **M1 — Consume:** resolve identity dari registry 8004 KANONIK (Ethereum
  mainnet, Base saat live) — bukan cuma registry gaya-8004 milik sendiri di
  chain 97. Trust Score bisa dihitung untuk agent 8004 mana pun.
- **M2 — Publish:** terbitkan Trust Score/atestasi dalam format yang bisa
  dikonsumsi ekosistem 8004 (reputation registry entry; BAS attestation di
  BNB sebagai jalur paralel).
- **M3 — Validate:** interop dengan validation registry (vault action sebagai
  bukti tervalidasi).

Efek samping strategis: M1+M2 = prasyarat jalur **Base Builder Grant** dan
**EF ESP (tim dAI)** — lihat FUNDING_RESEARCH_2026-07.md. Satu kerjaan, tiga
pintu.

## Kalimat siap pakai (pitch/grant/DM)
- EN: "ERC-8004 gives agents an identity. Verdix gives that identity teeth —
  enforced policy and a computed, decomposable score."
- Footer situs (sudah live, konsisten): "ERC-8004 tells you who an agent is.
  Verdix tells you how it has behaved."
- Anti-kompetitor satu baris: "We don't compete with the standard — we're the
  enforcement and scoring layer the standard was designed to enable."
