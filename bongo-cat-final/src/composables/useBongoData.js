import { ref, computed } from 'vue';
import skinsData from '../data/skins.json';
import accessoriesData from '../data/accessories.json';
import emotesData from '../data/emotes.json';
import { QUALITY_ORDER, QUALITY_COLORS } from '../data/constants.js';

/**
 * Metadata, Catalog Querying & Rarity Grouping Composable
 */
export function useBongoData() {
  const skins = ref(skinsData);
  const accessories = ref(accessoriesData);
  const emotes = ref(emotesData);

  // Grouped by Quality Tier
  const skinGroups = computed(() => {
    return QUALITY_ORDER
      .map((q) => ({
        quality: q,
        color: QUALITY_COLORS[q],
        items: skins.value.filter((s) => s.rarity === q),
      }))
      .filter((g) => g.items.length > 0);
  });

  const accessoryGroups = computed(() => {
    return QUALITY_ORDER
      .map((q) => ({
        quality: q,
        color: QUALITY_COLORS[q],
        items: accessories.value.filter((a) => a.rarity === q),
      }))
      .filter((g) => g.items.length > 0);
  });

  const emoteGroups = computed(() => {
    return QUALITY_ORDER
      .map((q) => ({
        quality: q,
        color: QUALITY_COLORS[q],
        items: emotes.value.filter((e) => e.rarity === q),
      }))
      .filter((g) => g.items.length > 0);
  });

  function findSkin(name) {
    return skins.value.find((s) => s.name === name) || skins.value[0];
  }

  function findAccessory(name) {
    return accessories.value.find((a) => a.name === name) || null;
  }

  function findEmote(name) {
    return emotes.value.find((e) => e.name === name) || null;
  }

  return {
    skins,
    accessories,
    emotes,
    skinGroups,
    accessoryGroups,
    emoteGroups,
    findSkin,
    findAccessory,
    findEmote,
  };
}
