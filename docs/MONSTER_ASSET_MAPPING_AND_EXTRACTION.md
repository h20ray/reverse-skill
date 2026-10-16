# Summoners War Monster Asset Extraction & Mapping Guide

Dokumentasi teknis ekstraksi aset gambar (*unit portraits / monster icons*), struktur `monster_id` (Master ID), konvensi penamaan file aset (`unit_icon_XXXX_Y_Z.png`), dan strategi resolusi mapping pada project **xstomper** dan **reverse-skill**.

---

## 1. Ringkasan & Status Aset

| Komponen | Lokasi Sumber / Tujuan | Jumlah Item | Keterangan |
| :--- | :--- | :---: | :--- |
| **Base APK** | `/data/app/.../split_asset_base.apk` | 1.523 file | Aset bawaan paket installasi game |
| **Patch Resources** | `/sdcard/Android/data/.../files/Downloads/Resource/un/` | 911 file | Update in-game berkala (2A baru, collab, monster baru) |
| **Total Unik Gabungan** | `dungeon_drop_assets/unit_portraits/` | **2.199 file** | Koleksi lengkap seluruh icon di perangkat |
| **Database Monster** | `xstomper-protocol/data/monsters.min.json` | 1.778 monster | Master ID monster aktif |
| **Coverage Mapping** | Resolusi ID -> File Icon | **99.8% (1.775/1.778)** | 3 sisa adalah monster starter dengan penamaan khusus |

---

## 2. Lokasi Aset pada Perangkat Android (ADB Root)

Summoners War (`com.com2us.smon.normal.freefull.google.kr.android.common`) membagi aset visual ke dalam dua tempat:

### A. Base APK Assets
- **Path**: `/data/app/~~<hash>/com.com2us.smon.../split_asset_base.apk`
- **Isi**: `assets/unit_icon_*.png`
- **Karakteristik**: File statis dari APK Google Play Store / installer awal (berisi 1.523 portrait generasi lama s/d menengah).

### B. In-Game Downloaded Patch Assets
- **Path Storage**: `/sdcard/Android/data/com.com2us.smon.normal.freefull.google.kr.android.common/files/Downloads/Resource/un/`
- **Path Direct (Root)**: `/data/media/0/Android/data/com.com2us.smon.normal.freefull.google.kr.android.common/files/Downloads/Resource/un/`
- **Isi**: File lepas `unit_icon_*.png`
- **Karakteristik**: Diunduh otomatis saat game melakukan patch update. Terdapat **676 icon baru** yang tidak ada di dalam Base APK (termasuk monster 2A terbaru).

---

## 3. Prosedur Ekstraksi & Sinkronisasi via ADB Root

### Langkah 1: Ekstraksi dari Base APK
```bash
# Buat direktori tujuan
mkdir -p dungeon_drop_assets/unit_portraits

# Ekstraksi asset base dari split_asset_base.apk via ADB
adb shell "su -c 'cd /data/local/tmp && unzip -o /data/app/*smon*/split_asset_base.apk "assets/unit_icon*" -d extracted_apk/'"
adb pull /data/local/tmp/extracted_apk/assets/. dungeon_drop_assets/unit_portraits/
```

### Langkah 2: Sinkronisasi dari Downloaded Resource Folder
```bash
# Salin seluruh patch icon dari storage game
adb shell "su -c 'cp /data/media/0/Android/data/com.com2us.smon.normal.freefull.google.kr.android.common/files/Downloads/Resource/un/unit_icon* /data/local/tmp/patch_icons/'"
adb pull /data/local/tmp/patch_icons/. dungeon_drop_assets/unit_portraits/
```

---

## 4. Struktur Master ID (`monster_id`)

Format ID monster 5-digit: `[FFF][A][E]` (atau 7-digit `1000101` untuk Homunculus)

```text
Format:  [ F F F ] [ A ] [ E ]
Contoh:     1 0 1     1     1   -> Elucia (Water Fairy Awakened)
            1 1 0     3     2   -> Raoq (2A) (Fire Inugami 2A)
```

### Breakdown Komponen ID:
1. **`FFF` (Family ID — 3 digit awal)**:
   - `101`: Fairy
   - `102`: Imp
   - `103`: Pixie
   - `106`: Hellhound
   - `110`: Inugami
   - `115`: Griffon
   - `180`: Brownie Magician
   - `201`: Neostone Agent, dll.

2. **`A` (Awakening / Evolution Status — Digit ke-4)**:
   - `0`: **Unawakened** (Bentuk dasar)
   - `1`: **Awakened** (Bentuk awakened biasa)
   - `2`: **Awakened Khusus** (Beberapa varian form)
   - `3`: **Second Awakening (2A)**

3. **`E` (Elemen — Digit ke-5)**:
   - `1`: 💧 **Water**
   - `2`: 🔥 **Fire**
   - `3`: 🍃 **Wind**
   - `4`: ✨ **Light**
   - `5`: 🌑 **Dark**

---

## 5. Konvensi Penamaan File Aset (`unit_icon_XXXX_Y_Z.png`)

Com2uS menyusun icon unit dalam **Texture Sheet / Atlas Matrix 5x5**:

```text
unit_icon_[Sheet/Batch ID]_[Row (Elemen)]_[Col (Slot Bentuk)].png
```

### A. Pola Sheet Standar (Sheet `0000` s/d `0050`)
- **`XXXX`**: Index sheet atlas (misal `0000`, `0001`, `0002`...). Satu sheet 5x5 biasanya menampung 2–3 keluarga monster.
- **`Y`**: Index Elemen ($Y = E - 1$):
  - `0` = Water ($E=1$)
  - `1` = Fire ($E=2$)
  - `2` = Wind ($E=3$)
  - `3` = Light ($E=4$)
  - `4` = Dark ($E=5$)
- **`Z`**: Slot bentuk/varian keluarga di sheet tersebut:
  - **Sheet `0000` Contoh**:
    - `Z = 0`: Fairy Unawakened (`unit_icon_0000_0_0` s/d `4_0`)
    - `Z = 1`: Fairy Awakened / Elucia dkk (`unit_icon_0000_0_1` s/d `4_1`)
    - `Z = 2`: Imp Unawakened (`unit_icon_0000_0_2` s/d `4_2`)
    - `Z = 3`: Imp Awakened / Fynn dkk (`unit_icon_0000_0_3` s/d `4_3`)
    - `Z = 4`: Pixie Unawakened (`unit_icon_0000_0_4` s/d `4_4`)

### B. Pola Sheet Second Awakening (2A) & Update Patch
- **2A Gelombang 1 (Fairy, Pixie, Warbear, Inugami)**: Dikelompokkan pada sheet `0051`.
- **2A Gelombang 2 (Griffon)**: Sheet `0055`.
- **2A Gelombang 3 (High Elemental, Howl)**: Sheet `0074`, `0075`.
- **2A Gelombang 4 (Harpu)**: Sheet `0160`.
- **2A Gelombang Terbaru (Hellhound, Inferno, dll.)**: Menggunakan sheet `0211`, `0212`, dst. (Pada sheet ini orientasi $Z$ digunakan untuk elemen `1..5`, contoh `unit_icon_0211_3_1.png` s/d `unit_icon_0211_3_5.png`).

---

## 6. Strategi Implementasi di Codebase

### A. Resolusi Nama & Atribut (Algoritmik)
Dapat langsung diparsing secara instan tanpa ketergantungan file external untuk field dasar:
```rust
// Element formula
let element = match master_id % 10 {
    1 => "Water",
    2 => "Fire",
    3 => "Wind",
    4 => "Light",
    5 => "Dark",
    _ => "Unknown",
};

// Awakening formula
let is_2a = ((master_id / 10) % 10) == 3;
let is_awakened = ((master_id / 10) % 10) >= 1;
```

### B. Resolusi Asset Icon (Lookup Table)
Karena penempatan monster baru pada sheet atlas bertambah seiring patch game, pemetaan nama file icon menggunakan lookup table JSON:
- `crates/xstomper-protocol/data/monsters.min.json`
- Mapping format:
```json
{
  "10111": {
    "name": "Elucia",
    "element": "Water",
    "family": "Fairy",
    "archetype": "support",
    "speed": 104,
    "icon": "unit_icon_0000_0_1.png"
  },
  "10632": {
    "name": "Sieq (2A)",
    "element": "Fire",
    "family": "Hellhound",
    "archetype": "Attack",
    "speed": 115,
    "icon": "unit_icon_0211_3_2.png"
  }
}
```

---

## 7. Catatan Khusus & Edge Cases

1. **Starter Units (3 ID Khusus)**:
   - `10101` (Water Fairy unawakened), `10602` (Fire Hellhound unawakened), `15203` (Wind Vagabond unawakened).
   - Di asset asli Com2uS, starter unit yang langsung diberikan saat tutorial sering kali menggunakan asset form awakened (`unit_icon_0000_0_1.png` dan `unit_icon_0002_1_1.png`).
2. **Homunculus (`1000101` - `1000205`)**:
   - Memiliki master ID 7-digit. Mengikuti index sheet `0044` dan `0045`.
3. **Collab Monsters (Street Fighter, Witcher, Cookie Run, dll.)**:
   - Memiliki rentang ID keluarga khusus `2xxxx` dan tersimpan di patch resource sheets `01xx` dan `02xx`.
