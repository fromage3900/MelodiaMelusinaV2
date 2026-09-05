---
name: melodia-mesh-catalog
description: Catalog static meshes, find duplicates, propose reorganization (read-only). Use when auditing EnvSandbox/Melodia mesh sprawl, reconciling duplicate buckets (Greybox_Kit/Library), or enforcing the SM_ naming convention before a rename pass.
---

# melodia-mesh-catalog

Read-only catalog + proposal skill for BS_GodFile static mesh organization. It **never** moves or renames assets — it produces a JSON inventory and a move manifest that a human approves and a single-editor holder executes via `IAssetTools::RenameAssets` (redirector-safe).

## When to use

- EnvSandbox sprawl triage — `Meshes/` 87, `Greybox_Kit/` 78, `Library/` 52 pattern, or root `Content/Greybox_Kit` / `Content/Library` duplicate pairs.
- Any `validate_naming_conventions` violation sweep before a bulk rename.
- Pre-merge hygiene for the 103-commit feature branch that carries `Monoliths/SeaAbove` content.
- Any request that says "organize meshes", "clean labels", "find duplicates".

## When NOT to use

- Do not use for Niagara, material, or texture renames — those have their own validators (`material_query`, `niagara_query`).
- Do not use to execute moves — hand off the proposal to the build lane.

## Workflow

### 1. Snapshot (offline + Monolith reads, no mutations)

```powershell
# Disk truth (fast, gitignored Content/ is still on disk)
Get-ChildItem Content/EnvSandbox -Recurse -Filter "SM_*.uasset" | Group-Object Directory | Sort Count -Descending
Get-ChildItem Content/Greybox_Kit, Content/Library -Recurse -Filter *.uasset | Measure-Object
```

```python
# Registry truth (mounted/indexed packages only)
mesh_query get_mesh_catalog_stats
mesh_query validate_naming_conventions scan_path="/Game/EnvSandbox" max_results=150
mesh_query validate_naming_conventions scan_path="/Game/EnvSandbox/Meshes" max_results=150
mesh_query validate_naming_conventions scan_path="/Game/EnvSandbox/Meshes/Atlantis" max_results=150
project_query audit_orphan_assets limit=50
```

Disk and registry counts intentionally differ — registry only sees indexed packages; both numbers are evidence (see 2026-08-30: registry 722 meshes / 622 EnvSandbox assets scanned vs 1039 EnvSandbox mesh files on disk).

### 2. Emit `Saved/Audit/mesh_catalog_<date>.json`

Schema (committed example: `Saved/Audit/mesh_catalog_2026-08-30.json`):

```json
{
  "generated": "2026-08-30T22:30:00Z",
  "total_meshes_registry": 722,
  "categories": { "Greybox_Kit": 113, "EnvSandbox.Greybox_Kit": 80, ... },
  "disk_counts": { "EnvSandbox/Meshes/Atlantis": 333, "Greybox_Kit": 670 },
  "violations": { "EnvSandbox": 150, "Meshes": 60 },
  "red_line_paths": ["/Game/_PROJECT"],
  "proposed_renames": [{ "find": "BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_", "replace": "SM_ATL_Palace_", "count": 333 }],
  "proposed_moves": [{ "from": "/Game/Greybox_Kit", "to": "/Game/EnvSandbox/Greybox_Kit", "count": 670, "requires_signoff": true }],
  "archive_moves_done": [{ "from": "VFX/_Quarantine_2026-08-01", "to": "VFX/_Archive_2026-08-30/Quarantine_2026-08-01", "proven_zero_refs": true }]
}
```

This path is allowlisted in `.githooks/pre-commit` (`Saved/Audit/*.json`).

### 3. Produce a proposal doc (`Docs/Art/MESH_NAMING_CONVENTION_*.md` or handoff)

Each proposed move/rename lists: source path, target path, `find_references` result (`referenced_by: []` or not), and an owner checkbox. No move executes without a checked box.

For bulk renames, verify on disk that target names have no collisions:

```powershell
$names = Get-ChildItem Content/EnvSandbox/Meshes/Atlantis -Filter *.uasset |
  ForEach-Object { $_.BaseName -replace 'BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_', 'SM_ATL_Palace_' }
"$($names.Count) total, $($names | Sort-Object -Unique | Measure-Object | Select -Expand Count) unique"
$names | Group-Object | Where Count -gt 1
```

### 4. Hand off execution

The build lane (single editor, single 9316 listener) runs:

- `editor_query run_python` with `unattended: true` (suppresses the `Unable to Check Out From Revision Control!` modal storm on gitignored `Content/EnvSandbox/*` — observed 4:47 min wave 2026-08-30) or `mesh_query batch_rename_assets` with `dry_run: true` first.
- `project_query refresh_assets` / `get_asset_details` / `validate_naming_conventions` to verify.
- One batch at a time — a silent no-op and a wrong-actor move look identical from the return value.

## Guardrails

- **Read-only.** This skill never calls `batch_rename_assets` without `dry_run`, never calls `rename_asset`, never calls `delete_assets`.
- **No `Content/_PROJECT/` writes** — red line. Catalog it, never move it.
- **No filesystem renames of referenced assets** — `find_references` before any proposal; referenced assets must go through `IAssetTools` (redirector + fixup), not `Move-Item`.
- **`Content/EnvSandbox/*` is gitignored** (`.gitignore:183`) — disk moves there need registry verification, not `git status`.
- **One editor.** Never run catalog-mutating writes while another lane is saving (observed 2026-08-30: PBR_Auto 333-asset save wave interleaved with catalog reads caused Monolith timeouts).

## Reference

- Naming authority: `Docs/Art/MESH_NAMING_CONVENTION_2026-08-30.md` and `mesh_query validate_naming_conventions` prefix table (`SM_`, `SK_`, `M_`, `MI_`, `T_`, `BP_`, `NS_`, `NE_`, …).
- Folder hygiene precedent: `EnvSandbox/VFX` cruft → `_Archive_2026-08-30` (9 files, proven zero refs, 2026-08-30).
- Atlantis bulk precedent: staged script `Content/Python/org_atlantis_rename_2026-08-30.py` (333 `BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_*` → `SM_ATL_Palace_*`).

## Outputs

- `Saved/Audit/mesh_catalog_<date>.json` — committed.
- `Docs/Art/MESH_NAMING_CONVENTION_<date>.md` or `Docs/Handoffs/MESH_REORG_PROPOSAL_<date>.md` — committed.
- No `.uasset` mutations.
