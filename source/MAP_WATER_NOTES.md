# Mission-one map water correction — v0.3.2

This review build extends the cockpit color fixes on
`feature/cockpit-color-fixes-v0.3.1`. It is awaiting visual approval and merge.

The three enclosed water regions near the top of the briefing map had the
land color inside their outlines. The contour tracer already distinguishes
outer land boundaries from water holes by winding, but the renderer filled
every polygon as land.

`scripts/build_menus.py` now uses signed contour area to choose land or water
fill. Enclosing polygons are filled before smaller nested regions, then the
existing coastline outlines and grid are drawn. The original map geometry,
line colors, grid and native carrier marker are preserved.

Only `pack/menu_map.png` changes visually from v0.3.1: 5,404 pixels switch
from land to water within the three enclosed regions. All coastline pixels,
the other 29 PNGs and every functional HD-pack rule remain unchanged. The
approved windshield, attitude tick and dial work is included.

Build with `python3 scripts/build_pack.py` using Pillow 12.3.0 and NumPy
2.3.5. An isolated full build reproduced the delivered 32-file pack. The builder
uses the named artwork masters in `source/`; its public manifest omits ROM
and replay identifiers and generated-asset UUID provenance.

Validation replays 777 input frames in the supplied MesenCE 2.2.1, covering
briefing, missile selection, confirmation and takeoff. Before/after game
state matches on every frame, all 35 exported checkpoints match, and PCM
audio is identical. Of 34 nonempty screenshot checkpoints, 27 change only
inside the water regions and seven later screens remain identical.
See `validation/map_water_v0.3.2.json` for aggregate results.

Replay recordings, save states, captures and their identifying metadata
remain outside this branch. This check covers the stated mission-one
sequence; earlier cockpit validation is recorded separately in
`validation/cockpit_colors_v0.3.1.json`.
