# 02 — Vue 3 Component API Reference

Comprehensive reference for all components in `src/components/`.

---

## 1. `<BongoCat />`

The standalone core 4-layer sprite renderer.

### Props

| Prop | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skin` | `String` | `'Cat'` | Skin asset name (e.g. `'Cat'`, `'Demon'`, `'Alien'`). |
| `frames` | `Object` | **Required** | Object containing `[x,y,w,h]` for `left`, `left_punch`, `right`, `right_punch`. |
| `hat` | `String` | `null` | Equipped accessory/hat name (e.g. `'BlackWizardHat'`, `'AngelHalo'`). |
| `hatFrame` | `Array` | `null` | `[x,y,w,h]` coordinate array for hat positioning. |
| `emote` | `String` | `null` | Particle sprite to spawn on tap (e.g. `'FaceHeartSmileEmoji'`). |
| `size` | `Number` | `180` | Render box diameter in pixels. |
| `bob` | `Boolean` | `true` | Enables/disables idle squash bobbing. |
| `hitDuration` | `Number` | `160` | Duration to hold punch frame before returning to idle (ms). |
| `interactive` | `Boolean` | `true` | Enables tap pointer handling & particle bursts. |
| `assetBasePath` | `String` | `''` | Custom prefix for CDN or Laravel public path (e.g. `'/images/bongo-cat'`). |

### Events

| Event | Payload | Description |
| :--- | :--- | :--- |
| `@tap` | `PointerEvent` | Emitted whenever the cat is clicked/tapped. |
| `@punch` | `{ side: 'left' \| 'right' }` | Emitted on paw strike with the active side. |

### Exposed Methods (via Template Ref)

```javascript
const catRef = ref(null);

// Trigger a single paw tap programmatically
catRef.value.triggerTap();

// Spawn a custom particle burst
catRef.value.spawnParticle({ type: 'emoji', src: '/emotes/AnimalCatEmoji.png' });
```

---

## 2. `<BongoAttendancePet />`

Drop-in replacement for Niskala's `AttendancePetAnimation.vue`. Automatically handles streak stage transitions (`egg`, `hatching_1`, `hatching_2`, `hatched`, `evolved`).

### Props

| Prop | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `stage` | `String` | `'hatched'` | Current streak stage (`'egg'`, `'hatching_1'`, `'hatching_2'`, `'hatched'`, `'evolved'`). |
| `currentStreak` | `Number` | `1` | Total attendance streak days. |
| `outfits` | `Object` | `{ skin: 'Cat', hat: null, emote: null }` | Current equipped wardrobe items. |
| `size` | `Number` | `180` | Cat size in px. |
| `bob` | `Boolean` | `true` | Idle bobbing toggle. |
| `assetBasePath` | `String` | `''` | CDN or Laravel asset prefix. |

### Events

| Event | Payload | Description |
| :--- | :--- | :--- |
| `@tap` | `PointerEvent` | Emitted when tapped (used by parent to grant EXP and trigger dialogue). |

---

## 3. `<BongoWardrobeModal />`

Full Dressing Room / Wardrobe modal with split-screen fitting mirror and catalog tabs.

### Props

| Prop | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `open` (v-model) | `Boolean` | `false` | Modal open/close state. |
| `currentOutfit` | `Object` | `{ skin: 'Cat', hat: null, emote: null }` | Current outfit to preview/edit. |
| `assetBasePath` | `String` | `''` | Base path for assets. |

### Events

| Event | Payload | Description |
| :--- | :--- | :--- |
| `@update:open` | `Boolean` | Emitted when modal closes. |
| `@save` | `{ skin, hat, emote }` | Emitted when employee clicks **Save Outfit**. |

---

## 4. `<BongoNavWidget />`

Miniature Bongo Cat companion (40px–48px) designed for the **right slot** or right floating corner of the mobile navigation bar.

### Props

| Prop | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skin` | `String` | `'Cat'` | Equipped skin. |
| `hat` | `String` | `null` | Equipped hat. |
| `label` | `String` | `'Streak Pet'` | Optional text label below sprite. |
| `showLabel` | `Boolean` | `false` | Whether to display text label. |
| `assetBasePath` | `String` | `''` | Base path for assets. |

### Events

| Event | Payload | Description |
| :--- | :--- | :--- |
| `@click` / `@tap` | `PointerEvent` | Emitted on tap to open Wardrobe or navigate to `/my-day`. |
