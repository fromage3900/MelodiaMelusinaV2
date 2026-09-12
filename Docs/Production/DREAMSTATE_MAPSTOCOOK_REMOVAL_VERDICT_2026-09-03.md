# MapsToCook Dreamstate removal — verdict 2026-09-03 (lane: build)

**Action taken:** removed
`+MapsToCook=(FilePath="/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate")`
from `Config/DefaultGame.ini` (owner approval 2026-09-03: "dreamstate is now kaleidonave").

## Evidence

| Claim | Source |
|---|---|
| Asset missing on disk | `Get-ChildItem -Recurse Content -Filter L_Melodia_Dreamstate.uasset` → 0 results (2026-09-03). Cook #3 log 2026-09-02: "Unable to find package for cooking /Game/Melodia/Levels/Opening/L_Melodia_Dreamstate". |
| Map was renamed, not deleted | `Docs/Handoffs/CLAUDE_HANDOFF_2026-07-31.md`: "L_KaleidoNave (formerly L_Melodia_Dreamstate)". |
| Merged route is canonical | `Docs/ECHO/campaign_01_rhythm_damage_delta.md` + 08-27 ledger row: route is `L_MelusinaMorning → L_KaleidoNave`. |
| Allowlist does not author it | `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` (allowlist SSOT) — no Dreamstate entry; live authority is `DA_MelodiaIntegrationConfig → TravelLevelIds` (carries `LV_SeaAbove_Prototype`). |
| Stale ini comment removed | Old comment "Dreamstate and ZenForestTest stay listed so the cook covers the route" described a pre-merge route; rewritten in the ini. |

## Residual verification owed (editor session)

Per the evidence standard (dumps confirm presence, never absence — rule 20), the
`bRelaxedAllowlistInEditor=true` escape hatch means a stale travel id would pass in PIE
with only a warning. One reflection read of `DA_MelodiaIntegrationConfig → TravelLevelIds`
during the next editor session settles it: assert no `L_Melodia_Dreamstate` entry. If one
exists, it is a silent-no-op travel shipped in the 2026-09-02 package and must be removed.

## Related coverage gap (not blocking, unchanged)

`SM_Rock` (`/Game/AdvWorldInteraction/StarterContent/Props/`) also missing from disk per
cook #3 log. Booted packaged build has 0 fatals, so nothing load-critical references it;
verify no packaged-route level references it before the next cook.
