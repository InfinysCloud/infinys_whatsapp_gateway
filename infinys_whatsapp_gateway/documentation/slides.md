# Infinys WhatsApp Gateway — Presentation Slides

> Outline presentasi dalam format Markdown. Setiap `---` memisahkan satu slide.
> Versi siap-presentasi (fullscreen) tersedia di `slides.html`.

---

## Slide 1 — Cover

**Infinys WhatsApp Gateway**

Kirim notifikasi WhatsApp satu arah langsung dari Odoo.

Odoo 19 Community Edition · Infinys System Indonesia

---

## Slide 2 — Masalah

- Notifikasi penting (pengingat, peringatan, status pesanan) sering terlewat lewat email.
- WhatsApp punya tingkat keterbacaan jauh lebih tinggi.
- Tim butuh cara mudah mengirim notifikasi WA langsung dari Odoo, tanpa integrasi rumit.

---

## Slide 3 — Solusi

**Gateway WhatsApp satu arah** terintegrasi penuh di Odoo:

- Kirim pesan teks & media langsung dari Odoo.
- Otomatis terjadwal lewat scheduler.
- Semua pesan tercatat untuk audit & analisis.

---

## Slide 4 — Fitur Utama

- 💬 Pesan teks satu arah dari Odoo
- 🖼️ Dukungan media: gambar, video, audio, dokumen
- ⏱️ Penjadwalan otomatis (cron, batch 20/menit)
- 📋 Outbox log untuk kepatuhan & analisis
- 🔌 Model sederhana `infinys.wapi.outbox`, mudah diintegrasikan

---

## Slide 5 — Cara Kerja (Alur)

1. **Settings** menyimpan kredensial WAPI (URL, user, token, nomor pengirim).
2. **Outbox** menampung pesan (`is_queued = True`).
3. **Cron** memproses antrian → memanggil **WhatsApp API**.
4. Status record diperbarui: `is_delivered`, `sent_date`, atau `error_msg`.

---

## Slide 6 — Dua Mode Pengiriman

| Mode | Perilaku | Kapan dipakai |
|------|----------|---------------|
| **Send** | Masuk antrian, dikirim scheduler | Massal / terjadwal |
| **Send Immediate** | Kirim seketika | Mendesak / pengujian |

---

## Slide 7 — Format Nomor Telepon

Wajib **internasional, digit saja, tanpa `+` dan `-`**.

- ✅ `+62 817-6057-749` → `628176057749` (dibersihkan otomatis)
- ✅ `628176057749`
- ❌ `08176057749` (berawalan 0 — ditolak, minta format internasional)

Validasi & normalisasi otomatis saat input dan simpan.

---

## Slide 8 — Format Pesan (HTML → WhatsApp)

Tulis normal di editor Odoo; otomatis dikonversi:

- **Tebal** → `*tebal*`
- *Miring* → `_miring_`
- Daftar → `• item`
- Tautan → `teks (url)`

---

## Slide 9 — Arsitektur Teknis

- **models/** — `wapi_outbox` (inti), `res_config_settings` (kredensial)
- **controllers/** — endpoint health check publik
- **utils/** — normalisasi nomor, konversi HTML
- **views/** — list, form, settings, menu
- **data/** — scheduled action (cron)
- **security/** — hak akses model

Odoo 19 · Python 3.12+ · depends: `base`, `mail`

---

## Slide 10 — Cara Instalasi

1. Salin modul ke folder addons Odoo.
2. Pastikan `addons_path` benar di `odoo.conf`.
3. Restart Odoo & **Update Apps List**.
4. Apps → cari **"Infinys"** → **Install**.
5. Settings → panel **Infinys Whatsapp** → isi kredensial → **Check Health**.

---

## Slide 11 — Integrasi dari Modul Lain

```python
self.env['infinys.wapi.outbox'].create({
    'name': 'Order Confirmation',
    'phone': '+62 817-6057-749',   # → 628176057749
    'message': '<b>Order #SO001</b> dikonfirmasi.',
    'module_name': 'sale',
}).send_message_immediate()
```

Nomor dibersihkan otomatis; HTML dikonversi ke gaya WhatsApp.

---

## Slide 12 — Terima Kasih

**Infinys WhatsApp Gateway**

Hubungi Tim Odoo Infinys untuk WhatsApp API tenant.

🌐 https://integra.isi.id/ · Infinys System Indonesia
