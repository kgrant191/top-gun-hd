TOP GUN HD - v0.4.0
Enemy aircraft and combat-effects review build

TESTED WITH
MesenCE 2.2.1, using the Linux emulator supplied for this project.
Top Gun (USA).nes
HD pack format 109; 4x graphics (1024 x 960).

INSTALL
1. Open your Top Gun (USA).nes ROM in MesenCE.
2. Enable NES HD packs in the emulator's NES/video settings.
3. Use Tools > Install HD Pack and select Top_Gun_HD_v0.4.0.zip.
4. Reset/reload the ROM.

Manual installation: extract this ZIP directly into:
  <Mesen data folder>/HdPacks/Top Gun (USA)/
The directory must contain hires.txt directly. If you rename the ROM,
rename this directory to exactly match the ROM filename without .nes.
Use the emulator's Open Mesen Folder command to locate its data folder.
Do not place another ZIP inside the pack folder.

IN THIS BUILD
- Painted enemy aircraft: rear, approaching and overhead views, banks,
  inverted views and native distance sizes (116 mapped layouts).
- Native-timed missiles, tracers, ignition flashes, explosions and smoke
  (23 mapped layouts), restricted to the windshield and sprite palettes.
- New TOP GUN HD title artwork and blinking Start prompt.
- Sunset carrier launch with eight exhaust states and two director poses,
  synchronized to the original flame and arm animation.
- Detailed cockpit housing, instrument frames and centered decorative dial scales.
- Neutral metal windshield edge across runway, flight and cloud transitions.
- Matching pale attitude-display ticks, including the right-hand mark.
- Mission-one tactical map with filled inland water, original coastline and carrier marker.
- Three distinct missile cards, clean typography and a native-controlled selector.
- Selection confirmation preserves the chosen weapon and hides unselected cards.
- Fitted missile and weapon labels; clean altitude/speed readouts.
- Visible filled/empty fuel segments and a blue/brown attitude display.
- HD cockpit stays active during damage; its artwork follows native impact shake.
- Thin targeting brackets, precise gunsight, clean radar typography/grid and contacts.
- Landing instructions and guidance symbols use the same display styling.
- Missile count is rendered from all four native tiles for each displayed digit.
- Fuel includes the intermediate half-filled segment.
- The game's changing radar, altitude, speed, fuel, missile count and
  weapon selection continue to be driven by the original game.
- Original sound and game logic; no ROM patches, cheats or audio replacements.

SCOPE / STILL ORIGINAL
This is an opening review build, not a finished whole-game HD remake.
Clouds and ocean/terrain still use original graphics. Later-mission briefing
maps/menus, landing carrier/world art, refuelling and endings need art passes.
The combat pass covers mapped mission-one layouts and observed palettes;
other missions and palette variants still need coverage.
The small circular cockpit gauges are redrawn decorative scales, not new
flight simulation instruments. Native fuel, altitude, speed, attitude and
weapon values still update under game control.

VERIFICATION
The v0.4.0 combat pass checks 2,054 opening/flight frames against native
output and 8,253 combat-to-landing frames against the approved HD baseline.
Game-state traces, checkpoints and PCM audio match. Screenshot changes are
confined to combat sprite cells; all 30 existing PNGs are preserved.
A separate test fixture verifies all 116 aircraft and 23 effect layouts.
The fixture is not part of this installable pack.
See validation/combat_art_v0.4.0.json in the source repository.

The v0.3.2 correction replays 777 input frames from the mission briefing,
through missile selection and confirmation, to takeoff in MesenCE 2.2.1.
Game-state traces, exported checkpoints and PCM audio match v0.3.1.
Only menu_map.png changes visually; the other 29 PNGs and functional
HD-pack rules are unchanged. See validation/map_water_v0.3.2.json.

Included v0.3.1 cockpit fixes were checked against native output with
2,054 frames of runway/flight/cloud transitions and 180 impact frames.
See validation/cockpit_colors_v0.3.1.json for those historical results.
These reports cover their stated sequences, not whole-game QA.

ROM and emulator are not included. Fan-made visual enhancement.
Original Top Gun game and associated marks belong to their respective owners.
Artwork masters were created with the built-in image generation tool.
