TOP GUN HD / v0.2.0 / 2026-11-01

Direction: realistic painted arcade aviation; navy, steel, warm carrier sunset,
green live instrumentation. This revision fixes impact graphics and updates the combat/landing HUD.
Do not mark the full game complete. Await art review before expanding.

Workflow retained from Holy Diver and Mario Rome:
- User-supplied ROM, MesenCE 2.2.1 and deterministic .mmo input.
- CHR RAM content plus palette keys, not assumptions about fixed ROM tiles.
- New artwork integrated into hires.txt, then captured from live Mesen output.
- Compare actual emulator frames and native RAM/audio between HD and original.
- Keep package ZIP and source ZIP separate; no nested ZIP deliverables.

Important discoveries:
- The executable named Mesen in Mesen_2.2.1_Linux_x64.zip is MesenCE 2.2.1.
- Default data directory here is ~/.config/MesenCE.
- Create settings.json before headless startup to bypass first-run UI.
- Lua file I/O: Debug.ScriptWindow.AllowIoOsAccess = true.
- CLI: --testRunner with absolute ROM and Lua paths.
- emu.setInput(inputTable,0) runs from inputPolled; start precedes select
  in this movie's UD L R S s B A input columns.
- Load the embedded state in an exec callback; remove callback after loading.
- Full source frame is 256 x 240. Cockpit split begins at scanline 130;
  tilemap row 128 does not render at the top of scanline 128.
- Title detection uses its logo tile at (88,56).
- Carrier detection uses the tail tile at (112,80).
- Cockpit detection uses its central coaming tile at (120,132), clear of
  the edge crossed by horizontal impact shake.
- Several alphabet glyphs share CHR byte patterns with numbers. Retain
  their actual shared shapes unless adding verified positional conditions.
- First matching conditional replacement wins. Keep scene-specific rules first.
- Background priority 10 is behind NES background; 30 is in the foreground.
- Native recorder captures CSCD AVI and WAV without X11. The local capture
  hook calls Mesen's exported AviRecord/WaveRecord APIs and changes no game
  memory or emulation parameters. Lua synchronizes start/stop via marker files.
- io.popen and dynamic Lua module loading are unavailable in this build.

Source package layout:
pack/      installable pack files
source/    original artwork masters, build manifest, these notes
scripts/   build_pack.py, build_launch.py, build_panels.py, build_flight_ui.py
           and replay/isolated-digit-test templates
tools/     native recording hook source (Linux)
captures/baseline/  CHR, nametable, palette, OAM, RAM and state reference data
reference/ supplied movie for reproducible private testing
validation/ exact verification results

Build: Python 3 with Pillow and NumPy, run scripts/build_pack.py from any CWD.
The source build writes pack/ only. Install the resulting pack separately.
No ROM or emulator executable is included. The replay template contains
__PROJECT_ROOT__ and __CAPTURE_NAME__ placeholders to substitute locally.
Use absolute paths for Mesen CLI loading and a writable output directory.
When using capture_hook.c, set MESEN_CORE_PATH to MesenCore.so and
TOPGUN_CAPTURE_SYNC to the same absolute marker prefix used by the replay.
Compile hook with cc -shared -fPIC -O2 ... -ldl -lpthread.
Clear only the run's old .go/.ack/.done/.end marker files before a rerun.

V0.1.1 CHANGE NOTES
- Generated a clean carrier plate, two registered director poses and four
  exhaust artwork phases. Eight intensity/shape states follow the original
  sprite patterns at (48,145). The director uses native nametable $229C.
- Full-screen alpha overlays register the feet and engine emission roots;
  the carrier and aircraft remain stable. Exhaust uses additive blending.
- Instrument panels and labels fit exact native readout bounds. Positional
  rules protect shared CHR glyphs elsewhere. Fuel distinguishes filled and
  empty segments; the attitude display retains native horizon/marker data.
- Large missile digits retain their changing native quadrant patterns with
  smooth alpha edges. Type T-11 and other native type values use smaller text.
- launch_mappings.json preserves the captured native keys, making the source
  rebuild independent of the temporary per-frame launch trace.
- Later scenes still require separate coverage. This is not a whole-game release.

V0.2.0 CHANGE NOTES
- Damage shook the original nametable by one pixel. The old (80,132) scene
  anchor crossed the left edge, disabling the whole cockpit pack every other
  damage frame. (120,132) remains inside the stable center coaming.
- RAM $007E = $01/$FF registers artwork to native -1/+1 pixel displacement.
  Wider positional bounds keep all shifted numeric/fuel/attitude tiles intact.
- The supplied Top_Gun_HD.mmo starts in combat, includes an impact at input
  frames 76-91, radar contacts and a complete landing through mission success.
- Radar typography, thin grid, ownship/contact symbols, reticle, attitude
  pointer and landing guidance are updated. Tile $71 is half-filled fuel.
- Missile count uses ten verified four-tile definitions from ROM file offset
  $1E0B8. Horizontal nametable mirroring places the display at PPU $2A5A/$2A5C.
  The original memory values select HD digits; no game memory is modified.
- I/O glyph sharing is handled by position in landing words and numeric rows.
- build_flight_ui.py is the final compositor, after build_panels.py.
- Replay validation includes every frame's RAM, nametable, OAM and palette;
  full CHR/emulation state checkpoints and bit-identical native PCM audio.
- Approved title, clean launch plate, eight exhaust layers and two director
  poses stay byte-identical to v0.1.1.

Digit test: all ten native values were rendered in both counter positions in
an isolated emulator fixture. Only that fixture writes test nametable data;
the production HD pack and normal replay never modify game memory.

The cockpit condition also requires its right display border at (180,148).
The briefing scene shares the flat coaming tile pattern, so this second
stable anchor prevents flight artwork from appearing over the briefing.
The opening/title/launch/briefing/weapon menu replay is compared with v0.1.1.
