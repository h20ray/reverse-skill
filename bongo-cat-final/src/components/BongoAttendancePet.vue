<template>
  <div
    class="relative flex flex-col items-center justify-center cursor-pointer select-none group"
    @click="handleTap"
  >
    <!-- Stage: Egg / Hatching -->
    <div
      v-if="isEggStage"
      class="flex flex-col items-center justify-center p-4 transition-transform duration-200 group-hover:scale-105"
    >
      <div class="relative w-32 h-32 flex items-center justify-center">
        <!-- Egg sprite or egg icon with pulsing halo -->
        <div class="w-24 h-28 bg-gradient-to-t from-amber-400 via-amber-200 to-amber-50 rounded-[50%/60%_60%_40%_40%] shadow-lg border-2 border-amber-300 flex items-center justify-center relative overflow-hidden animate-bounce">
          <div class="absolute top-3 left-4 w-6 h-8 bg-white/40 rounded-full blur-[1px]"></div>
          <span class="text-2xl select-none">✨</span>
        </div>
      </div>
      <span class="text-xs font-semibold text-amber-500 mt-2 uppercase tracking-wide">
        {{ eggStageLabel }}
      </span>
    </div>

    <!-- Stage: Hatched / Evolved Bongo Cat -->
    <div v-else class="relative flex flex-col items-center">
      <!-- Evolved Glow Aura for 30+ Streak -->
      <div
        v-if="isEvolved"
        class="absolute -inset-4 bg-gradient-to-r from-amber-500/20 via-primary/20 to-purple-500/20 rounded-full blur-xl animate-pulse pointer-events-none"
      />

      <BongoCat
        ref="bongoCatRef"
        :skin="skin"
        :frames="skinFrames"
        :hat="hat"
        :hat-frame="hatFrame"
        :emote="emote"
        :size="size"
        :bob="bob"
        :asset-base-path="assetBasePath"
        @tap="$emit('tap', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import BongoCat from './BongoCat.vue';
import { useBongoData } from '../composables/useBongoData.js';
import { PET_STAGES, DEFAULT_CAT_SIZE } from '../data/constants.js';

const props = defineProps({
  stage: {
    type: String,
    default: PET_STAGES.HATCHED,
  },
  currentStreak: {
    type: Number,
    default: 1,
  },
  outfits: {
    type: Object,
    default: () => ({
      skin: 'Cat',
      hat: null,
      emote: null,
    }),
  },
  size: {
    type: Number,
    default: DEFAULT_CAT_SIZE,
  },
  bob: {
    type: Boolean,
    default: true,
  },
  assetBasePath: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['tap']);

const bongoCatRef = ref(null);
const { findSkin, findAccessory } = useBongoData();

const isEggStage = computed(() => {
  return [PET_STAGES.EGG, PET_STAGES.HATCHING_1, PET_STAGES.HATCHING_2].includes(props.stage);
});

const isEvolved = computed(() => {
  return props.stage === PET_STAGES.EVOLVED || props.currentStreak >= 30;
});

const eggStageLabel = computed(() => {
  if (props.stage === PET_STAGES.HATCHING_1) return 'Incubating (Streak 1)';
  if (props.stage === PET_STAGES.HATCHING_2) return 'Cracking Soon (Streak 2)';
  return 'Mystery Egg (Streak 0)';
});

const skin = computed(() => props.outfits?.skin || 'Cat');
const hat = computed(() => props.outfits?.hat || null);
const emote = computed(() => props.outfits?.emote || null);

const currentSkinObj = computed(() => findSkin(skin.value));
const skinFrames = computed(() => currentSkinObj.value?.frames || {});

const currentHatObj = computed(() => (hat.value ? findAccessory(hat.value) : null));
const hatFrame = computed(() => currentHatObj.value?.frame || null);

function handleTap(e) {
  emit('tap', e);
  if (bongoCatRef.value) {
    bongoCatRef.value.triggerTap();
  }
}
</script>
