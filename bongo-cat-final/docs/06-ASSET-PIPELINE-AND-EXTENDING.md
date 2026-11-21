# 06 — Asset Pipeline & Extending Custom Assets

This guide covers how to add custom skins or hats, and how to use the automated extraction scripts in `tools/`.

---

## 1. Adding a Custom Skin Manually

To add a new skin (e.g. `CompanyMascot`):

1. **Create the asset folder**:
   ```text
   public/skins/CompanyMascot/
   ├── left.png          # Idle Body + Left Paw Rest
   ├── left_punch.png    # Left Paw Hit Down
   ├── right.png         # Idle Face + Right Paw Rest
   └── right_punch.png   # Right Paw Hit Down
   ```
2. **Add entry to `src/data/skins.json`**:
   ```json
   {
     "id": "CompanyMascot",
     "name": "CompanyMascot",
     "displayName": "Company Mascot",
     "rarity": "legendary",
     "qualityColor": "#FFB000",
     "frames": {
       "left": [25, 23, 107, 107],
       "left_punch": [25, 23, 107, 107],
       "right": [124, 23, 107, 107],
       "right_punch": [124, 23, 107, 107]
     }
   }
   ```

---

## 2. Adding a Custom Hat / Accessory

1. Place the PNG file in `public/hats/CompanyCap.png` (transparent background, normalized inside `256 x 256` reference box).
2. Add entry to `src/data/accessories.json`:
   ```json
   {
     "id": "CompanyCap",
     "name": "CompanyCap",
     "displayName": "Company Cap",
     "rarity": "rare",
     "qualityColor": "#258ED4",
     "frame": [68, 140, 120, 85]
   }
   ```

---

## 3. Unity Asset Extraction Pipeline (`tools/`)

The `tools/` folder contains the Python extraction pipeline built with `UnityPy`:
- `tools/extract_assets.py`: Reads `BongoCat_Data/sharedassets0.assets` and dumps cropped PNGs for skins, hats, and emotes.
- `tools/build_manifest.py`: Extracts texture rect coordinates directly from the Unity serialized data structures and produces the frame JSON files.

See `tools/README.md` for full Python usage instructions.
