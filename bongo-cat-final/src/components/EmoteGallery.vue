<template>
  <div
    class="relative flex flex-col items-center justify-center p-2 rounded-xl border bg-slate-900/60 hover:bg-slate-800/80 transition-all cursor-pointer select-none group"
    :class="[
      selected ? 'ring-2 ring-emerald-500 border-emerald-500 bg-emerald-500/10' : 'border-slate-800 hover:border-slate-700',
    ]"
    :style="{ borderColor: selected ? color : undefined }"
    @click="$emit('select', name)"
  >
    <!-- Emote Image -->
    <div class="relative w-16 h-16 sm:w-20 sm:h-20 flex items-center justify-center">
      <img
        :src="getEmoteUrl(name)"
        class="max-w-full max-h-full object-contain filter drop-shadow group-hover:scale-115 transition-transform"
        alt=""
        loading="lazy"
        decoding="async"
      />
    </div>

    <!-- Emote Name & Rarity -->
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

function getEmoteUrl(emoteName) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/emotes/${emoteName}.png`;
}
</script>
