<script setup>
import { computed, ref } from 'vue';
import BongoCat from '../BongoCat.vue';
import CatGallery from './CatGallery.vue';
import AccessoryGallery from './AccessoryGallery.vue';
import EmoteGallery from './EmoteGallery.vue';
import MobileNavBar from './MobileNavBar.vue';
import skinFrames from '../skin-frames.json';
import skinRarity from '../skin-rarity-map.json';
import hatFrames from '../hat-frames.json';
import emoteItems from '../emote-items.json';

// Rarity hex (decoded from SteamItemBasic.GetColorForQuality IL).
const QUALITY = {
  common:    '#B0B0B0',
  uncommon:  '#5ACC3D',
  rare:      '#258ED4',
  epic:      '#B939DB',
  legendary: '#FFB000',
  special:   '#000000',
};
const ORDER = ['common', 'uncommon', 'rare', 'epic', 'legendary'];

// Current active tab ('skins', 'accessories', 'emotes', 'cat', 'more')
const activeTab = ref('skins');

// --- Skins List & Grouping ---
const skins = Object.keys(skinFrames).map((name) => ({
  name,
  frames: skinFrames[name],
  rarity: skinRarity[name]?.quality || 'common',
}));

const skinGroups = computed(() =>
  ORDER
    .map((q) => ({ quality: q, color: QUALITY[q], items: skins.filter((s) => s.rarity === q) }))
    .filter((g) => g.items.length),
);

// --- Accessories List & Grouping ---
const accessories = Object.keys(hatFrames).map((name) => ({
  name,
  displayName: hatFrames[name].displayName || name,
  frame: hatFrames[name].frame,
  rarity: hatFrames[name].quality || 'common',
}));

const accessoryGroups = computed(() =>
  ORDER
    .map((q) => ({ quality: q, color: QUALITY[q], items: accessories.filter((a) => a.rarity === q) }))
    .filter((g) => g.items.length),
);

// --- Emotes List & Grouping ---
const emotes = Object.keys(emoteItems).map((name) => ({
  name,
  displayName: emoteItems[name].displayName || name,
  rarity: emoteItems[name].quality || 'common',
}));

const emoteGroups = computed(() =>
  ORDER
    .map((q) => ({ quality: q, color: QUALITY[q], items: emotes.filter((e) => e.rarity === q) }))
    .filter((g) => g.items.length),
);

// --- Main navbar cat skin, hat, and emote state ---
const mainName = ref('Cat');
const mainHat = ref(null);   // e.g. 'PaperBag', 'BlackWizardHat', 'AngelHalo'
const mainEmote = ref(null); // e.g. 'FaceHeartSmileEmoji', 'AnimalShrimpEmoji'

const mainFrames = computed(() => skins.find((s) => s.name === mainName.value)?.frames || skins[0].frames);
const mainColor = computed(() =>
  QUALITY[skins.find((s) => s.name === mainName.value)?.rarity] || QUALITY.common,
);
const mainHatFrame = computed(() => mainHat.value ? hatFrames[mainHat.value]?.frame : null);

function selectSkin(name) {
  if (name && mainName.value !== name) mainName.value = name;
}

function selectAccessory(name) {
  if (mainHat.value === name) {
    mainHat.value = null; // unequip if clicking the already equipped one
  } else {
    mainHat.value = name;
  }
}

function selectEmote(name) {
  if (mainEmote.value === name) {
    mainEmote.value = null; // reset to random emojis
  } else {
    mainEmote.value = name;
  }
}
</script>

<template>
  <div class="page">
    <!-- Main Bongo Cat (floats above bottom-right navbar) -->
    <BongoCat
      :nav-h="64"
      :skin="mainName"
      :frames="mainFrames"
      :hat="mainHat"
      :hat-frame="mainHatFrame"
      :emote="mainEmote"
      :color="mainColor"
      :bob="true"
      :hit-duration="160"
    />

    <!-- Mobile-only bottom appbar with active tab binding -->
    <MobileNavBar :current-tab="activeTab" @update:tab="activeTab = $event" />

    <!-- Top Navigation Bar (desktop & mobile synced) -->
    <header class="navbar-header">
      <div class="brand">
        <span class="brand-paw">🐾</span>
        <span class="brand-title">Bongo Cat Studio</span>
      </div>
      <nav class="desktop-tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'skins' }"
          @click="activeTab = 'skins'"
        >
          Skins <span class="tab-count">{{ skins.length }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'accessories' }"
          @click="activeTab = 'accessories'"
        >
          Accessories <span class="tab-count">{{ accessories.length }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'emotes' }"
          @click="activeTab = 'emotes'"
        >
          Emotes <span class="tab-count">{{ emotes.length }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'cat' }"
          @click="activeTab = 'cat'"
        >
          My Cat
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'more' }"
          @click="activeTab = 'more'"
        >
          More
        </button>
      </nav>
    </header>

    <!-- TAB 1: SKINS -->
    <main v-if="activeTab === 'skins'" class="tab-content">
      <div class="header">
        <h1>All Bongo Cat Skins</h1>
        <p>{{ skins.length }} skins grouped by Steam rarity. Click any skin to equip it. Tap the main cat to punch & float hearts!</p>
      </div>

      <section v-for="g in skinGroups" :key="g.quality" class="group">
        <h2 class="group-title" :style="{ '--rk': g.color }">
          {{ g.quality[0].toUpperCase() + g.quality.slice(1) }}
          <span class="count">· {{ g.items.length }}</span>
        </h2>
        <div class="grid">
          <CatGallery
            v-for="s in g.items"
            :key="s.name"
            :name="s.name"
            :frames="s.frames"
            :color="g.color"
            :size="110"
            :selected="s.name === mainName"
            @select="selectSkin"
          />
        </div>
      </section>
    </main>

    <!-- TAB 2: ACCESSORIES (HATS, MASKS, GLASSES) -->
    <main v-else-if="activeTab === 'accessories'" class="tab-content">
      <div class="header">
        <h1>All Accessories & Hats</h1>
        <p>{{ accessories.length }} accessories & hats from Steam item definitions. Click any accessory to equip or unequip it on your cat!</p>
        <button
          v-if="mainHat"
          class="unequip-all-btn"
          @click="mainHat = null"
        >
          ✕ Remove Equipped Accessory ({{ hatFrames[mainHat]?.displayName || mainHat }})
        </button>
      </div>

      <section v-for="g in accessoryGroups" :key="g.quality" class="group">
        <h2 class="group-title" :style="{ '--rk': g.color }">
          {{ g.quality[0].toUpperCase() + g.quality.slice(1) }}
          <span class="count">· {{ g.items.length }}</span>
        </h2>
        <div class="grid">
          <AccessoryGallery
            v-for="a in g.items"
            :key="a.name"
            :name="a.name"
            :display-name="a.displayName"
            :frame="a.frame"
            :color="g.color"
            :size="110"
            :selected="a.name === mainHat"
            @select="selectAccessory"
          />
        </div>
      </section>
    </main>

    <!-- TAB 3: EMOTES (PARTICLES) -->
    <main v-else-if="activeTab === 'emotes'" class="tab-content">
      <div class="header">
        <h1>All Emoji & Emote Particles</h1>
        <p>{{ emotes.length }} official Steam emotes (`itemslot:emote`). Click any emote to set it as your cat's tap particle!</p>
        <button
          v-if="mainEmote"
          class="unequip-all-btn"
          @click="mainEmote = null"
        >
          ✕ Reset to Random Emotes (Current: {{ emoteItems[mainEmote]?.displayName || mainEmote }})
        </button>
      </div>

      <section v-for="g in emoteGroups" :key="g.quality" class="group">
        <h2 class="group-title" :style="{ '--rk': g.color }">
          {{ g.quality[0].toUpperCase() + g.quality.slice(1) }}
          <span class="count">· {{ g.items.length }}</span>
        </h2>
        <div class="grid">
          <EmoteGallery
            v-for="e in g.items"
            :key="e.name"
            :name="e.name"
            :display-name="e.displayName"
            :color="g.color"
            :size="95"
            :selected="e.name === mainEmote"
            @select="selectEmote"
          />
        </div>
      </section>
    </main>

    <!-- TAB 4: CAT SPOTLIGHT -->
    <main v-else-if="activeTab === 'cat'" class="tab-content cat-spotlight">
      <div class="spotlight-card">
        <h2>Equipped Bongo Cat</h2>
        <div class="spotlight-details">
          <p><strong>Current Skin:</strong> <span :style="{ color: mainColor }">{{ mainName }}</span></p>
          <p><strong>Accessory:</strong> <span>{{ mainHat ? (hatFrames[mainHat]?.displayName || mainHat) : 'None (Naked)' }}</span></p>
          <p><strong>Tap Emote:</strong> <span>{{ mainEmote ? (emoteItems[mainEmote]?.displayName || mainEmote) : 'Random Hearts & Emojis' }}</span></p>
        </div>
        <div class="spotlight-actions">
          <button class="action-btn" @click="mainHat = null" :disabled="!mainHat">Remove Hat</button>
          <button class="action-btn" @click="mainEmote = null" :disabled="!mainEmote">Randomize Emotes</button>
          <button class="action-btn" @click="selectSkin('Cat')">Reset to Default Cat</button>
        </div>
        <p class="hint-text">💡 Tap the cat at the bottom right to make it bongo, pet it, and see speech bubbles & floating emojis!</p>
      </div>
    </main>

    <!-- TAB 5: MORE / INFO -->
    <main v-else-if="activeTab === 'more'" class="tab-content more-section">
      <div class="info-card">
        <h2>About Bongo Cat Web Port</h2>
        <p>A web implementation of the Steam Bongo Cat game featuring:</p>
        <ul>
          <li><strong>{{ skins.length }} Skins</strong> with authentic textureRect positioning.</li>
          <li><strong>{{ accessories.length }} Hats & Accessories</strong> layered directly above the cat with true Z-depth.</li>
          <li><strong>{{ emotes.length }} Official Emotes & Particles</strong> (`CatPatter` & `EmoteSpawner`).</li>
          <li><strong>Zero Glitch 60fps</strong> multi-layer pre-rendered engine.</li>
        </ul>
      </div>
    </main>
  </div>
</template>


<style>
html,body{margin:0;background:#0f1116;color:#e6e6e6;
  font-family:system-ui,-apple-system,sans-serif;}
#app{min-height:100%;}
.page{padding:16px 20px 80px;box-sizing:border-box;}
@media (max-width:680px){
  .page{padding-bottom:calc(64px + env(safe-area-inset-bottom) + 24px);}
}

.navbar-header{
  display:flex;align-items:center;justify-content:space-between;
  padding-bottom:16px;border-bottom:1px solid #1f232c;margin-bottom:20px;
}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:18px;}
.brand-paw{font-size:20px;}

.desktop-tabs{display:flex;gap:8px;}
.tab-btn{
  background:#171a22;border:1px solid #282c37;color:#9aa0a6;
  padding:8px 16px;border-radius:10px;font-size:14px;cursor:pointer;
  font-family:inherit;transition:all .15s ease;display:flex;align-items:center;gap:6px;
}
.tab-btn:hover{background:#222631;color:#fff;border-color:#3a4050;}
.tab-btn.active{background:#258ED4;color:#fff;border-color:#258ED4;font-weight:600;}
.tab-count{background:rgba(0,0,0,0.3);padding:2px 6px;border-radius:8px;font-size:11px;}

.header h1{margin:0 0 8px;font-size:24px;}
.header p{color:#9aa0a6;font-size:14px;line-height:1.5;max-width:720px;margin-bottom:12px;}
.unequip-all-btn{
  background:#262a35;border:1px solid #3c4252;color:#f07070;padding:6px 14px;
  border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;margin-bottom:16px;
  transition:all .15s ease;
}
.unequip-all-btn:hover{background:#3a2020;border-color:#e05050;color:#ff8080;}

.group{margin-top:28px;}
.group-title{display:flex;align-items:baseline;gap:8px;margin:0 0 12px;
  font-size:18px;color:var(--rk);border-left:4px solid var(--rk);padding-left:10px;}
.group-title .count{font-size:13px;color:#7b7f87;}
.grid{display:flex;flex-wrap:wrap;gap:10px;}
.grid > *{flex:0 0 auto;}

.spotlight-card, .info-card{
  background:#171a22;border:1px solid #262a35;padding:24px;border-radius:16px;max-width:600px;
}
.spotlight-details p{font-size:15px;margin:8px 0;}
.spotlight-actions{display:flex;gap:10px;margin:20px 0;}
.action-btn{
  background:#242834;border:1px solid #373d4e;color:#e6e6e6;padding:8px 16px;
  border-radius:8px;cursor:pointer;font-family:inherit;
}
.action-btn:hover:not(:disabled){background:#32384a;border-color:#4c546b;}
.action-btn:disabled{opacity:0.5;cursor:not-allowed;}
.hint-text{font-size:13px;color:#858b96;margin-top:16px;}
</style>

