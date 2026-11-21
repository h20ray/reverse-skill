<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
    @click.self="$emit('update:open', false)"
  >
    <div class="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
            <Sparkles class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white leading-tight">Bongo Cat Wardrobe</h2>
            <p class="text-xs text-slate-400">Dress up your attendance streak companion</p>
          </div>
        </div>
        <button
          class="w-8 h-8 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 flex items-center justify-center transition-colors"
          @click="$emit('update:open', false)"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Main Body (Split layout: Preview Mirror on Left / Catalog on Right) -->
      <div class="flex-1 grid grid-cols-1 md:grid-cols-12 gap-0 overflow-hidden">
        <!-- Left: Live Preview Stage (5 Cols) -->
        <div class="md:col-span-5 p-6 bg-gradient-to-b from-slate-950/80 to-slate-900 border-b md:border-b-0 md:border-r border-slate-800 flex flex-col items-center justify-between">
          <div class="w-full flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Fitting Room</span>
            <span class="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase" :style="{ backgroundColor: activeRarityColor + '20', color: activeRarityColor }">
              {{ activeRarity }}
            </span>
          </div>

          <!-- Centered Interactive Cat -->
          <div class="my-6 flex flex-col items-center">
            <BongoCat
              :skin="tempOutfit.skin"
              :frames="tempSkinFrames"
              :hat="tempOutfit.hat"
              :hat-frame="tempHatFrame"
              :emote="tempOutfit.emote"
              :size="200"
              :bob="true"
              :asset-base-path="assetBasePath"
            />
            <div class="text-sm font-bold text-white mt-4">
              {{ tempOutfit.skin }}
              <span v-if="tempOutfit.hat" class="text-amber-400 text-xs font-normal ml-1">
                + {{ tempOutfit.hat }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">Click or tap to test bongo hits</p>
          </div>

          <!-- Reset / Unequip Actions -->
          <div class="w-full flex gap-2">
            <button
              v-if="tempOutfit.hat"
              class="flex-1 py-2 px-3 text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg hover:bg-amber-500/20 transition-colors"
              @click="tempOutfit.hat = null"
            >
              Remove Hat
            </button>
            <button
              v-if="tempOutfit.emote"
              class="flex-1 py-2 px-3 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition-colors"
              @click="tempOutfit.emote = null"
            >
              Remove Emote
            </button>
          </div>
        </div>

        <!-- Right: Catalog Tabs & Grids (7 Cols) -->
        <div class="md:col-span-7 flex flex-col h-full overflow-hidden bg-slate-900/40">
          <!-- Navigation Tabs -->
          <div class="flex border-b border-slate-800 bg-slate-950/30 px-4 pt-2 gap-2">
            <button
              class="px-4 py-2.5 text-xs font-bold transition-colors border-b-2"
              :class="activeTab === 'skins' ? 'border-primary text-primary' : 'border-transparent text-slate-400 hover:text-slate-200'"
              @click="activeTab = 'skins'"
            >
              Skins ({{ skins.length }})
            </button>
            <button
              class="px-4 py-2.5 text-xs font-bold transition-colors border-b-2"
              :class="activeTab === 'hats' ? 'border-amber-500 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'"
              @click="activeTab = 'hats'"
            >
              Hats & Accessories ({{ accessories.length }})
            </button>
            <button
              class="px-4 py-2.5 text-xs font-bold transition-colors border-b-2"
              :class="activeTab === 'emotes' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'"
              @click="activeTab = 'emotes'"
            >
              Emotes ({{ emotes.length }})
            </button>
          </div>

          <!-- Search Bar & Filter -->
          <div class="p-4 border-b border-slate-800 flex items-center gap-3">
            <div class="relative flex-1">
              <Search class="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search items..."
                class="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary"
              />
            </div>
            <select
              v-model="filterRarity"
              class="bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 py-1.5 px-3 focus:outline-none"
            >
              <option value="all">All Rarities</option>
              <option value="common">Common</option>
              <option value="uncommon">Uncommon</option>
              <option value="rare">Rare</option>
              <option value="epic">Epic</option>
              <option value="legendary">Legendary</option>
            </select>
          </div>

          <!-- Catalog Scroll Container -->
          <div class="flex-1 p-4 overflow-y-auto max-h-[480px]">
            <!-- Skins Grid -->
            <div v-if="activeTab === 'skins'" class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <CatGallery
                v-for="s in filteredSkins"
                :key="s.name"
                :name="s.name"
                :display-name="s.displayName"
                :frames="s.frames"
                :rarity="s.rarity"
                :color="s.qualityColor"
                :selected="tempOutfit.skin === s.name"
                :asset-base-path="assetBasePath"
                @select="selectSkin(s.name)"
              />
            </div>

            <!-- Hats Grid -->
            <div v-else-if="activeTab === 'hats'" class="grid grid-cols-3 sm:grid-cols-4 gap-3">
              <AccessoryGallery
                v-for="a in filteredAccessories"
                :key="a.name"
                :name="a.name"
                :display-name="a.displayName"
                :rarity="a.rarity"
                :color="a.qualityColor"
                :selected="tempOutfit.hat === a.name"
                :asset-base-path="assetBasePath"
                @select="selectHat(a.name)"
              />
            </div>

            <!-- Emotes Grid -->
            <div v-else-if="activeTab === 'emotes'" class="grid grid-cols-3 sm:grid-cols-4 gap-3">
              <EmoteGallery
                v-for="e in filteredEmotes"
                :key="e.name"
                :name="e.name"
                :display-name="e.displayName"
                :rarity="e.rarity"
                :color="e.qualityColor"
                :selected="tempOutfit.emote === e.name"
                :asset-base-path="assetBasePath"
                @select="selectEmote(e.name)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Action -->
      <div class="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-950/80">
        <span class="text-xs text-slate-400">Streak Level: Unlocks premium legendary items</span>
        <div class="flex gap-3">
          <button
            class="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            @click="$emit('update:open', false)"
          >
            Cancel
          </button>
          <button
            class="px-5 py-2 text-xs font-bold text-white bg-primary hover:bg-primary/90 rounded-lg shadow-lg shadow-primary/20 transition-all flex items-center gap-1.5"
            @click="saveOutfit"
          >
            <Check class="w-4 h-4" />
            Save Outfit
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { Sparkles, X, Search, Check } from 'lucide-vue-next';
import BongoCat from './BongoCat.vue';
import CatGallery from './CatGallery.vue';
import AccessoryGallery from './AccessoryGallery.vue';
import EmoteGallery from './EmoteGallery.vue';
import { useBongoData } from '../composables/useBongoData.js';
import { QUALITY_COLORS } from '../data/constants.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  currentOutfit: {
    type: Object,
    default: () => ({
      skin: 'Cat',
      hat: null,
      emote: null,
    }),
  },
  assetBasePath: { type: String, default: '' },
});

const emit = defineEmits(['update:open', 'save']);

const {
  skins,
  accessories,
  emotes,
  findSkin,
  findAccessory,
} = useBongoData();

const activeTab = ref('skins');
const searchQuery = ref('');
const filterRarity = ref('all');

const tempOutfit = ref({
  skin: props.currentOutfit?.skin || 'Cat',
  hat: props.currentOutfit?.hat || null,
  emote: props.currentOutfit?.emote || null,
});

watch(
  () => props.currentOutfit,
  (val) => {
    if (val) {
      tempOutfit.value = {
        skin: val.skin || 'Cat',
        hat: val.hat || null,
        emote: val.emote || null,
      };
    }
  },
  { deep: true, immediate: true }
);

const currentSkinObj = computed(() => findSkin(tempOutfit.value.skin));
const tempSkinFrames = computed(() => currentSkinObj.value?.frames || {});
const activeRarity = computed(() => currentSkinObj.value?.rarity || 'common');
const activeRarityColor = computed(() => QUALITY_COLORS[activeRarity.value] || QUALITY_COLORS.common);

const currentHatObj = computed(() => (tempOutfit.value.hat ? findAccessory(tempOutfit.value.hat) : null));
const tempHatFrame = computed(() => currentHatObj.value?.frame || null);

// Search & Filtered Lists
const filteredSkins = computed(() => {
  return skins.value.filter((s) => {
    const matchQuery = s.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       (s.displayName && s.displayName.toLowerCase().includes(searchQuery.value.toLowerCase()));
    const matchRarity = filterRarity.value === 'all' || s.rarity === filterRarity.value;
    return matchQuery && matchRarity;
  });
});

const filteredAccessories = computed(() => {
  return accessories.value.filter((a) => {
    const matchQuery = a.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       (a.displayName && a.displayName.toLowerCase().includes(searchQuery.value.toLowerCase()));
    const matchRarity = filterRarity.value === 'all' || a.rarity === filterRarity.value;
    return matchQuery && matchRarity;
  });
});

const filteredEmotes = computed(() => {
  return emotes.value.filter((e) => {
    const matchQuery = e.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                       (e.displayName && e.displayName.toLowerCase().includes(searchQuery.value.toLowerCase()));
    const matchRarity = filterRarity.value === 'all' || e.rarity === filterRarity.value;
    return matchQuery && matchRarity;
  });
});

function selectSkin(name) {
  tempOutfit.value.skin = name;
}

function selectHat(name) {
  tempOutfit.value.hat = tempOutfit.value.hat === name ? null : name;
}

function selectEmote(name) {
  tempOutfit.value.emote = tempOutfit.value.emote === name ? null : name;
}

function saveOutfit() {
  emit('save', { ...tempOutfit.value });
  emit('update:open', false);
}
</script>
