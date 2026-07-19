# VERDIX v9 ADDENDUM — Reposisi Moat & Identity Transfer

*2026-07-19 — hasil review adversarial atas VERDIX_PROTOCOL_FINAL_v8. Dua koreksi
yang HARUS masuk sebelum pitch ke siapa pun. Selebihnya v8 tetap berlaku.*

---

## 1. Koreksi Moat: "Economic Memory tidak bisa di-fork" itu SETENGAH benar

### Masalah di framing v8

v8 bilang moat = Economic Memory yang tidak bisa direplikasi, analogi web graph
Google / data FICO. Tapi ada perbedaan fatal yang v8 lewatkan:

```
Google TIDAK publish web graph-nya.
FICO  TIDAK publish data biro kreditnya.
Verdix versi naif MEM-PUBLISH asetnya sendiri —
karena semua yang ditulis ke public chain bisa dibaca siapa pun.
```

Kompetitor tidak perlu mem-fork apa pun. Cukup baca chain yang sama, bangun
scorer yang lebih bagus, dan numpang gratis di data yang Verdix susah payah
kumpulkan. On-chain data = public good, bukan aset proprietary.

### Reposisi (v9)

Arsitektur dipecah eksplisit jadi dua bagian dengan peran berbeda:

```
ON-CHAIN  (public, komoditas — SENGAJA)
  → bukti: settlement, escrow release, ruling, attestation
  → commitment: dataHash (hash payload, bukan payload-nya)
  → log perpindahan kontrol identity
  → Ini layer INTEROPERABILITAS. Terbuka itu fitur, bukan kebocoran.

OFF-CHAIN (proprietary — INI MOAT-NYA)
  → payload lengkap di balik tiap dataHash:
    spec task, isi negosiasi AI↔AI, konteks keputusan delegasi,
    telemetri perilaku saat stress — hanya ada di store Verdix,
    terverifikasi karena hash-nya match dengan commitment on-chain
  → graph intelligence + model scoring yang dituning dari payload itu
  → analogi yang benar: chain = laporan transaksi publik,
    Verdix = biro kredit + FICO di atasnya
```

Konsekuensi produk: yang dijual BUKAN "akses ke log on-chain" (gratis, memang
untuk semua) tapi **akses ke payload terverifikasi + Trust Intelligence** via
Reputation API. SDK Verdix menulis hash on-chain dan payload ke store Verdix
dalam satu panggilan — di situ data eksklusifnya lahir.

Implementasi Phase 1 sudah sesuai ini by design: `EconomicMemory` hanya simpan
`dataHash`; payload tinggal di sisi kita (dogfood: journal bot). Jangan pernah
"upgrade" ini jadi payload on-chain.

## 2. Identity ERC-8004 = NFT → reputasi bisa DIBELI. Ini first-class problem

Draft ERC-8004 terbaru menjadikan agent = token ERC-721: identity **by design
transferable**. Tanpa mitigasi, cara termurah nge-game Trust Score bukan farming
(mahal, kena bond + diversity screening) tapi **beli agentId yang skornya sudah
tinggi**.

Mitigasi (sudah diimplementasi Phase 1):

```
1. Registry mencatat SETIAP perpindahan kontrol:
   - transfer NFT (ownership_transfer) — wallet operasional lama auto-dicabut
   - set/unset operational wallet (wallet_set / wallet_unset, wajib
     signature consent si wallet)
   → controlChangesOf(agentId) = input WAJIB Trust Intelligence

2. Scorer men-discount history pra-perpindahan (carryover 0.4 per perpindahan):
   - evidence yang gugur dihitung sebagai KETIDAKPASTIAN di success rate
     (bukan sekadar re-weight — supaya rasio suksesnya ikut turun)
   - graph diversity ikut ter-discount (relasi = milik controller lama)
   → hasil: identity hasil beli < identity fresh < identity konsisten.
     Membeli reputasi jadi rugi; insentifnya membangun, bukan membeli.
```

Prinsip: **skor mengikuti perilaku controller, bukan token-nya.** Ini analog
cost-of-forgery v8: manfaat membeli identity harus selalu < harganya.

## 3. Catatan kecil yang ikut berubah dari v8

- "AgentID ERC-8004 compatible" sekarang berarti implement interface draft asli
  (register/agentURI/metadata/setAgentWallet), bukan registry domain sendiri —
  supaya setiap agent ERC-8004 bisa langsung punya Verdix memory tanpa daftar ulang.
- Storage entry full on-chain hanya untuk testnet/demo; produksi: event + merkle
  root, entry direkonstruksi indexer (biaya nulis per-entry harus mendekati nol
  supaya micro-task ekonomis).
- Arbitrator tunggal & bond 10% = parameter MVP, bukan desain final. Jalan
  keluarnya bukan menaikkan bond (membunuh micro-task) tapi memperkuat
  statistical screening Tier 4 di scorer — yang kebetulan juga aset proprietary
  (lihat bagian 1).
