# Mission 4 night combat — v0.12.0

Base: approved v0.11.2 commit `5b53b7b84529bd5a72e648b5a70964169e7d6fc1`.
GitHub main was confirmed merged at `6b19e505d87ebf531fe08847383d3271d95290a3`.
Branch: `feature/mission4-v0.12.0`. Review build; not pushed or merged.

The user supplied `Top_Gun_HD(10).mmo`, containing 10,352 inputs. Its embedded
state starts at the end of Mission 3. It includes Mission 4 briefing, weapon
selection, takeoff, cloud-top flight, the air-to-sea transition, naval combat,
three lethal hits, retries, and game over. It does not reach later terrain,
refueling, the space-shuttle target or the ending.

## Native scene selection

Mission 4 is RAM $0030 = 4. The opening purple cloud flight uses background
palette `0F333103`; the ocean section uses `0F120C01`. Takeoff uses `0F001103`.
The night sky is an intentional interpretation of the supplied purple palette.
The native bank at $0050 and PPU vertical scroll drive the same seven surface
geometries as the earlier approved scenery.

RAM $0037 progresses from 0 to 1 at the air-to-sea transition. Palette changes
select the normal cloud/ocean layers, preserving the original transition frame.
During the shared impact palette, $0037 selects the appropriate night surface.
This avoids the old generic impact rule showing daylight clouds over the sea.
The original warm damage wash, native timing, health and retry remain intact.

Exact palette copies retain the approved cockpit, HULL, danger, reticle,
aircraft, projectiles, cloud sprites and naval targets. Six newly recorded
banked aircraft layouts reuse the approved front/rear masters, with relative
sprite signatures and per-cell fallbacks. The previously unmapped distant boat
and four-cell near boat use the same approved boat master. No new gameplay,
ROM, input, collision, audio or timing writes are introduced.

The briefing traces the captured native geography and retains the native X
and moving ship marker, text progression and weapon-selection values.
All previous rules remain in their original order, and new exact palette keys
retain older generic alternatives outside Mission 4. All 186 approved PNGs
remain byte-identical.

## Artwork and source

The built-in image generator created three lighting variants from the existing
sky, cloud-deck and water masters. Prompts requested a full-bleed painted
aviation texture, preserving perspective and composition: indigo-violet sky
with sparse faint stars and no moon; silver-lavender cloud tops; dark teal-blue
water with subdued silver highlights and no reflection stripe. No objects or
text were added. The exact generated masters are retained in source as
`mission4_sky_master.png`, `mission4_clouddeck_master.png`, and
`mission4_water_master.png`. Cropping, resizing, bank transforms, alpha seams,
and sprite assembly are deterministic pack production operations.

`mission4_mappings.json` stores native terrain patterns, map geography and boat
layouts. `mission4_aircraft_mappings.json` stores the six new native aircraft
layouts. `build_mission4.py` runs last in `build_pack.py` and does not require
the private ROM, emulator or movie to rebuild.

## Verification

`validation/mission4_v0.12.0.json` records complete native RAM, nametable, OAM,
palette and CHR stream comparison, sampled state and bit-identical PCM for
all 10,352 inputs. The approved Mission 3 base-flyover/impact movie provides
2,683 additional inputs, with unchanged rendered video. All pack files are
compared with an isolated clean source rebuild. The original-art audit scans
the full Mission 4 gameplay video, with intentional native blank frames
excluded. Visual review covers the menu, takeoff, all bank stages, new aircraft,
new boat sizes, terrain transition, damage and retries.

The preview is actual Mesen output with its original recorded audio. The
installer contains pack files at the ZIP root, with no ROM or emulator.
