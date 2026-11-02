# Top Gun HD

Development review build **v0.4.0** for the NES Top Gun (USA), using a Mesen HD pack. This is unfinished work, not a full-game release.

## Install

Copy the contents of `pack/` (not the surrounding source tree) into the emulator’s HD pack folder associated with your own Top Gun (USA) ROM. Enable HD packs and reopen the ROM. No ROM or emulator executable is included.

## New combat artwork

- Painted enemy jets in rear, approaching and overhead views, with native banks, inverted views and distance sizes: 116 mapped layouts using 145 tile patterns.
- Missiles, tracers, ignition flashes, fireballs and smoke: 23 mapped layouts using 37 tile patterns.
- Native positions, animation timing, hit detection and audio remain under game control.

The new artwork is limited to the windshield and exact sprite palettes. All 30 existing pack PNGs are preserved, including the approved cockpit and map fixes. See `source/COMBAT_ART_NOTES.md` and `validation/combat_art_v0.4.0.json` for integration details and tested coverage.

## Preserved work

- Title and native-timed carrier launch, with director and exhaust animation.
- Cockpit HUD, damage-shake registration, radar and landing displays.
- Centered cockpit dials and a cleanly clipped lower dial.
- A windshield edge that stays neutral across runway/sky/cloud colors, with matching attitude-display ticks.
- Mission-one tactical briefing map with correctly filled inland water and all three missile-selection diagrams.
- Artwork masters, build scripts, capture references, supplied replay movies, and recorded validation reports.

Clouds, ocean, terrain, later missions and refuelling still need further artwork and coverage. The combat pass covers the recovered mission-one layouts and observed palettes; it is not a full-game QA claim. See `source/MAP_WATER_NOTES.md`, `source/COCKPIT_COLOR_NOTES.md` and `source/SCREEN_POLISH_NOTES.md` for the included earlier fixes. `README.txt` and `source/PROJECT_NOTES.txt` preserve the earlier handoff.

## Build

Use Python 3 with Pillow and NumPy installed, then run:

```sh
python3 scripts/build_pack.py
```

The build writes `pack/` and build metadata. The original v0.2.0 recovery was checked with Pillow 13.0.0 and NumPy 2.3.5, and all 22 pack files matched its saved installer byte-for-byte. The v0.3.0 menu pass uses Pillow 12.3.0 and NumPy 2.3.5; all existing pack PNGs, including the corrected cockpit dials and approved intro artwork, remain byte-identical to the merged v0.2.1 baseline.

The v0.3.1 color fixes use the same Python libraries. They change the upper coaming and right attitude tick, add three small foreground caps for normal/left/right impact positions, and preserve the other 23 PNGs. The supplied 2,054-frame replay and a 180-frame impact replay match native game state and PCM audio; see `validation/cockpit_colors_v0.3.1.json`.

The v0.3.2 map correction fills the three enclosed water regions with the sea color while preserving the coastline, grid and carrier marker. Only `menu_map.png` changes; the other 29 PNGs and all functional HD-pack rules remain unchanged from v0.3.1. See `validation/map_water_v0.3.2.json` for the 777-frame menu-to-cockpit replay checks.

`validation/checkpoint_pack_sha256.json` records the preserved pack hashes. `validation/checkpoint_recovery.json` records recovery checks. `scripts/validate_release.py` requires additional original/HD captures and audio from emulator replays; those full replay outputs are not included here, so that script was not rerun during recovery.

## Repository workflow

The approved cockpit color and map corrections are merged into `main` at `f23e0c16669c328e8d556f0c20fbe909a8f72efb`. This combat pass is on `feature/enemy-aircraft-v0.4.0` for review. Keep further edits on feature branches and review before merging. Do not treat a development checkpoint as a release or permission to merge.
