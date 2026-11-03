# Damage and rear-threat display — v0.6.0

Development review build based on approved v0.5.1 main commit
`c373a9e665690780c72ecb3613c97cd304c83c20`.

## Corrections

- The original health strip was hidden by the painted panel. A twelve-segment
  HULL bar and percentage now occupy that strip, with green, amber and red
  states. Both register with the existing native one-pixel impact shake.
- Native RAM `$004E` is initialized to 12. The bullet-hit routine subtracts 3;
  a lethal missile sets it to zero and respawn restores 12. The supplied
  danger movie demonstrates 9 → 6, and the missile movie 12 → 0 → 12.
  The pack only reads this value. It does not alter damage or add regeneration.
- The rear-threat instrument uses clean amber outlines and a smooth moving
  aircraft symbol. Its original heading visibility and target movement remain
  native. Two nametable checks distinguish this screen from landing guidance.
- Enemy missile growth includes previously absent CHR variants. The new
  high-contrast silver/red nose-on artwork is split into the original native
  sprite cells. It retains native position, footprint and collision behavior.
- Seven observed flame layouts now have coherent artwork. Nearby checks use
  exposed top-rim tiles because incoming missiles can cover the flame center.
  Nearby offsets must be inverted for mirrored sprites before atlas slicing.
- The missile death flash uses palette `0F301016`, absent from the earlier
  scenery pass. It now retains the banked cloud layer, with a translucent warm
  damage wash, rather than displaying native red/gray scenery. The separate
  native solid-center sprites are hidden only during lethal impact.

## Build and validation

`scripts/build_damage_hud.py` is the final stage of `scripts/build_pack.py`.
`source/damage_hud_mappings.json` preserves captured CHR keys and layouts, so
rebuilding needs no ROM or private movie. The two generated artwork masters
are `incoming_missile_master.png` and `impact_burst_master.png`. Instrument
geometry, typography, health segments and damage tint are deterministic code.

All 58 existing v0.5.1 PNGs remain byte-identical. New foreground layers use
separate priorities for the health strip and impact wash, avoiding the
existing windshield-cap layer. The rear-threat instrument is behind native
sprites so its moving aircraft remains live.

`scripts/validate_damage_hud.py WORK_DIR PREVIOUS_WORK_DIR` checks native game
state, checkpoints, PCM audio, pack bounds and the five native health levels.
See `validation/damage_hud_v0.6.0.json` for measured results. The health-level
fixture is isolated test code, excluded from the installable pack. Ordinary
movie replays and the production pack never write game memory.

This covers the two supplied movies plus the existing mission-one opening
and combat-to-landing regressions. It is not a whole-game QA claim.

## Artwork prompts

Built-in image generation supplied the two new transparent production assets:

- Incoming missile: near-frontal missile flying toward the viewer; red-orange
  nose, ivory/silver metal, four X-shaped fins, dark outline and bright edge
  highlights for small-size readability; compact amber engine glow; no trail,
  background or target ring.
- Impact burst: compact frontal fireball with a bright ivory-yellow center,
  orange flame lobes and short ember tendrils; coherent rounded silhouette,
  no black center, debris, background or text.
