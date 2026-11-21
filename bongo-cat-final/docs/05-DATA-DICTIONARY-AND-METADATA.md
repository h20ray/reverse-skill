# 05 — Data Dictionary & Asset Categorization

All assets have been audited against the game's Unity assembly and classified into 5 distinct categories:

---

## 1. Asset Directory Breakdown

| Directory | Count | Description |
| :--- | :--- | :--- |
| `public/skins/` | **213 folders** | 4 frames each (`left.png`, `left_punch.png`, `right.png`, `right_punch.png`). Base cat models. |
| `public/hats/` | **374 files** | Genuine wearable headwear, accessories, masks, wigs, and costumes. |
| `public/emotes/` | **105 files** | Emoji reaction icons that float upward as particles during tap interactions. |
| `public/ui/` | **158 files** | System UI, Advent Calendar drawers (`AdventDrawer_Closed-0`..`-5`), banners, buttons, backgrounds, frames. |
| `public/icons/` | **695 files** | Inventory & shop thumbnail icons (`*Icon.png`) for every wearable item and skin. |

---

## 2. Quality Rarity System

Decoded from Steam Item Rarity tiers:

| Tier | Quality Key | Hex Color | Visual Style |
| :--- | :--- | :--- | :--- |
| **Common** | `common` | `#B0B0B0` | Subtle grey border |
| **Uncommon** | `uncommon` | `#5ACC3D` | Vibrant green glow |
| **Rare** | `rare` | `#258ED4` | Electric blue glow |
| **Epic** | `epic` | `#B939DB` | Purple mystical glow |
| **Legendary** | `legendary` | `#FFB000` | Golden radiant glow |
| **Special** | `special` | `#000000` | Obsidian / Void border |

---

## 3. Metadata Schemas (`src/data/`)

### `skins.json` (213 items)
```json
[
  {
    "id": "Cat",
    "name": "Cat",
    "displayName": "Cat",
    "rarity": "common",
    "qualityColor": "#B0B0B0",
    "frames": {
      "left": [25, 23, 107, 107],
      "left_punch": [25, 23, 107, 107],
      "right": [124, 23, 107, 107],
      "right_punch": [124, 23, 107, 107]
    }
  }
]
```

### `accessories.json` (374 items)
```json
[
  {
    "id": "BlackWizardHat",
    "name": "BlackWizardHat",
    "displayName": "Black Wizard Hat",
    "rarity": "epic",
    "qualityColor": "#B939DB",
    "frame": [68, 140, 120, 85]
  }
]
```

### `emotes.json` (105 items)
```json
[
  {
    "id": "FaceHeartSmileEmoji",
    "name": "FaceHeartSmileEmoji",
    "displayName": "Face Heart Smile Emoji",
    "rarity": "common",
    "qualityColor": "#B0B0B0"
  }
]
```

### `ui_assets.json` (158 items)
```json
[
  {
    "id": "AdventCalendar_Background",
    "name": "AdventCalendar_Background",
    "width": 1920,
    "height": 1080
  },
  {
    "id": "AdventDrawer_Closed-0",
    "name": "AdventDrawer_Closed-0",
    "width": 128,
    "height": 128
  }
]
```
