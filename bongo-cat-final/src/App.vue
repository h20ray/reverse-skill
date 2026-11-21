<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans pb-28 md:pb-8">
    <!-- Top Header -->
    <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40 px-4 sm:px-8 py-3.5 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-amber-500 flex items-center justify-center font-black text-slate-950 shadow-md shadow-amber-500/20">
          🐱
        </div>
        <div>
          <h1 class="text-sm sm:text-base font-bold text-white leading-tight">
            Niskala Streak Pet — Bongo Cat Handover Package
          </h1>
          <p class="text-[11px] text-slate-400">Vue 3 + Vuetify/Tailwind + Laravel Integration Engine</p>
        </div>
      </div>

      <!-- Mode Selector Tabs -->
      <div class="flex items-center bg-slate-950 border border-slate-800 p-1 rounded-xl gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
          :class="currentTab === tab.id ? 'bg-primary text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'"
          @click="currentTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
    </header>

    <!-- Main Content Stage -->
    <main class="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6">
      <!-- TAB 1: Niskala Attendance "My Day" Simulation -->
      <div v-if="currentTab === 'my-day'" class="max-w-xl mx-auto space-y-4">
        <!-- Page Title -->
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-white">My Day / Attendance</h2>
            <p class="text-xs text-slate-400">Simulation of <code class="text-amber-400">/admin/attendance/my-day</code> in Niskala</p>
          </div>
          <button
            class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
            @click="isWardrobeOpen = true"
          >
            <Sparkles class="w-3.5 h-3.5 text-amber-400" />
            Open Wardrobe
          </button>
        </div>

        <!-- Hero Attendance Clock Card -->
        <div class="bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center justify-between">
          <div>
            <div class="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              Currently Clocked In
            </div>
            <div class="text-2xl sm:text-3xl font-extrabold text-white mt-1">
              07:28:42 <span class="text-xs font-normal text-slate-400">worked today</span>
            </div>
            <div class="text-xs text-slate-400 mt-0.5">Shift: Morning Duty (08:00 - 17:00)</div>
          </div>
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-xl">
            ✓
          </div>
        </div>

        <!-- Niskala Attendance Pet Card (Simulated exact component) -->
        <div class="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 p-5 shadow-xl">
          <!-- Background glow decoration -->
          <div class="pointer-events-none absolute -top-12 -right-12 w-44 h-44 rounded-full bg-primary/10 blur-2xl"></div>
          <div class="pointer-events-none absolute -bottom-12 -left-12 w-44 h-44 rounded-full bg-amber-500/10 blur-2xl"></div>

          <!-- Header: Pet Name, Rarity & Streak Flame -->
          <div class="relative z-10 flex items-center justify-between gap-3 mb-2">
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-base font-bold truncate text-white">
                {{ pet.pet_name }}
              </span>
              <button
                class="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
                title="Change Outfit / Wardrobe"
                @click="isWardrobeOpen = true"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <span class="text-[10px] font-bold uppercase tracking-wider py-0.5 px-2 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Lv. {{ pet.level }} {{ pet.stage }}
              </span>
            </div>

            <!-- Streak Flame Badge -->
            <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold text-xs shadow-sm">
              <Flame class="w-4 h-4 fill-amber-500 text-amber-500 animate-pulse" />
              <span>{{ pet.current_streak }} Days Streak</span>
            </div>
          </div>

          <!-- Dialogue Speech Bubble -->
          <div class="relative z-10 my-2 bg-slate-950/60 border border-slate-800/80 rounded-xl px-3.5 py-2 text-xs text-slate-300 flex items-center gap-2">
            <span class="text-base">💬</span>
            <span class="italic font-medium">"{{ pet.dialogue }}"</span>
          </div>

          <!-- Interactive Bongo Cat Pet Animation Component -->
          <div class="relative z-10 flex flex-col items-center justify-center my-3">
            <BongoAttendancePet
              :stage="pet.stage"
              :current-streak="pet.current_streak"
              :outfits="pet.outfits"
              :size="180"
              :bob="true"
              @tap="handlePetTap"
            />

            <!-- Tap hint / Exp floating toast -->
            <div class="min-h-[22px] flex items-center justify-center mt-2">
              <span
                v-if="lastExpGained"
                class="text-xs font-bold text-emerald-400 animate-bounce flex items-center gap-1"
              >
                ✨ +{{ lastExpGained }} EXP Gained!
              </span>
              <span
                v-else
                class="text-[11px] text-slate-400 hover:text-amber-400 cursor-pointer transition-colors flex items-center gap-1"
                @click="handlePetTap"
              >
                <Sparkles class="w-3 h-3 text-amber-400" />
                Tap Bongo Cat to play & gain daily EXP
              </span>
            </div>
          </div>

          <!-- Level & EXP Progress Bar -->
          <div class="relative z-10 mt-3 pt-3 border-t border-slate-800/80">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="font-bold text-slate-200 flex items-center gap-1.5">
                <Trophy class="w-3.5 h-3.5 text-amber-400" />
                Level {{ pet.level }}
              </span>
              <span class="text-slate-400 text-[11px] font-medium">
                {{ pet.total_exp }} / {{ pet.exp_next_level }} EXP ({{ expPercentage }}%)
              </span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-amber-500 via-emerald-500 to-primary transition-all duration-500 rounded-full"
                :style="{ width: `${expPercentage}%` }"
              />
            </div>
          </div>
        </div>

        <!-- Testing Controls Box -->
        <div class="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-xs space-y-3">
          <div class="font-bold text-slate-300">Live Stage & Streak Switcher:</div>
          <div class="flex flex-wrap gap-2">
            <button
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              @click="setStage('egg', 0)"
            >
              Egg Stage (0 Streak)
            </button>
            <button
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              @click="setStage('hatching_1', 1)"
            >
              Hatching 1 (1 Streak)
            </button>
            <button
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              @click="setStage('hatching_2', 2)"
            >
              Hatching 2 (2 Streak)
            </button>
            <button
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              @click="setStage('hatched', 12)"
            >
              Hatched Bongo Cat (12 Streak)
            </button>
            <button
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              @click="setStage('evolved', 45)"
            >
              Evolved Aura (45 Streak)
            </button>
          </div>
        </div>
      </div>

      <!-- TAB 2: Full Wardrobe Browser -->
      <div v-else-if="currentTab === 'wardrobe'" class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold text-white">Full Asset Catalog</h2>
            <p class="text-xs text-slate-400">
              Browse all 213 extracted skins, 372 hats/accessories, and 106 emotes
            </p>
          </div>
          <button
            class="px-4 py-2 rounded-xl bg-primary hover:bg-primary/90 font-bold text-xs text-white shadow-lg shadow-primary/20 transition-all flex items-center gap-1.5"
            @click="isWardrobeOpen = true"
          >
            <Sparkles class="w-4 h-4" />
            Open Dressing Room Modal
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
          <CatGallery
            v-for="s in previewSkins"
            :key="s.name"
            :name="s.name"
            :display-name="s.displayName"
            :frames="s.frames"
            :rarity="s.rarity"
            :color="s.qualityColor"
            :selected="pet.outfits.skin === s.name"
            @select="onSkinSelect(s.name)"
          />
        </div>
      </div>

      <!-- TAB 3: Mobile Nav Preview -->
      <div v-else-if="currentTab === 'nav'" class="max-w-md mx-auto space-y-6 pt-4 text-center">
        <div class="space-y-1">
          <h2 class="text-xl font-bold text-white">5-Column Mobile Navigation Bar</h2>
          <p class="text-xs text-slate-400">
            Center attendance clock button preserved. Bongo Cat positioned as companion widget on the right.
          </p>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl text-left space-y-4">
          <div class="flex items-center gap-3">
            <div class="w-3 h-3 rounded-full bg-emerald-400"></div>
            <span class="text-xs font-bold text-slate-300">Mobile Navigation Breakdown</span>
          </div>
          <ul class="text-xs text-slate-400 space-y-2 list-disc pl-4">
            <li><strong class="text-slate-200">Slot 1 (Left):</strong> Dashboard Home (<code class="text-amber-400">/admin/dashboard</code>)</li>
            <li><strong class="text-slate-200">Slot 2:</strong> POS Terminal (<code class="text-amber-400">/admin/pos</code>)</li>
            <li><strong class="text-emerald-400">Slot 3 (CENTER):</strong> Clock-in / Work Timer (<code class="text-amber-400">7:28</code> worked today) with animated pulse ring</li>
            <li><strong class="text-slate-200">Slot 4:</strong> Notification Center (<code class="text-amber-400">/admin/notifications</code>)</li>
            <li><strong class="text-amber-400">Slot 5 (RIGHT):</strong> Bongo Cat Streak Pet Widget (<code class="text-amber-400">🔥 12d</code>) with tap reaction and direct link to Wardrobe</li>
          </ul>
        </div>
      </div>
    </main>

    <!-- Wardrobe Modal -->
    <BongoWardrobeModal
      v-model:open="isWardrobeOpen"
      :current-outfit="pet.outfits"
      @save="onOutfitSave"
    />

    <!-- Bottom Mobile Navigation Bar Component -->
    <NiskalaMobileNavBarDemo
      :work-time="'7:28'"
      :streak="pet.current_streak"
      :skin="pet.outfits.skin"
      :hat="pet.outfits.hat"
      @open-attendance="currentTab = 'my-day'"
      @open-wardrobe="isWardrobeOpen = true"
      @cat-tap="handlePetTap"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Sparkles, Pencil, Flame, Trophy } from 'lucide-vue-next';
import BongoAttendancePet from './components/BongoAttendancePet.vue';
import BongoWardrobeModal from './components/BongoWardrobeModal.vue';
import CatGallery from './components/CatGallery.vue';
import NiskalaMobileNavBarDemo from './components/NiskalaMobileNavBarDemo.vue';
import { useBongoStreakPet } from './composables/useBongoStreakPet.js';
import { useBongoData } from './composables/useBongoData.js';

const tabs = [
  { id: 'my-day', label: '1. My Day Attendance Screen' },
  { id: 'wardrobe', label: '2. Wardrobe & Catalog' },
  { id: 'nav', label: '3. Mobile Navbar' },
];
const currentTab = ref('my-day');
const isWardrobeOpen = ref(false);

const {
  pet,
  lastExpGained,
  interactPet,
  setSkin,
  setHat,
  setEmote,
} = useBongoStreakPet();

const { skins } = useBongoData();
const previewSkins = computed(() => skins.value.slice(0, 18));

const expPercentage = computed(() => {
  if (!pet.value.exp_next_level) return 0;
  return Math.min(100, Math.round((pet.value.total_exp / pet.value.exp_next_level) * 100));
});

function handlePetTap() {
  interactPet();
}

function onSkinSelect(name) {
  setSkin(name);
}

function onOutfitSave(newOutfit) {
  pet.value.outfits = { ...newOutfit };
}

function setStage(stageName, streak) {
  pet.value.stage = stageName;
  pet.value.current_streak = streak;
}
</script>

<style>
/* Base Tailwind & Component Palette */
:root {
  --primary: #3b82f6;
}
.bg-primary {
  background-color: var(--primary);
}
.text-primary {
  color: var(--primary);
}
.border-primary {
  border-color: var(--primary);
}
.ring-primary {
  --tw-ring-color: var(--primary);
}
</style>
