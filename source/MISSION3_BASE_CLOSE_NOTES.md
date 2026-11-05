# Mission 3 base flyover and missile impact — v0.11.2

Base: v0.11.1 review commit `160fdb7`. Same feature branch; review only.

`Top_Gun_HD(9).mmo` contains 2,683 controller inputs. It starts at base
distance stage 6, reaches stages 7–12, passes over the base, begins another
approach, and records a lethal missile impact at stage 4 followed by retry.

The prior build covered base stages 0–6. Five new scroll-following plates
reuse the same base master for stages 7–11. Stage 12 holds the identical
stage-11 native layout and reuses that plate. Stages 8 onward cross the
vertical nametable boundary, so the captured geometry includes both pages.
Exact stable layouts take priority over distance-counter fallbacks during
multi-frame native transfers. The base clears with its native presence flag.

Nine close ground-gun components reuse the existing turret master. Nearby
guns were separated by native tile groups before assembling the replacement;
their movement, sprite overlap, clipping and independent lifetime remain
native. Each complete component has relative signatures and per-key fallbacks.

The missile-impact reversion was the base switching to a palette whose
replacement coverage only included the smaller base in the earlier footage.
All 211 captured base background patterns now have exact normal-desert and
damage-palette masks. The existing base plates and impact wash remain visible
through the recorded hit and reset. No game-state, input, collision, timing,
health or audio writes are introduced.

`mission3_base_close_mappings.json` stores captured geometry and CHR patterns.
`build_mission3_base_close.py` adds five plates and one gun atlas after the
radar-edge correction. All 180 v0.11.1 PNGs and the existing rules are retained.

Verification is recorded in `validation/mission3_base_close_v0.11.2.json`.
All 7,976 inputs preserve native state and PCM audio. The common video frames
of all six prior recordings remain identical to v0.11.1. The new recording's
original-color audit is clean, all 180 previous PNGs are byte-identical, and
the isolated rebuild reproduces every pack file exactly.
The new movie is compared against the native game's RAM, nametable, OAM,
palette and CHR streams, sampled CPU state and recorded PCM audio. The six
previous movies provide regression coverage. The video recorder can omit one
final frame; native traces and audio cover every input. A separate source
rebuild checks pack reproducibility. Boss defeat, Mission 3 landing and later
missions remain outside the recorded coverage.
