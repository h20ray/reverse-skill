import { ref, computed } from 'vue';
import { PET_STAGES } from '../data/constants.js';

/**
 * Niskala Attendance Streak Pet Integration Composable
 * Matches App\Models\AttendanceStreakPet and resources/js/modules/admin/components/attendance/pet/composables/useAttendancePet.js
 */
export function useBongoStreakPet(initialData = {}) {
  const pet = ref({
    id: initialData.id || 1,
    pet_name: initialData.pet_name || 'Bongo Koko',
    pet_type: initialData.pet_type || 'bongo_cat',
    current_streak: initialData.current_streak !== undefined ? initialData.current_streak : 12,
    longest_streak: initialData.longest_streak || 15,
    total_exp: initialData.total_exp || 2450,
    level: initialData.level || 6,
    stage: initialData.stage || PET_STAGES.HATCHED,
    flame_tier: initialData.flame_tier || 2,
    exp_current_level: initialData.exp_current_level || 2000,
    exp_next_level: initialData.exp_next_level || 3500,
    level_progress_percentage: initialData.level_progress_percentage || 30,
    is_today_clocked_in: initialData.is_today_clocked_in ?? true,
    can_interact_today: initialData.can_interact_today ?? true,
    dialogue: initialData.dialogue || 'Meow! Great job clocking in on time today! 🐱',
    outfits: initialData.outfits || {
      skin: 'Cat',
      hat: 'BlackWizardHat',
      emote: 'FaceHeartSmileEmoji',
    },
  });

  const isLoading = ref(false);
  const isInteracting = ref(false);
  const lastExpGained = ref(null);

  const isEgg = computed(() => {
    return [PET_STAGES.EGG, PET_STAGES.HATCHING_1, PET_STAGES.HATCHING_2].includes(pet.value.stage);
  });

  const isEvolved = computed(() => {
    return pet.value.stage === PET_STAGES.EVOLVED || pet.value.current_streak >= 30;
  });

  const activeSkin = computed(() => pet.value.outfits?.skin || 'Cat');
  const activeHat = computed(() => pet.value.outfits?.hat || null);
  const activeEmote = computed(() => pet.value.outfits?.emote || null);

  function setSkin(skinName) {
    if (!pet.value.outfits) pet.value.outfits = {};
    pet.value.outfits.skin = skinName;
  }

  function setHat(hatName) {
    if (!pet.value.outfits) pet.value.outfits = {};
    pet.value.outfits.hat = pet.value.outfits.hat === hatName ? null : hatName;
  }

  function setEmote(emoteName) {
    if (!pet.value.outfits) pet.value.outfits = {};
    pet.value.outfits.emote = pet.value.outfits.emote === emoteName ? null : emoteName;
  }

  /**
   * Simulates/Executes pet tap interaction
   */
  async function interactPet() {
    if (isInteracting.value) return null;
    isInteracting.value = true;
    
    // Simulate backend response if standalone
    const expGained = Math.floor(Math.random() * 10) + 5;
    lastExpGained.value = expGained;
    pet.value.total_exp += expGained;
    
    setTimeout(() => {
      isInteracting.value = false;
      lastExpGained.value = null;
    }, 1500);

    return { exp_gained: expGained, pet: pet.value };
  }

  return {
    pet,
    isLoading,
    isInteracting,
    lastExpGained,
    isEgg,
    isEvolved,
    activeSkin,
    activeHat,
    activeEmote,
    setSkin,
    setHat,
    setEmote,
    interactPet,
  };
}
