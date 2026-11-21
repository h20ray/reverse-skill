<template>
  <!-- One interactive cat preview. body/front stacked in a SRC box, each frame
       positioned by the skin's real textureRect (game Body+BodyFront contract).
       Hover = continuous random left/right bongo loop; click = select this skin. -->
  <div
    class="cat-cell"
    :class="{ struck, selected }"
    :style="cellStyle"
    @pointerenter="enter"
    @pointerleave="leave"
    @pointerdown.prevent="select"
  >
    <div
      class="cat-box"
      :style="boxStyle"
      @pointerenter="enter"
      @pointerleave="leave"
      @pointerdown.prevent="select"
    >
      <img :src="url('left')" :style="bodyIdleStyle" class="layer body"
           :class="{ hidden: farHit }" alt="" loading="lazy" decoding="async">
      <img :src="url('left_punch')" :style="bodyPunchStyle" class="layer body punch"
           :class="{ hidden: !farHit }" alt="" loading="lazy" decoding="async">
      <img :src="url('right')" :style="frontIdleStyle" class="layer front"
           :class="{ hidden: nearHit }" alt="" loading="lazy" decoding="async">
      <img :src="url('right_punch')" :style="frontPunchStyle" class="layer front punch"
           :class="{ hidden: !nearHit }" alt="" loading="lazy" decoding="async">
    </div>
    <div class="cat-name" :style="{ color: color }">{{ name }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';

const SRC = 256;

const props = defineProps({
  name:     { type: String, required: true },   // asset name, e.g. 'Cat'
  frames:   { type: Object, required: true },   // {left,left_punch,right,right_punch} -> [x,y,w,h]
  color:    { type: String, default: '#B0B0B0' },
  size:     { type: Number, default: 120 },     // cell box px
  selected: { type: Boolean, default: false },  // this skin is the current navbar cat
});
const emit = defineEmits(['select']);

// Vite serves public/ at root -> /skins/<name>/left.png etc.
const url = (f) => `/skins/${props.name.replace(/\.+$/, '')}/${f}.png`;

// Same decode as BongoCat.vue: textureRect (Unity y-up) -> CSS % in the SRC box.
function frameStyle(f) {
  if (!f) return {};
  const [x, y, w, h] = f;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const dx = cx - SRC / 2;
  const dy = cy - SRC / 2;
  return {
    width:  (w / SRC * 100) + '%',
    height: (h / SRC * 100) + '%',
    left:   (50 + dx / SRC * 100) + '%',
    top:    (50 - dy / SRC * 100) + '%',
    transform: 'translate(-50%, -50%)',
  };
}

const struck = ref(false);
const hovering = ref(false);
const wasLeft = ref(false);   // which paw shows the strike frame (far=body / near=front)
let loopTimer = null;

// One bongo "beat": show a random paw strike, hold briefly, release, then
// schedule the next beat after a random gap while still hovering.
function playStep() {
  if (!hovering.value) return;
  struck.value = true;
  wasLeft.value = Math.random() < 0.5;   // random side each beat
  const hold = 70 + Math.random() * 80;  // random strike hold (ms)
  loopTimer = setTimeout(() => {
    struck.value = false;
    wasLeft.value = !wasLeft.value;
    if (hovering.value) {
      const gap = 60 + Math.random() * 160;  // random rest (ms)
      loopTimer = setTimeout(playStep, gap);
    }
  }, hold);
}

function enter() {
  if (hovering.value) return;
  hovering.value = true;
  playStep();
}
function leave() {
  hovering.value = false;
  if (loopTimer) { clearTimeout(loopTimer); loopTimer = null; }
  struck.value = false;
}

function select() {
  emit('select', props.name);
}

// farHit = strike the BODY (far) paw; nearHit = strike the FRONT (near) paw.
const farHit  = computed(() => struck.value && !wasLeft.value);
const nearHit = computed(() => struck.value &&  wasLeft.value);

const bodyIdleStyle   = computed(() => frameStyle(props.frames.left));
const bodyPunchStyle  = computed(() => frameStyle(props.frames.left_punch));
const frontIdleStyle  = computed(() => frameStyle(props.frames.right));
const frontPunchStyle = computed(() => frameStyle(props.frames.right_punch));

const boxStyle = computed(() => ({
  width: props.size + 'px',
  height: props.size + 'px',
}));
const cellStyle = computed(() => ({
  '--rk': props.color,
  width: (props.size + 16) + 'px',
}));

onBeforeUnmount(() => { if (loopTimer) clearTimeout(loopTimer); });
</script>

<style scoped>
.cat-cell{
  display:flex;flex-direction:column;align-items:center;gap:4px;
  padding:8px 6px;border-radius:14px;background:#1a1d24;
  border:1px solid #26282f;cursor:pointer;
  transition:border-color .15s ease, transform .15s ease;
  user-select:none;
}
.cat-cell:hover{border-color:var(--rk);transform:translateY(-2px);}
.cat-cell.selected{
  border-color:var(--rk);
  background:#242a35;
  box-shadow:0 0 0 2px var(--rk);
}
.cat-box{position:relative;flex:none;}
.cat-box .layer{position:absolute;pointer-events:none;}
.cat-box .layer.hidden{opacity:0;visibility:hidden;}
/* Draw order: body then front -> near paw on top. */
.cat-box .front{filter:drop-shadow(0 1px 1px rgba(0,0,0,.35));}
.cat-name{font-size:11px;line-height:1;text-align:center;color:#c8ccd2;
  max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
</style>

