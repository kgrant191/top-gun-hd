# Top Gun HD

Development review build **v0.8.0** for the NES Top Gun (USA), using a Mesen HD pack. This is unfinished work, not a full-game release.

## Install

Copy the contents of `pack/` (not the surrounding source tree) into the emulator’s HD pack folder associated with your own Top Gun (USA) ROM. Enable HD packs and reopen the ROM. No ROM or emulator executable is included.

## Mission 2 naval combat and refueling

v0.8.0 extends the approved scenery, cockpit, aircraft and effects to the
Mission 2 palettes. It adds painted boats and submarines, the second tactical
map, a scrolling tanker, and a growing refueling boom. The live guidance
monitor preserves the game's instructions and coupling movement.

The refueling blackout came from landing and refueling sharing mode/state
numbers. The pack now checks the route as well, keeping the cockpit and sky
visible during refueling. All 132 approved v0.7.3 PNGs remain byte-identical.

Coverage follows the supplied 14,475-frame Mission 2 recording through the
refueling controls. Refueling completion, later Mission 2 encounters and later
missions need additional recordings. See `source/MISSION2_NOTES.md` and
`validation/mission2_v0.8.0.json` for implementation and replay checks.

## Carrier landing and gunfire

v0.7.3 fixes the flashes in the supplied `danger.mmo`, `danger2.mmo` and
`landing.mmo`: the danger display keeps its HD styling as radar rows replace
it, lethal damage retains the warning artwork, and additional deck-edge and
runway-light phases remain HD during rollout. All 131 v0.7.2 PNGs are unchanged.
See `source/TRANSITION_FLASH_NOTES.md` and `validation/transition_flashes_v0.7.3.json`.

- An opaque carrier deck and hull follow all 21 observed approach sizes.
- The side-on touchdown uses a painted carrier, gear-down aircraft, moving
  water and a soft aircraft shadow. Wheel contact follows the native deck.
- Rollout retains the moving deck edge and runway markings, without the gray
  foreground block or exposed blue strip. Native blank transitions stay blank.
- The mission debrief keeps the original live score, lives and bonus values.
- Player and enemy cannon rounds use compact glowing tracers. Actual missiles
  keep the approved v0.6.0 artwork; distant aircraft remain aircraft.

All 102 v0.6.0 PNGs are preserved. See `source/LANDING_NOTES.md` and
`validation/landing_v0.7.0.json` for scope, implementation and replay checks.

The v0.7.1 follow-up covers the recorded failed water landing: the painted
carrier and sea remain visible through impact and the pause afterward, and
six native-timed fire/spray stages replace the original crash sprites. It keeps
all 130 v0.7.0 PNGs. See `source/LANDING_FAILURE_NOTES.md` and
`validation/landing_failure_v0.7.1.json` for the focused replay checks.

v0.7.2 removes the one-frame original-art flashes when entering the debrief and
leaving it for the following briefing. It changes scene conditions only and
preserves all 131 PNGs. See `source/LANDING_TRANSITION_NOTES.md` and
`validation/landing_transition_v0.7.2.json`.

## Damage and danger display

- A live HULL bar and percentage show native health, including bullet damage,
  lethal missile hits and the reset after losing a plane.
- A clean amber rear-threat display preserves the original warning timing and
  moving enemy-aircraft symbol.
- Incoming missiles have a bright silver/red silhouette at every observed size.
- The impact burst is complete, and the HD sky/cloud scenery stays visible
  beneath the native-timed warm damage flash.

All 58 v0.5.1 PNGs are preserved. See `source/DAMAGE_HUD_NOTES.md` and
`validation/damage_hud_v0.6.0.json` for scope and replay checks.

## Turning and cloud-horizon correction

- Native white clouds keep their own painted cloud artwork at every mapped distance size. They no longer become smoke or fireballs as they approach.
- A painted maritime sky, detailed ocean surface, weathered runway and ivory runway dashes replace the flat scenery colors.
- Sky, ocean and the new continuous cloud deck follow the native bank stages. The flight horizon follows vertical scroll, with a soft cloud/sky blend and no native blue/white dither strip.
- Takeoff deck boundaries and runway markings retain native motion. Ocean texture reaches the landing carrier; v0.7.0 adds the carrier and landing artwork described above.
- All 32 previously approved PNGs are unchanged, including the cockpit, aircraft, missiles and orange explosion artwork.

See `source/HORIZON_NOTES.md` and `validation/horizon_v0.5.1.json` for the turning correction and replay checks. `source/ENVIRONMENT_NOTES.md` records the initial scenery pass.

## Preserved combat artwork

- Painted enemy jets in rear, approaching and overhead views, with native banks, inverted views and distance sizes: 116 mapped layouts using 145 tile patterns.
- Missiles, tracers, ignition flashes, fireballs and smoke: 19 mapped combat layouts using 27 tile patterns, plus four cloud distance layouts corrected in v0.5.0.
- Native positions, animation timing, hit detection and audio remain under game control.

The new artwork is limited to the windshield and exact sprite palettes. All 30 existing pack PNGs are preserved, including the approved cockpit and map fixes. See `source/COMBAT_ART_NOTES.md` and `validation/combat_art_v0.4.0.json` for integration details and tested coverage.

## Preserved work

- Title and native-timed carrier launch, with director and exhaust animation.
- Cockpit HUD, damage-shake registration, radar and landing displays.
- Centered cockpit dials and a cleanly clipped lower dial.
- A windshield edge that stays neutral across runway/sky/cloud colors, with matching attitude-display ticks.
- Mission-one tactical briefing map with correctly filled inland water and all three missile-selection diagrams.
- Artwork masters, build scripts, capture references, supplied replay movies, and recorded validation reports.

Other landing failure outcomes, unrecorded Mission 2 encounters, refueling completion and later missions still need further artwork and coverage. This is recording-based coverage, not a full-game QA claim. See `source/MAP_WATER_NOTES.md`, `source/COCKPIT_COLOR_NOTES.md` and `source/SCREEN_POLISH_NOTES.md` for the included earlier fixes. `README.txt` and `source/PROJECT_NOTES.txt` preserve the earlier handoff.

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

The approved v0.7.3 work is merged into `main` at
`9c05e3d0c25c468791894377cc250fd4086e9af4`. This development review is on
`feature/mission2-v0.8.0`. Keep edits on feature branches and review before
merging. A review build is not a public release or permission to merge.
