# User Guide — Infinys WhatsApp Gateway

Panduan langkah demi langkah untuk menggunakan modul **Infinys WhatsApp Gateway**
di Odoo 19. Dokumen ini ditujukan untuk pengguna akhir dan administrator.

---

## Daftar Isi

1. [Sekilas Aplikasi](#1-sekilas-aplikasi)
2. [Sebelum Mulai](#2-sebelum-mulai)
3. [Langkah 1 — Konfigurasi Kredensial](#3-langkah-1--konfigurasi-kredensial)
4. [Langkah 2 — Membuka WhatsApp Outbox](#4-langkah-2--membuka-whatsapp-outbox)
5. [Langkah 3 — Mengirim Pesan Teks](#5-langkah-3--mengirim-pesan-teks)
6. [Langkah 4 — Mengirim Pesan dengan Media](#6-langkah-4--mengirim-pesan-dengan-media)
7. [Format Nomor Telepon](#7-format-nomor-telepon)
8. [Antrian vs Kirim Langsung](#8-antrian-vs-kirim-langsung)
9. [Memantau Status & Log](#9-memantau-status--log)
10. [Scheduled Action (Cron)](#10-scheduled-action-cron)
11. [Format Pesan (HTML → WhatsApp)](#11-format-pesan-html--whatsapp)
12. [Troubleshooting](#12-troubleshooting)
13. [FAQ](#13-faq)

---

## 1. Sekilas Aplikasi

Infinys WhatsApp Gateway mengirim **notifikasi WhatsApp satu arah** dari Odoo —
ideal untuk pengingat, peringatan, dan notifikasi sistem. Aplikasi ini **tidak**
menerima balasan atau melakukan chat dua arah.

Setiap pesan disimpan sebagai record di **WhatsApp Outbox**, lengkap dengan status
pengiriman, untuk keperluan audit dan analisis.

---

## 2. Sebelum Mulai

Pastikan hal berikut sudah siap:

- Modul **Infinys WhatsApp Gateway** sudah terinstal (lihat `architecture.md`
  bagian Instalasi).
- Anda memiliki **WhatsApp API tenant** dari Tim Odoo Infinys, berupa:
  - API Endpoint (Base URL)
  - Phone Number (nomor pengirim)
  - WAPI User
  - WAPI Token
- Akun Odoo Anda punya akses ke menu Settings / Technical.

---

## 3. Langkah 1 — Konfigurasi Kredensial

1. Buka **Settings** (menu utama Odoo).
2. Gulir / cari panel **Infinys Whatsapp**.
3. Isi bidang berikut:
   - **API Endpoint** — Base URL layanan WAPI (mis.
     `https://wapi.infinysystem.com/v1`).
   - **Phone Number** — nomor pengirim, format digit saja (mis. `628176057749`).
   - **WAPI User** — username tenant Anda.
   - **WAPI Token** — token rahasia (ditampilkan tersembunyi).
4. Klik **Save**.
5. Klik tombol **Check Health**.
   - Jika berhasil, muncul notifikasi hijau **"WAPI connection successful!"**.
   - Jika gagal, muncul notifikasi merah berisi pesan error — periksa kembali
     endpoint/token dan koneksi internet server.

> Nomor pengirim otomatis dibersihkan dari `+`, `-`, dan spasi saat disimpan.
> Jika formatnya salah, Odoo akan menolak penyimpanan dengan pesan jelas.

---

## 4. Langkah 2 — Membuka WhatsApp Outbox

Menu outbox berada di area Technical:

1. Aktifkan **Developer Mode** bila belum (Settings → Developer Tools →
   Activate the developer mode).
2. Buka **Settings → Technical → Automation → WhatsApp Outbox Logs**.

Anda akan melihat daftar (list) semua pesan keluar dengan kolom: Created, Phone,
Subject, Is Queued, Is Delivered, Sent Date, Has Media, Media Filename.

Warna baris:
- **Hijau** — pesan sudah terkirim.
- **Kuning** — pesan masih dalam antrian.
- **Abu-abu** — pesan gagal / tidak dalam antrian.

---

## 5. Langkah 3 — Mengirim Pesan Teks

1. Di list **WhatsApp Outbox Logs**, klik **New**.
2. Isi form:
   - **Subject** — judul/penanda pesan (opsional).
   - **Phone Number** — nomor tujuan (mis. `628176057749`). Boleh ketik dengan
     `+` / `-` / spasi; akan dibersihkan otomatis.
   - **Scheduled Date** — waktu rencana kirim (default sekarang).
   - **Module Name** / **Note** — opsional, untuk pelacakan.
3. Buka tab **Content**, tulis isi pesan di field **Message** (editor mendukung
   teks tebal, miring, list, link).
4. Klik **Save**.
5. Kirim pesan:
   - **Send** — masukkan ke antrian; akan dikirim oleh scheduler.
   - **Send Immediate** — kirim sekarang juga.
6. Periksa status di tab/field **Is Delivered** dan **Sent Date**.

---

## 6. Langkah 4 — Mengirim Pesan dengan Media

1. Buat record baru (atau buka yang sudah ada).
2. Pada field **Attachment**, unggah satu file. Tipe yang didukung:
   - Gambar: JPEG, PNG, GIF
   - Video: MP4, 3GP
   - Dokumen: PDF, DOC/DOCX, XLS/XLSX, PPT/PPTX
   (maksimal **1 file** per pesan)
3. Setelah file diunggah, tab **Media** akan muncul otomatis dan menampilkan
   metadata (URL, filename, MIME type).
4. Tulis caption di field **Message** bila perlu.
5. Klik **Save**, lalu **Send** atau **Send Immediate**.

> Sistem otomatis mendeteksi jenis media dari ekstensi file dan memilih endpoint
> WAPI yang tepat (image/video/audio/document).

---

## 7. Format Nomor Telepon

Gateway mewajibkan **format internasional, digit saja, tanpa `+` dan tanpa `-`**.

| Yang Anda ketik | Disimpan menjadi | Status |
|-----------------|------------------|--------|
| `+62 817-6057-749` | `628176057749` | ✅ valid |
| `0062 817 6057 749` | `628176057749` | ✅ valid |
| `62.817.6057.749` | `628176057749` | ✅ valid |
| `628176057749` | `628176057749` | ✅ valid |
| `08176057749` | `08176057749` | ❌ ditolak (berawalan 0) |
| `0817-6057-749` | `08176057749` | ❌ ditolak (berawalan 0) |

**Penting:** nomor lokal berawalan `0` **tidak** diterima dan tidak ditebak
otomatis. Anda harus memasukkan format internasional penuh, contoh: ganti awalan
`0` Indonesia menjadi `62` → `628176057749`.

Jika nomor tidak valid, Odoo menampilkan pesan:
> *Invalid phone number '...'. Use international format with digits only, no '+'
> or '-' and no leading zero. Example: 628176057749*

---

## 8. Antrian vs Kirim Langsung

| Aksi | Perilaku | Kapan dipakai |
|------|----------|---------------|
| **Send** | Pesan masuk antrian (`Is Queued = True`). Dikirim oleh scheduler pada siklus berikutnya. | Pengiriman massal / terjadwal, performa lebih baik. |
| **Send Immediate** | Pesan dikirim seketika tanpa menunggu cron. | Pesan mendesak / pengujian. |

Pada pengiriman, sistem terlebih dulu mengirim status "sedang mengetik"
(composing) ke WhatsApp untuk tampilan yang lebih natural.

---

## 9. Memantau Status & Log

Setiap record outbox menyimpan jejak lengkap:

- **Is Queued** — masih menunggu dikirim.
- **Is Delivered** — sudah terkirim ke WAPI.
- **Sent Date** — waktu pengiriman.
- **Error Message** (tab **Technical Details**) — muncul bila pengiriman gagal,
  berisi detail penyebab (mis. token salah, nomor tidak terdaftar, timeout).

Gunakan list view + filter/sort untuk meninjau riwayat pengiriman, mengidentifikasi
pesan gagal, dan menganalisis volume notifikasi.

---

## 10. Scheduled Action (Cron)

Modul memasang Scheduled Action **"Infinys WhatsApp API: Send Queued Messages"**.

- Berjalan setiap **1 menit**.
- Memproses hingga **20 pesan** antrian per siklus (urut berdasarkan
  `scheduled_date`).
- Memberi jeda singkat antar pengiriman untuk kestabilan.

Untuk mengelolanya: **Settings → Technical → Automation → Scheduled Actions** →
cari nama di atas. Di sini Anda bisa menonaktifkan, mengubah interval, atau
menjalankan manual ("Run Manually").

---

## 11. Format Pesan (HTML → WhatsApp)

Editor pesan menggunakan HTML, tetapi WhatsApp memakai format teks sederhana.
Sistem otomatis mengonversi sebelum kirim:

| Di editor Odoo | Dikirim ke WhatsApp |
|----------------|---------------------|
| **Tebal** (`<b>`/`<strong>`) | `*tebal*` |
| *Miring* (`<i>`/`<em>`) | `_miring_` |
| Daftar (`<li>`) | `• item` |
| Tautan (`<a href>`) | `teks (url)` |
| Judul (`<h1>`/`<h2>`) | `*Judul*` |
| Baris baru / paragraf | baris baru |

Tag lain dan style inline dihapus, lalu spasi dirapikan. Jadi cukup tulis pesan
secara normal di editor; hasilnya akan rapi di WhatsApp.

---

## 12. Troubleshooting

| Gejala | Kemungkinan Penyebab | Solusi |
|--------|----------------------|--------|
| **Check Health** gagal | Endpoint/token salah, server tak punya akses internet | Periksa kembali kredensial; pastikan server bisa menjangkau Base URL |
| Pesan tetap **Is Queued** | Scheduler nonaktif atau belum jalan | Cek Scheduled Action aktif; jalankan manual untuk uji |
| **Error Message** terisi setelah kirim | Nomor tidak terdaftar di WA, token kedaluwarsa, timeout | Baca detail di tab Technical Details; verifikasi nomor & token |
| Nomor ditolak saat Save | Format salah (berawalan 0 / ada huruf) | Pakai format internasional digit saja, mis. `628176057749` |
| Media tidak terkirim | File >1 atau tipe tidak didukung | Unggah satu file dengan tipe yang didukung |
| Menu Outbox tidak terlihat | Developer Mode nonaktif | Aktifkan Developer Mode; menu ada di Technical → Automation |

---

## 13. FAQ

**Q: Apakah bisa membalas pesan masuk dari pelanggan?**
A: Tidak. Aplikasi ini khusus pengiriman satu arah (notifikasi).

**Q: Apakah bisa mengirim ke banyak nomor sekaligus?**
A: Setiap record outbox = satu nomor tujuan. Untuk banyak nomor, buat banyak
record (mis. lewat integrasi dari model lain), lalu biarkan scheduler memproses
antrian. Untuk blasting massal, gunakan WhatsApp Blasting oleh Infinys.

**Q: Bagaimana mengirim notifikasi otomatis dari Sales/Purchase Order?**
A: Buat record `infinys.wapi.outbox` dari kode model Anda lalu panggil
`send_message()` atau `send_message_immediate()`. Lihat contoh di
`architecture.md` bagian Integrasi.

**Q: Berapa cepat pesan antrian dikirim?**
A: Scheduler berjalan tiap 1 menit, hingga 20 pesan per siklus. Untuk pengiriman
seketika, gunakan **Send Immediate**.

**Q: Di mana melihat riwayat pengiriman?**
A: Settings → Technical → Automation → **WhatsApp Outbox Logs**.

---

Untuk detail teknis arsitektur, struktur kode, dan instalasi, lihat
[`architecture.md`](architecture.md).
