# Danger, loss and rollout flash correction — v0.7.3

Base: approved v0.7.2, merged to main at
`918a176408d2ecdf31933851813d1abab01c9421`.
The supplied `danger.mmo`, `danger2.mmo` and `landing.mmo` contain
1,028, 387 and 4,214 controller frames respectively.

## Findings and corrections

- Danger-to-radar: the native game replaces the center display one row at a
  time. Its row-21 rear-aircraft anchors disappear before rows 22–25 clear.
  The previous whole-display gate exposed native green/white fragments during
  those last rows. Position-scoped slices of the approved rear-threat artwork
  now cover the remaining cells, following the native row clearing and shake.
- Loss: lethal damage changes the HUD background palette from `0F2A0A31` to
  `0F2A0A16`. The exact-palette warning masks and amber letters now cover that
  alternate palette too. The game's flash, target, health and reset remain live.
- Rollout: this recording contains two additional mixed sea/deck background
  patterns and seven moving light patterns. The edge patterns join the
  existing first-visible-row ordering, closing the blue gap. The lights use
  the same ivory masks and native sprite positions as the approved rollout.

`scripts/build_transition_flashes.py` runs after the v0.7.2 transition pass.
Captured pattern keys and positions are in `transition_flash_mappings.json`;
the build requires neither a ROM nor private recordings. All 131 v0.7.2 PNGs
are byte-identical. One new atlas contains slices of the existing code-drawn
instrument and the additional ivory light masks. No new generated artwork is
required, and there are no ROM, audio, input or game-memory writes.

## Validation

All three recordings are replayed in the user-supplied MesenCE 2.2.1 build.
Per-frame RAM, nametable, OAM and palette traces, full emulation checkpoints
and native PCM audio are compared with HD packs disabled. Video frame hashes
compare the final pack with v0.7.2; corrected frames and pixel bounds are
reported in `validation/transition_flashes_v0.7.3.json`.

Headless replay uses `--testRunner --timeout=600`; the default 100-second
runner limit can terminate a long HD capture on a busy host. Incomplete
captures are rejected by frame-count and native-trace assertions. Use the
repository replay template and native recording hook, with absolute paths.

An isolated full source rebuild must match the tested pack byte for byte.
The installer contains only installable pack files. Private recordings,
captures, ROM and emulator binaries are excluded from this change.

Coverage is these three mission-one recordings. Other mission artwork,
refuelling and unrecorded failure outcomes remain outside this correction.
