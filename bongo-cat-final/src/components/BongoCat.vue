<template>
  <div class="bongo-container" :style="containerStyle">
    <!-- Floating Particles & Emoji Reaction Overlay -->
    <div class="bongo-particles">
      <div
        v-for="p in particles"
        :key="p.id"
        class="bongo-particle"
        :style="p.style"
      >
        <img
          v-if="p.type === 'emoji' && p.src"
          :src="p.src"
          class="w-6 h-6 object-contain filter drop-shadow"
          alt=""
        />
        <div
          v-else-if="p.type === 'chat'"
          class="bg-slate-900/90 text-white text-xs font-semibold px-2.5 py-1 rounded-full border border-slate-700 shadow-md whitespace-nowrap"
        >
          {{ p.text }}
        </div>
      </div>
    </div>

    <!-- 4-Layer Sprite Renderer Box -->
    <div
      class="bongo-sprite-box"
      :class="{ bobbing: bob, patted: isPatted }"
      @pointerdown="handlePointerDown"
    >
      <!-- Layer 1: Body Base (Idle / Punch) -->
      <img
        :src="getSkinUrl('left')"
        :style="bodyIdleStyle"
        class="bongo-layer body"
        :class="{ hidden: farHit }"
        alt=""
        decoding="async"
      />
      <img
        :src="getSkinUrl('left_punch')"
        :style="bodyPunchStyle"
        class="bongo-layer body punch"
        :class="{ hidden: !farHit }"
        alt=""
        decoding="async"
      />

      <!-- Layer 2: Hat / Accessory (Middle Layer) -->
      <img
        v-if="hat && hatStyle"
        :src="getHatUrl(hat)"
        :style="hatStyle"
        class="bongo-layer hat"
        alt=""
        decoding="async"
      />

      <!-- Layer 3: Body Front / Near Paw (Top Layer) -->
      <img
        :src="getSkinUrl('right')"
        :style="frontIdleStyle"
        class="bongo-layer front"
        :class="{ hidden: nearHit }"
        alt=""
        decoding="async"
      />
      <img
        :src="getSkinUrl('right_punch')"
        :style="frontPunchStyle"
        class="bongo-layer front punch"
        :class="{ hidden: !nearHit }"
        alt=""
        decoding="async"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount } from 'vue';
import { useBongoCat } from '../composables/useBongoCat.js';
import { DEFAULT_CAT_SIZE, DEFAULT_HIT_DURATION } from '../data/constants.js';

const props = defineProps({
  skin: {
    type: String,
    default: 'Cat',
  },
  frames: {
    type: Object,
    required: true, // { left: [x,y,w,h], left_punch: [...], right: [...], right_punch: [...] }
  },
  hat: {
    type: String,
    default: null,
  },
  hatFrame: {
    type: Array,
    default: null,
  },
  emote: {
    type: String,
    default: null,
  },
  size: {
    type: Number,
    default: DEFAULT_CAT_SIZE,
  },
  bob: {
    type: Boolean,
    default: true,
  },
  hitDuration: {
    type: Number,
    default: DEFAULT_HIT_DURATION,
  },
  interactive: {
    type: Boolean,
    default: true,
  },
  assetBasePath: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['tap', 'punch']);

const {
  farHit,
  nearHit,
  isPatted,
  particles,
  computeFrameStyle,
  triggerTap,
  spawnParticle,
  cleanup,
} = useBongoCat({ hitDuration: props.hitDuration });

onBeforeUnmount(() => {
  cleanup();
});

const containerStyle = computed(() => ({
  '--bongo-size': `${props.size}px`,
}));

// Asset URL resolvers
function cleanSkinName(name) {
  return (name || 'Cat').replace(/\.+$/, '');
}

function getSkinUrl(frameName) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/skins/${cleanSkinName(props.skin)}/${frameName}.png`;
}

function getHatUrl(hatName) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/hats/${hatName}.png`;
}

function getEmoteUrl(emoteName) {
  const base = props.assetBasePath ? props.assetBasePath.replace(/\/$/, '') : '';
  return `${base}/emotes/${emoteName}.png`;
}

// Coordinate calculations for 4 frames
const bodyIdleStyle = computed(() => computeFrameStyle(props.frames?.left));
const bodyPunchStyle = computed(() => computeFrameStyle(props.frames?.left_punch));
const frontIdleStyle = computed(() => computeFrameStyle(props.frames?.right));
const frontPunchStyle = computed(() => computeFrameStyle(props.frames?.right_punch));
const hatStyle = computed(() => (props.hatFrame ? computeFrameStyle(props.hatFrame) : null));

function handlePointerDown(e) {
  if (!props.interactive) return;
  
  triggerTap();
  emit('tap', e);
  emit('punch', { side: farHit.value ? 'left' : 'right' });

  // Spawn particle
  if (props.emote) {
    spawnParticle({
      type: 'emoji',
      src: getEmoteUrl(props.emote),
    });
  } else {
    const defaultEmotes = [
      'FaceHeartSmileEmoji',
      'FaceLoveEmoji',
      'FaceCelebrateEmoji',
      'FaceHappyEmoji',
      'FaceLaughEmoji',
      'FaceBlushEmoji',
      'FaceGiggleEmoji',
      'HeartSparklingEmoji',
      'HeartBaseEmoji',
      'SymbolSparkleEmoji',
      'PawThumbsUpEmoji',
      'PawWaveEmoji',
      'FoodDonutEmoji',
      'FoodStrawberryEmoji',
      'FoodCoffeeEmoji',
      'FoodBirthdayCakeEmoji'
    ];
    const randomEmote = defaultEmotes[Math.floor(Math.random() * defaultEmotes.length)];
    spawnParticle({
      type: 'emoji',
      src: getEmoteUrl(randomEmote),
    });
  }
}

// Expose methods for parent control
defineExpose({
  triggerTap,
  spawnParticle,
});
</script>

<style scoped>
@import '../assets/bongo-cat.css';
</style>
