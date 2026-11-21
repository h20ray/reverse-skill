/**
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
