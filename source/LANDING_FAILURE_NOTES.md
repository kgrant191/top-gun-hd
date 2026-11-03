# Failed water landing — v0.7.1

This follows the reviewed v0.7.0 artwork at
`22b85bb4943baf7c496eb9d8200afa05ad01caa8`. The supplied
`Top_Gun_HD(4).mmo` has 885 controller frames: final approach, a landing short
of the carrier, water impact, a pause, debrief and the next mission briefing.
The private recording, ROM and emulator remain outside this change.

## Cause and fix

The painted side scene previously required landing substate `$009F == 3`.
The water-impact sequence changes that value to 6, then 7, while the native
carrier scene stays on screen. This disabled the HD scene and exposed its
original carrier, sea and crash sprites for the rest of the sequence.

`build_landing_failure.py` adds the same scene artwork for substates 6–7,
requiring the side-scene nametable signature too. Those substates are also used
by successful cockpit rollout, so the state check alone would be unsafe.
The original successful-scene rules remain in their original relative order.
All 130 existing PNGs remain byte-identical.

The six native crash layouts are stored in `landing_failure_mappings.json`.
An existing native shadow sprite supplies the moving origin. Twenty render-only
addition tiles form one complete crash image, preventing holes where the native
late-stage spray uses a sparse sprite layout. Nearby original sprite signatures
select each stage, including the last spray frame after the native state has
advanced to its pause. Nothing is scheduled using movie-frame numbers.
Original crash-effect keys and the obsolete aircraft shadow are hidden only in
this failure scene; synthetic additions are transparent everywhere else.

The new `landing_crash_master.png` was made with the built-in image generator.
Prompt: a transparent six-frame sheet in a 3-column, 2-row grid, straight side
view, painted realistic navy-aircraft water impact, equal cells with aligned
waterlines; compact orange fuel burst, expanding fireball, fire/steam and white
spray, mostly steam/spray, falling spray, residual foam/mist; no aircraft, ship,
ocean rectangle, horizon, labels or background. The build crops individual
cells, fits them to the native effect footprint and aligns their waterlines.

## Preservation and coverage

The aircraft trajectory, impact trigger, animation duration, audio, score,
remaining-plane count and mission transition remain under native control.
The game's own debrief still says "MISSION ACCOMPLISHED" after this failed
landing; the pack preserves that text and the displayed zero remaining planes.
The following mission's unfinished artwork is outside this change.

`scripts/validate_landing_failure.py` checks native state/PCM parity for both
landing movies, pixel equality of the successful landing, the exact window of
changed failed-landing frames, prior artwork/rule preservation and package
references. Audio-device metadata is excluded from state comparisons; actual
PCM samples are compared separately. See
`validation/landing_failure_v0.7.1.json` for the recorded results.

This covers the supplied water-impact failure. Other failed-landing paths,
later missions and refuelling still require recordings and additional coverage.
