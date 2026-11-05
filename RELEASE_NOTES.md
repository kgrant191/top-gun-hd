# Top Gun HD v1.0.0

The first approved release of Top Gun HD, a 4x graphics pack for the NES
version of **Top Gun (USA)** on Mesen / MesenCE.

- Painted title, animated carrier launch, cockpit and briefing screens.
- Detailed skies, ocean, desert and night scenery across four missions.
- HD aircraft, naval and ground targets, helicopters, missiles and effects.
- Live HULL display, amber danger screen, carrier landings and aerial refueling.
- Final shuttle target, award screen and sunset carrier celebration.
- Correct **10000 PTS** text, consistent deck crew and a steady pilot wave.

The pack keeps the original game logic, input, collision, scores, animation
timing and audio. No ROM or emulator is included.

## Downloads

**Players:** download `Top_Gun_HD_v1.0.0.zip`. Extract all contents into the
HD pack folder matching your own ROM filename, enable HD packs, then reopen
the ROM. Keep `hires.txt` and all PNGs together. Replace the old pack files
when upgrading. GitHub's automatic source archives are for development.

**Posting:** `Top_Gun_HD_v1.0.0_Before_After_Images.zip` contains four
1080×1920 before/after PNGs: carrier launch, desert combat, final shuttle
target and mission accomplished. The gallery is also visible in the README.

## Validation

The release preserves all 271 approved v0.15.1 PNGs and every graphics rule.
The supplied replay suite covers all four missions, recorded target
approaches, damage and retry transitions, refueling, landings and both endings.
The release media uses matched game-state and CHR traces for every capture pair.

This is recording-based coverage, not an exhaustive certification of every
outcome. Mission 3 boss defeat/landing and the continuous shuttle-defeat-to-success
transition remain absent from the supplied recordings. Details are in
`validation/` and `source/`.
