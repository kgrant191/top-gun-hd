# Mission 3 close tank orientation — v0.10.1

Base: v0.10.0 commit `db32be23953e31ff5fb003bec59e4014ef847738`.
The user's `Top_Gun_HD(8).mmo` contains 901 inputs and reproduces the issue.

The 24×24 tank layout uses the same nine CHR patterns in two horizontally
mirrored arrangements. The previous recording only supplied the mirrored
arrangement. Its rules required `hmirror`, so the other arrangement lacked
eight tile fallbacks and the correct composite rule for its shared F8 tile.
It reverted to native graphics during 156 inputs of the new recording.

`build_mission3_tanks.py` adds the opposite arrangement after the Mission 3
build stage. It reflects the captured sprite offsets, reverses the mirror
predicate and reuses the exact existing atlas cells. Group signatures keep
the shared F8 pattern distinct from its independent frontal-tank piece.
Both existing ground palettes have matching anchor predicates. Eight
missing tile fallbacks per palette cover partial groups without replacing
the earlier shared-pattern fallback.

The fix adds 18 composite rules, 16 fallbacks and 36 relative conditions.
No new CHR/palette key, PNG, ROM patch or memory write is introduced. All
171 v0.10.0 PNG files remain byte-identical. Other missions are excluded.

`validate_mission3_tanks.py` compares the native and fixed 901-input replay,
PCM audio, sampled CPU state, CHR data and the full before/after HD video.
It checks changes against the native tank sprite bounds and evaluates the
new predicates over the earlier 21,467-input Mission 3 trace. It also checks
pack syntax, the deterministic final build stage and installer contents.

This is a review build on `feature/mission3-v0.10.0`. The source bundle
includes the unmerged v0.10.0 work and this correction. Mission 3 boss and
landing remain outside the recordings supplied so far.
