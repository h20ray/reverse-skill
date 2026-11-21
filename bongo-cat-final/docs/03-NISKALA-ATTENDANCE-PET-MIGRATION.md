# 03 — Niskala Attendance Streak Pet Migration Guide

This step-by-step guide walks through migrating the placeholder Attendance Streak Pet in [`C:\GitHub\niskala`](file:///c:/GitHub/niskala) to the **Bongo Cat 4-Layer Sprite Engine & Wardrobe System**.

---

## Step 1: Copy Assets to Niskala Public Directory

Copy the static sprite folders from `bongo-cat-final/public/` to Niskala's public asset directory:

```bash
# Target: C:\GitHub\niskala\public\images\bongo-cat\
mkdir -p C:\GitHub\niskala\public\images\bongo-cat
cp -r bongo-cat-final/public/* C:\GitHub\niskala\public\images\bongo-cat/
```

Assets will now be accessible in Niskala under:
- `/images/bongo-cat/skins/{skinName}/left.png`
- `/images/bongo-cat/hats/{hatName}.png`
- `/images/bongo-cat/emotes/{emoteName}.png`

---

## Step 2: Copy Reusable Components & Composables

Copy the following files from `bongo-cat-final/src/` into Niskala's attendance module:

| Source File | Destination in Niskala |
| :--- | :--- |
| `src/components/BongoCat.vue` | `resources/js/modules/admin/components/attendance/pet/BongoCat.vue` |
| `src/components/BongoAttendancePet.vue` | `resources/js/modules/admin/components/attendance/pet/BongoAttendancePet.vue` |
| `src/components/BongoWardrobeModal.vue` | `resources/js/modules/admin/components/attendance/pet/BongoWardrobeModal.vue` |
| `src/components/CatGallery.vue` | `resources/js/modules/admin/components/attendance/pet/CatGallery.vue` |
| `src/components/AccessoryGallery.vue` | `resources/js/modules/admin/components/attendance/pet/AccessoryGallery.vue` |
| `src/components/EmoteGallery.vue` | `resources/js/modules/admin/components/attendance/pet/EmoteGallery.vue` |
| `src/components/BongoNavWidget.vue` | `resources/js/components/layouts/backend/BongoNavWidget.vue` |
| `src/composables/useBongoCat.js` | `resources/js/modules/admin/components/attendance/pet/composables/useBongoCat.js` |
| `src/composables/useBongoData.js` | `resources/js/modules/admin/components/attendance/pet/composables/useBongoData.js` |
| `src/data/*` | `resources/js/modules/admin/components/attendance/pet/data/` |
| `src/assets/bongo-cat.css` | `resources/js/modules/admin/components/attendance/pet/assets/bongo-cat.css` |

---

## Step 3: Update `AttendancePetCard.vue` (Attendance "My Day" Screen)

In [`resources/js/modules/admin/components/attendance/pet/AttendancePetCard.vue`](file:///c:/GitHub/niskala/resources/js/modules/admin/components/attendance/pet/AttendancePetCard.vue):

1. **Import `BongoAttendancePet.vue` and `BongoWardrobeModal.vue`**:
```vue
<script setup>
import { ref, computed } from "vue";
import BongoAttendancePet from "./BongoAttendancePet.vue";
import BongoWardrobeModal from "./BongoWardrobeModal.vue";
import { Sparkles, Pencil, Flame, Trophy } from "lucide-vue-next";

// ... existing props and composables
const showWardrobeModal = ref(false);

async function handleOutfitSave(outfit) {
  // Sync outfit with backend API
  await axios.post("admin/attendance/pet/outfit", { outfit });
  pet.value.outfits = outfit;
}
</script>
```

2. **Replace the Pet Animation Container in the template**:
```vue
<!-- Interactive Bongo Cat Pet Animation -->
<div class="relative z-10 flex flex-col items-center justify-center my-1">
  <BongoAttendancePet
    :stage="pet.stage"
    :current-streak="pet.current_streak"
    :outfits="pet.outfits"
    :size="180"
    asset-base-path="/images/bongo-cat"
    @tap="handlePetTap"
  />

  <!-- EXP Toast / Tap Hint -->
  <div class="min-h-[22px] flex items-center justify-center mt-1">
    <span
      v-if="toastExp"
      class="text-xs font-bold text-emerald-600 dark:text-emerald-400 animate-bounce"
    >
      {{ $t("attendance.streak_pet_exp_toast", { count: toastExp }) }} ✨
    </span>
    <span
      v-else
      class="text-[11px] text-muted-foreground/80 cursor-pointer hover:text-primary transition-colors flex items-center gap-1"
      @click="handlePetTap"
    >
      <Sparkles class="h-3 w-3 text-amber-500" />
      {{ $t("attendance.streak_pet_tap_hint") }}
    </span>
  </div>
</div>

<!-- Wardrobe Dressing Room Modal -->
<BongoWardrobeModal
  v-model:open="showWardrobeModal"
  :current-outfit="pet.outfits"
  asset-base-path="/images/bongo-cat"
  @save="handleOutfitSave"
/>
```

3. **Wire up the Edit/Pencil button next to the Pet Name**:
```vue
<Button
  variant="ghost"
  size="icon"
  class="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-muted"
  title="Wardrobe Dressing Room"
  @click="showWardrobeModal = true"
>
  <Pencil class="h-3.5 w-3.5" />
</Button>
```

---

## Step 4: Mobile Navigation Bar Integration

> [!IMPORTANT]
> **Key UX Decision**:
> - **Center Attendance Button** ([`AttendanceMobileButton.vue`](file:///c:/GitHub/niskala/resources/js/components/layouts/backend/AttendanceMobileButton.vue)): **Preserved 100% as the work timer / clock-in status button** (`7:28` worked today).
> - **Bongo Cat Companion**: Positioned on the **right side** of the mobile navigation bar in [`BackendMobileNavBarComponent.vue`](file:///c:/GitHub/niskala/resources/js/components/layouts/backend/BackendMobileNavBarComponent.vue).

### In `BackendMobileNavBarComponent.vue`:

You can either attach the mini Bongo Cat as a badge on the Profile slot or add a dedicated right-hand companion widget:

```vue
<!-- Slot 4 / Slot 5: Profile or Dedicated Pet Companion on the Right -->
<div
  class="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-lg py-1 transition-colors text-muted-foreground hover:text-primary cursor-pointer"
  title="Attendance Pet Streak"
  @click="$router.push({ name: 'admin.attendance.self' })"
>
  <BongoNavWidget
    :skin="authStore.userStreakPet?.outfits?.skin || 'Cat'"
    :hat="authStore.userStreakPet?.outfits?.hat"
    asset-base-path="/images/bongo-cat"
  />
  <span class="text-[9px] font-bold text-amber-500">
    🔥 {{ authStore.userStreakPet?.current_streak || 0 }}d
  </span>
</div>
```

---

## Step 5: Verify & Run

1. Run Vite dev server in Niskala:
   ```bash
   npm run dev
   ```
2. Open `/admin/attendance/my-day` (or `/my-day`).
3. Click Bongo Cat to test paw punches and floating EXP particles.
4. Click the Pencil icon to open the Wardrobe Modal, customize the cat, and verify live equipment changes.
