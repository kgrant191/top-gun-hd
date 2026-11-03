# Turning and cloud-horizon correction — v0.5.1

This follows local v0.5.0 review commit
`9da7d3df6267525d13f228328d614bc6dbf12cac` on
`feature/environment-v0.5.0`. It is a development build pending review.

## Cause and correction

The first scenery pass positioned a horizontal material plane from a tile at
the left edge of the screen. During turns, the native horizon tilted while
the painted plane stayed horizontal. The original blue/white dither masks
remained visible over it. An enlarged individual cloud also left a broad pale
field surrounding one stationary billow.

`scripts/build_horizon.py` now creates sky, ocean and cloud-deck variants for
the game's seven bank stages. Signed RAM `$0050` selects bank -3 through +3;
the corresponding native slopes are +1/8, +1/16, +1/32, 0, -1/32, -1/16,
and -1/8. The world horizon is at nametable y=192. Mesen's vertical background
scroll ratio of 1 follows the game's PPU scroll, written from RAM `$00FC`.
These values were checked against controller-driven left/right/pitch replays
and native scroll writes. The pack only reads native state; it does not write
memory, patch the ROM or inject emulator code.

Palette entry `$3F06 == $30` selects the cloud layer; other observed flight
palettes select the ocean. Non-carrier native flight dither tiles are
transparent. The carrier outline and markings retain their existing masks.
The runway still uses tile-anchored materials while the takeoff deck reaches
the bottom of the windshield because its world layout differs from flight.

The new cloud-deck master has distant haze and distributed detail across the
whole layer. It fades into the sky over 12 native pixels, beginning four
pixels before the nominal horizon. Ocean uses a tighter two-pixel fade.
Banked sky variants shear padded original pixels at the same scale, avoiding
a zoom at the first bank stage. This uses native discrete banks, not a 3D
world model. No extra horizontal parallax is invented.

## Preservation and validation

The v0.5.0 cloud sprite atlas, all 32 pre-environment pack PNGs, and approved
cockpit/combat rules remain unchanged. The new deck is a fifth generated
environment master; its direction is recorded in `environment_prompts.json`.
The old enlarged cloud plane is removed from the installable pack.

Run `python3 scripts/build_pack.py` to rebuild without private replay inputs.
`scripts/validate_horizon.py BANK_WORK ENVIRONMENT_WORK` checks native trace,
checkpoint state, PCM audio, unchanged cockpit/intro images and pack references.
The four replays cover 16,810 frames: 1,020 cloud-turn frames, a 4,520-frame
landing-input fixture (including 3,500 original lead-in frames), the 3,017-frame
opening/takeoff recording and the 8,253-frame combat-to-landing recording.
The cloud fixture uses ordinary controller input and exercises all seven banks.
The landing fixture adds the same inputs after the ocean transition; native
landing mode locks the bank level, so this is not an ocean free-turn test.
Only HD audio-device metadata is excluded from checkpoint state comparison;
PCM is compared separately. See `validation/horizon_v0.5.1.json` for results.

Mission-one coverage only. Later missions, terrain and refuelling need
coverage, and the carrier itself still needs a dedicated HD redraw.
