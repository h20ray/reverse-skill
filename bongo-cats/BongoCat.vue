<template>
  <div class="bongo-wrap" :style="wrapStyle">
    <!-- Floating Emotes & Chat Bubbles Container -->
    <div class="particles-container">
      <div
        v-for="p in particles"
        :key="p.id"
        class="particle"
        :class="p.type"
        :style="p.style"
      >
        <img v-if="p.type === 'emoji'" :src="p.src" class="particle-img" alt="">
        <div v-else-if="p.type === 'chat'" class="chat-bubble">
          <span class="chat-text">{{ p.text }}</span>
        </div>
      </div>
    </div>

    <div
      class="bongo"
      :class="{ bob, struck: punchActive, patted: isPatted }"
      @pointerdown.prevent="handleTap"
    >
      <!-- 
        Render all 4 dedicated frame layers instead of swapping src/style dynamically:
        1. Body Idle (left.png)
        2. Body Punch (left_punch.png)
        3. Front Idle (right.png)
        4. Front Punch (right_punch.png)
      -->
      <!-- 1. BODY Layer (Cat base) -->
      <img
        :src="url('left')"
        :style="bodyIdleStyle"
        class="layer body"
        :class="{ hidden: farHit }"
        alt=""
        decoding="async"
      >
      <img
        :src="url('left_punch')"
        :style="bodyPunchStyle"
        class="layer body punch"
        :class="{ hidden: !farHit }"
        alt=""
        decoding="async"
      >

      <!-- 2. HAT / ACCESSORY Layer (Worn on head/body, between Body and BodyFront) -->
      <img
        v-if="hat && hatStyle"
        :src="`/hats/${hat}.png`"
        :style="hatStyle"
        class="layer hat"
        alt=""
        decoding="async"
      >

      <!-- 3. BODYFRONT Layer (Near / right paw - topmost layer in front of hat & body) -->
      <img
        :src="url('right')"
        :style="frontIdleStyle"
        class="layer front"
        :class="{ hidden: nearHit }"
        alt=""
        decoding="async"
      >
      <img
        :src="url('right_punch')"
        :style="frontPunchStyle"
        class="layer front punch"
        :class="{ hidden: !nearHit }"
        alt=""
        decoding="async"
      >
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';

const SRC = 256;               // shared source rect size

const props = defineProps({
  navH:        { type: Number, default: 64 },   // existing bottom nav height (px)
  catSize:     { type: Number, default: 180 },  // must match CSS --cat-size
  skin:        { type: String, default: 'Cat' },
  frames:      { type: Object, required: true },// {left,left_punch,right,right_punch}->[x,y,w,h]
  hat:         { type: String, default: null }, // equipped hat/accessory name
  hatFrame:    { type: Array, default: null },  // [x,y,w,h] for hat
  emote:       { type: String, default: null }, // equipped emote particle name
  color:       { type: String, default: '#B0B0B0' },
  bob:         { type: Boolean, default: false },// idle squash bob (game CatBobbing)
  hitDuration: { type: Number, default: 160 },  // punch frame hold, ~game _hitDuration (ms)
});

// textureRect -> CSS in the shared box (%). Center-anchored.
function frameStyle(f) {
  if (!f) return {};
  const cx = f[0] + f[2] / 2;          // art center x in texture
  const cy = f[1] + f[3] / 2;          // art center y in texture (y from bottom)
  const dx = cx - SRC / 2;             // px right of source center
  const dy = cy - SRC / 2;             // px above  source center (y-up)
  const left = 50 + dx / SRC * 100;    // % from box left
  const top  = 50 - dy / SRC * 100;    // % from box top (y flips to CSS top-down)
  return {
    width:    (f[2] / SRC * 100) + '%',
    height:   (f[3] / SRC * 100) + '%',
    left:     left + '%',
    top:      top + '%',
    transform: 'translate(-50%, -50%)',
  };
}

const url = (k) => `/skins/${props.skin.replace(/\.+$/, '')}/${k}.png`;

// Main cat: punches once per click (random paw)
const punchActive = ref(false);
const wasLeft = ref(false);
const isPatted = ref(false);
let punchTimer = null;
let patTimer = null;

// --- Emote & Chat Particle System (Steam Bongo Cat EmoteSpawner / CatPatter) ---
const DEFAULT_EMOTES = [
  'HeartBaseEmoji',
  'HeartSparklingEmoji',
  'FaceHeartSmileEmoji',
  'HeartMendedEmoji',
  'HeartShotEmoji',
];

const CHAT_PHRASES = [
  'Meow! ✨',
  'Nya~ ❤️',
  'Bongo! 🐾',
  'Purr~ 🐱',
  '*Taps* 🎶',
  'uwu 💖',
  'ฅ^•ﻌ•^ฅ',
];

const particles = ref([]);
let nextParticleId = 0;
let tapCount = 0;

function spawnParticle() {
  tapCount++;
  const id = ++nextParticleId;
  const isChat = tapCount % 4 === 0; // show cute speech bubble every few taps

  const startX = 35 + Math.random() * 30; // 35% - 65% across cat width
  const driftX = (Math.random() - 0.5) * 40; // drift left/right -20px to +20px
  const rotateDeg = (Math.random() - 0.5) * 30; // slight tilt

  const activeEmoteName = props.emote || DEFAULT_EMOTES[Math.floor(Math.random() * DEFAULT_EMOTES.length)];

  const particleObj = {
    id,
    type: isChat ? 'chat' : 'emoji',
    src: isChat ? null : `/emotes/${activeEmoteName}.png`,
    text: isChat ? CHAT_PHRASES[Math.floor(Math.random() * CHAT_PHRASES.length)] : null,
    style: {
      left: `${startX}%`,
      '--drift-x': `${driftX}px`,
      '--rot': `${rotateDeg}deg`,
    },
  };

  particles.value.push(particleObj);

  // Auto clean-up after float animation finishes (1.1s)
  setTimeout(() => {
    particles.value = particles.value.filter((p) => p.id !== id);
  }, 1100);
}

function handleTap() {
  // 1. Alternating paw strike
  if (!punchActive.value) {
    punchActive.value = true;
    wasLeft.value = Math.random() < 0.5;
    punchTimer = setTimeout(() => {
      punchActive.value = false;
      punchTimer = null;
    }, props.hitDuration);
  }

  // 2. Pat pulse animation (CatPatter squash-and-stretch)
  isPatted.value = true;
  if (patTimer) clearTimeout(patTimer);
  patTimer = setTimeout(() => {
    isPatted.value = false;
    patTimer = null;
  }, 220);

  // 3. Spawn floating emote or speech bubble
  spawnParticle();
}

// Hit state flags for alternating paw strikes
const farHit   = computed(() => punchActive.value && !wasLeft.value);
const nearHit  = computed(() => punchActive.value &&  wasLeft.value);

// Dedicated styles for each of the 4 frame layers + equipped hat
const bodyIdleStyle   = computed(() => frameStyle(props.frames.left));
const bodyPunchStyle  = computed(() => frameStyle(props.frames.left_punch));
const frontIdleStyle  = computed(() => frameStyle(props.frames.right));
const frontPunchStyle = computed(() => frameStyle(props.frames.right_punch));

// Unity Hat RectTransform offset:
// In the Unity hierarchy, Body/BodyFront are at pos=(-6.3, 9.8), whereas Hat is at pos=(10.0, 45.0) in 128 space.
// Offset: dx = +16.3/128 (+12.73% right), dy = +35.2/128 (+27.5% upwards towards the head).
function hatFrameStyle(f) {
  if (!f) return null;
  const [x, y, w, h] = f;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const dx = cx - SRC / 2;
  const dy = cy - SRC / 2;
  const offsetX = (10.0 - (-6.3)) / 128 * 100; // +12.734%
  const offsetY = (45.0 - 9.8) / 128 * 100;    // +27.500% (upwards in Unity -> minus in CSS top)
  const left = 50 + (dx / SRC * 100) + offsetX;
  const top  = 50 - (dy / SRC * 100) - offsetY;
  return {
    width:    (w / SRC * 100) + '%',
    height:   (h / SRC * 100) + '%',
    left:     left + '%',
    top:      top + '%',
    transform: 'translate(-50%, -50%)',
  };
}

const hatStyle = computed(() => hatFrameStyle(props.hatFrame));


// Standard Bongo Cat desk baseline across skins is at y = 59 in the 256x256 texture.
const wrapStyle = computed(() => ({
  right: '10px',
  '--rk': props.color,
  '--cat-size': props.catSize + 'px',
  '--nav-h': props.navH + 'px',
}));

onBeforeUnmount(() => {
  if (punchTimer) clearTimeout(punchTimer);
  if (patTimer) clearTimeout(patTimer);
});
</script>

<style>
/* Fixed cat wrapper anchored to bottom navbar */
.bongo-wrap{
  position:fixed;
  width:var(--cat-size,180px);
  height:var(--cat-size,180px);
  bottom:calc(var(--nav-h, 64px) + env(safe-area-inset-bottom, 0px) - (var(--cat-size, 180px) * 59 / 256));
  z-index:40;
  pointer-events:none;
}

/* Floating Particles Container */
.particles-container{
  position:absolute;
  top:0;left:0;width:100%;height:100%;
  pointer-events:none;
  overflow:visible;
  z-index:50;
}

.particle{
  position:absolute;
  top:20%;
  pointer-events:none;
  animation:float-up 1.1s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.particle-img{
  width:32px;
  height:32px;
  object-fit:contain;
  filter:drop-shadow(0 2px 6px rgba(0,0,0,0.45));
}

/* Chat Speech Bubble */
.chat-bubble{
  background:rgba(26, 29, 36, 0.94);
  color:#f0f3f8;
  border:1px solid #3d424e;
  padding:4px 10px;
  border-radius:12px;
  font-size:12px;
  font-weight:600;
  white-space:nowrap;
  box-shadow:0 4px 14px rgba(0,0,0,0.5);
  display:flex;
  align-items:center;
  transform:translate(-50%, -50%);
  position:relative;
}

.chat-bubble::after{
  content:'';
  position:absolute;
  bottom:-5px;
  left:50%;
  transform:translateX(-50%);
  border-width:5px 5px 0;
  border-style:solid;
  border-color:rgba(26, 29, 36, 0.94) transparent;
}

@keyframes float-up{
  0%{
    opacity:0;
    transform:translate(-50%, 0) scale(0.6) rotate(0deg);
  }
  20%{
    opacity:1;
    transform:translate(calc(-50% + var(--drift-x, 0px) * 0.3), -25px) scale(1.15) rotate(var(--rot, 0deg));
  }
  70%{
    opacity:1;
    transform:translate(calc(-50% + var(--drift-x, 0px) * 0.8), -65px) scale(1) rotate(var(--rot, 0deg));
  }
  100%{
    opacity:0;
    transform:translate(calc(-50% + var(--drift-x, 0px)), -90px) scale(0.85) rotate(var(--rot, 0deg));
  }
}

/* The cat itself */
.bongo{
  width:100%;height:100%;
  position:relative;
  cursor:pointer;
  pointer-events:auto;
  transition:transform .12s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform-origin: 50% calc(100% * (1 - 59 / 256));
}

/* Pat pulse animation (CatPatter) */
.bongo.patted{
  transform:scale(1.06, 0.92);
}

.bongo .layer{
  position:absolute;
  pointer-events:none;
  user-select:none;
}
.bongo .layer.hidden{
  opacity:0;
  visibility:hidden;
}

/* Idle bob */
.bongo.bob{
  animation: bongo-bob .75s ease-in-out infinite alternate;
}
@keyframes bongo-bob{
  from{transform:scaleY(.95);}
  to{transform:scaleY(1);}
}

@media (min-width:600px){
  .bongo-wrap{
    --cat-size: 230px;
  }
  .particle-img{
    width:38px;
    height:38px;
  }
  .chat-bubble{
    font-size:13px;
    padding:5px 12px;
  }
}
</style>


