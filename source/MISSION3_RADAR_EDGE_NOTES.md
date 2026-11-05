# Mission 3 radar silhouette correction — v0.11.1

Base: v0.11.0 review commit `9ba93d6`. Same feature branch; review only.

Both `enemy-radar.mmo` and `enemy-radar2.mmo` show rectangular gaps in
the radar dish. The native radar uses an incomplete tile grid, often omitting
its upper-left cell. The HD master extends into those empty cells, but the
earlier build only exported cells with a native sprite. This clipped the
painted dish and occasionally a small corner of its base.

`build_mission3_radar_edges.py` reproduces the original artwork transforms
and exports only the 13 omitted cells across 12 complete captured layouts.
Native sprite additions anchor the pieces to an existing radar cell. Exact
relative sprite signatures, the Mission 3 combat scene and two recorded
radar palettes control visibility. Each synthetic key has a transparent
fallback. Pieces disappear with their native radar and do not change OAM,
game memory, collision, timing or audio.

The new `mission3_radar_edges.png` atlas leaves all 179 v0.11.0 PNGs and
existing rules unchanged. Dish size, orientation and source artwork are
preserved. Screen-clipped fragment captures are not treated as complete
objects when deriving missing cells.

Validation is recorded in `validation/mission3_radar_edges_v0.11.1.json`.
All 5,293 input frames preserve native memory/CHR and PCM audio. Frame-by-frame
video comparisons find changes only inside the missing radar cells: 413
frames in `enemy-radar` and 193 in `enemy-radar2`. The common recorded video
frames in the aircraft, wall and boss clips are identical. The asynchronous
video recorder may omit one final frame; native traces and audio still cover
every input. A separate full source rebuild matches all pack files exactly.
The two radar recordings cover 1,060 inputs, including changing distance,
turns, overlapping radars, missiles and explosions. The other four v0.11.0
recordings provide regression coverage. Unrecorded Mission 3 boss stages,
defeat, landing and later missions retain the earlier coverage limitations.
