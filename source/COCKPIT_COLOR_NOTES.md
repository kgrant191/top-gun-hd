# Cockpit color corrections — v0.3.1

Branch: `feature/cockpit-color-fixes-v0.3.1`.
Base: merged v0.3.0 main, `afef647b114539c8e1a84f3e1df9933b74d7280e`.
This is a visual review checkpoint.

## Windshield edge

Two separate issues produced the blue/green line above the cockpit:

1. The cockpit master included a small sky-colored margin in its upper crop.
2. The native world renderer continues through scanlines 128–129, while the
   HD coaming begins at scanline 128. Those foreground pixels could overdraw
   the coaming with changing palette colors.

The first vertical source segment now starts at native-equivalent row 131
instead of 126 and still maps into destination rows 128–143. This fits the
existing painted metal to the windshield boundary. Everything from row
144 downward retains the previous geometry. The FIRE CONTROL label is
centered again within the resulting metal area.

`build_flight_ui.py` copies the first two coaming scanlines into a transparent
foreground cap at priority 30. The cap masks only the world/coaming overlap;
it does not cover the instruments. Its normal and two damage variants use
the existing native impact conditions and exact four-HD-pixel shift.

## Right attitude tick

Native CHR pattern `$75` contains the right-hand tick. Its color-index-one
pixels were receiving the ground fill instead of the tick color. It is now
included with the other pale tick mappings, scoped to the attitude window.
The horizon and bank/pitch pointer remain native-driven.

## Build and validation

Run `python3 scripts/build_pack.py` with Pillow 12.3.0 and NumPy 2.3.5.
Every PNG-writing build stage uses `scripts/pack_io.py` for atomic replacement,
so a reader receives a complete image. This also protects the cockpit asset
updated by successive build stages. Valid image output remains byte-identical.

Only four existing PNGs change: the three cockpit positions and
`panel_details.png`. The three new `windshield_cap*.png` files contain the
foreground strips. The other 23 existing PNGs are byte-identical, including
all title, launch and menu art. The original artwork masters are preserved.

Validation covers 2,054 input frames of runway, takeoff, flight, cloud
transitions and opening combat, plus 180 input frames exercising damage
shake. Every frame's game-state trace and the PCM audio match native output.
The metal cap is checked in all 2,053 recorded flight frames, and the damage
check confirms the existing four-HD-pixel left/right displacement.

The public validation report contains test results and counts. Recordings,
save states, capture data and their identifying metadata stay outside this
branch. The validation script accepts the owner's private input path with
`--movie`; use the established replay capture workflow locally.

Only the initial state-load frame is absent from each video recording.
The scope is these two cockpit defects. Later-mission screens, remaining
world/combat artwork, refuelling and endings still need separate passes.
