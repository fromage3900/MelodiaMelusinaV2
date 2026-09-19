# Proof B — Castle / Zen Shrine SurrealPlan → ROLE_UE_HINTS (2026-09-19)

**Status:** Live apply succeeded in UE 5.8 BS_GodFile, then the editor hung (sticky `UnrealEditor` process; PC restart required). Fixtures and apply script are committed so re-apply is one command after relaunch.

## What was proven

1. Offline schema validation against `Config/world_schema.json` (`surreal_arch_world_v1`).
2. ROLE_UE_HINTS resolution for `CASTLE` and `ZEN_SHRINE` styles against on-disk MIs.
3. `hism_groups` built by `(role, lib)` on both fixtures.
4. Live `import_world_manifest` dry-run + `--apply` via `Content/Python/proof_b_run_import_apply.py`:
   - Castle: 15 StaticMeshActors
   - Zen shrine: 8 StaticMeshActors
   - Greybox_Kit meshes for `static_mesh_path`

## Tracked entry points

| Item | Path |
|------|------|
| Castle fixture | `deploy/fixtures/SurrealPlan_Castle_ProofB.world.json` |
| Zen fixture | `deploy/fixtures/SurrealPlan_ZenShrine_ProofB.world.json` |
| One-shot apply | `Content/Python/proof_b_run_import_apply.py` |
| Importer | `Content/Python/import_world_manifest.py` |
| Export hints | `deploy/surreal_world/export.py` |
| Evidence | `Docs/Evidence/proof_b_*_2026-09-19.json` |

## Re-apply after UE relaunch

In the editor Output Log / Python console (absolute path required):

```text
py "C:\EnvironmentPortfolio\BS_GodFile\Content\Python\proof_b_run_import_apply.py"
```

Or from Monolith `editor_query` / `run_console_command` with that same `py "..."` string.

## Fixes included in this commit

- `import_world_manifest.py`: soft-skip schema validation when UE-embedded Python lacks `jsonschema` (offline validation remains the gate).
- `export.py`: `Show_*` materials point at `.../Showcase/` (not missing `.../Stylized/` paths); `ZEN_SHRINE` sacred uses `MI_Zen_Karesansui` until `MI_Zen_HondenSanctum` exists.

## Still open (not proven)

- True `HierarchicalInstancedStaticMesh` spawn from `hism_groups` (importer still uses StaticMeshActors).
- Assigning materials from `ue_material_hint` during apply.
- Editor hang after bulk spawn (D3D12 Ensure history on PIE / Outliner); re-apply in smaller batches if hang repeats.
- PR scaffold on `cursor/realtime-world-compiler-b196` / MelodiaMelusinaV2#248 may already overlap fixtures/docs — reconcile on merge.

## Do not lose on restart

Local ignored copies also live under `Saved/Audit/proof_b_*` (gitignored). Tracked copies under `deploy/fixtures/` and `Docs/Evidence/` are the source of truth after this commit.
