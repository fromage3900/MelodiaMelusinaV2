# Batch F — Freeze Mechanics — 2026-09-12

## Done

1. **LOD phantoms remapped** (specs only, design prose untouched):
   `M_Master_FarawayMother_Fabric` → `M_Universal_Enhanced_Fabric`;
   `M_Master_Melusina_Costume` + `M_Master_Starskiff_Rigid` →
   `M_Master_Toon_Universal`. Files: `optical_material_instances.v1.json`
   (48 refs), `optical_lod_manifest.v1.json` (11), `FarawayMother_CelestialSilk_LookDev.json`
   (1). JSON re-validated, 0 phantom strings remain in the 3 files.
2. **Baseline re-frozen:** `verify_baseline.py --update` accepted the 4
   attributed drifts (BandRelief SDF-lane 319→285 nodes; Nikki_Landscape -3.4KB
   same nodes; HeightBlend identical bytes+nodes GUID churn; Toon_Universal
   1319→1326 Root-C, already on main). Re-verify: 53/53 green.
3. **Full static chain green:** reachability ok, live-path ok, sweep ok
   (SHADOWED/DUPES/unreadable 0), ui_lint ok, baseline ok.
4. **Ledger:** `static_gates → pass` (2026-09-12 04:36 UTC, session
   freeze-20260912). First PASS row since 09-06.

## Freeze declaration (effective on merge of this batch)

- Allowed parents: the graph doc's table. No new master without owner sign-off.
- No instance may parent to a phantom/demoted master (census-checkable).
- Read-only sweep gate: 0 ReadOnly under Content/.
- MPC move stays a separate rebuild task. Boot maps + dup-slot renames +
  hair maps + sheep photo stay Blender/owner-side HOLDs with names attached.
- After this, materials ride PRs against the frozen graph or not at all.

**Evidence level:** live-proven (chain outputs + ledger row).
