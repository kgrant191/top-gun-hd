# Mission 2 naval combat and refueling — v0.8.0

Base: approved v0.7.3, main commit
`9c05e3d0c25c468791894377cc250fd4086e9af4`.
Work branch: `feature/mission2-v0.8.0`.
Private input: Top_Gun_HD(5).mmo, 14,475 controller frames, Top Gun (USA)
ROM SHA1 A39376136CCCA0025063F3356B9EB41666AFF0BE.

## Implementation

- Mission 2 ($0030 = 2) changes the sky/HUD palette from $31 to $21.
  Exact rules and palette-sensitive anchors reuse the existing artwork with
  Mission 2 conditions. Additional banked sea/sky edge patterns reveal the
  approved scenery plates rather than native blue strips.
- The second briefing map traces its native coastline and inland water.
  Approved panels and typography are reused; live map markers remain native.
- Boats and submarines use new transparent painted masters fitted into their
  captured metasprite bounds. Additional aircraft patterns reuse the approved
  front/rear aircraft artwork, with native distance, position and bank changes.
- Landing and refueling both use main mode $0018 = 7 and overlapping $009F
  stages. Route $002E = 4 identifies refueling; landing-specific black plates
  and transitions now exclude that route. Normal sky/cockpit clauses include it.
- A tanker plate follows native nametable scrolling at foreground priority 31,
  preventing cloud sprites from drawing over the tanker body. The separate sprite boom
  follows native size stages and steering. Shared shaft patterns use a stable
  metal strip, avoiding seams from sampling differently sized full images.
- The refueling monitor appears from $009F >= 2. Labels, moving aircraft and
  coupling diagram stay driven by the original game. The radar stays live
  during tanker entry. No game memory, input, ROM or audio is modified.
- New exact pattern/palette keys carry forward prior default alternatives:
  Mesen can otherwise suppress defaults even when a new condition is false.

`scripts/build_mission2.py` is the last artwork build stage. Its captured
pattern/layout data is in `source/mission2_mappings.json`; rebuilding requires
neither the ROM nor the private recording. The 132 baseline PNGs stay unchanged.

## Artwork provenance

Four new transparent masters were generated with OpenAI ImageGen for this
project: a gray patrol boat, a surfaced dark submarine, a rear-view four-engine
refueling tanker, and a separate rear-view metal boom/nozzle. The requested
style was realistic painted naval aviation artwork with clean silhouettes,
neutral illumination, no lettering and no scenery background. The exact saved
masters are the source of record; rebuilding does not regenerate them.

The front/rear aircraft source slices come from the approved project atlas.
Masks, resizing, tile assembly, map paths and the monitor are deterministic
Pillow/NumPy build operations. Original screenshots are used only for native
positions and pattern mappings. No ROM or emulator is distributed.

## Validation and scope

The supplied movie is replayed with HD packs disabled and with the final pack
in MesenCE 2.2.1. Per-frame RAM, nametable, OAM and palette traces, periodic CHR
and full-state snapshots, and decoded PCM audio are compared. Audio-device
metadata is excluded from state dictionaries; PCM is checked separately.

The repository's 8,253-frame Mission 1 recording is replayed against approved
v0.7.3 and v0.8.0. State, sound and video frame hashes are compared to detect
regressions from shared pattern keys and refueling/landing conditions.
The first 8,080 HD video frames match; the last 172 update the Mission 2
briefing after Mission 1 completes. The subsequent tanker-layer-only change
is checked to be inactive throughout this regression recording.

The native screenshot API returns 256x240 even with HD enabled. Visual review
and the delivered preview use the emulator's actual 1024x960 AVI output.
The installer contains only installable pack files. Validation results and
pack hashes are recorded in `validation/mission2_v0.8.0.json`.

Coverage ends during refueling guidance, where the supplied movie ends.
Refueling completion/failure, the rest of Mission 2 and later missions are
not claimed complete. Preserve these limits when preparing any release notes.
