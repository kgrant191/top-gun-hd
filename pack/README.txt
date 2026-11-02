TOP GUN HD - v0.3.0
Mission-one briefing and missile-selection review build

TESTED WITH
MesenCE 2.2.1, using the Linux emulator supplied for this project.
Top Gun (USA).nes
SHA1: A39376136CCCA0025063F3356B9EB41666AFF0BE
SHA256: e7f3b03d59f8d8cfd4cda5ef301a59e3fa1af1533a9cc0f134d67091d7c2f94c
HD pack format 109; 4x graphics (1024 x 960).

INSTALL
1. Open your Top Gun (USA).nes ROM in MesenCE.
2. Enable NES HD packs in the emulator's NES/video settings.
3. Use Tools > Install HD Pack and select Top_Gun_HD_v0.3.0.zip.
4. Reset/reload the ROM.

Manual installation: extract this ZIP directly into:
  <Mesen data folder>/HdPacks/Top Gun (USA)/
The directory must contain hires.txt directly. If you rename the ROM,
rename this directory to exactly match the ROM filename without .nes.
Use the emulator's Open Mesen Folder command to locate its data folder.
Do not place another ZIP inside the pack folder.

IN THIS BUILD
- New TOP GUN HD title artwork and blinking Start prompt.
- Sunset carrier launch with eight exhaust states and two director poses,
  synchronized to the original flame and arm animation.
- Detailed cockpit housing, instrument frames and centered decorative dial scales.
- Mission-one tactical map with the original coastline and carrier marker.
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
Enemy aircraft, projectiles, explosions, clouds and ocean/terrain still use
original graphics. Later-mission briefing maps/menus, landing carrier/world
art, refuelling and endings still need art passes.
The small circular cockpit gauges are redrawn decorative scales, not new
flight simulation instruments. Native fuel, altitude, speed, attitude and
weapon values still update under game control.

VERIFICATION
This revision replays the supplied 777-frame menu movie in MesenCE 2.2.1,
with original and HD output compared. Input-only Select-button variants
exercise the Wolf and Tiger choices; no game memory is altered by the tests.
See the repository's validation/menu_validation_v0.3.0.json for exact results. Earlier reports
remain historical records of their respective builds. The preview compares
actual MesenCE output from the merged v0.2.1 baseline and this v0.3.0 menu pass.
All previous pack images, including the title, launch animation and corrected
cockpit backgrounds, are byte-identical to the merged baseline.

ROM and emulator are not included. Fan-made visual enhancement.
Original Top Gun game and associated marks belong to their respective owners.
Artwork masters were created with the built-in image generation tool.
