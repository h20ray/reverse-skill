# Bongo Cat — Production Handover Package & Attendance Streak Pet System

> **Target Stack:** Vue 3 (Composition API) / Vuetify / Tailwind CSS / Laravel 10+ / Vite  
> **Reference Project:** [`C:\GitHub\niskala`](file:///c:/GitHub/niskala)

---

## 🎯 Executive Summary

This package provides a **production-ready 4-layer sprite rendering engine, Tamagotchi growth chart, and coin wardrobe economy** for the Bongo Cat attendance streak pet. It has been specifically designed to replace the placeholder streak pet in Niskala with an interactive, gamified companion on both the **Attendance "My Day" Screen** (`/admin/attendance/my-day`) and the **Mobile Navigation Bar**.

---

## 📁 Package Architecture

```text
bongo-cat-final/
├── README.md                           # Team Onboarding & Quickstart Guide
├── package.json                        # Vite + Vue 3 build environment
├── vite.config.js                      # Configured for clean imports and production build
├── docs/                               # Comprehensive Handover Documentation
│   ├── 01-ARCHITECTURE-AND-CORE-CONCEPTS.md      # 4-layer sprite engine & coordinate math
│   ├── 02-VUE-COMPONENT-API.md                   # Props, slots, events & usage reference
│   ├── 03-NISKALA-ATTENDANCE-PET-MIGRATION.md    # Step-by-step Niskala drop-in guide
│   ├── 04-LARAVEL-BACKEND-INTEGRATION.md         # Database schema, Eloquent model, API endpoints
│   ├── 05-DATA-DICTIONARY-AND-METADATA.md        # Schemas for skins, accessories, emotes, and rarity
│   ├── 06-ASSET-PIPELINE-AND-EXTENDING.md        # Adding custom skins/hats & asset pipeline
│   └── 07-TAMAGOTCHI-GROWTH-CHART-AND-COIN-ECONOMY.md # Tamagotchi evolution engine & Coin shop
├── src/
│   ├── components/                     # Production Vue 3 Components
│   │   ├── BongoCat.vue                # Standalone interactive 4-layer Bongo Cat sprite engine
│   │   ├── BongoAttendancePet.vue      # Drop-in replacement for AttendancePetAnimation.vue
│   │   ├── BongoWardrobeModal.vue      # Dressing Room modal (Skin / Hat / Emote pickers + preview)
│   │   ├── CatGallery.vue              # Skin selector grid with live hover punch & rarity badges
│   │   ├── AccessoryGallery.vue        # Hat/Accessory selector grid with equipment toggles
│   │   ├── EmoteGallery.vue            # Emote particle selector grid
│   │   ├── BongoNavWidget.vue          # Mini Bongo Cat companion badge for the navigation bar
│   │   └── NiskalaMobileNavBarDemo.vue # 5-slot mobile nav demo (Center attendance timer + Right pet)
│   ├── composables/                    # Vue 3 Composition API utilities
│   │   ├── useBongoCat.js              # State machine for tap/punch/bob/particles & coordinate math
│   │   ├── useBongoStreakPet.js        # Direct bridge to Niskala's attendance pet state + wardrobe
│   │   └── useBongoData.js             # Skin/hat/emote querying, grouping, rarity & search
│   ├── data/                           # Consolidated, Clean JSON Datasets
│   │   ├── skins.json                  # 213 skins (frames, rarity, quality colors)
│   │   ├── accessories.json            # 374 wearable accessories (frame offsets, display names, rarity)
│   │   ├── emotes.json                 # 105 emote icons & metadata
│   │   ├── ui_assets.json              # 158 UI elements, banners, buttons, advent drawers
│   │   └── constants.js                # Rarity hex map, default timings, size constants
│   ├── assets/
│   │   └── bongo-cat.css               # Shared CSS variables, bounce keyframes & layer styles
│   ├── App.vue                         # Interactive demo dashboard showcasing all 3 modes
│   └── main.js                         # Application entrypoint
├── public/                             # Optimized Static Assets (Audited & Separated)
│   ├── skins/                          # 213 skin folders (852 PNG frames)
│   ├── hats/                           # 374 wearable hat & accessory sprites (Zero UI clutter)
│   ├── emotes/                         # 105 reaction emoji particles
│   ├── ui/                             # 158 UI elements (Advent drawers, banners, buttons, dialogs)
│   └── icons/                          # 695 store/inventory thumbnail icons (*Icon.png)
└── tools/                              # Asset Maintenance & Pipeline Scripts
    ├── README.md                       # How to run extraction & updates
    ├── extract_assets.py               # Unity extraction pipeline (UnityPy)
    └── build_manifest.py               # Generates consolidated JSON metadata
```

---

## 🧭 Navigation & Mobile Bar Rule

> **Important UI Specification**:
> - **Center Attendance Button**: Preserved 100% for the clock-in status / live worked hours timer (e.g. `7:28` worked today).
> - **Bongo Cat Companion**: Positioned on the **right side** of the mobile navigation bar as a mini interactive companion (`BongoNavWidget.vue`) that indicates active streak days (`🔥 12d`) and opens the Dressing Room on tap.

---

## 📚 Handover Documentation Sitemap

1. [**01 — Architecture & Core Concepts**](./docs/01-ARCHITECTURE-AND-CORE-CONCEPTS.md): How the 4-layer sprite stack works, coordinate normalization equations, and animation state machines.
2. [**02 — Vue Component API**](./docs/02-VUE-COMPONENT-API.md): Full Props, Events, Slots, and CSS variable reference for all components.
3. [**03 — Niskala Migration Guide**](./docs/03-NISKALA-ATTENDANCE-PET-MIGRATION.md): Turnkey drop-in guide for replacing `AttendancePetAnimation.vue`, integrating `BongoWardrobeModal.vue`, and embedding the right nav companion.
4. [**04 — Laravel Backend Integration**](./docs/04-LARAVEL-BACKEND-INTEGRATION.md): Eloquent model casts, migrations, and wardrobe API endpoints.
5. [**05 — Data Dictionary & Metadata**](./docs/05-DATA-DICTIONARY-AND-METADATA.md): Full schemas for skins, accessories, emotes, UI assets, and rarity tiers.
6. [**06 — Asset Pipeline & Extending**](./docs/06-ASSET-PIPELINE-AND-EXTENDING.md): Adding custom mascot skins and re-running Unity extraction scripts.
7. [**07 — Tamagotchi Growth Chart & Coin Economy**](./docs/07-TAMAGOTCHI-GROWTH-CHART-AND-COIN-ECONOMY.md): Dual-track progression, dynamic evolution windows (~3 months to Legendary), and attendance coin mechanics.
