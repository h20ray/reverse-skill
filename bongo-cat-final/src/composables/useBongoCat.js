import { ref, computed } from 'vue';
import { SPRITE_SOURCE_SIZE, DEFAULT_HIT_DURATION } from '../data/constants.js';

/**
 * Core Bongo Cat Interaction & Coordinate Translation Composable
 */
export function useBongoCat(options = {}) {
  const hitDuration = options.hitDuration || DEFAULT_HIT_DURATION;
  
  // Animation state
  const farHit = ref(false);     // Left paw punch down
  const nearHit = ref(false);    // Right paw punch down
  const wasLeft = ref(false);    // Alternation tracker
  const isPatted = ref(false);   // Whole cat squash reaction
  const particles = ref([]);     // Floating emoji/particle burst list
  
  let leftTimer = null;
  let rightTimer = null;
  let patTimer = null;

  const punchActive = computed(() => farHit.value || nearHit.value);

  /**
   * Converts Unity TextureRect coordinates [x, y, w, h] to CSS percentage positioning
   * centered inside a 256x256 reference bounding box.
   */
  function computeFrameStyle(frame, sourceSize = SPRITE_SOURCE_SIZE) {
    if (!frame || !Array.isArray(frame) || frame.length < 4) {
      return {};
    }
    const [x, y, w, h] = frame;
    const cx = x + w / 2;
    const cy = y + h / 2;
    const dx = cx - sourceSize / 2;
    const dy = cy - sourceSize / 2;

    return {
      width: `${(w / sourceSize) * 100}%`,
      height: `${(h / sourceSize) * 100}%`,
      left: `${50 + (dx / sourceSize) * 100}%`,
      top: `${50 - (dy / sourceSize) * 100}%`, // Invert Y because Unity is Y-Up while CSS is Y-Down
      transform: 'translate(-50%, -50%)',
    };
  }

  /**
   * Triggers a single bongo drum hit with alternating paws
   */
  function triggerTap() {
    if (wasLeft.value) {
      // Right paw strikes down -> Immediately release left paw to idle
      farHit.value = false;
      if (leftTimer) {
        clearTimeout(leftTimer);
        leftTimer = null;
      }

      nearHit.value = true;
      if (rightTimer) clearTimeout(rightTimer);
      rightTimer = setTimeout(() => {
        nearHit.value = false;
      }, hitDuration);
    } else {
      // Left paw strikes down -> Immediately release right paw to idle
      nearHit.value = false;
      if (rightTimer) {
        clearTimeout(rightTimer);
        rightTimer = null;
      }

      farHit.value = true;
      if (leftTimer) clearTimeout(leftTimer);
      leftTimer = setTimeout(() => {
        farHit.value = false;
      }, hitDuration);
    }
    wasLeft.value = !wasLeft.value;
  }

  /**
   * Triggers a squash & stretch reaction
   */
  function triggerPat() {
    isPatted.value = true;
    if (patTimer) clearTimeout(patTimer);
    patTimer = setTimeout(() => {
      isPatted.value = false;
    }, 700);
  }

  /**
   * Spawns floating particles / reaction bubbles above the cat
   */
  function spawnParticle({ type = 'emoji', src = null, text = null } = {}) {
    const id = Date.now() + Math.random();
    const dx = (Math.random() - 0.5) * 80;
    const particle = {
      id,
      type,
      src,
      text,
      style: {
        '--dx': `${dx}px`,
        left: `${45 + (Math.random() - 0.5) * 20}%`,
        top: '15%',
      },
    };

    particles.value.push(particle);
    setTimeout(() => {
      particles.value = particles.value.filter((p) => p.id !== id);
    }, 1250);
  }

  function cleanup() {
    if (leftTimer) clearTimeout(leftTimer);
    if (rightTimer) clearTimeout(rightTimer);
    if (patTimer) clearTimeout(patTimer);
  }

  return {
    farHit,
    nearHit,
    wasLeft,
    isPatted,
    particles,
    punchActive,
    computeFrameStyle,
    triggerTap,
    triggerPat,
    spawnParticle,
    cleanup,
  };
}
