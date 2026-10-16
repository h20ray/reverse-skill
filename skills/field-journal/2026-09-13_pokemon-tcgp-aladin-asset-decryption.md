# Field Journal — 2026-09-13 — Pokemon TCG Pocket `.aladin` asset decryption & extraction

- case: 20260912-235959-pokemon-tcg-pocket-asset-extract
- primary_skill: apk-reverse (R1)
- target: `jp.pokemon.pokemontcgp` on MuMu Player instance 3 "Game Lib" (Android 15, ADB 127.0.0.1:16480)
- auth: offline-sample preset, granted (user-owned emulator, user-installed game, personal asset appreciation)
- outcome: **success** — 65,342/65,354 blobs decrypted to UnityFS; 3,091 card illustrations batch-exported to PNG

## What worked (reusable chain)

1. **Root ADB on MuMu**: `MuMuManager.exe adb -v 3 -c root` → `restarting adbd as root`; afterwards plain adb has full access to `/storage/emulated/0/Android/data/<pkg>`.
2. **Android 15 MuMu image** → adb lives in `nx_device\15.0\shell\adb.exe` (12.0 path does not exist on this install; `nx_main\adb.exe` works too). `MuMuManager info -v all` shows `android_version` per instance. Git Bash needs `MSYS_NO_PATHCONV=1` for remote paths, and Windows-style `C:\...` for the local pull target.
3. **Split APK pull**: `pm path jp.pokemon.pokemontcgp` → base + `split_bundledtree.apk` (assetpack) + arm64 config.
4. **Sub-key**: base.apk `assets/bin/Data/4d2341dcb511242f2853ce941ef20146` is a Unity serialized file (6000.0.78f1) containing TextAsset `src_cph_1001` (1024 bytes: u32be offset 0x1FC + u32be len 0x20 + 32-byte sub-key). UnityPy export must roundtrip bytes via `m_Script.encode('utf-8','surrogateescape')` — plain latin-1 encode corrupts it.
5. **Decrypt**: [aladump](https://github.com/SombrAbsol/aladump) release binary. Input dir = merged `blob/` + `index/` + `src_cph_1001`. Cipher = modified ChaCha20 (custom sigma, 5/6 double rounds, content_hash as IV), two-key bootstrap (sub-key decrypts main-key blob).
6. **Export**: UnityPy with `UnityPy.config.FALLBACK_UNITY_VERSION='6000.0.78f1'`; card ID grammar `c{PK|TR}_{gen}_{num}_{ver}_{NAME}_{RAR}` + variant token before `_ILL`.

## Gotchas

- On-device `Sharin.Resources/Default/index/` held only 2 files (13 MB) but covers all 65k blobs; the preinstalled bundledtree index (1.3 MB) is a subset.
- `su` does NOT exist on MuMu Android 15 shell — use `adb root` instead.
- Merge with `cp -ru` so on-device blobs win over preinstalled ones.
- Blob store is content-addressed by xxHash-64 of plaintext; index FlatBuffers entries carry the ChaCha20 IV (`content_hash`).

## Deliverables

- `work/20260912-235959-pokemon-tcg-pocket-asset-extract/ASSET_MAPPING.md` (full tree map + pipeline)
- `work/.../export_card_art.py` (batch ILL exporter, incremental-safe)
- `work/.../card_art/*.png` (~3,091 card illustrations)
- `work/.../sample/` (APKs, libs, global-metadata.dat — IL2CPP dump possible later with Il2CppDumper if code-level work needed)

## Follow-ups

- Master data (`aladin` namespace FlatBuffers tables) for card-name/EN mapping — no public batch extractor yet.
- Audio `.acb/.awb` via vgmstream; ONNX battle AI at `Assets/Lettuce/_Data/Raw/Common/AI/battle.ort`.
- If game updates: re-pull index first; only new blobs need decryption (aladump rerun is cheap).

## English mapping addendum (same day)

- en_US locale bundle TextAssets are a custom `KVRF` (magic `KVRF`) KV format: FlatBuffers-style header + UTF-16LE `[u32 len][data]` records. Keys: `CARD_NAME_<n>`, `ATTACK_NAME/DESC`, `ABILITY_NAME/DESC`, `FLAVOR`, `ILLUSTRATOR`, `SERIES_NAME`. Dumped to `locale_en_US/*.bin`.
- `<n>` cannot be linked to asset ids offline (masterdata namespace is CDN-downloaded, absent on-device).
- Working bridge: flibustier/pokemon-tcg-pocket-database `cards.json` — `image` field IS the internal asset id. 3,091/3,091 art files matched with English names/sets/rarities (`build_english_mapping.py`).
- Gotchas: DB URL-encodes non-ASCII in `image` (`%E2%99%80`); export-time filenames can carry cp1252-mojibake (Nidoran ♀/♂, Zygarde ％) — repair via `.encode('cp1252').decode('utf-8')`.

## Render architecture addendum (same day)

- Cards are runtime-assembled 3D layer stacks, NOT flattened images (see `work/.../RENDER_ARCHITECTURE.md`).
- Per-card bundle = CardSettings MonoBehaviour (internal key + species) + L prefab/material/ILL texture + M prefab with per-language text-plate textures only (`_US_UT`…) + thumbnail. Art ships once (L), shared by both views.
- Shared library `Common/CardNew`: Parts/Base + Parts/Layer (Window_Image, Hologram/Metalic/Marble/Parallax) + Parts/Effect (KiraPuyo, Prism S/SSR, StackEffect per rarity) + Template settings (DesignSettings, 39 MaterialConditions, FontGroupConditions) + 132 shaders (Card_Illust, Card_Frame_Holo*, Card_Parallax_*, Card_Prism, Video_Immersive for immersive rares).
- Art clipping = Unity stencil buffers (InnerStencil/OuterStencil/IllustStencil GOs), not alpha masks.
- UR backgrounds are shared UzumakiPlate textures + separate mask textures; prism_ssr_C = chromatic sparkle sprite sheet.
- If code-level confirmation needed: Il2CppDumper on libil2cpp.so + global-metadata.dat (both already in `sample/`).
