<template>
  <!-- Mobile-only bottom appbar with real tab navigation. -->
  <nav class="appbar">
    <button
      v-for="item in items"
      :key="item.id"
      class="appbar-item"
      :class="{ active: currentTab === item.id }"
      type="button"
      @click="$emit('update:tab', item.id)"
    >
      <span class="appbar-icon" v-html="item.icon"></span>
      <span class="appbar-label">{{ item.label }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  currentTab: { type: String, default: 'skins' },
});

defineEmits(['update:tab']);

const items = [
  {
    id: 'skins',
    label: 'Skins',
    icon: `<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>`,
  },
  {
    id: 'accessories',
    label: 'Accessories',
    icon: `<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M12 3L2 12h3v8h14v-8h3L12 3zm0 4.5l5 4.5H7l5-4.5zM12 17a2 2 0 110-4 2 2 0 010 4z"/></svg>`,
  },
  {
    id: 'emotes',
    label: 'Emotes',
    icon: `<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"/></svg>`,
  },
  {
    id: 'cat',
    label: 'Cat',
    icon: `<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>`,
  },
  {
    id: 'more',
    label: 'More',
    icon: `<svg viewBox="0 0 24 24" width="22" height="22"><circle fill="currentColor" cx="12" cy="5" r="2"/><circle fill="currentColor" cx="12" cy="12" r="2"/><circle fill="currentColor" cx="12" cy="19" r="2"/></svg>`,
  },
];
</script>

<style>
/* Global so the fixed bar sits above content; only on small/portrait. */
.appbar{
  position:fixed;
  left:0;right:0;bottom:0;
  height:64px;
  z-index:30;
  display:flex;
  align-items:stretch;
  background:rgba(18,20,26,.92);
  backdrop-filter:blur(10px);
  -webkit-backdrop-filter:blur(10px);
  border-top:1px solid #26282f;
  padding-bottom:env(safe-area-inset-bottom);
}
.appbar-item{
  flex:1 1 0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;
  background:none;border:none;padding:6px 0;
  color:#7b7f87;cursor:pointer;
  font-family:inherit;
}
.appbar-item .appbar-icon{display:flex;line-height:1;}
.appbar-item .appbar-label{font-size:10px;line-height:1;}
.appbar-item.active{color:var(--appbar-accent,#258ED4);}
.appbar-item.active .appbar-icon{filter:drop-shadow(0 0 6px var(--appbar-accent,#258ED4));}

/* Show only on small viewports OR portrait orientation. */
@media (min-width:681px) and (orientation:landscape){
  .appbar{display:none;}
}
</style>
