# Refueling tanker entrance — v0.8.2

Base: v0.8.1, `660db25f66a9b44a9927b45f5ee66d399b7d8375`.
Continue the unmerged `feature/mission2-v0.8.0` branch.

The two-page tanker plate contained an aircraft on each horizontal page.
At the start of refueling, the first copy appeared in the center and moved
off the left side while the intended aircraft entered from the right. The
native movie shows only the latter entrance.

`build_refuel_entry.py` adds a plate containing only the original right-page
aircraft. It is selected at the same foreground priority during Mission 2,
flight mode, refueling route, and native arrival stage ($009F = 1). When that
stage ends, the original plate handles the native scroll reset, climb and
boom sequence. Existing artwork, dimensions, timing and input are preserved.
All 138 v0.8.1 PNGs remain byte-identical; the new plate is an exact extraction
from the existing tanker asset, with the first page transparent.

Validation compares the supplied native recording and actual HD output,
including the arrival-to-climb transition. The report records native-state
and audio parity, unchanged video outside arrival, preserved asset hashes,
and an isolated source rebuild. Coverage ends during the recorded refueling
controls; completion and later encounters remain unrecorded.
