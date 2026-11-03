# Carrier landing and cannon tracers — v0.7.0

Based on approved v0.6.0, merged as `b8c0ea52fe609bbdcb103f5cc4004187cb77ddb0`.
The supplied `Top_Gun_HD(3).mmo` contains 4,302 controller frames, including a
successful mission-one approach, side-on touchdown, deck rollout and debrief.
The private recording, ROM, emulator and captures are excluded from this change.

## Findings and changes

The earlier environment pass made the native carrier tiles transparent without
providing a complete replacement hull. Three new image-generated source masters
provide the aft approach carrier, flat side-profile carrier and left-facing
gear-down jet. Their prompts specified painted naval steel, an opaque deck and
hull, a right-side island for the aft view, horizontal broadside geometry, and
no text or logos. Asset preparation trims transparency and scales those masters
to the game's observed geometry; it does not generate replacement art in code.

`landing_mappings.json` contains 21 native carrier layouts, nametable signatures,
CHR-RAM patterns and palettes. The approach plates follow native PPU scroll and
distance stages. They sit above the ocean and below the cockpit's lower mask.
Selection uses the actual rendered nametable rather than a timer that advances
before the geometry is ready.

The side-on scene uses a flat deck and a gear-down aircraft centered on the
native sprite. Two render-only addition tiles allow a slightly larger jet without
changing OAM, movement or collision state. The wheels meet the original deck
height. The native shadow becomes a translucent oval. Four subtle sea offsets
follow bits 2–3 of native frame counter `$001A`; no independent replay timer or
game-memory writes are used. Carrier visibility is checked against the rendered
side-scene tile, keeping transitional frames black until the scene is ready.

During rollout, a background-priority solid sprite previously became a large
gray rectangle over the transparent scenery. Its replacement is transparent
only in the rollout scene. Observed deck lights retain their native masks and
positions but use ivory instead of green. The first actual sea/deck row is
detected across the observed mixed edge patterns, so the painted material
planes meet the moving native boundary without a bright blue gap.

The mission debrief uses the existing console design with new carrier art and
native-position glyphs. Mission status, live score, bonus and remaining planes
continue to come from the game.

## Projectile analysis

The earlier combat atlas gave the small projectile family a tapered missile-like
silhouette. Temporal inspection establishes that the game uses that family for
both incoming cannon fire and outgoing player fire:

- Incoming rounds in the combat recording grow through CHR tiles `$0F`, `$0E`,
  `$0D` (examples at frames 24, 46, 64) before health falls at frame 76.
- After an A-button shot at frame 849, the player's round shrinks through `$0D`,
  `$0E`, `$0F`, `$13` (frames 852, 854, 856, 858) toward the aiming reticle.
- The same palette is used in both directions, so palette alone does not
  distinguish player and enemy rounds. Both now use small, finless warm tracers
  with bright cores, maintaining their original centers and growth/shrink timing.
- `$13` also appears in a multi-tile effect. Its existing layout condition takes
  priority for that effect. `$0A` is a distant aircraft and is left unchanged.
- The actual incoming missile, outgoing missile and impact-burst mappings from
  v0.6.0 are preserved. There are no weapon, damage, hitbox or sound changes.

## Build and scope

`scripts/build_pack.py` runs `scripts/build_landing.py` last. All 102 prior PNGs
remain byte-identical. The new mappings override only their intended scenes and
sprite palettes. The pack contains no ROM patch, music or sound replacement.

`scripts/validate_landing.py` verifies private replay traces, common checkpoints,
audio, HD-pack references, preservation of prior artwork and agreement between
the tested and packaged files. See `validation/landing_v0.7.0.json` for results.
Emulator audio-device metadata is excluded from state comparison; actual PCM
samples are compared separately.

Coverage is the supplied successful mission-one landing plus existing combat,
damage, incoming-missile and opening regressions. Landing failure outcomes,
later missions and refuelling are not newly covered. The game's underlying
landing physics and trajectory remain unchanged; this is a rendering update.
