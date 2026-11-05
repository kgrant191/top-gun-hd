# Mission 3 desert combat — v0.10.0

Base: approved v0.9.1 source commit `74167a8`; merged main is
`e2af94b7e37740616eb3abfb881a801f5a914f45`.
Branch: `feature/mission3-v0.10.0`. Development review, not a public release.

The user's `Top_Gun_HD(7).mmo` supplies 21,467 controller frames. It starts
with the preceding Mission 2 debrief, then includes Mission 3 briefing,
weapon selection, takeoff, desert combat, refueling through connection and
departure, further combat and game over. It does not reach the base boss
or Mission 3 landing. ROM SHA1: A39376136CCCA0025063F3356B9EB41666AFF0BE.

## Implementation

- Mission 3 is native RAM $0030 = 3. The flight instruments and enemy aircraft
  share Mission 2 palettes; the ground uses $3F06 = $27. Read-only scoped
  rules reuse the approved cockpit, warning, health, effects and flight art.
- Seven desert plates follow native signed bank $0050 and vertical PPU
  scroll. Haze softens the horizon. Bank-matched sky strips prevent the
  previous scroll value from wrapping sand onto the first scanline.
- The third briefing traces the recorded geography and inland water, with
  warm sand colors, the approved console frame and native moving markers.
- Radar emplacements, armored targets and repeating barricades use captured
  CHR content, palette and OAM layouts. Relative sprite signatures separate
  shared pieces. Mirroring, screen position, size progression and lifetime
  follow native sprites; fallbacks retain coverage when a group is clipped.
- Two missing banked aircraft layouts reuse the approved front/rear masters.
  Ground-palette projectile patterns reuse existing combat art.
- Tanker entrance/departure, monitor and boom reuse the Mission 2 artwork.
  Two additional growth keys and the largest fully connected boom stage
  are added from the same master. Specific refueling rules precede generic
  instrument rules. A three-scanline sky strip closes the raster split gap
  above the cockpit while allowing the boom to render in front.
- New exact keys retain earlier default alternatives. All 154 approved pack
  PNGs are byte-identical. No ROM patches, game-memory writes, input changes,
  hitbox changes, replacement music or replacement sound are included.

## Source and artwork

`build_mission3.py` is the last stage in `build_pack.py`.
`mission3_mappings.json` contains captured patterns and sprite geometry, so
rebuilding does not need the private ROM, emulator or temporary recordings.
`map_geometry.py` extracts the existing Mission 2 contour routines unchanged.

Four source masters were created with the built-in image generator:

- `mission3_desert_master.png`: full-bleed forward-looking ochre desert
  terrain, fine distant ridges, warm haze, sand and rocky gullies; realistic
  painted aviation style; no sky, buildings, roads, vehicles or text.
- `mission3_radar_master.png`: isolated olive radar dish, metallic mesh,
  stout pedestal and armored base, seen slightly from above and in front;
  crisp daylight silhouette on transparency, no scenery or effects.
- `mission3_tank_master.png`: isolated olive armored tank, front three-quarter
  view from above, readable tracks, turret and foreshortened barrel; subtle
  sand wear and silver highlights, transparent background, no insignia.
- `mission3_barrier_master.png`: one square steel barricade module with
  diagonal X braces and short feet, frontal slight top view, sand wear and
  bright rim; transparent background, no lettering or scenery.

The saved masters are authoritative. Generated alpha is preserved; crops,
resizing, banking and tile assembly are deterministic production operations.
Aircraft, tanker, boom, sky and cockpit source art are reused unchanged.

## Validation and handoff

See `validation/mission3_v0.10.0.json` for the current release replay,
per-frame native RAM/nametable/OAM/palette and CHR checks, sampled CPU state,
PCM comparison, visual checks, preserved assets, rebuild and installer hashes.
The full recording is replayed from its embedded state. The final ten-rule
takeoff-mask correction is checked separately across inputs 1801–2400 against
an identical native run. It adds no image or exact palette keys and changes
only Mission 3 takeoff mode 6; the preceding full replay covers all other modes.
Mesen's default test-runner wall-clock timeout is too short for this recording;
use `--testRunner --timeout=900` and isolated runtime folders/settings.
Native recording uses the existing capture hook. Screenshots in this runtime
return the actual 1024x960 HD output; the original capture is 256x240.

Private QA and the user-supplied ROM/emulator remain outside the installer.
The install ZIP contains only `pack/` contents at its root. The Git bundle is
a separate source handoff, based on approved commit `74167a8`.
Review approval is still required before pushing/merging or publishing a release.
