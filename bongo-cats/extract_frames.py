#!/usr/bin/env python3
# Emit per-skin textureRect (x,y,w,h) for the 4 frames, decoded from Sprite.rD,
# so each skin's frames position exactly like the game's Body/BodyFront stacking.
import os, json, UnityPy

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\BongoCat\BongoCat_Data"
SRC = os.path.join(GAME, "sharedassets0.assets")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "skin-frames.json")

env = UnityPy.load(SRC)
sprites = {}
for obj in env.objects:
    if obj.type.name == "Sprite":
        try:
            d = obj.read()
        except Exception:
            continue
        sprites[d.m_Name] = d

# Build set of skins = any name ending LeftPunch whose siblings exist
names = set(sprites)
skins = set()
for n in names:
    if n.endswith("LeftPunch"):
        b = n[:-len("LeftPunch")]
        if f"{b}Left" in names and f"{b}Right" in names and f"{b}RightPunch" in names:
            skins.add(b)

SUFFIX = {"left": "Left", "left_punch": "LeftPunch", "right": "Right", "right_punch": "RightPunch"}
result = {}
for skin in sorted(skins):
    frames = {}
    for key, suf in SUFFIX.items():
        d = sprites.get(skin + suf)
        if d is None:
            continue
        # m_RD.textureRect = (x, y, width, height) in texture space (Unity y-up).
        # This is the art's real position/size inside the shared 256x256 source rect.
        tr = getattr(d.m_RD, "textureRect", None)
        if tr is None:
            continue
        frames[key] = [round(float(tr.x), 1), round(float(tr.y), 1),
                       round(float(tr.width), 1), round(float(tr.height), 1)]
    if len(frames) == 4:
        result[skin] = frames

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
print("skins", len(result), "->", OUT)
