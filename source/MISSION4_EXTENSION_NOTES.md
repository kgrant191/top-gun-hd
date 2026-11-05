# Mission 4 ground combat and refueling — v0.13.0

Previous review build: v0.12.0, `235658ec0b1b7b32462a7f5a520edd01bae7686c`.
Approved integration base: v0.11.2, `5b53b7b84529bd5a72e648b5a70964169e7d6fc1`.
Continue the unmerged Mission 4 review branch. The new bundle includes both
Mission 4 revisions above the approved base; no publishing or merging yet.

## Recording coverage

| Movie | Inputs | Coverage |
| --- | ---: | --- |
| Top_Gun_HD1.mmo | 651 | Missing opposite bank fighter views |
| Top_Gun_HD2.mmo | 978 | Naval distance views and combat |
| Top_Gun_HD3.mmo | 252 | Close and mirrored boat views |
| Top_Gun_HD4.mmo | 256 | Two small fighter sizes |
| Top_Gun_HD(20261105-175157).mmo | 6,535 | Ocean-to-red-ground transition, ground combat, refueling, dark terrain, damage and retry |

The five recordings total 8,672 inputs. They do not show the final target or
ending. Phase names describe the recorded appearance; no new game mechanics
or terrain semantics are inferred.

## Rendering changes

The old non-Mission-2/3 tanker fallback selected a two-page aircraft plate in
Mission 4. Mission 4 now receives the approved right-page arrival and
left-page departure plates, plus the phase-before-8 visibility gate. The old
fallback explicitly excludes Mission 4. The connection/release transition
retains the large boom for the one frame where phase 6 begins before the OAM
pose changes. Exact CHR, mirroring and Y predicates match only that frame in
the recorded phase-6 sequence.

A night sky plate above NES background and below sprites clears wrap-boundary
fill cells during refueling. The tanker remains at foreground priority 31;
native boom, clouds, movement and lifetime remain controlled by the game.
Separate narrow raster edges cover the top and bottom during the return.
Mission 4 palette aliases hide the native solid sprite columns at both screen
edges. A scoped small-flame fallback keeps the upper corner HD when an
incoming missile obscures its neighboring sprite.

Two imagegen terrain masters provide muted red-violet desert and cool slate
rocky terrain. Seven affine bank transforms and the established scrolling
geometry follow native state. Palette checks clear the ground during tanker
flight, while phase predicates retain terrain through the damage palette.
Captured background keys suppress the old colored horizon cells.

Ground targets reuse the approved Mission 3 tank, radar and barricade rules,
including render-only additions that complete radar edges. Refueling guidance,
boom, cockpit, effects and terrain palettes receive scoped aliases. Newly
captured boat and fighter layouts reuse existing imagegen masters, preserving
native OAM positions, orientation and sizes. Exact palette additions retain
older generic alternatives outside their scope.

All 216 v0.12.0 PNGs remain byte-identical. The extension adds 16 PNGs. The
pack changes no ROM, game memory, input, collisions, timing, score or audio.

## Validation

`scripts/validate_mission4_extension.py` compares each supplied recording with
native Mesen output: every input's RAM, nametable, OAM, palette and CHR data;
state checkpoints; and bit-identical PCM. It also checks the original
10,352-input Mission 4 recording, scans actual HD video for original sprite
colors, validates atlas references, preserves prior PNG hashes and verifies
an isolated rebuild. The earlier recording remains pixel-identical to v0.12.0, including its
pre-existing small-flame native-color candidates. Final edge and flame fixes
apply only to refueling and ground phases absent from that recording.
Detailed results are in
`validation/mission4_extension_v0.13.0.json`.

The preview is captured from the actual HD emulator and includes all five
new clips in upload order with native audio. Captures can omit one or two
edge video frames, while traces and PCM cover every supplied input.
