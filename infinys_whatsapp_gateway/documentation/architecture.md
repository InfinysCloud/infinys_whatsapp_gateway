# Architecture — Infinys WhatsApp Gateway

Dokumen ini menjelaskan arsitektur teknis modul **Infinys WhatsApp Gateway**
untuk Odoo 20 Community Edition: tujuan aplikasi, struktur folder, struktur kode,
penjelasan setiap modul Python, view, manifest, serta cara instalasi.

---

## 1. Tujuan Aplikasi

**Infinys WhatsApp Gateway** adalah solusi sederhana untuk mengirim **notifikasi
WhatsApp satu arah** (one-way) dari Odoo. Modul ini cocok untuk pengingat
(reminder), peringatan (alert), dan notifikasi sistem — **bukan** untuk chat dua
arah atau membalas pesan masuk.

Karakteristik utama:

- Mengirim pesan teks WhatsApp dari Odoo melalui WhatsApp API tenant (WAPI).
- Mendukung pesan dengan media: gambar, video, audio, dan dokumen.
- Penjadwalan otomatis lewat Scheduled Action (cron) untuk pengiriman antrian.
- Mencatat semua pesan keluar (outbox log) untuk kepatuhan dan analisis.
- Model sederhana `infinys.wapi.outbox` yang mudah diintegrasikan dari model atau
  controller Odoo lain (mis. Sales Order, Purchase Order).

Aplikasi ini bergantung pada WhatsApp API tenant yang disediakan oleh Tim Odoo
Infinys. Endpoint, user, dan token dikonfigurasi di Settings.

---

## 2. Struktur Folder

```
infinys_whatsapp_gateway/
├── __init__.py                     # Inisialisasi package: import controllers, models, utils
├── __manifest__.py                 # Metadata modul, dependensi, daftar data files
├── MIGRATION.md                    # Catatan migrasi 18 -> 19
├── readme.md                       # Ringkasan singkat modul
│
├── controllers/
│   ├── __init__.py
│   └── wuzapi_controller.py        # Endpoint HTTP/JSON publik (health check)
│
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py      # Pengaturan kredensial WAPI + health check
│   └── wapi_outbox.py              # Model inti outbox + logika kirim pesan + cron
│
├── utils/
│   ├── __init__.py
│   ├── generic_utils.py            # Helper: MIME, base64, normalisasi nomor telepon
│   └── texttohtml_utils.py         # Helper: konversi HTML <-> teks WhatsApp
│
├── views/
│   ├── res_config_settings_views.xml   # Form Settings (app Infinys Whatsapp)
│   └── wapi_outbox_views.xml           # List + Form + Action + Menu outbox
│
├── data/
│   └── ir_cron_data.xml            # Scheduled Action pengiriman antrian
│
├── security/
│   └── ir.access.csv               # Hak akses model (format Odoo 20)
│
├── static/
│   └── description/                # Aset Apps store (icon, banner, screenshot)
│
└── documentation/
    ├── architecture.md             # Dokumen ini
    └── user_guide.md               # Tutorial penggunaan aplikasi
```

---

## 3. Alur Kerja Tingkat Tinggi

```
                    +---------------------------+
                    |  Settings (res.config)    |
                    |  wapi.base_url / user /   |
                    |  token / phone_number     |
                    +-------------+-------------+
                                  |  baca via ir.config_parameter
                                  v
 (buat record)   +-------------------------------+      Scheduled Action (cron)
 model lain  --> |  infinys.wapi.outbox          | <--- _cron_send_queued_messages()
 atau manual     |  (antrian pesan, is_queued)   |      tiap 1 menit, batch 20
                 +---------------+---------------+
                                 |  execute_send_message()
                                 v
                 +-------------------------------+
                 |  send_text_message / media    |  HTTP POST (requests)
                 |  -> WhatsApp API (WAPI)       | -----------------------> WAPI Tenant
                 +-------------------------------+
                                 |
                                 v
                 update record: is_delivered / sent_date / error_msg
```

Dua jalur pengiriman:

1. **Tombol "Send"** — menandai record masuk antrian (`is_queued = True`). Cron
   akan memprosesnya pada siklus berikutnya.
2. **Tombol "Send Immediate"** — langsung memanggil `execute_send_message()` saat
   itu juga, tanpa menunggu cron.

---

## 4. Penjelasan Manifest (`__manifest__.py`)

| Key | Nilai | Keterangan |
|-----|-------|------------|
| `name` | Infinys Whatsapp Gateway | Nama tampil di Apps |
| `version` | `20.0.1.0.0` | Format versi penuh Odoo 20 |
| `category` | Tools | Kategori modul |
| `license` | AGPL-3 | Lisensi |
| `depends` | `base`, `mail` | Dependensi minimal |
| `data` | lihat di bawah | File yang dimuat saat install |
| `installable` | True | Bisa diinstal |
| `application` | False | Bukan aplikasi penuh (modul utilitas) |

Urutan `data` penting — resource harus didefinisikan sebelum direferensikan:

```python
"data": [
    "security/ir.access.csv",              # 1. Hak akses lebih dulu (format Odoo 20)
    "views/res_config_settings_views.xml",  # 2. Konfigurasi
    "views/wapi_outbox_views.xml",          # 3. View utama + menu
    "data/ir_cron_data.xml",                # 4. Cron terakhir (butuh model_id)
]
```

Cron dimuat terakhir karena merujuk `model_infinys_wapi_outbox`, yang baru ada
setelah model di-load.

---

## 5. Penjelasan Modul Python

### 5.1 `models/wapi_outbox.py` — Model Inti

Model `infinys.wapi.outbox` adalah jantung aplikasi: menyimpan pesan keluar,
menormalkan nomor, dan menjalankan logika pengiriman.

**Field utama:**

| Field | Tipe | Keterangan |
|-------|------|------------|
| `name` | Char | Subjek pesan |
| `phone` | Char | Nomor tujuan, digit saja (mis. `628176057749`) |
| `message` | Html | Isi pesan (HTML diizinkan, dikonversi sebelum kirim) |
| `error_msg` | Text | Pesan error jika gagal |
| `hasmedia` | Boolean (compute) | Otomatis True bila ada attachment/media |
| `media_url` / `media_filename` / `media_base64` / `media_mime_type` | — | Metadata media |
| `attachment_id` | Many2many(ir.attachment) | Lampiran |
| `module_name` | Char | Penanda asal pesan (sales, purchase, dll) |
| `note` | Text | Catatan bebas |
| `scheduled_date` | Datetime | Jadwal kirim |
| `sent_date` | Datetime | Waktu terkirim |
| `is_queued` | Boolean | Masih dalam antrian |
| `is_delivered` | Boolean | Sudah terkirim |

Catatan: `create_date` **tidak** didefinisikan ulang sebagai field manual karena
itu kolom log otomatis Odoo (penting untuk kompatibilitas v19).

**Metode penting:**

- `_normalize_phone(phone)` (staticmethod) — membungkus
  `generic_utils.normalize_phone_number`, menghapus `+`, `-`, spasi, dll.
- `_onchange_phone()` — membersihkan nomor secara live di form.
- `_check_phone()` (`@api.constrains`) — menolak nomor tidak valid (bukan 8–15
  digit / berawalan 0) dengan pesan jelas + contoh `628176057749`.
- `create()` (`@api.model_create_multi`) & `write()` — menormalkan `phone`
  sebelum disimpan, sehingga nilai tersimpan selalu bersih.
- `_compute_hasmedia()` (`@api.depends('attachment_id')`) — mengisi metadata
  media dari attachment, set `hasmedia`.
- `send_message()` — menandai record masuk antrian (diproses cron).
- `send_message_immediate()` — langsung mengirim sekarang.
- `execute_send_message(queued_records)` — inti pengiriman: set presence,
  pilih jalur teks/media, panggil API, lalu update status record. Try/except
  ter-scope per record agar kegagalan satu record tidak menghentikan lainnya.
- `_extract_error(result)` (staticmethod) — mengambil pesan error dari hasil
  pengiriman secara aman.
- `_cron_send_queued_messages()` (`@api.model`) — dipanggil Scheduled Action,
  memproses sampai 20 pesan antrian per siklus.
- `set_user_typing()` — mengirim status "composing" ke WAPI (simulasi mengetik).
- `send_text_message(phone_to, message)` — POST `/chat/send/text`.
- `send_media_message(...)` — POST `/chat/send/{image|video|audio|document}`
  sesuai MIME type.
- `mark_as_delivered()` — helper menandai terkirim.

Semua kredensial WAPI dibaca runtime dari `ir.config_parameter`
(`wapi.base_url`, `wapi.user`, `wapi.token`, `wapi.phone_number`).

### 5.2 `models/res_config_settings.py` — Pengaturan

Mewarisi `res.config.settings` (TransientModel). Menyimpan kredensial sebagai
system parameter via atribut `config_parameter`:

| Field | config_parameter |
|-------|------------------|
| `wapi_phone_number` | `wapi.phone_number` |
| `wapi_url` | `wapi.base_url` (default `https://wapi.infinysystem.com/v1`) |
| `wapi_user` | `wapi.user` |
| `wapi_token` | `wapi.token` (ditampilkan sebagai password) |

Metode:

- `_onchange_wapi_phone_number()` — normalisasi nomor pengirim secara live.
- `set_values()` — menormalkan + memvalidasi nomor pengirim sebelum disimpan;
  menolak format salah dengan `ValidationError`.
- `get_wapi_status()` — memanggil endpoint `/health` WAPI; dipakai tombol dan
  controller.
- `action_wapi_check_health()` — tombol "Check Health"; menampilkan notifikasi
  sukses/gagal.

### 5.3 `controllers/wuzapi_controller.py` — Endpoint Publik

Controller `WuzapiController` mengekspos satu route JSON:

```
POST /api/wapi/wuzapi/health   (auth='public', csrf=False)
```

Memanggil `res.config.settings.get_wapi_status()` dan mengembalikan response JSON
terstruktur (`success_response` / `error_response`). Berguna untuk health check
dari sistem eksternal.

### 5.4 `utils/generic_utils.py` — Helper Umum

- `normalize_phone_number(phone)` — menghapus `+`, `-`, spasi, titik, kurung;
  membuang awalan `+`; mengubah prefix `00` ke format internasional; menyisakan
  digit saja.
- `is_valid_phone_number(phone)` — True bila 8–15 digit tanpa awalan nol.
- `convert_data_uri_to_bytes(mime_type, url)` — mengambil konten dari URL dan
  meng-encode base64 (untuk media).
- `get_mime_type_from_filename(filename)` — menentukan kategori (image/video/
  audio/document) dari ekstensi file.

### 5.5 `utils/texttohtml_utils.py` — Konversi Teks/HTML

- `clean_html_for_whatsapp(html)` — mengubah HTML editor Odoo menjadi teks
  ber-format WhatsApp (mis. `<b>` -> `*tebal*`, `<i>` -> `_miring_`, list -> `•`,
  link -> `teks (url)`), membuang tag sisa, dan merapikan spasi.
- `formatHtml`, `formatText`, `HTMLToTextParser`, `safe_replace` — utilitas
  pendukung. Semua regex memakai raw-string (aman di Python 3.12).

---

## 6. Penjelasan View

### 6.1 `views/wapi_outbox_views.xml`

- **List view** (`view_infinys_wapi_outbox_tree`) — memakai elemen `<list>`
  (standar v19, bukan `<tree>`). Dekorasi baris: hijau bila terkirim, kuning bila
  antri, abu-abu bila gagal/tidak antri.
- **Form view** (`view_infinys_wapi_outbox_form`) — header berisi tombol **Send**
  dan **Send Immediate** (muncul saat `is_queued`). Field nomor memakai
  `widget="phone"` dengan placeholder `e.g. 628176057749`. Notebook 3 tab:
  Content (pesan), Media (muncul bila `hasmedia`), Technical Details (error).
- **Action** (`action_infinys_wapi_outbox`) — `view_mode="list,form"`.
- **Menu** (`menu_infinys_wapi_outbox`) — "WhatsApp Outbox Logs" di bawah
  `base.menu_automation` (Settings → Technical → Automation).

### 6.2 `views/res_config_settings_views.xml`

Mewarisi `base.res_config_settings_view_form` dan menambahkan blok **app**
"Infinys Whatsapp" memakai struktur modern `<app>/<block>/<setting>`. Berisi
field endpoint, nomor pengirim, user, token, dan tombol **Check Health**.

---

## 7. Data & Security

- **`data/ir_cron_data.xml`** — `ir.cron` "Infinys WhatsApp API: Send Queued
  Messages", state `code`, kode `model._cron_send_queued_messages()`, interval 1
  menit, dijalankan sebagai `base.user_root`. `noupdate="1"` agar tidak ditimpa
  saat upgrade.
- **`security/ir.access.csv`** (format `ir.access` Odoo 20, kolom `operation`=`crud`) — memberi akses penuh
  (read/write/create/unlink) ke `infinys.wapi.outbox` bagi `base.group_user`.

---

## 8. Cara Instalasi

### Prasyarat

- Odoo **20.0** Community Edition.
- Python **3.12+**.
- Library `requests` (umumnya sudah tersedia di environment Odoo).
- WhatsApp API tenant (endpoint, user, token) dari Tim Odoo Infinys.

### Langkah

1. **Salin modul** ke folder addons Odoo:
   ```bash
   cp -r infinys_whatsapp_gateway /path/to/odoo/addons/
   ```
   Atau extract `infinys_whatsapp_gateway.zip` ke folder addons.

2. **Pastikan path addons** terdaftar di konfigurasi Odoo (`odoo.conf`):
   ```ini
   addons_path = /path/to/odoo/addons, /path/to/custom/addons
   ```

3. **Restart server Odoo** dan **update daftar Apps**:
   ```bash
   ./odoo-bin -c odoo.conf -u all   # atau update list via UI
   ```
   Atau di UI: aktifkan Developer Mode → Apps → **Update Apps List**.

4. **Install modul**: Apps → cari **"Infinys"** → **Infinys WhatsApp Gateway** →
   **Install**.

5. **Konfigurasi kredensial**: Settings → cari panel **Infinys Whatsapp** →
   isi API Endpoint, Phone Number, WAPI User, WAPI Token → **Save** →
   klik **Check Health** untuk verifikasi koneksi.

> Catatan: aset gambar di `static/description/` (icon, banner, screenshot) tidak
> termasuk dalam paket migrasi ini. Modul tetap berjalan tanpanya; salin dari
> modul asli bila ingin menampilkan logo dan gambar Apps store.

---

## 9. Integrasi dari Modul Lain

Untuk mengirim notifikasi dari model/controller lain, cukup buat record outbox:

```python
self.env['infinys.wapi.outbox'].create({
    'name': 'Order Confirmation',
    'phone': '+62 817-6057-749',          # akan dinormalkan -> 628176057749
    'message': '<b>Order #SO001</b> telah dikonfirmasi.',
    'module_name': 'sale',
}).send_message_immediate()                 # atau .send_message() untuk antrian
```

Nomor otomatis dibersihkan; format HTML otomatis dikonversi ke gaya WhatsApp.

---

## 10. Ringkasan Perubahan Migrasi 18 → 19

Detail lengkap ada di `MIGRATION.md`. Singkatnya: penyesuaian field `create_date`,
penghapusan anti-pattern import controller di model, type hints, pembersihan
import berbahaya, perampingan utils, raw-string regex, perbaikan bug pengiriman
media, serta penambahan fitur normalisasi & validasi nomor telepon.
