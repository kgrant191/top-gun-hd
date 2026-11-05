# v0.15.0 — close shuttle and recorded endings

The two supplied movies are preserved as `reference/mission4_close_and_award.mmo`
(4,755 inputs) and `reference/mission4_victory.mmo` (2,205 inputs). Native traces
supply the read-only CHR, palette, nametable and OAM selectors in
`ending_mappings.json`. `scripts/build_ending.py` runs last in the full build.

## Shuttle

Distance stages 7–12 reuse the v0.14.0 shuttle master. Exact nametable-layout
signatures precede distance fallbacks. Two-page scrolling remains native.
The upper tower becomes sprites at close range; those keys are suppressed
only while the corresponding boss body is visible and are included in the
registered HD plate. No collision, health or distance logic is changed. Three unique explosion-edge
keys also retain their approved HD cells when overlapping bursts occlude the
normal neighboring anchors during a Mission 4 hull hit.

## Endings

Mode 8 game over, mode 9 award, mode 10 Mission 4 summary and mode 11 carrier
celebration use visible nametable signatures. Outgoing carrier/game-over
frames retain their artwork until native nametable transfer replaces them.
Live score digits are selected individually from the original nametable.
Background crop offsets are nonnegative source offsets, as required by Mesen.

The carrier body and sunset stay registered across five recorded canopy/pilot
layouts. Every sprite anchor in a pose must match, preventing the shared
arm-down key from selecting arm-up. Native exhaust layouts and flypast
positions select their matching overlays. The small floating symbol and
start prompt retain native movement and visibility. Deck crew use the
original static poses; no timer, RAM write or input modification is added.

## Scope and reproducibility

All 240 previous PNGs and their rule order are preserved. New artwork is
appended. Source masters and the deterministic builder are committed; the
runtime ZIP contains only pack files. Full replay validation checks native
RAM, CHR, nametables, OAM, palette, state checkpoints and PCM audio, as well
as actual rendered video and an isolated rebuild.

The two recordings begin on opposite sides of the shuttle outcome; they do
not show the continuous defeat-to-success transition. Other unrecorded
outcomes, including Mission 3 boss defeat and landing, remain unverified.
