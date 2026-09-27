# 10 — Gate 10 (P0/P1): `TOP_Foundry_BakeFarm`

| | |
|---|---|
| **Purpose** | Hermes invokes **one PDG mission** instead of driving hundreds of nodes by hand. The farm executes validated recipes; it does not invent them. |
| **Authority** | Universe Foundry compiles missions (`Tools/universe_foundry.py`). Hermes dispatches. The BakeFarm executes recipes against existing HDAs/Hython families. Evidence goes back to the mission task. The farm is not a second mission compiler or a second task ledger. |
| **Inputs** | `melodia.houdini_foundry_bake_request.v1` (`specs/houdini_foundry/houdini_foundry_bake_request.v1.schema.json`). First workload: `recipes/houdini_foundry/bake_farm_first_workload.v1.json` (cathedral regen + Sea Above test tile). `mission_ref` binds to a Universe Foundry task **when one exists**. There is no Sea Above genome today, so it is `null`. |
| **Outputs** | Per recipe: the same outputs and `bake_manifest.json` as a manual cook; one request-level `farm_report.json` (per work item: recipe_id, tile_id, status, manifest path, duration). |
| **Evidence** | `Saved/Audit/houdini_foundry/bake_farm/<request_id>/` |
| **Status** | STAGED — schema + first request + CLI entry point. No `.hip` exists. |

## Minimal TOP graph (build it this small first)

```text
json_input   (python script TOP: read request; expand recipes via `houdini_foundry.py plan` → one work item per recipe/tile)
  ↓
validate     (python script TOP: `houdini_foundry.py validate <recipe>`; fail item on error)
  ↓
cook         (hda processor / python processor: the recipe's source — HDA or Hython script — with seed/params/bounds attributes)
  ↓
verify       (python script TOP: `houdini_foundry.py verify <manifest>`)
  ↓
report       (wait-for-all + python: write farm_report.json)
```

Future branches are added under `cook` only when that product's manual gate is green: erosion, volumetric ecology, flow volume, deposition, Copernicus, cathedral variants, textile variants. Do not pre-build empty branches.

## CLI / Hython entry point

The farm lives in `hda/TOP_Foundry_BakeFarm_1.0.hda` (or a `.hip` under `Houdini/`, if the owner prefers a scene file) and is run headless:

```powershell
& $env:HOUDINI_HYTHON_EXE Tools/Houdini/foundry/run_bake_farm.py --request recipes/houdini_foundry/bake_farm_first_workload.v1.json
```

`run_bake_farm.py` is **written at college** (`git add -f`): load the TOP HDA, set `request` parm, `cookWorkItems(block=True)`, and exit non-zero if any item failed. It stays under 100 lines. Validation, tile planning and hash verification are imported from `houdini_foundry.py`, so there is no second implementation.

## Rules

- Scheduler: local, with a max-procs cap that leaves the interactive lane usable.
- Work-item seeds come from `plan` only.
- `stop_on_fail: true` stops downstream items; the report still lists every item.
- Hermes gets: the request path, the farm report path, and PASS/HOLD. It never edits nodes.

## Done when

Strong: the farm cooks the cathedral recipe and matches the manual Gate 2 hashes. Stretch: the full first workload runs from one command, and every manifest verifies.
