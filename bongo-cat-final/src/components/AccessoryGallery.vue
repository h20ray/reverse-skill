<template>
  <div
    class="relative flex flex-col items-center justify-center p-2 rounded-xl border bg-slate-900/60 hover:bg-slate-800/80 transition-all cursor-pointer select-none group"
    :class="[
      selected ? 'ring-2 ring-amber-500 border-amber-500 bg-amber-500/10' : 'border-slate-800 hover:border-slate-700',
    ]"
    :style="{ borderColor: selected ? color : undefined }"
    @click="$emit('select', name)"
  >
    <!-- Hat Image -->
    <div class="relative w-20 h-20 sm:w-24 sm:h-24 flex items-center justify-center">
      <img
        :src="getHatUrl(name)"
        class="max-w-full max-h-full object-contain filter drop-shadow group-hover:scale-110 transition-transform"
        alt=""
        loading="lazy"
        decoding="async"
      />
    </div>

    <!-- Hat Name & Rarity -->
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
const props = defineProps({
  name: { type: String, required: true },
  displayName: { type: String, default: '' },
  rarity: { type: String, default: 'common' },
  color: { type: String, default: '#B0B0B0' },
  selected: { type: Boolean, default: false },
  assetBasePath: { type: String, default: '' },
});

defineEmits(['select']);

function getHatUrl(hatName) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/hats/${hatName}.png`;
}
</script>
