const fs = require('fs');
const path = require('path');

function write(filePath, content) {
  const full = path.join('bongo-cat-final', filePath);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, 'utf8');
  console.log('Wrote:', filePath);
}

// 1. constants.js
write('src/data/constants.js', /**
 * Bongo Cat Configuration & System Constants
 */

export const QUALITY_TIERS = {
  COMMON: 'common',
  UNCOMMON: 'uncommon',
  RARE: 'rare',
  EPIC: 'epic',
  LEGENDARY: 'legendary',
  SPECIAL: 'special',
};

export const QUALITY_COLORS = {
  common: '#B0B0B0',
  uncommon: '#5ACC3D',
  rare: '#258ED4',
  epic: '#B939DB',
  legendary: '#FFB000',
  special: '#000000',
};

export const QUALITY_ORDER = [
  'common',
  'uncommon',
  'rare',
  'epic',
  'legendary',
  'special',
];

export const PET_STAGES = {
  EGG: 'egg',
  HATCHING_1: 'hatching_1',
  HATCHING_2: 'hatching_2',
  HATCHED: 'hatched',
  EVOLVED: 'evolved',
};

/**
 * Standard 256x256 bounding box size used in Unity texture atlas coordinate calculations
 */
export const SPRITE_SOURCE_SIZE = 256;

/**
 * Standard animation hold duration for punch frames (milliseconds)
 */
export const DEFAULT_HIT_DURATION = 160;

/**
 * Default cat scale (px)
 */
export const DEFAULT_CAT_SIZE = 180;
);

// 2. bongo-cat.css
write('src/assets/bongo-cat.css', /**
 * Bongo Cat Sprite Engine & Animation Styles
 */

:root {
  --bongo-size: 180px;
  --bongo-hit-duration: 160ms;
}

.bongo-container {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  user-select: none;
  -webkit-user-select: none;
  touch-action: manipulation;
}

/* 4-Layer Sprite Stacking Box */
.bongo-sprite-box {
  position: relative;
  width: var(--bongo-size);
  height: var(--bongo-size);
  cursor: pointer;
  transform-origin: bottom center;
  transition: transform 0.1s ease-out;
}

.bongo-sprite-box:active {
  transform: scale(0.97);
}

.bongo-layer {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
  transform-origin: center center;
}

.bongo-layer.hidden {
  display: none !important;
}

/* Layer Z-Index Stacking Order:
 * 1. Body Base (left.png / left_punch.png) -> z-index 10
 * 2. Hat / Accessory                      -> z-index 20
 * 3. Body Front / Paws (right / right_punch) -> z-index 30
 * 4. Particles & Floating Bubbles         -> z-index 40
 */
.bongo-layer.body {
  z-index: 10;
}

.bongo-layer.hat {
  z-index: 20;
}

.bongo-layer.front {
  z-index: 30;
}

/* Idle Bobbing Animation (Game CatBobbing sequence) */
.bongo-sprite-box.bobbing {
  animation: bongoBob 1.5s ease-in-out infinite;
}

@keyframes bongoBob {
  0%, 100% {
    transform: scaleY(1) translateY(0);
  }
  50% {
    transform: scaleY(0.95) translateY(2%);
  }
}

/* Pet Pat / Squash Animation */
.bongo-sprite-box.patted {
  animation: bongoPat 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes bongoPat {
  0% { transform: scale(1, 1); }
  25% { transform: scale(1.1, 0.85); }
  60% { transform: scale(0.9, 1.12); }
  100% { transform: scale(1, 1); }
}

/* Floating Particles Container */
.bongo-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: visible;
  z-index: 40;
}

.bongo-particle {
  position: absolute;
  pointer-events: none;
  will-change: transform, opacity;
  animation: bongoFloatUp 1.2s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes bongoFloatUp {
  0% {
    opacity: 0;
    transform: translate(0, 0) scale(0.5);
  }
  15% {
    opacity: 1;
    transform: translate(calc(var(--dx, 0px) * 0.2), -15px) scale(1.15);
  }
  100% {
    opacity: 0;
    transform: translate(var(--dx, 0px), -65px) scale(0.9);
  }
}
);

console.log('Base data & styles generated.');
