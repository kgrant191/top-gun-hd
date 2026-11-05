# Mission 3 missing views and base approach — v0.11.0

Base: merged main `dce71e720f4fb98dd39f030dabccb6590636db23` (approved v0.10.1).
Branch: `feature/mission3-completion-v0.11.0`. Development review only.

## Supplied recordings

| Movie | Input frames | Coverage |
| --- | ---: | --- |
| enemy-plane.mmo | 389 | Opposite bank of the large aircraft |
| enemy-plane2.mmo | 290 | Additional banked fighter, missiles and impacts |
| enemy-wall.mmo | 665 | Repeated large barricade columns and loss/retry |
| enemy-radar.mmo | 731 | Close rotating radar, including the missing side |
| enemy-radar2.mmo | 329 | Radar palette/layout variant and overlapping impacts |
| boss(1).mmo | 2889 | Base approach stages 0–6, damage and retry |

All 5,293 inputs belong to Mission 3 flight mode. This is coverage of the
supplied recordings; later base sizes, boss defeat, Mission 3 landing,
Mission 4 and ending have not been tested.

## Corrections

The earlier banked aircraft rules admitted only unmirrored OAM sprites.
Opposite banks now use the exact same atlas pieces with the opposite mirror
gate. One newly captured banked pose reuses the approved front aircraft
master. Two radar layouts use the existing dish master with full relative
sprite signatures; per-key fallbacks cover their clipped pieces. The large
wall's repeating upper cell and short foot reuse the existing brace module.
No approved image is repainted.

Native Mission 3 base CHR overlapped older explosion substitutions. Seven
stable nametable layouts now select seven sizes of one consistent base.
Each plate follows native PPU scrolling. A presence check clears the plate
when the original base clears, and the native distance counter provides a
single fallback during partial nametable transfers. Independent ground-gun
sprites use the approved turret component and retain their own lifetimes.

The damage palette temporarily replaces desert colors with shared impact
colors. Desert plates and exact world-tile masks now cover this palette's
entire lifetime, including the final reset frames. The approved impact wash
still applies. Incoming missiles also retain their approved tile pieces
when overlapping explosions break the original complete-sprite signature.

## Boss health

Six native OAM cells at x=192..232, y=29 drive the BASE display. Tile 10 is
full, 11 is half and 12 is empty (hexadecimal tile numbers). Exact CHR keys,
palette, position and Mission 3 conditions select the replacement. There is
no guessed RAM health counter, fixed fill, game-memory write or change to
hit detection. The recording shows four full and two empty cells whenever
the bar is visible; it does not exercise boss-health depletion. Half-cell
art is included from the native CHR pattern but is not replay-exercised.

## Artwork and reproducibility

`mission3_base_master.png` was produced with the built-in image generator.
Final prompt: an isolated desert outpost with two round olive-gray domed
buildings arranged lower-left/upper-right, dark recessed front openings,
thin antennas and three small utility sheds; weathered olive steel and
sand-colored concrete, warm upper-left sunlight, crisp painted arcade art,
transparent spaces, no terrain, effects, text or HUD. A follow-up requested
clean transparent cutout edges and unchanged buildings. Generated alpha is
preserved. Only deterministic cropping, resizing and tile/plate assembly
are used in the build.

The additional aircraft, radar, barrier and turret art reuse existing source
masters. `mission3_completion_mappings.json` stores the captured geometry
and CHR keys. `build_mission3_completion.py` runs after the tank correction
in the complete build. Seven world plates and one 69-cell atlas are added;
all 171 v0.10.1 pack PNGs remain byte-identical.

## Verification

`validation/mission3_completion_v0.11.0.json` records replay comparisons,
PNG preservation, exact native-color checks, native health states, rule
references, pack hashes and the isolated deterministic rebuild. The actual
1024×960 replay was inspected through all recorded approach sizes and the
damage/retry transition. RAM, nametable, OAM, palette and CHR streams are
compared frame-by-frame; sampled CPU state excludes only audio-device
metadata, while recorded PCM audio is compared separately.

The install ZIP contains only pack files at its root. Private movies,
ROM, emulator and capture intermediates are excluded. Source changes are
available as a separate incremental Git bundle. Approval is required before
pushing/merging this new review build or publishing a release.
