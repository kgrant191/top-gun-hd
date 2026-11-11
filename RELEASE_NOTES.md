# Top Gun HD v1.0.1

Refueling corrections for the 4× Top Gun (USA) HD pack on MesenCE 2.2.1.

- Correct **REFUEL1NG COMPLETE** to **REFUELING COMPLETE**. The native tile is shared by the letter I and numeral 1; the override applies only to the completion-message cell. Numeric counters remain unchanged.
- Keep the **Mission 2 connected refueling boom** in HD. Reuse the approved connected-pose artwork already mapped for Missions 3 and 4.
- Define 305 referenced conditions before their first use, eliminating HD-pack loader warnings. Preserve graphics-rule priority and later condition redefinitions.

All 271 artwork PNGs are unchanged. No ROM, gameplay, input, collision, timing or audio patches are included.

## Install or update

Download `Top_Gun_HD_v1.0.1.zip`, open your supported ROM in standalone MesenCE 2.2.1, and use **Tools > HD Packs (NES) > Install HD Pack**. Select the ZIP, then accept the reset to activate it. The ZIP contains only the installable pack.

## Regression coverage

34 distinct supplied recordings, totaling 122,329 recorded inputs, were replayed to collect native-state checkpoints. The v1.0.0 and v1.0.1 packs were rendered from the same 1,003 checkpoints spanning all four missions, menus, takeoff, combat, damage, retries, landings, refueling and endings. 995 checkpoints are pixel-identical; eight contain the intended text or boom corrections. A separate continuous 1,380-input refueling replay matched native RAM on every frame. See `validation/regression_v1.0.1.json` for results.

This is checkpoint-based visual regression, not an inspection of every rendered frame. Unrecorded outcomes remain outside coverage, including Mission 3 boss defeat/landing and the continuous shuttle-defeat-to-success transition. This build is prepared for user review before publication.
