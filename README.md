# Top Gun HD

Development review build **v0.3.0** for the NES Top Gun (USA), using a Mesen HD pack. This is unfinished work, not a full-game release.

## Install

Copy the contents of `pack/` (not the surrounding source tree) into the emulator’s HD pack folder associated with your own Top Gun (USA) ROM. Enable HD packs and reopen the ROM. The recorded ROM SHA-1 is `A39376136CCCA0025063F3356B9EB41666AFF0BE`. No ROM or emulator executable is included.

## Preserved work

- Title and native-timed carrier launch, with director and exhaust animation.
- Cockpit HUD, damage-shake registration, radar and landing displays.
- Centered cockpit dials and a cleanly clipped lower dial.
- Mission-one tactical briefing map and all three missile-selection diagrams.
- Artwork masters, build scripts, capture references, supplied replay movies, and recorded validation reports.

More artwork and gameplay work remains. Enemy/world/projectile graphics, later missions and refuelling need further coverage. See `source/SCREEN_POLISH_NOTES.md` for this revision and `README.txt`, `source/PROJECT_NOTES.txt` and `source/build_manifest.json` for the earlier handoff. Validation reports identify the exact tested revision and scope; they are not a full-game QA claim.

## Build

Use Python 3 with Pillow and NumPy installed, then run:

```sh
python3 scripts/build_pack.py
```

The build writes `pack/` and build metadata. The original v0.2.0 recovery was checked with Pillow 13.0.0 and NumPy 2.3.5, and all 22 pack files matched its saved installer byte-for-byte. The v0.3.0 menu pass uses Pillow 12.3.0 and NumPy 2.3.5; all existing pack PNGs, including the corrected cockpit dials and approved intro artwork, remain byte-identical to the merged v0.2.1 baseline.

`validation/checkpoint_pack_sha256.json` records the preserved pack hashes. `validation/checkpoint_recovery.json` records recovery checks. `scripts/validate_release.py` requires additional original/HD captures and audio from emulator replays; those full replay outputs are not included here, so that script was not rerun during recovery.

## Repository workflow

The v0.2.0 recovery and v0.2.1 dial fix were merged into `main` at `135f618af35893614cd921c084e7134f40b0efc7`. The v0.3.0 menu pass starts there on `feature/screen-polish-v0.3.0`. Keep further edits on feature branches and review before merging. Do not treat a development checkpoint as a release or permission to merge.
