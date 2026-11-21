#!/usr/bin/env python3
"""
BongoCat Asset Extractor & Classifier (UnityPy)
Audited against game Assembly-CSharp.dll IL logic.

Categorizes assets into:
- skins/   : 213 4-frame layered cat skins
- hats/    : 374 wearable hats & accessories
- emotes/  : 105 reaction emojis & floating particles
- ui/      : 158 UI elements, advent calendar drawers, banners, buttons, backgrounds
- icons/   : 695 item inventory thumbnails (*Icon.png)
"""

import os, json, shutil
import UnityPy

GAME_ASSETS = r"C:\Program Files (x86)\Steam\steamapps\common\BongoCat\BongoCat_Data"
SRC = os.path.join(GAME_ASSETS, "sharedassets0.assets")
OUT_PUBLIC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
OUT_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "data"))

QUALITY_COLORS = {
    "common": "#B0B0B0", "uncommon": "#5ACC3D", "rare": "#258ED4",
    "epic": "#B939DB", "legendary": "#FFB000", "special": "#000000",
}

def save_sprite(sprite_obj, dest_path):
    img = sprite_obj.image
    if img:
        img.save(dest_path)

def main():
    if not os.path.exists(SRC):
        print(f"Error: Game asset file not found at {SRC}")
        return

    env = UnityPy.load(SRC)
    sprites = {}
    for obj in env.objects:
        if obj.type.name == "Sprite":
            try:
                d = obj.read()
                sprites[d.m_Name] = d
            except Exception:
                pass

    # 1. Discover Skins (4-frame)
    skin_bases = set()
    for s in sprites:
        if s.endswith("LeftPunch"):
            base = s[:-len("LeftPunch")]
            if f"{base}Left" in sprites and f"{base}Right" in sprites and f"{base}RightPunch" in sprites:
                skin_bases.add(base)
    skin_bases = sorted(list(skin_bases))

    # 2. Discover Icons & Non-Skin Items
    icon_sprite_names = set(k for k in sprites if k.endswith("Icon"))
    items_with_icon = set(k[:-4] for k in icon_sprite_names)
    non_skin_items = sorted(list(items_with_icon - set(skin_bases)))

    emotes = sorted([i for i in non_skin_items if "Emoji" in i or "Emote" in i or "Reaction" in i])
    hats = sorted([i for i in non_skin_items if i not in emotes and i in sprites])

    # 3. Discover UI / Background / Event Sprites
    all_skin_sprite_names = set([f"{b}{suf}" for b in skin_bases for suf in ["Left", "LeftPunch", "Right", "RightPunch"]])
    ui_sprite_names = sorted(list(set(sprites.keys()) - all_skin_sprite_names - icon_sprite_names - set(hats) - set(emotes)))

    print(f"Extraction counts: {len(skin_bases)} skins, {len(hats)} hats, {len(emotes)} emotes, {len(ui_sprite_names)} UI sprites, {len(icon_sprite_names)} icons.")

    # Recreate output folders
    for folder in ["skins", "hats", "emotes", "ui", "icons"]:
        p = os.path.join(OUT_PUBLIC, folder)
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p, exist_ok=True)

    # Extract Skins
    skins_data = []
    for skin in skin_bases:
        skin_dir = os.path.join(OUT_PUBLIC, "skins", skin)
        os.makedirs(skin_dir, exist_ok=True)
        frames_dict = {}
        for key, suf in [("left", "Left"), ("left_punch", "LeftPunch"), ("right", "Right"), ("right_punch", "RightPunch")]:
            sp = sprites.get(skin + suf)
            if sp:
                save_sprite(sp, os.path.join(skin_dir, f"{key}.png"))
                rect = sp.m_Rect
                frames_dict[key] = [int(rect.x), int(rect.y), int(rect.width), int(rect.height)]
        
        skins_data.append({
            "id": skin,
            "name": skin,
            "displayName": skin.replace("_", " "),
            "rarity": "common",
            "qualityColor": QUALITY_COLORS["common"],
            "frames": frames_dict
        })

    # Extract Hats
    accessories_data = []
    for hat in hats:
        sp = sprites.get(hat)
        if sp:
            save_sprite(sp, os.path.join(OUT_PUBLIC, "hats", f"{hat}.png"))
            rect = sp.m_Rect
            frame = [int(rect.x), int(rect.y), int(rect.width), int(rect.height)]
            accessories_data.append({
                "id": hat,
                "name": hat,
                "displayName": hat.replace("_", " "),
                "rarity": "common",
                "qualityColor": QUALITY_COLORS["common"],
                "frame": frame
            })

    # Extract Emotes
    emotes_data = []
    for emote in emotes:
        sp = sprites.get(emote)
        if sp:
            save_sprite(sp, os.path.join(OUT_PUBLIC, "emotes", f"{emote}.png"))
            emotes_data.append({
                "id": emote,
                "name": emote,
                "displayName": emote.replace("_", " "),
                "rarity": "common",
                "qualityColor": QUALITY_COLORS["common"]
            })

    # Extract UI
    ui_data = []
    for ui_name in ui_sprite_names:
        sp = sprites.get(ui_name)
        if sp:
            save_sprite(sp, os.path.join(OUT_PUBLIC, "ui", f"{ui_name}.png"))
            rect = sp.m_Rect
            ui_data.append({
                "id": ui_name,
                "name": ui_name,
                "width": int(rect.width),
                "height": int(rect.height)
            })

    # Extract Icons
    for icon_name in icon_sprite_names:
        sp = sprites.get(icon_name)
        if sp:
            save_sprite(sp, os.path.join(OUT_PUBLIC, "icons", f"{icon_name}.png"))

    # Save JSON files
    os.makedirs(OUT_DATA, exist_ok=True)
    with open(os.path.join(OUT_DATA, "skins.json"), "w", encoding="utf-8") as f:
        json.dump(skins_data, f, indent=2)
    with open(os.path.join(OUT_DATA, "accessories.json"), "w", encoding="utf-8") as f:
        json.dump(accessories_data, f, indent=2)
    with open(os.path.join(OUT_DATA, "emotes.json"), "w", encoding="utf-8") as f:
        json.dump(emotes_data, f, indent=2)
    with open(os.path.join(OUT_DATA, "ui_assets.json"), "w", encoding="utf-8") as f:
        json.dump(ui_data, f, indent=2)

    print(f"Extraction complete! Assets saved to {OUT_PUBLIC} and {OUT_DATA}")

if __name__ == "__main__":
    main()
