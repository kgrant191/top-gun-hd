# Scenery and cloud correction — v0.5.0

This review branch starts from approved v0.4.0 main commit
`e3bb36e83e7dba56426dadb9ab5c202191159957`.

## Cloud bug

Four native white-cloud distance layouts were incorrectly classified as three
smoke sizes and one explosion. Their ten CHR patterns now use a dedicated white
cloud atlas. The existing nearby-sprite and mirror predicates still assemble
each size. Exact sprite palettes and the cockpit/world conditions remain in
force. The orange combat explosion family has separate keys and is unchanged.
The corrected classification is 19 combat-effect layouts plus four cloud
layouts, rather than 23 combat-effect layouts.

The original combat atlases and rules remain authoritative for approved combat
art. New cloud rules take precedence over the mistaken family. Existing radar,
panel and menu fallbacks remain present. No sprite-zero timing tile is replaced.

## Scenery

Four painted masters supply the maritime sky, ocean, runway and cloud art.
`scripts/build_environment.py` runs after the combat stages. Native background
tile anchors select the water/cloud and runway material planes once per frame.
Transparent replacements expose those planes; small native masks retain the
horizon boundary, runway dashes and landing-carrier outline and markings.

The native game continues to determine the horizon, deck edge, dash movement,
sprite position, distance changes, animation, hit detection and audio. The pack
does not inject emulator code or modify game memory or ROM. Continuous material
planes avoid a large per-pixel position-rule table and its ocean-scene slowdown.
A lower-screen mask preserves the original black underlay behind the approved
cockpit. All 32 existing PNGs remain byte-identical to v0.4.0.

The landing sequence changes background CHR banks as the carrier approaches.
The mapping includes the observed banks so the surrounding ocean does not
leave native-blue squares. The carrier itself still needs a dedicated HD redraw.

## Rebuild and validation

Run `python3 scripts/build_pack.py` with Pillow and NumPy. Build inputs are
stored in `source/environment_*`; no private replay, ROM, state or capture is
needed to rebuild this stage. The PNG masters are pixel-only copies without
generation metadata. `environment_prompts.json` records the artwork direction.

`scripts/validate_environment.py` validates the two supplied replay sequences,
the unchanged existing art, preserved cockpit and intro checkpoints, loader
output, and installable-pack references. Its report is
`validation/environment_v0.5.0.json`. State comparison excludes only the HD
audio-device metadata, as in the earlier validation. PCM audio is compared
separately. Review videos are derived from recorded emulator frames; recorder
container recovery, if needed, is documented separately from game-state parity.

## Remaining scope

This is mission-one opening, takeoff, clouds, combat and landing coverage. The
carrier model, terrain, later missions, refuelling and full-game QA remain future
work. The new artwork is a development review, not an approval to merge.

## Artwork source

The built-in image generation tool produced four raster masters. The prompts
requested a hazy blue maritime sky, subdued navy/teal ocean ripples, weathered
gray non-skid runway surface without baked-in markings, and a transparent white
cumulus cloud with a pale blue underside. Build code sizes and masks the art to
the original game's geometry. It does not generate substitute raster artwork.
