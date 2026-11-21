# BongoCat — Asset Extraction & Animation Analysis

STATUS: assets extracted + animation logic decoded from IL. Ready to port to web.

## Where the game lives
`C:\Program Files (x86)\Steam\steamapps\common\BongoCat\`
- `BongoCat_Data\Managed\Assembly-CSharp.dll` — all game logic (Mono / .NET, Unity IL2CPP-IL, Mono.Cecil-readable)
- `BongoCat_Data\sharedassets0.assets` — **the bongo sprites** (2185 Texture2D + 2184 Sprite)
- `BongoCat_Data\StreamingAssets\aa\*` — Addressables bundles (mostly localization .bundle), NOT the cat animation
- `BongoCat_Data\resources.assets` / `sharedassets0.assets.resS` (458MB) — serialized blob; the resS is the raw texture stream backing the sprites

Note: the local `bongo-cats/patcher/` repo folder is a **key-counter booster** ("bongo" key auto-down-multiplier), unrelated to the animation. Ignore it for porting.

## Asset extraction (DONE)
`bongo-cats/extract_assets.py` (UnityPy 1.25.3, Python 3.14) → `bongo-cats/extracted/`
- **213 skins** × **4 frames** = **852 PNGs** + `manifest.json`
- Repo folder `bongo-cats/extracted/` holds them, e.g. `Cat/left.png`, `Cat/right.png`, …

### Sprite naming convention (from `Cat.SetSkin` IL)
```
<Skin>Left        → _catNormal        (idle, facing camera, arm up — bounce frame)
<Skin>LeftPunch   → _catLeft          (hit — left paw strikes down)
<Skin>Right       → _catNormalFront   (idle, cat turned/arm-rest)
<Skin>RightPunch  → _catRightFront    (hit — right paw strikes down)
```
Skinless default = `<Skin>` = `Cat`  (i.e. `CatLeft`, `CatLeftPunch`, `CatRight`, `CatRightPunch`).
`MemoryImageCache` loads sprites by name; `SetSkin(SteamItemRuntime)` builds `Base + "Left"`, `+ "LeftPunch"`, `+ "Right"`, `+ "RightPunch"`.

## THE ANIMATION (decoded `Cat.cs`, `CatPatter.cs`, `CatRotator.cs`)

### 1. Bongo hit — `Cat.Tap(int)` (called on input)
Each tap does a **two-drum alternating punch**:
```
Tap():
  if _wasLeft (last hit was left side) →
    _catFront.sprite = _catRightFront        // <Skin>RightPunch
    StartCoroutine(CatHitRight())            // wait _hitDuration, restore to _catNormalFront
  else →
    _catImage.sprite = _catLeft              // <Skin>LeftPunch
    StartCoroutine(CatHitLeft())             // wait _hitDuration, restore to _catNormal
  _wasLeft = !_wasLeft                       // alternate sides
```
CatHitLeft/Right coroutines (from `MoveNext` IL):
```
ResumeRendering()
yield WaitForSeconds(_hitDuration)
  _catImage.sprite = _catNormal   // back to idle
  _routineLeft = null
TryPauseRendering()
```
So the core cycle is a **2-frame alternation**: idle sprite ↔ punch sprite, side toggling each tap.

### 2. Bobbing — `Cat.BounceSequence()` (idle bob, toggleable `CatBobbing` setting)

### 2.1 Hats & emotes
- **Hats**: `Cat.SetHat` (from `SetHat`/`GetHatSprite` IL) sets `_hatImage.sprite` to the single
  `<Hat>` sprite (e.g. `BongoCatHat`, `AngelHalo`), overlaid on the cat. Hats are 1 frame, not
  per-punch — the game just sits the hat on the cat's head. Layered `_hatImage` is above `_catImage`
  and `_catFront`.
- **Emotes**: `EmoteSpawner.SpawnEmoteParticle(Sprite, EmoteBehaviorOverride, Transform, Action)`
  floats the item's `Icon` sprite up from the cat on tap (heart particles in `CatPatter.SpawnHearts`).
  `EmoteBehaviorOverride` enum drives float/spin/fade behavior.
DOTween sequence on `_bobTransform.scaleY`:
```
seq = DOTween.Sequence()
  .Append(bob.DOScaleY(0.95, 0.75))    // squash down
  .Append(bob.DOScaleY(1.00, 0.75))    // back up
  .SetLoops(-1)                        // infinite
  .SetLink(gameObject)
```
`GetBobbingAnimationStart()` seeks the sequence to a random offset so multiplayer cats aren't in sync.

### 3. Pat — `CatPatter.PatSequence()` (tap of the WHOLE cat w/ heart particles)
```
ScaledVector(1,0.85): _squishedScale       // x1 y0.85
ScaledVector(0.9,1.1): _expandedScale      // x0.9 y1.1
baseScale = ScaledVector(1,1)
sequence:
  Append(DOScale(_squishedScale, 0.2).Ease(OutQuad))     // squash
  AppendCallback(→ SpawnHearts(amount) if amount>0)
  Append(DOScale(_expandedScale, 0.2)
  Append(DOScale(baseScale, 0.3)
  OnComplete(...)
```
`ScaledVector` multiplies by `CatScaleSetting.GetRealScaleFactor()` unless multiplayer.

### 4. Rotation — `CatRotator` (press default binding `R`)
`TurnBy(dir)`: `_rotationState = (_rotationState + dir + 4) % 4`; rotates `CatTransform` via
`DOLocalRotate(Vector3(0,0,dir*90), 0.2, RotateMode)`; 4 states = 0/90/180/270°.
Also clamps multi-cat layout `KeepRotatedCatOnScreen`.

### Side/facing
`FlipVisuals` flips `_catTransform.localScale.x` (scale.x=-1) to mirror the cat; `Cat.UpdateFlip`
does the same on the hat image. So "right/front" is the same art mirrored, and the game picks
`_catNormalFront`/`_catRightFront` for the front-facing state.

## FRAME DIRECTORY (what each extracted PNG is)

| folder / file | pose |
|---|---|
| `<Skin>/left.png` | idle, arm-up, camera-facing |
| `<Skin>/left_punch.png` | left paw strike |
| `<Skin>/right.png` | idle, arm-rest / turned |
| `<Skin>/right_punch.png` | right paw strike |

## GROUPING / RARITY (decoded from SteamJsonParser, CatInventory, Cat.SetSkin)

Assets are grouped into **categories** (`itemslot`) and **rarities** (`quality`). Both are
assigned by STEAM INVENTORY item tags (`quality:common`, `itemslot:hat`), fetched per-account —
**rarity is NOT shipped in the game files.** What IS local is the color map + all the art.

### Categories
| class | item slot | asset shape | extracted to |
|---|---|---|---|
| **skin** | `skin` | 4-frame cat (<Skin>Left/LeftPunch/Right/RightPunch) | `skins/<Skin>/{left,left_punch,right,right_punch}.png` (213) |
| **hat** | `hat` | 1 sprite overlay drawn on cat | `hats/<Hat>.png` (143) |
| **emote** | `emote` | particle sprite that floats up (item `Icon`) | `emotes/<Emote>.png` (336) |
| **skin icon** | (skin) | per-skin thumbnail | `quint_icons/<Skin>.png` (213) |

Default skinless skin = `Cat` (folder `skins/Cat/`). A pre-baked sheet `Cat_atlas.png` (2×2)
ships for the default skin.

### Rarity → color (decoded from `SteamItemBasic.GetQualityColor` IL; hex = same values)
```
common    #B0B0B0  (gray)      uncommon  #5ACC3D  (green)
rare      #258ED4  (blue)      epic      #B939DB  (purple)
legendary #FFB000  (gold)      special   #000000
```
Rarer items also get `itemslot` metatagging: `featured` flag on some, and `*Cosmetic` vs `*Emote`
enum split. For a web port, assign each item a quality client-side (e.g. from a small JSON you
author), using these hexes for rarity borders/badges.

### Total content
- 213 skins (852 frames) + 143 hats + 336 emotes + 213 icons = **1544 sprites** extracted.

## PORT TO WEB — recommended approach
This is a Unity uGUI game; the animation is trivially replicable in plain HTML/CSS/JS (or a JS
sprite engine). The game logic to reimplement is tiny:

## 5. REVERSE-ENGINEERED WEB PORT SPECIFICATION & ARCHITECTURE

### 5.1 Coordinate Space & Desk Baseline
* **Shared Atlas Space**: All sprites are drawn inside a $256 \times 256$ source texture coordinate system with center pivot $(128, 128)$ or $(0.5, 0.5)$.
* **Fixed Desk Baseline**: Across all 213 skins, the cat's resting desk/table line (flat belly line) is drawn at **$y = 59.0$** (Unity y-up texture coordinates, corresponding to $256 - 59 = 197\text{px}$ from top, or $76.95\%$ from the top of the box).
* **Responsive Bottom Alignment**:
  ```css
  /* Pull down by 59/256 of cat size so the desk line sits flush against the navbar top */
  bottom: calc(var(--nav-h, 64px) + env(safe-area-inset-bottom, 0px) - (var(--cat-size, 180px) * 59 / 256));
  ```
* **Hanging Accessories**: Skins with long kimono sleeves (`YukiOnna`, $y=35.0$) or icicles (`FreezingCold`, $y=47.0$) naturally drape *over* the navbar because `.bongo-wrap` is set to `z-index: 40` (above navbar `z-index: 30`).

---

### 5.2 Layer Stacking & Z-Depth Order
Directly decoded from Unity's `BobTransform` GameObject hierarchy across all game scenes:
```
GameObject "BobTransform"
 ├── 1. "Body"      (Z=0: Left idle & LeftPunch strike - background base)
 ├── 2. "Hat"       (Z=1: Worn hat / accessory - middle layer)
 └── 3. "BodyFront" (Z=2: Right idle & RightPunch strike - foreground near paw)
```
* **Paw Priority**: The cat's right / near paw (`BodyFront`) rests and strikes **in front of the equipped accessory** (e.g. over scarves, hats, and belly elements).

---

### 5.3 Hat / Accessory RectTransform Positioning
In Unity's `Cat` prefab:
```
GameObject "Body"      -> pos = (-6.3,  9.8), size = (128, 128), pivot = (0.5, 0.5)
GameObject "BodyFront" -> pos = (-6.3,  9.8), size = (128, 128), pivot = (0.5, 0.5)
GameObject "Hat"       -> pos = (10.0, 45.0), size = (128, 128), pivot = (0.5, 0.5)
```
* **Relative Head Offset**:
  * $\Delta X = \frac{10.0 - (-6.3)}{128} \times 100\% = \mathbf{+12.734\%}$ (Shifted right)
  * $\Delta Y = \frac{45.0 - 9.8}{128} \times 100\% = \mathbf{+27.500\%}$ (Shifted upwards towards head)
* **Hat CSS Formula**:
  ```javascript
  function hatFrameStyle(f) {
    const cx = f[0] + f[2] / 2;
    const cy = f[1] + f[3] / 2;
    const dx = cx - 128;
    const dy = cy - 128;
    const left = 50 + (dx / 256 * 100) + 12.734;
    const top  = 50 - (dy / 256 * 100) - 27.500;
    return {
      width:  (f[2] / 256 * 100) + '%',
      height: (f[3] / 256 * 100) + '%',
      left:   left + '%',
      top:    top + '%',
      transform: 'translate(-50%, -50%)',
    };
  }
  ```

---

### 5.4 Zero-Glitch 60fps Pre-rendered Layer Architecture
* Rather than swapping `src` and dynamic `style` on click (which causes image decoding latency and 1-frame geometry stretching), **all 4 frame layers + hat layer** are pre-rendered into the DOM with permanent `style` geometry:
  * Layer 1: Body Idle (`left.png`)
  * Layer 2: Body Punch (`left_punch.png`)
  * Layer 3: Hat Overlay (`<Hat>.png`)
  * Layer 4: Front Idle (`right.png`)
  * Layer 5: Front Punch (`right_punch.png`)
* Striking toggles `.layer.hidden` (`opacity: 0; visibility: hidden;`), enabling instantaneous 60fps GPU compositor layer switching.

---

### 5.5 Animations & Particle Physics
* **Bobbing Squash-and-Stretch (`Cat.BounceSequence`)**:
  * Origin pinned to desk baseline: `transform-origin: 50% calc(100% * (1 - 59 / 256))` ($76.95\%$ from top).
  * The bottom stays $100\%$ stationary on the navbar while only the head squashes down (`scaleY(0.95)`) and bounces back.
* **Pat Pulse (`CatPatter.PatSequence`)**:
  * Interactive click squish: `scale(1.06, 0.92)` pulse (220ms).
* **Floating Emote Particles (`EmoteSpawner.SpawnEmoteParticle`)**:
  * Floating upward curve (`translateY(-90px)`), random drift $\pm 20\text{px}$, rotation tilt $\pm 15^\circ$, scale in and fade out ($1.1\text{s}$).
* **Chat Speech Bubbles**:
  * Periodic cute speech popups with pop animation and speech pointer.

---

### 5.6 Official Steam Item Content Breakdown
Audited strictly against `inventorymsgcache/BEDAF4EE132800E385A8703F383F6767D6D700FE.cachedmsg`:
1. **Skins (`itemslot:skin`)**: 213 total (Common: 32, Uncommon: 25, Rare: 48, Epic: 43, Legendary: 65).
2. **Accessories / Hats (`itemslot:hat`)**: 372 total (Common: 97, Uncommon: 73, Rare: 51, Epic: 39, Legendary: 112).
3. **Emotes (`itemslot:emote`)**: 106 total (Common: 35, Uncommon: 30, Rare: 24, Epic: 9, Legendary: 8).

---

## Reusable commands
```bash
# Re-extract skins
python bongo-cats/extract_assets.py

# Run Vite dev server
npm run dev -- --port 5173
```

