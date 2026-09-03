# Sculpt → Unreal asset intake — 2026-08-11

**For:** dropping new sculpts into MelodiaMelusinaV2 without burning LFS or creating redirectors.  
**Echo stage:** `author` only until the mesh is imported, compiled, and (if gameplay-facing) covered by static/runtime gates.  
**Companion:** [`MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md`](MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md) (Polycam/Kiri → ZBrush → inbox), [`LIVEOPS_GIT_SOP_2026-08-11.md`](LIVEOPS_GIT_SOP_2026-08-11.md), [`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md)

## While you sculpt (now)

Keep working in Blender / ZBrush. Do **not** push WIP FBX every hour.

When a checkpoint is ready:

1. Export to `Imports/Sculpt/Inbox/` with versioned name (`SM_…_v01.fbx`).
2. Optional sidecar: copy [`specs/sculpt/sidecar.example.json`](../specs/sculpt/sidecar.example.json) → `SameStem.sculpt.json`.
3. Offline check (no editor):

```bash
python Tools/sculpt_intake_check.py --limit-mb 50
```

4. Tell an agent / yourself: “import inbox” — one editor session, one LFS commit.

## Destinations (pick before import)

| Kind | Preferred UE path | Notes |
|------|-------------------|--------|
| Ornament / prop | `/Game/EnvSandbox/Meshes/Ornament/` | Existing helper: `Content/Python/import_ornament_fbx.py` (KitbashExport path — adapt inbox) |
| Universal material test | MI under EnvSandbox Materials | Assign `M_Master_Toon_Universal` after import |
| Melusina wardrobe / body | `/Game/Melodia/Characters/Melusina/…` | Never overwrite existing SK without a new path |
| Integration-only props | `/Game/MelodiaIntegration/…` | Fits `slice50` collab pack |

**Hard rule:** if `git ls-files` already has that asset stem, choose a **new** package path. FBX into an occupied path = redirector (AGENTS.md).

## LFS / 50 MB sharing

- Single mesh drop ≤50 MB → stays in collab budget (`cursor/` / `collab/` branches).
- Hero sculpt >50 MB → `feature/sculpt-…` branch, `MELODIA_LFS_LIMIT_MB=512`, still **one** commit when done.
- Do not commit `Imports/Sculpt/Inbox/*` binaries to git by default (gitignored except README). Publish source FBX only when intentionally sharing DCC.

## After import (Windows)

1. Compile / open mesh; assign Universal MI if environment prop.
2. If PCG / physics placement: register with Universal scatter tags (`PCG_Ground` / volume) — Lane E / `placement50`.
3. Move FBX → `Imports/Sculpt/Archive/`.
4. Commit **only** the new `.uasset` (+ textures), not a mixed refactor.
5. Echo: mesh drops do not close `runtime`. Gameplay still needs campaign ledger rows.

## Parallel with play-proof

Sculpting does not need Monolith. Lane A (runtime gate) and sculpt intake can proceed in parallel as long as **one** editor owns Content writes.
