# Bongo Cat Asset Extraction & Build Tools

These standalone Python utilities allow extracting and reconstructing all Bongo Cat sprites and bounding box coordinates directly from the game's Unity assets if updates are ever needed.

---

## Prerequisites

- Python 3.10+
- `UnityPy` (`pip install UnityPy`)
- `Pillow` (`pip install Pillow`)

---

## 1. `extract_assets.py`

Extracts all Texture2D and Sprite assets from the game directory (`sharedassets0.assets`) and saves cropped PNG frames for:
- Skins: 213 skins $\times$ 4 frames (`left.png`, `left_punch.png`, `right.png`, `right_punch.png`)
- Hats / Accessories: 372 items
- Emotes: 106 items

### Usage:
```bash
python tools/extract_assets.py --game-dir "C:/Program Files (x86)/Steam/steamapps/common/BongoCat"
```

---

## 2. `build_manifest.py`

Reads Unity Sprite metadata from `sharedassets0.assets` and generates the frame coordinate mapping (`[x, y, w, h]` within `256 x 256` bounding box) for every skin and hat.

### Usage:
```bash
python tools/build_manifest.py --game-dir "C:/Program Files (x86)/Steam/steamapps/common/BongoCat"
```
