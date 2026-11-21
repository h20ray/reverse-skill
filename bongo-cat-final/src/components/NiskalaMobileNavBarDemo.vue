<template>
  <nav
    class="fixed bottom-0 left-0 z-[60] grid grid-cols-5 w-full items-center border-t border-slate-800 bg-slate-950/95 backdrop-blur px-2 py-2 pb-[calc(1rem+env(safe-area-inset-bottom,0px))] shadow-2xl"
    aria-label="Mobile navigation"
  >
    <!-- Slot 1: Dashboard -->
    <a
      href="#dashboard"
      class="flex flex-1 flex-col items-center justify-center gap-1 rounded-lg py-2 transition-colors text-slate-400 hover:text-primary"
      title="Dashboard"
    >
      <Home class="w-5 h-5 shrink-0" />
      <span class="text-[10px] font-medium">Home</span>
    </a>

    <!-- Slot 2: POS -->
    <a
      href="#pos"
      class="flex flex-1 flex-col items-center justify-center gap-1 rounded-lg py-2 transition-colors text-slate-400 hover:text-primary"
      title="POS"
    >
      <Calculator class="w-5 h-5 shrink-0" />
      <span class="text-[10px] font-medium">POS</span>
    </a>

    <!-- Slot 3 (CENTER): Attendance Status & Work Duration Timer -->
    <div class="relative flex flex-1 flex-col items-center justify-center">
      <!-- Pulsing ripple for active work session -->
      <span
        class="absolute top-0 h-12 w-12 rounded-full bg-emerald-500/20 animate-ping pointer-events-none"
        style="margin-top: -1.25rem;"
      />
      <a
        href="#my-day"
        class="relative flex h-12 w-12 items-center justify-center rounded-full shadow-lg transition-all duration-300 focus:outline-none bg-emerald-500 text-white hover:bg-emerald-600 ring-2 ring-primary ring-offset-2 ring-offset-slate-950"
        style="margin-top: -1.25rem;"
        title="Attendance: 7h 28m worked today"
        @click.prevent="$emit('open-attendance')"
      >
        <span class="text-xs font-bold leading-none">{{ workTime }}</span>
      </a>
      <span class="text-[10px] font-medium text-emerald-400 mt-1">Clocked In</span>
    </div>

    <!-- Slot 4: Notifications -->
    <button
      type="button"
      class="flex flex-1 flex-col items-center justify-center gap-1 rounded-lg py-2 transition-colors text-slate-400 hover:text-primary"
      title="Notifications"
    >
      <span class="relative inline-flex">
        <Bell class="w-5 h-5 shrink-0" />
        <span class="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white">
          3
        </span>
      </span>
      <span class="text-[10px] font-medium">Alerts</span>
    </button>

    <!-- Slot 5 (RIGHT): Bongo Cat Streak Pet Companion Slot / Profile -->
    <div
      class="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-lg py-1 transition-colors text-slate-400 hover:text-primary cursor-pointer"
      title="Attendance Bongo Cat Streak"
      @click="$emit('open-wardrobe')"
    >
      <BongoNavWidget
        :skin="skin"
        :hat="hat"
        :asset-base-path="assetBasePath"
        @tap="$emit('cat-tap')"
      />
      <span class="text-[10px] font-bold text-amber-400 flex items-center gap-0.5">
        🔥 {{ streak }}d
      </span>
    </div>
  </nav>
</template>

<script setup>
import { Home, Calculator, Bell } from 'lucide-vue-next';
import BongoNavWidget from './BongoNavWidget.vue';

defineProps({
  workTime: { type: String, default: '7:28' },
  streak: { type: Number, default: 12 },
  skin: { type: String, default: 'Cat' },
  hat: { type: String, default: 'BlackWizardHat' },
  assetBasePath: { type: String, default: '' },
});

defineEmits(['open-attendance', 'open-wardrobe', 'cat-tap']);
</script>
