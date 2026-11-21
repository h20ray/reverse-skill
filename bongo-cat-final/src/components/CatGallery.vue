<template>
  <div
    class="relative flex flex-col items-center justify-center p-2 rounded-xl border bg-slate-900/60 hover:bg-slate-800/80 transition-all cursor-pointer select-none group"
    :class="[
      selected ? 'ring-2 ring-primary border-primary bg-primary/10' : 'border-slate-800 hover:border-slate-700',
    ]"
    :style="{ borderColor: selected ? color : undefined }"
    @pointerenter="startHoverLoop"
    @pointerleave="stopHoverLoop"
    @click="$emit('select', name)"
  >
    <!-- Live Preview Box -->
    <div class="relative w-24 h-24 sm:w-28 sm:h-28 flex items-center justify-center">
      <!-- 4 layers -->
      <img
        :src="getSkinUrl('left')"
        :style="bodyIdleStyle"
        class="absolute pointer-events-none"
        :class="{ hidden: farHit }"
        alt=""
        loading="lazy"
        decoding="async"
      />
      <img
        :src="getSkinUrl('left_punch')"
        :style="bodyPunchStyle"
        class="absolute pointer-events-none"
        :class="{ hidden: !farHit }"
        alt=""
        loading="lazy"
        decoding="async"
      />
      <img
        :src="getSkinUrl('right')"
        :style="frontIdleStyle"
        class="absolute pointer-events-none"
        :class="{ hidden: nearHit }"
        alt=""
        loading="lazy"
        decoding="async"
      />
      <img
        :src="getSkinUrl('right_punch')"
        :style="frontPunchStyle"
        class="absolute pointer-events-none"
        :class="{ hidden: !nearHit }"
        alt=""
        loading="lazy"
        decoding="async"
      />
    </div>

    <!-- Cat Name & Rarity -->
    <div class="w-full text-center mt-1">
      <div class="text-xs font-semibold truncate text-slate-200" :style="{ color: selected ? color : undefined }">
        {{ displayName || name }}
      </div>
      <div class="text-[10px] font-bold uppercase tracking-wider opacity-75" :style="{ color }">
        {{ rarity }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onBeforeUnmount } from 'vue';
import { useBongoCat } from '../composables/useBongoCat.js';

const props = defineProps({
  name: { type: String, required: true },
  displayName: { type: String, default: '' },
  frames: { type: Object, required: true },
  rarity: { type: String, default: 'common' },
  color: { type: String, default: '#B0B0B0' },
  selected: { type: Boolean, default: false },
  assetBasePath: { type: String, default: '' },
});

defineEmits(['select']);

const {
  farHit,
  nearHit,
  computeFrameStyle,
  triggerTap,
  cleanup,
} = useBongoCat({ hitDuration: 140 });

let hoverInterval = null;

function startHoverLoop() {
  triggerTap();
  if (hoverInterval) clearInterval(hoverInterval);
  hoverInterval = setInterval(() => {
    triggerTap();
  }, 220);
}

function stopHoverLoop() {
  if (hoverInterval) {
    clearInterval(hoverInterval);
    hoverInterval = null;
  }
}

onBeforeUnmount(() => {
  stopHoverLoop();
  cleanup();
});

function cleanSkinName(name) {
  return (name || 'Cat').replace(/\.+$/, '');
}

function getSkinUrl(frame) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/skins/${cleanSkinName(props.name)}/${frame}.png`;
}

const bodyIdleStyle = computed(() => computeFrameStyle(props.frames?.left));
const bodyPunchStyle = computed(() => computeFrameStyle(props.frames?.left_punch));
const frontIdleStyle = computed(() => computeFrameStyle(props.frames?.right));
const frontPunchStyle = computed(() => computeFrameStyle(props.frames?.right_punch));
</script>
