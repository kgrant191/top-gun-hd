# Carrier approach and ordinal correction — v0.9.1

Base: v0.9.0, `2d0953ef9dc4c2e1342b2f805e36b6092794e517`.
Continue `feature/mission2-v0.8.0`; this is a review build.

## Corrected interpretation

The new 2,445-frame `Top_Gun_HD(6).mmo` shows the carrier advancing through
its distance stages without being destroyed. The E0/E1 and C2/C3 background
layouts used in v0.9.0 are healthy approach views. They were incorrectly
given a damaged ship and an impact burst. The new stage overrides both.

Twelve stable native background layouts cover the far silhouette through
the close pass. Painted 4× plates follow the original horizontal/vertical
scroll. Exact nametable signatures choose the current layout; the native
$0078 distance counter supplies a single fallback during multi-frame tile
transfers. All plates share one priority, so two sizes cannot overlap.
A native center-cell presence check clears the plate when the original
carrier background clears. The cockpit remains above the world layer.
The largest wake crosses the native nametable boundary and is covered on
both sides. The existing level-flight sky edge also covers the first-scanline
scroll remnant, preventing a sliver of that wake from wrapping onto the sky.

The deck is opaque, including interior tiles that the original draws with
the same blue colors as the sea and sky. Captured native carrier keys are
masked only in Mission 2's cockpit/world combat region. Existing artwork
and HUD rules elsewhere are retained.

## Native bridge and guns

At larger sizes, the bridge and guns are independent native OAM sprites.
They are mapped independently using a new matching component sheet. Their
position, size, animation, clipping and disappearance remain native-driven.
Nearby sprite signatures distinguish shared CHR pieces across sizes; a
per-key fallback covers partially clipped groups. The background plate has
no fixed bridge at these sizes, so it cannot leave a ghost tower when the
native sprite disappears.

Three previously unmapped fighter layouts use the approved front-view
aircraft, rotated to the recorded bank and sliced to the original tile
geometry. Existing aircraft, missiles, explosions and clouds retain their
previous replacements. Only missing patterns are added.
The native solid missile-impact center outlives the hull-impact RAM flag by
two frames in this recording. Its two exact sprite keys remain masked during
Mission 2 combat so the existing HD flame burst stays visible throughout.

## 1ST TARGET!

The original tile 02 doubles as numeral 1 and letter I. The general word
mapping produced `IST TARGET!`. An exact position and neighboring native
ST sequence select a numeral 1 for this ordinal alone. Other instruction
words retain their letter I. Native text placement and timing are unchanged.

## Artwork provenance

The built-in image tool created `mission2_boss_approach_master.png` using
the native close carrier silhouette and approved landing artwork as view
and style references. Prompt: healthy intact carrier from ahead and above;
broad slate-gray deck, bridge on the upper left, squared near end, thick
steel hull, crisp silver sunlit rim, restrained ivory runway markings and
compact white bow spray; full isolated ship, transparent background; no
fire, smoke, damage, fighters, HUD or text.

`mission2_boss_components_master.png` was generated from that carrier with
this modular layout: top half, intact deck/hull with island removed and
continuous flight deck; lower left, isolated matching bridge/island/mast;
lower right, compact twin-barrel deck gun viewed slightly from above, with
barrels facing the viewer. Each asset has transparent gutters, matching
painted steel, crisp silhouettes and no labels, background or muzzle fire.
Crop rectangles are stored in `mission2_approach_mappings.json`; generated
alpha is preserved. The approved fighter master is reused unchanged.

## Validation scope

The new close-approach movie and earlier 5,877-frame boss movie passed:
8,322 native RAM/nametable/OAM/palette frames, sampled CHR and CPU state,
and PCM audio are identical. The earlier movie also covers the ordinal,
loss/retry, landing and debrief. Its 4,846 unchanged HD frames are identical;
all changed frames remain within Mission 2 combat. Actual 1024×960 HD video
was inspected through the recorded approach sizes and transitions. Exact
native blue, green and yellow artifact-color audits are clean. The install
ZIP is byte-identical to pack/ and to a complete isolated rebuild.

All 141 previous pack PNGs are byte-identical. The build adds twelve world
plates and one sprite/font atlas, with no ROM patches or replacement audio.
Only recorded sizes and outcomes are covered; later missions remain outside
this review build.
