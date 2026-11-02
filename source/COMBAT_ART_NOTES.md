# Enemy aircraft and combat effects — v0.4.0

This approved combat pass starts from v0.3.2 main commit
`f23e0c16669c328e8d556f0c20fbe909a8f72efb`.

The new aircraft cover rear, approaching and overhead views, native banks,
inversion and distance sizes: 116 mapped layouts using 145 tile patterns.
Missiles, tracers, ignition, fireballs and smoke cover 23 layouts using
37 patterns. Native positions, animation timing, hit detection and audio
remain controlled by the game.

All new rules require the cockpit scene, a sprite origin above native y=128
and an exact transparent-sprite palette. Palette-independent matching can
replace shared sky patterns, so combat rules use `N` defaults. Nearby-sprite
signatures and explicit mirror conditions choose the correct pieces when
patterns are reused across several effect sizes. Existing radar, menu and
panel replacements are carried into overlapping exact keys, preserving
their behavior when world conditions fail. Sprite-zero timing tile 0x20 is
excluded. No ROM patch, custom audio or test fixture is installed.

## Authoritative build inputs

The reviewed atlases and rule blocks are preserved directly as source assets:

- `source/enemy_aircraft_atlas.png` and `source/aircraft_rules.txt`
- `source/combat_effects_atlas.png` and `source/combat_effects_rules.txt`

These are the exact approved artwork pixels and mapping rules. The atlases
contain only PNG image chunks, with no generation/provenance metadata.
The original high-resolution generation masters are not required to rebuild.
The interrupted publishing session lost some intermediate local source files;
using the saved approved atlases preserves the complete installable result
without regenerating or changing the artwork.

Run `python3 scripts/build_pack.py`. The combat stages insert their image
declarations before use, resolve `@IMAGE@` to the current image index and
reject duplicate stage installation. All 30 earlier PNGs and every base rule
are preserved. The 34-file output must match the approved installer byte for
byte. Verify with:

```sh
python3 scripts/validate_combat.py --approved-zip /path/to/Top_Gun_HD_v0.4.0.zip
```

The validator checks PNG decoding, atlas bounds, declared conditions, sprite
palette restrictions, preserved baseline files/rules and complete ZIP parity.
It records historical emulator results separately from this artifact check.

## Emulator validation completed before approval

- 2,054 opening/flight/cloud/combat frames matched native state and PCM.
- 8,253 combat-to-landing frames matched the approved HD baseline state and PCM.
- A 1,390-frame fixture checked all 116 aircraft and 23 effect layouts;
  84,454 opaque pixels matched at the recorded RGB tolerance of six.
- All 48 opening and 119 longer-replay visual checkpoints changed only within
  moving combat sprite cells. Existing cockpit, radar and background art stayed
  unchanged.

`scripts/qa_aircraft_template.lua` preserves sprite zero when injecting test
poses and is excluded from the installable pack. Private replay recordings,
states, captures and their identifying metadata are not added to this branch.
This is mission-one coverage, not a full-game, refuelling or ending QA claim.
Clouds, sea, terrain and later-mission art still need further work.

## Artwork direction

The built-in image generation tool supplied three matching steel-blue/gray
twin-engine fighter views (rear, head-on and overhead), plus a tail-on silver
missile, a white-hot orange fireball and a compact gray smoke puff. Transparent
backgrounds and painted aviation detail keep the silhouettes readable at
native sizes. The atlas assembly fits those images to the game's existing
sprite cells; the reviewed atlas pixels are now the stable rebuild sources.
