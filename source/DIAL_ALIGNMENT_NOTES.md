# Dial alignment review — v0.2.1

Based on `feature/hd-baseline-v0.2.0` at
`e6125b272b0bbb034ded3a06a4188b8abd37d801`. Pending visual approval;
this is not a full-game release.

- Center each decorative scale on its painted bezel after the existing
  cockpit vertical remapping. Use separate horizontal/vertical scale radii
  to match the two upper faces and the taller lower face.
- Clip the lower markings before HD row 903, leaving the foreground metal
  lip and panel clear. Apply the clip after antialiasing to prevent bleed.
- Keep the original cockpit master and all live instrument mappings intact.
  Both impact backgrounds are regenerated from the corrected cockpit using
  the existing four-HD-pixel horizontal shifts.
- `scripts/build_dials.py` owns the scale geometry and is called by
  `scripts/build_pack.py`; the normal build reproduces the corrected pack.

Validation: the build passed; only `cockpit.png`, `cockpit_left.png`, and
`cockpit_right.png` changed among the 22 pack files. All other 19 files,
including `hires.txt`, match the checkpoint byte-for-byte. Pixel checks
confirmed the changes are confined to the dial region, the lower panel
matches the unmarked master, and both impact variants use the exact expected
shift. See `validation/dial_alignment_v0.2.1.json`.

Preview is a static pack-artwork comparison. No new MesenCE gameplay replay
was run because the ROM and emulator executable are not available in this
workspace. Previous checkpoint replay results do not validate this revision.
