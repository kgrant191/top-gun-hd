# Mission 2 review corrections — v0.8.1

Base: v0.8.0 review commit `7abdedf0ef4cabecfa255afcfffd5f4c7a8a5685`.
Continue the existing unmerged `feature/mission2-v0.8.0` branch.
The user's five issue screenshots refer to the same 14,475-frame movie.

## Findings and corrections

1. The blue horizon appears in input frames 2074–2129. These use takeoff
   mode $0018 = 6, with route bytes acting as animation stages. The previous
   masks required flight mode 7 and route < 5. A separate Mission 2 takeoff
   condition now covers the nine captured sea/sky edge patterns.
   Tanker entry also exposes native blue across the upper three scanlines
   for one frame. During level-flight refueling entry, a three-row strip of
   the existing sky is drawn above native background pixels, below sprites
   and the tanker. It leaves the full frame visible and uses no overscan crop.
2. The small black silhouette in issue2 is sprite pattern CB under the
   aircraft palette. It was outside the first pass's aircraft pattern range.
   It now uses the approved front-view fighter, fitted to a readable six-pixel
   footprint inside the same native sprite cell. Surface submarines also use
   a brighter gray hull and white wake, retaining their native layouts.
3. The danger target starts before the complete rear-display anchors appear
   and can remain after they clear. Its approved amber artwork now follows
   the entire native HUD-sprite lifetime.
4. B9 is the smallest approaching boat. The previous small-sprite helper
   incorrectly assigned impact artwork to every non-CA pattern. A narrow
   Mission 2 combat override now uses the boat master for B9. Real missile
   and explosion mappings are preserved.
5. During refueling entry, the radar adds vertical line pattern 9A. Its exact
   palette key had only danger/control alternatives, exposing native green
   cells before the control phase. A thin muted radar segment now covers the
   entry and preparatory phases, starting before the tanker arrives. The
   native heading, grid, own-aircraft marker and subsequent
   guidance continue to update normally.

## Build and artwork

`build_mission2_fixes.py` runs after the original Mission 2 stage. It adds
`mission2_fixes.png`, the small `mission2_refuel_sky_edge.png`, and scoped
overrides; existing rule order and
all 136 v0.8.0 PNGs are retained. Capture-derived keys are in
`mission2_fix_mappings.json`. The build does not require private input files.
New exact palette keys inherit the existing default artwork where necessary.

`mission2_submarine_bright_master.png` is an ImageGen edit of the v0.8.0
submarine. Edit prompt: preserve diagonal perspective, hull proportions,
periscope, fins, orientation and transparency; brighten the upper hull to
medium-light steel gray with broad silver highlights, a readable conning
tower, dark underside and continuous white foam wake; no text or scenery.
Existing fighter, boat and amber HUD artwork are reused. Generated alpha is
preserved when packing. No ROM, input, game-memory or audio modifications.

## Validation

The movie is replayed with every-frame CHR and native-state captures to inspect
all recorded sizes and transitions. Actual 1024x960 HD video is checked for
native blue sea/sky pixels and bright native green pixels within the central
HUD. Focused before/after clips cover all five reports, including the early
refueling radar before CONTROL appears. Full native-state and PCM comparisons
confirm gameplay and sound parity. The Mission 1 regression movie is compared
against v0.8.0. An isolated full source rebuild must match the tested pack.

Detailed counts and hashes are in `validation/mission2_fixes_v0.8.1.json`.
Coverage ends where the supplied movie ends, during refueling controls.
Refueling completion/failure and later Mission 2 sections remain unrecorded.
