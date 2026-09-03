# HERO Graph Review Queue — 2026-08-07

**Status:** Ready for review. All graphs verified headless in Blender 5.2 (build + per-parameter evaluation).
**Review file:** `KitbashExport/HeroGraphs_Review_2026-08-07.blend`
Open it, then walk the Review Queue: Melodia Studio N-panel → Stage → Review Prev / Solo / Next (`surreal_arch.review_queue_cycle`).

## The Queue (5 pieces, left → right)

| # | Object | Builder / Tree | Nodes | Links | Params | Verified |
|---|--------|----------------|-------|-------|--------|----------|
| 1 | Hero_NikkiFloraQuarter | `MEL_nikki_quarter` | 478 | 689 | 44 | Modes 0–3 distinct, bare-toggle pass |
| 2 | Hero_EscherBelvedere | `MEL_escher_belvedere` | 157 | 231 | 16 | Rotation 0/45°, toggles distinct |
| 3 | Hero_EscherPenroseStairs | `MEL_escher_penrose_stairs` | 486 | 742 | 12 | Runs 3–8, tier gating distinct |
| 4 | Hero_EscherWaterfall | `MEL_escher_waterfall` | 185 | 279 | 14 | Cascade/Tribar/Splash/Pillars toggles |
| 5 | Hero_SkyObservatory | `MEL_sky_observatory` | 224 | 297 | 14 | Ring Count 0–5, Planets/Lanterns/Deck |

All objects carry a **live `MelodiaHero` GN modifier** — tweak any parameter in the modifier tab and the review piece updates in place. Registry now holds **66 builders** (was 39 at last audit).

## Per-piece review notes

1. **Nikki Flora Quarter** — the set-dressing workhorse. Try: Mode 0 + Roof Mode 1 (onion) / 3 (clerestory); Mode 1 Tier Count 3 for the festival pavilion; Mode 2 Section Count 6 + Floating Base for Dreamstate spires; Mode 3 for ruin scatter. Defaults produce the townhouse; Variation + Seed drive the facade wobble.
2. **Escher Belvedere Loggia** — two-story impossible loggia. Upper Rotation 45° is the money shot (staircase visibly misses the upper floor); Tall Threading Columns is the impossible read. 0° gives a sane aligned stack for comparison.
3. **Escher Penrose Stairs** — Ascending and Descending loop. Runs 4 + Second Loop ON reads endless. Step Rise 0.35 + Runs 6 is the classic poster.
4. **Escher Waterfall** — perpetual descent. Side Drop 0.8 makes the cascade drama; Tribar Arch + Splash Ring complete the composition. Cycle Side Drop from 0.1 → 1.5.
5. **Celestial Dream Observatory** — the hero silhouette (5.3k verts default). Ring Count 5 + Planets = orrery crown; Lanterns hang from the outer ring; Star Finial tops the dome. This is the Dreamstate floating-spire and KaleidoNave centerpiece candidate.

## Integration status

- Registered: `GROUP_BUILDERS` / `GROUP_METADATA` (66 total), `STUDIO_LABELS` (panel hints), GN route `ARCH_TO_GN` + prefixes `NIKKI_`, `ESCHER_`, collections `NikkiGN_Editable` / `EscherGN_Editable`.
- Style genome: `deploy/surreal_os/genomes/nikki_fiora_quarter.json` (NikkiFlorawish family, `default_graph: NIKKI_FLORA_QUARTER`).
- Files: `deploy/surreal_arch/melodia_gn/{nikki_quarter,escher_belvedere,escher_penrose_stairs,escher_waterfall,sky_observatory}.py`

## Next steps after your review

1. Bake the chosen heroes → FBX kit (`Tools/` regen pattern) → UE import (`import_ornament_fbx.py`) → `/Game/EnvSandbox/Meshes/`.
2. **KaleidoNave dress pass** (first): nave bays, chandeliers, stained glass, statuary + Observatory as the centerpiece.
3. Dreamstate: Observatory + Spire variants as floating ruins; bifrost bridge kit.
4. ZenForest (protection lifted by owner): festival pavilions, stalls, garlands.

## Verify commands

```
python -m py_compile deploy/surreal_arch/melodia_gn/nikki_quarter.py  # + each new module
blender -b --factory-startup --python-exit-code 1 -P <verify script>   # build + per-case eval
```
Evidence from today's runs: `ALL_HERO_GRAPHS_VERIFY_PASS` (5/5 registered, all evaluate with distinct geometry, zero zero-face cases).
