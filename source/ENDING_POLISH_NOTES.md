# v0.15.1 — bonus numeral and ending proportions

The original bonus command in the supplied ROM writes BONUS at PPU $2A8D,
then 10000 PTS. at $2ACB. Tile 02 shares the I/numeral-1 pattern. An exact
phrase and position condition now selects the existing font's numeral 1;
word forms elsewhere retain their rules and palettes. The ROM is unchanged.
The supplied victory movie begins after the bonus, so a separate visual-only
nametable fixture checks that native command in the emulator.

All four yellow crew use a uniform 0.31 scale and the same source helmet-to-
boot geometry. Their poses are positioned by head center and foot baseline;
raised arms no longer determine an independently stretched body size.

The front pilot uses a single 49-by-61-pixel canvas anchored at (746,395).
His helmet, torso, near arm and seat remain identical. The lowered-arm edit
is composited only inside a bounded far-arm mask. Both wave frames retain
the same scale and position. Native OAM selects the existing animation poses.
The rear pilot also uses uniform scaling.

Only the five carrier-celebration plates are replaced. All other v0.15.0
PNGs remain unchanged. The v0.15.0 full-replay report remains the prior
regression evidence; the focused v0.15.1 validation replays the victory movie,
checks native state and PCM, checks the bonus fixture and fixed-body pixels,
and verifies a fresh full build.

Artwork edit prompt: lower only the pilot's raised far arm, preserving his
helmet, head, torso, seat, framing and transparent background. The built-in
image editor produced ending_pilot_arm_down_master.png; the builder locks
all pixels outside the arm mask to the existing reference pose.
