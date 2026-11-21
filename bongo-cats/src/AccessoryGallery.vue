<template>
  <div
    class="acc-cell"
    :class="{ selected }"
    :style="cellStyle"
    @pointerdown.prevent="toggle"
  >
    <div class="acc-box" :style="boxStyle">
      <img
        :src="`/hats/${name}.png`"
        class="acc-layer"
        alt=""
        loading="lazy"
        decoding="async"
      >
    </div>
    <div class="acc-name" :style="{ color: color }">{{ displayName || name }}</div>
    <div v-if="selected" class="equipped-badge">Equipped</div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  name:        { type: String, required: true },
  displayName: { type: String, default: '' },
  frame:       { type: Array, required: true },
  color:       { type: String, default: '#B0B0B0' },
  size:        { type: Number, default: 110 },
  selected:    { type: Boolean, default: false },
});

const emit = defineEmits(['select']);

const boxStyle = computed(() => ({
  width: props.size + 'px',
  height: props.size + 'px',
}));


const cellStyle = computed(() => ({
  '--rk': props.color,
  width: (props.size + 16) + 'px',
}));

function toggle() {
  emit('select', props.name);
}
</script>

<style scoped>
.acc-cell{
  display:flex;flex-direction:column;align-items:center;gap:4px;
  padding:8px 6px;border-radius:14px;background:#1a1d24;
  border:1px solid #26282f;cursor:pointer;
  transition:border-color .15s ease, transform .15s ease;
  user-select:none;
  position:relative;
}
.acc-cell:hover{border-color:var(--rk);transform:translateY(-2px);}
.acc-cell.selected{
  border-color:var(--rk);
  background:#242a35;
  box-shadow:0 0 0 2px var(--rk);
}
.acc-box{
  position:relative;
  flex:none;
  display:flex;
  align-items:center;
  justify-content:center;
}
.acc-layer{
  max-width:85%;
  max-height:85%;
  object-fit:contain;
  pointer-events:none;
  filter:drop-shadow(0 2px 6px rgba(0,0,0,.45));
}
.acc-name{
  font-size:11px;line-height:1;text-align:center;
  max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.equipped-badge{
  font-size:9px;font-weight:700;text-transform:uppercase;
  background:var(--rk);color:#0f1116;padding:2px 6px;
  border-radius:6px;letter-spacing:0.5px;
}
</style>

