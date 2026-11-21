#!/usr/bin/env python3
# BongoCat asset extractor (UnityPy)
#
# Pulls all bongo sprites + metadata from the game's sharedassets0.assets.
#
# Sprite naming convention (decoded from Assembly-CSharp.dll / Cat::SetSkin):
#   <Skin>Left        - arm-normal, cat facing viewer (bounce idle)  -> _catNormal
#   <Skin>LeftPunch   - left paw down (hit)                         -> _catLeft
#   <Skin>Right       - cat turned, arm-normal                       -> _catNormalFront
#   <Skin>RightPunch  - right paw down (hit)                        -> _catRightFront
# The skinless default uses "Cat" as <Skin>.
#
# Animation (decoded from Cat.cs / CatPatter.cs / CatRotator.cs IL):
#   - Tap flips _wasLeft; CatHitLeft swaps _catImage sprite to <Skin>LeftPunch for
#     _hitDuration sec, then back to <Skin>Left.
#   - CatHitRight swaps _catFront sprite to <Skin>RightPunch, then back to <Skin>Right.
#   - BounceSequence (CatBobbing toggle) DOTween-squishes _bobTransform scaleY 0.95->1
#     loops -1.
#   - CatPatter.PatSequence DOTween-squishes whole-transform scale on tap.

import os, re, sys, json
import UnityPy

GAME_ASSETS = r"C:\Program Files (x86)\Steam\steamapps\common\BongoCat\BongoCat_Data"
SRC = os.path.join(GAME_ASSETS, "sharedassets0.assets")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extracted")

def main():
    os.makedirs(OUT, exist_ok=True)
    env = UnityPy.load(SRC)

    sprites = {}   # name -> Sprite data
    tex = {}       # path_id -> Texture2D data (for manifest)
    for obj in env.objects:
        t = obj.type.name
        if t == "Sprite":
            try: d = obj.read()
            except Exception: continue
            sprites[d.m_Name] = d
        elif t == "Texture2D":
            try: tex[obj.path_id] = obj.read()
            except Exception: continue

    # Discover skins: every "<base>Left" with "<base>Right" + both Punch partners.
    base_re = re.compile(r"^(.+)Left$")
    skins = set()
    for name in sprites:
        m = base_re.match(name)
        if not m: continue
        base = m.group(1)
        if f"{base}Right" in sprites and f"{base}LeftPunch" in sprites and f"{base}RightPunch" in sprites:
            skins.add(base)
    # Ensure skinless default "Cat" is present even if naming differs.
    if not any(s == "Cat" for s in skins):
        skins.add("Cat")

    manifest = {"source": SRC, "skin_count": len(skins), "skins": [], "frames": {}}
    saved = 0
    for skin in sorted(skins):
        for framekey, suffix in [("left","Left"),("left_punch","LeftPunch"),
                                 ("right","Right"),("right_punch","RightPunch")]:
            name = skin + suffix
            d = sprites.get(name)
            if d is None: continue
            rel = os.path.join(skin, f"{framekey}.png")
            abspath = os.path.join(OUT, skin, f"{framekey}.png")
            os.makedirs(os.path.dirname(abspath), exist_ok=True)
            img = d.image
            if img is not None:
                img.save(abspath)
            manifest["frames"][name] = {
                "path": rel, "w": d.m_Rect.width, "h": d.m_Rect.height,
            }
            saved += 1
        manifest["skins"].append(skin)

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"skins={len(skins)} frames_saved={saved} -> {OUT}")

if __name__ == "__main__":
    main()
