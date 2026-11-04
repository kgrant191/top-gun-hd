# Mission 2 completion and carrier boss — v0.9.0

**Corrected in v0.9.1:** the longer close-approach recording shows that the
E0/E1 and C2/C3 layouts below are healthy distance stages, not damaged or
destroyed ships. `MISSION2_APPROACH_NOTES.md` documents the replacement
mapping. This file retains the historical v0.9.0 implementation details.

Base: v0.8.2, `960018bdd237ed4ce7516e2a885065b0dcaccb44`.
Continue the unmerged `feature/mission2-v0.8.0` branch.

## Refueling departure

The two-page tanker plate repeats horizontally. During native phase 7,
the left copy departs and the right copy becomes an unintended second plane.
Phase 8 then resets horizontal scroll, exposing a centered tanker again.

`build_mission2_completion.py` adds an exact left-page extraction, selected
only during Mission 2 departure (mode $0018=7, route $002E=4, phase $009F=7).
The original plate is disabled for Mission 2 phases 8 and later. Arrival's
right-page plate and phases 2–6 are unchanged. Other missions retain their
original rule. No input, RAM, ROM, timing or gameplay is modified.

## Horizon and carrier encounter

The previous Mission 2 sea masks were limited to route<5. The carrier boss
uses route 6, exposing large blue native banked horizon tiles. Fourteen
captured sea/sky-only keys are now transparent within this route's world
region. The existing painted sky and ocean show through.

The carrier is background art, not a sprite. Three observed two-cell layouts
are mapped at their native positions and footprints: intact broadside,
damaged/listing ship and destruction. The first reuses the approved landing
carrier; the last reuses the approved impact burst. The damaged carrier is a
new matching asset. Ocean-colored pixels surrounding all three are transparent.

The six native health-meter sprites are restyled as an amber CARRIER meter.
Each cell preserves its native full/empty state and appears/clears on the
same frame. The mapping is scoped to the meter's exact x positions and the
28/29 sprite-origin/visible-row coordinates,
so its common solid pattern cannot turn world sprites into meter segments.

Carrier tiles and meter sprites also remain HD during the short loss/retry
interval after the game changes the route. The approved radar letters are
reused under the lethal palette, which otherwise selects warning-only exact
keys and suppresses the ordinary font fallback. Rollout initialization keeps
the existing black transition until phase 5's timer starts, covering one
stale blue scanline without changing the native blank-screen interval.

## Artwork provenance

`mission2_boss_damaged_master.png` was generated with the built-in image
tool from the approved `landing_broadside_master.png`, using this prompt:

> Use case: precise-object-edit. Asset type: damaged enemy aircraft-carrier
> game sprite for the Top Gun HD remake. Reference image is the existing
> approved carrier artwork, to preserve its realistic painted steel style,
> hull identity and island on the left half. Create ONE isolated badly
> damaged version: ship listing about 18 degrees clockwise (bow/right end
> lower), seen at a slightly elevated broadside angle so some flight deck is
> visible, bright silvery gray sunlit rim and readable deck, with a modest
> compact orange fire and pale gray smoke rising from the middle of the deck.
> Keep long aircraft-carrier silhouette recognizable. Full ship and entire
> smoke plume within the canvas, spacious transparent margins. Opaque steel
> hull, crisp clean alpha silhouette, no background, no sky, no water plane,
> no text, no labels, no black rectangle, no cast shadow. This is a tiny
> in-game target so simplify micro-details and make hull/bridge/fire read at
> 48 pixels wide. Preserve similar colors to the reference, adding bright
> daylight edges for separation against dark blue sea.

The generated alpha is preserved. Existing masters and all 139 prior pack
PNGs remain byte-identical. Two pack PNGs are added: departure plate and
completion atlas. Source mappings include exact captured pattern keys.

## Replay scope

The new recordings contain 1,380 frames (`after-refuel.mmo`) and 5,877 frames
(`boss.mmo`). They cover disconnect, departure, return to combat, banked
approach to the boss, loss/retry, carrier damage/destruction, successful
landing and debrief. The validation report compares every native
RAM/nametable/OAM/palette frame, sampled CHR/CPU state, and PCM audio, checks
actual 1024×960 HD output, and verifies a reproducible source rebuild.

Only the carrier sizes/states present in these recordings are newly mapped.
Later missions and unrecorded outcomes remain outside this review build.
