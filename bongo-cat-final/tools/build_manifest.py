#!/usr/bin/env python3
# BongoCat asset extractor + category classifier (UnityPy)
#
# Content classes (decoded from Assembly-CSharp IL):
#   skin  — layered cat, 4 frames each (<Skin>Left / LeftPunch / Right / RightPunch),
#           default skinless = "Cat". Laid out by Cat.SetSkin.
#   hat   — single overlay sprite drawn on the cat (item class "hat"), e.g. CheetahHat,
#           AngelHalo. Laid out by Cat.SetHat -> _hatImage. Single frame.
#   emote — particle sprite that floats up on tap (item class "emote"); the item's
#           Icon is the art itself (EmoteSpawner uses SteamItemRuntime.Icon).
#   skin_icon — per-skin Icon thumbnails.
#
# Rarity/quality (common/uncommon/rare/epic/legendary) is assigned per-account by
# Steam inventory item tags (quality:common, itemslot:hat, ...) — NOT shipped in the
# game data. The color map below is decoded from SteamItemBasic IL.
#
# Usage:  python build_manifest.py     (writes into extracted/ + groups/spritesheets)

import os, re, json, collections
import UnityPy

GAME_ASSETS = r"C:\Program Files (x86)\Steam\steamapps\common\BongoCat\BongoCat_Data"
SRC = os.path.join(GAME_ASSETS, "sharedassets0.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "extracted")

QUALITY_COLORS = {
    "common": "#B0B0B0", "uncommon": "#5ACC3D", "rare": "#258ED4",
    "epic": "#B939DB", "legendary": "#FFB000", "special": "#000000",
}
HAT_RE = re.compile(r"Hat|Cap|Crown|Halo|Earmuff|Head|Glasses|Bow|Veil|Bandana|Wizard|Beret|Turban|Headband|Wings|Antenna|Hair|Horn|Ear|Wig|Circlet|Visor|Sunglass|Scarf|Necklace|Poncho|Cape|Fez|Hood", re.I)

def save_sprite(d, rel_dir, fname):
    img = d.image
    if img is None:
        return False
    rel = os.path.join(rel_dir, fname)
    abspath = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(abspath), exist_ok=True)
    img.save(abspath)
    return rel

def main():
    os.makedirs(OUT, exist_ok=True)
    env = UnityPy.load(SRC)
    sprites = {}
    for obj in env.objects:
        if obj.type.name == "Sprite":
            try: d = obj.read()
            except Exception: continue
            sprites[d.m_Name] = d
    names = set(sprites)

    # ---- classify skins (4-frame sets) ----
    skins = set()
    for n in names:
        if n.endswith("LeftPunch"):
            b = n[:-len("LeftPunch")]
            if f"{b}Left" in names and f"{b}Right" in names and f"{b}RightPunch" in names:
                skins.add(b)

    # ---- hats: name (not Icon) that isn't a skin, matched by HAT_RE ----
    icon_bases = set(n[:-len("Icon")] for n in names if n.endswith("Icon"))
    hats = sorted(b for b in icon_bases if b not in skins and HAT_RE.search(b))
    emotes = sorted(b for b in icon_bases if b not in skins and not HAT_RE.search(b))
    skin_icons = sorted(b for b in icon_bases if b in skins)

    # ---- write category dirs ----
    skin_files, hat_files, emote_files, icon_files = {}, {}, {}, {}
    counts = collections.Counter()

    for skin in skins:
        frames = {}
        for key, suf in [("left","Left"),("left_punch","LeftPunch"),("right","Right"),("right_punch","RightPunch")]:
            d = sprites.get(skin + suf)
            if d is not None:
                frames[key] = save_sprite(d, os.path.join("skins", skin), f"{key}.png")
                counts["skin_frames"] += 1
        skin_files[skin] = frames

    for h in hats:
        d = sprites.get(h)
        if d is not None:
            hat_files[h] = save_sprite(d, "hats", f"{h}.png"); counts["hats"] += 1
    for e in emotes:
        d = sprites.get(e)
        if d is not None:
            emote_files[e] = save_sprite(d, "emotes", f"{e}.png"); counts["emotes"] += 1
    for si in skin_icons:
        d = sprites.get(si + "Icon")
        if d is not None:
            icon_files[si] = save_sprite(d, "quint_icons", f"{si}.png"); counts["skin_icons"] += 1

    manifest = {
        "source": SRC,
        "quality_colors": QUALITY_COLORS,
        "quality_is_steam_sided": True,
        "note": "Rarity is assigned per-account by Steam inventory item tags; not shipped on disk. Colors decoded from SteamItemBasic IL.",
        "counts": dict(counts),
        "skins": {k: {"frames": v, "icon": icon_files.get(k)} for k, v in skin_files.items()},
        "hats": hat_files,
        "emotes": emote_files,
        "skin_icons": icon_files,
    }
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("skins", len(skins), "hats", len(hats), "emotes", len(emotes), "skin_icons", len(skin_icons))
    print("saved:", dict(counts), "->", OUT)

if __name__ == "__main__":
    main()
