# Mission 4 helicopters, danger display and shuttle — v0.14.0

Continue from v0.13.0, commit `26caa213315ecbbfb3227af57ae558459d418b14`,
on the unmerged Mission 4 review branch. Integration base remains approved
v0.11.2, `5b53b7b84529bd5a72e648b5a70964169e7d6fc1`.

## Recorded coverage

`Top_Gun_HD(20261105-184545).mmo` supplies 8,420 inputs: dark rocky combat,
helicopters, repeated danger/radar transitions, shuttle approach, damage,
retry and game over. It shows seven shuttle sizes, native distance stages
0–6. It does not show later sizes, target defeat, launch or the ending.

## Art and mapping

`mission4_helicopter_master.png` is an imagegen transparent sheet of front,
three-quarter and side helicopter fuselages. The recorded front/banked
poses reuse its front artwork. Seventeen captured layouts include the
smallest three-pixel silhouette. Relative sprite conditions select whole
layouts; per-pattern fallbacks retain clipped cells. Native white rotor
marks determine angle and animation phase. Metallic blade lines and the
mast connection are assembled inside the original sprite footprint.
No independent animation clock is added.

`mission4_shuttle_master.png` is an imagegen transparent shuttle and gantry
assembly, tower on the left and shuttle on the right. Seven native-sized
plates follow the game's nametable and scroll coordinates. Exact pattern
keys mask the original background structure in normal and damage palettes.
The six boss-health cells retain their full, half and empty native states;
the label is SHUTTLE. One- and two-pixel boss cannon rounds use the existing
painted impact master at their native positions and dimensions.
The lethal boss impact also retains the approved large explosion when
cannon rounds obscure a top-row matching condition. Its opposite outer
corner identifies the same native 32-pixel burst during that hit.

The new danger footage contains background curve patterns absent from the
earlier captures. Scoped masks remove those green fragments inside the
active rear display; heading and clearing-row rules reuse the approved
amber art. The moving rear aircraft and blinking warning remain native.

Every v0.13.0 PNG remains byte-identical (232 images). Eight PNGs are added.
Existing rules remain in their original order, with generic alternatives
preserved for any newly introduced exact palette key. No ROM, game memory,
inputs, collision, timing, score or audio changes are made.

## Verification

`validate_mission4_final_target.py` compares every supplied input's native
RAM, nametable, OAM, palette and CHR, available state checkpoints, and PCM audio.
It checks the earlier 6,535-input refueling/terrain replay and 10,352-input
night-flight replay against v0.13.0 HD frames. Final rotor/mast polishing
affects only helicopter patterns absent from those earlier recordings.
The final boss-impact condition is also inactive throughout both earlier
recordings, which is checked directly against their native traces.
The refueling regression lacks checkpoint 180; complete per-input native
and CHR traces, PCM audio and rendered-video comparison still cover it.

`audit_mission4_final_video.py` scans actual HD video for original world
colors and the original green monitor colors, including danger clearing.
Structural checks validate atlas coordinates, image/condition references,
preserved PNG hashes, old-rule ordering and an isolated reconstruction.
The complete results are in `validation/mission4_final_target_v0.14.0.json`.

The preview is the complete new replay captured from Mesen, with native
audio. Asynchronous video recording can omit one or two edge frames;
native trace and PCM checks cover all 8,420 supplied inputs.
