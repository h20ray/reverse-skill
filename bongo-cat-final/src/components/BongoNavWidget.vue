<template>
  <div
    class="relative flex flex-col items-center justify-center cursor-pointer select-none group"
    :title="title"
    @click="handleTap"
  >
    <!-- Mini floating cat sprite -->
    <div class="relative w-10 h-10 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
      <BongoCat
        ref="catRef"
        :skin="skin"
        :frames="skinFrames"
        :hat="hat"
        :hat-frame="hatFrame"
        :size="48"
        :bob="true"
        :asset-base-path="assetBasePath"
      />
    </div>

    <!-- Optional mini label -->
    <span v-if="showLabel" class="text-[10px] font-medium text-slate-400 group-hover:text-primary transition-colors">
      {{ label }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import BongoCat from './BongoCat.vue';
import { useBongoData } from '../composables/useBongoData.js';

const props = defineProps({
  skin: { type: String, default: 'Cat' },
  hat: { type: String, default: null },
  label: { type: String, default: 'Streak Pet' },
  showLabel: { type: Boolean, default: false },
  title: { type: String, default: 'My Attendance Bongo Cat' },
  assetBasePath: { type: String, default: '' },
});

const emit = defineEmits(['click', 'tap']);

const catRef = ref(null);
const { findSkin, findAccessory } = useBongoData();

const currentSkinObj = computed(() => findSkin(props.skin));
const skinFrames = computed(() => currentSkinObj.value?.frames || {});

const currentHatObj = computed(() => (props.hat ? findAccessory(props.hat) : null));
const hatFrame = computed(() => currentHatObj.value?.frame || null);

function handleTap(e) {
  emit('tap', e);
  emit('click', e);
  if (catRef.value) {
    catRef.value.triggerTap();
  }
}
</script>
