# Landing/debrief transition correction — v0.7.2

Base: `20544f0ccff39b29e06d9c6916942ccb1b105fe3` (v0.7.1).
The failed-landing preview revealed an original carrier frame at input frame
510, after the blank transition had begun. Full frame inspection also found an
original results frame at 705, just before the next briefing loads.
The successful-landing replay also exposes four transitional frames with
leftover cockpit or loading graphics at 4143, 4144, 4146 and 4148. They are
covered by the same pre-debrief blank guard.

Both come from the native game changing RAM mode `$0018` one frame before
clearing the old nametable. A mode-only scene gate therefore disabled the HD
overlay while the previous original scene was still rendered.

`scripts/build_landing_transition.py` adds two narrow extensions:

- In debrief mode `$0A`, reuse the existing black transition plate until the
  actual debrief glyph signature appears. This covers the stale carrier or
  cockpit frame without exposing original artwork between blank frames.
- In the next-briefing mode `$05`, retain the existing debrief panel and exact
  glyph replacements while its rendered signature is still present, the
  briefing initializer `$0019` is zero and transfer flag `$001B` is zero.
  The native transfer disables rendering before clearing the nametable;
  cached tile-position data can persist during that blank interval, so the
  loading-state checks are necessary to avoid showing an empty HD panel.

All existing rules retain their relative order, and all 131 PNGs are unchanged.
No artwork, duration, audio, score, gameplay state or mission outcome changes.
The next mission's own briefing artwork is outside this correction.

The successful and failed landing recordings are replayed and compared against
native state/PCM and v0.7.1 video frames. The transition frames receive explicit
pixel checks; every other captured video frame must be identical. See
`validation/landing_transition_v0.7.2.json` for results. The build also checks
image references and reproduces the tested pack from an isolated source copy.
