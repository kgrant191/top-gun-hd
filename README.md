# Top Gun HD

Development review build **v0.12.0** for the NES Top Gun (USA), using a Mesen HD pack. This is unfinished work, not a full-game release.

## Install

Copy the contents of `pack/` (not the surrounding source tree) into the emulator’s HD pack folder associated with your own Top Gun (USA) ROM. Enable HD packs and reopen the ROM. No ROM or emulator executable is included.

## Mission 4 night combat

v0.12.0 adds an indigo-violet night sky, a silver-lavender cloud deck and a
dark ocean surface. All seven native bank stages and vertical scrolling are
preserved. The night terrain remains visible during the missile-hit palette,
with the original impact wash, and after retry. The Mission 4 briefing retains
its geography, moving markers and live weapon selection.

The approved instruments, HULL bar, danger display, aircraft, clouds, effects
and naval targets now cover the recorded Mission 4 palettes. Six close banked
aircraft layouts and two boat distance sizes are added from the approved art.
All 186 v0.11.2 PNGs remain byte-identical. No ROM, input, collision, game-memory,
timing or audio changes are included.

The supplied 10,352-input recording covers the preceding debrief, Mission 4
briefing, takeoff, cloud-top combat, ocean transition, damage, retries and game
over. Later terrain, refueling, the space-shuttle target and ending are not in
this recording. See `source/MISSION4_NOTES.md` and `validation/mission4_v0.12.0.json`.

## Mission 3 desert combat

v0.11.2 completes the recorded base flyover through distance stage 12,
including the closer ground guns and geometry crossing the nametable boundary.
The base stays HD through the missile-hit palette and retry. All 180 v0.11.1
PNGs remain unchanged. See `source/MISSION3_BASE_CLOSE_NOTES.md`.

v0.11.1 fills the missing left edges of radar dishes in both radar recordings.
Render-only sprite additions complete the painted silhouette where the native
radar omits a tile. Existing dish size, orientation and artwork are retained;
all 179 v0.11.0 PNGs remain unchanged. See `source/MISSION3_RADAR_EDGE_NOTES.md`.

v0.11.0 fixes missing mirrored aircraft, close radar views and the large
barricade tiles shown in six additional recordings. Seven recorded base
approach sizes now use matching desert architecture instead of explosion
pieces. Independent gun sprites keep their native movement and lifetime.
The BASE health display preserves the native full, half and empty segments;
the supplied boss movie stays at four full cells out of six. Desert and base
art also remain HD during the recorded damage and retry transition.
All 171 approved v0.10.1 PNGs remain unchanged. See
`source/MISSION3_COMPLETION_NOTES.md` and `validation/mission3_completion_v0.11.0.json`.

v0.10.1 fixes close tanks reverting to NES artwork when viewed from the
opposite side. Both orientations reuse the same HD tank atlas. All 171
v0.10.0 PNGs are unchanged. See `source/MISSION3_TANK_FIX_NOTES.md`.

v0.10.0 adds a painted desert surface that follows native pitch and all seven
bank stages, radar emplacements, armored vehicles and modular barricades.
The Mission 3 briefing map preserves its geography and moving markers.
Approved cockpit, live HULL and danger displays, aircraft, projectiles,
clouds and the complete refueling sequence now cover the Mission 3 palettes.
Two newly recorded banked fighter layouts reuse the approved aviation art.

All 154 v0.9.1 PNGs remain unchanged. No ROM, game memory, collision, input,
score, timing or audio is modified. See `source/MISSION3_NOTES.md` and
`validation/mission3_v0.10.0.json` for replay checks and scope.
The supplied movie ends at game over after refueling and further combat;
v0.11.2 adds the full recorded base flyover described above; boss defeat and
Mission 3 landing still need coverage.

## Mission 2 naval combat and refueling

v0.9.1 corrects the carrier's close approach. Two views previously interpreted
as damage/destruction were healthy distance stages. Twelve captured sizes now
use an opaque HD deck, with separate bridge and gun sprites that follow their
native movement and lifetime. Three missing banked fighter layouts reuse the
approved aircraft art, and the ordinal reads **1ST TARGET!** with a numeral 1.
All 141 v0.9.0 PNGs remain unchanged; new mappings supersede the mistaken
carrier substitutions. See `source/MISSION2_APPROACH_NOTES.md` and
`validation/mission2_approach_v0.9.1.json`.

v0.9.0 completes the recorded refueling departure and carrier boss encounter.
The tanker exits once and stays gone when the scroll resets. Boss-route
horizon tiles are masked correctly during turns. It introduced carrier art
and an amber health meter driven by the original six meter cells. The
damage/destruction interpretation is corrected by v0.9.1 above.
All 139 v0.8.2 PNGs remain unchanged.
The two supplied movies also cover the return to combat, retry, successful
Mission 2 landing and debrief. See `source/MISSION2_COMPLETION_NOTES.md`
and `validation/mission2_completion_v0.9.0.json`.

v0.8.2 removes the duplicate tanker during refueling entry. One aircraft
enters from the right and reaches the center before the original boom and
guidance sequence continues. All 138 v0.8.1 PNGs remain unchanged.
See `source/TANKER_ENTRY_NOTES.md` and `validation/refuel_entry_v0.8.2.json`.

v0.8.1 fixes the five issues reported in the first Mission 2 review: blue
horizon strips during the takeoff-to-flight transition, an unmapped distant
enemy silhouette, the small boat incorrectly using impact artwork, the green
native danger target during HUD transitions, and green radar blocks at the
start of refueling. Submarines also have a brighter steel hull and white wake.
All 136 v0.8.0 PNGs remain unchanged; corrections add an atlas and a small sky-edge strip.
See `source/MISSION2_FIX_NOTES.md` and `validation/mission2_fixes_v0.8.1.json`.


v0.8.0 extends the approved scenery, cockpit, aircraft and effects to the
Mission 2 palettes. It adds painted boats and submarines, the second tactical
map, a scrolling tanker, and a growing refueling boom. The live guidance
monitor preserves the game's instructions and coupling movement.

The refueling blackout came from landing and refueling sharing mode/state
numbers. The pack now checks the route as well, keeping the cockpit and sky
visible during refueling. All 132 approved v0.7.3 PNGs remain byte-identical.

The original v0.8.0 coverage follows the supplied 14,475-frame Mission 2
recording through the refueling controls; v0.9.0 adds the completion and boss
recordings described above. Unrecorded target sizes, other outcomes and later
missions still need additional coverage. See `source/MISSION2_NOTES.md` and
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

Other landing failure outcomes, unrecorded encounters, Mission 3 boss defeat, landing and later missions still need further artwork and coverage. This is recording-based coverage, not a full-game QA claim. See `source/MAP_WATER_NOTES.md`, `source/COCKPIT_COLOR_NOTES.md` and `source/SCREEN_POLISH_NOTES.md` for the included earlier fixes. `README.txt` and `source/PROJECT_NOTES.txt` preserve the earlier handoff.

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

The approved v0.11.2 work is merged into `main` at
`6b19e505d87ebf531fe08847383d3271d95290a3` (approved source commit `5b53b7b`).
This development review continues from that exact approved source tree on
`feature/mission4-v0.12.0`. Keep edits on feature branches and review before
merging. A review build is not a public release or permission to merge.
