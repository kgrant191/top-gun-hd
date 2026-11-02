# Mission-one screen polish — v0.3.0

Review branch: `feature/screen-polish-v0.3.0`, based on merged main
`135f618af35893614cd921c084e7134f40b0efc7`.

## Presentation

The Mission 1 briefing and missile menu now share a dark metal console,
inset information panels, pale green text and brass accents. The tactical
map follows the native coastline and retains the native carrier marker.
Hound, Wolf and Tiger have distinct schematic silhouettes, aligned power
and quantity columns, and the original selector position and response.
On confirmation only the chosen weapon's card remains, in its native row.

The new backdrop master was created with the built-in image generation
tool; its prompt is saved alongside it. `scripts/build_menus.py` draws the
map, exact labels, cursor and missile diagrams as deterministic UI assets.
The six small files in `source/menu_reference/` contain only the CHR,
nametable and palette references needed to build those mappings. They
are extracted from frames 90 and 270 of the supplied movie, not a ROM.

## Rendering details

- The three native header anchors restrict the new rules to Mission 1.
- A live nametable check at PPU `$2082` requires the header's M tile to
  remain present. Mesen retains its rendered tile anchors while the PPU
  is disabled during the scene load; checking live memory prevents the
  menu artwork from lingering over that native black transition.
- Each simultaneous background layer has a different priority. Mesen
  chooses one matching background at a given priority.
- Native numeric positions disambiguate shared O/0, I/1 and S/5 patterns.
  Position checks cover the full eight native scanlines of each glyph.
- Missile art masks stop before the original multiplication symbol.
  Original power, quantity, text, input and timing remain game-controlled.
- Existing image indices and rules retain their order. All 20 previous
  PNGs, including the corrected dials, are unchanged byte-for-byte.

## Rebuild

Run `python3 scripts/build_pack.py` with Pillow and NumPy. This build was
checked with Pillow 12.3.0 and NumPy 2.3.5. A complete isolated rebuild
reproduced the pack byte-for-byte. Build scripts do not install the pack.

`reference/Top_Gun_HD_menus.mmo` is the new 777-input-frame movie. It starts
at the Mission 1 briefing, opens the selection menu, selects Hound with
Start at frame 382, then reaches cockpit takeoff. It is distinct from the
older long gameplay movie `reference/Top_Gun_HD.mmo`.

## Replay validation

The user-supplied MesenCE 2.2.1 Linux emulator and matching Top Gun (USA)
ROM were used locally. Neither is included in this repository or installer.
`validation/menu_validation_v0.3.0.json` records the measured results.

Replay the movie from its embedded initial state with
`scripts/replay_template.lua`, substituting a local working root and
capture name. Extract the movie's `Input.txt` and `SaveState.mss` into
that working root's `movie/` directory, and create `captures/<name>/`.
The input variants add only `t.select=true` before `emu.setInput` at
these one-based, inclusive frame ranges:

| Choice | Select frames | Native capture | HD capture |
| --- | --- | --- | --- |
| Hound | None | `native_original` | `review_final` |
| Wolf | 330–333 | `probe_select` | `wolf_select_hd` |
| Tiger | 330–333 and 355–358 | `tiger_select_native` | `tiger_final_hd` |

Compile `tools/capture_hook.c` with `gcc -shared -fPIC -O2 -pthread -ldl`.
Use its output with `LD_PRELOAD`, set `MESEN_CORE_PATH` to the emulator's
`MesenCore.so`, and `TOPGUN_CAPTURE_SYNC` to `<working-root>/captures/<name>`.
Run `Mesen --testRunner <ROM> <generated-Lua-script>`. Enable script file
access in Mesen's portable settings. For native runs add
`--nes.enableHdPacks=false`; for HD runs install this build in the HD pack
directory matching the ROM filename. Run recordings sequentially and use
fresh capture names, or clear the `.go`, `.ack`, `.done` and `.end`
handshake files before repeating a run. The capture hook replaces prior
AVI/WAV outputs and waits for the new AVI RIFF header before allowing the
emulator to exit. The validator rejects incomplete audio or video captures.

Use the same unmodified movie with the v0.2.1 pack for `baseline_hd`.
Then run:

```sh
python3 scripts/validate_menus.py <working-root>/captures <v0.2.1-pack-directory>
```

The validator compares every frame's RAM, nametable, sprite RAM and
palette, all exported checkpoints and PCM audio for each weapon choice.
Only HD audio device metadata is excluded from exported-state comparison.
It also checks pack references, atlas bounds, preserved assets/rules and
the transition/cockpit checkpoints against v0.2.1. The three HD videos
contain 776 frames after initial state loading; input and trace coverage
is 777 frames per choice.

The before/after preview uses actual v0.2.1 and v0.3.0 Mesen output with
the identical original audio. Full emulator traces, states and recordings
are local validation inputs and are not installer files.

## Scope

This is a Mission 1 visual review build. Later-mission maps and menus,
world art, enemy sprites, refuelling and endings remain outside this pass.
Earlier validation reports remain historical records; this pass does not
claim fresh full-game or landing QA. Review the visuals before merging.
