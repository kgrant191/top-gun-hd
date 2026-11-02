# Top Gun HD

Development checkpoint **v0.2.0** for the NES Top Gun (USA), using a Mesen HD pack. This is unfinished work, not a full-game release.

## Install

Copy the contents of `pack/` (not the surrounding source tree) into the emulator’s HD pack folder associated with your own Top Gun (USA) ROM. Enable HD packs and reopen the ROM. The recorded ROM SHA-1 is `A39376136CCCA0025063F3356B9EB41666AFF0BE`. No ROM or emulator executable is included.

## Preserved work

- Title and native-timed carrier launch, with director and exhaust animation.
- Cockpit HUD, damage-shake registration, radar and landing displays.
- Artwork masters, build scripts, capture references, supplied replay movies, and recorded validation reports.

More artwork and gameplay work remains. Enemy/world/projectile graphics, later missions and refuelling need further coverage. See `README.txt`, `source/PROJECT_NOTES.txt` and `source/build_manifest.json` for the detailed handoff. Existing reports describe prior emulator testing; they are not a new full-game QA claim.

## Build

Use Python 3 with Pillow and NumPy installed, then run:

```sh
python3 scripts/build_pack.py
```

The build writes `pack/` and build metadata. Recovery was checked with Pillow 13.0.0 and NumPy 2.3.5. All 22 rebuilt pack files matched the saved v0.2.0 installer byte-for-byte. This checkpoint preserves the original archive contents rather than replacing assets with newly generated artwork.

`validation/checkpoint_pack_sha256.json` records the preserved pack hashes. `validation/checkpoint_recovery.json` records recovery checks. `scripts/validate_release.py` requires additional original/HD captures and audio from emulator replays; those full replay outputs are not included here, so that script was not rerun during recovery.

## Repository workflow

Work is checkpointed on `feature/hd-baseline-v0.2.0`. Keep further edits on feature branches and review before merging. Do not treat this checkpoint as a release or permission to merge. The recovery commit descends from the existing repository initialization commit.
