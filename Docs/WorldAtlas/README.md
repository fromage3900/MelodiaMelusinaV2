# Melodia World Atlas

> *An indexed archive of places reached through resonance.*

The **Melodia World Atlas** is the canonical inventory of worlds, world families, routes, evidence and production provenance. Its machine-readable authority is [`specs/world_atlas.v1.json`](../../specs/world_atlas.v1.json).

It is deliberately **not** a second world generator, runtime, save system, PCG framework or compiler. Architecture remains owned by the existing world-building source of truth; current proof remains owned by `CURRENT_STATE.md`.

## Current seeded atlas

| World | Evidence | Route / implementation truth |
|---|---|---|
| Melusina's Morning | LIVE PROVEN (scoped) | Route 0; World Compiler + UE PCG dressing proof |
| Sea Above | LIVE PROVEN (scoped) | Route 1; Resonance Ecology certified on 1 of 9 graphs; full-route/package proof remains separate |
| Kaleido Nave | SOURCE PRESENT | Route 2; checked-in canonical map |
| Faraway Mother | SOURCE PRESENT | Genome + PCG architecture + Foundry source; staged UE prototype map is not on current main |
| Glassgarden Shoals / Reef That Looks Back | SOURCE PRESENT | Deferred Monolith concept / orchestration canary; no live map claimed |
| Monolithic Ecology | SOURCE PRESENT | World-language / visual-family concept; no live map claimed |

## PCG preservation contract

The Atlas protects the current Git source entry points for Resonance Ecology, Sea Above application, Hero Corner integration, World Compiler UE/editor consumers, World Compiler CLI/driver, and Universe Foundry. Atlas validation fails if those files disappear or become effective Perforce-owned content.

That protection is intentional: creative Unreal packages can move into Perforce without moving the engineering/editor source that produces and validates them.

Historical Sea Above External Actor snapshots still require comparison with the **live UE + Perforce** world before any recovery branch is retired. Do not restore an older World Partition actor set merely because it exists in Git history.

## Production spine

`World Atlas → Universe Foundry (mission planning) → World Compiler / Hython / Melodia Studio → UE PCG/runtime → Perforce creative content`

Git remains the code/contracts/tests/docs authority, including `Content/Python/`.

## Branch convergence

The companion [branch-retirement census](BRANCH_RETIREMENT_CENSUS_2026-09-25.md) separates obvious merged/canonized candidates from recovery, workstation, backup and salvage holds. Branch count is never itself a deletion criterion.
