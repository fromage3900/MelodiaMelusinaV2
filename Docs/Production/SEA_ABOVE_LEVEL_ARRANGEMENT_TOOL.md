# Landscape arrangement tool contract

Use [`Content/Python/level_arrangement_tools.py`](../../Content/Python/level_arrangement_tools.py) for any future level pass that must put imported static meshes on terrain. It is deliberately manifest driven so an agent cannot accidentally move every hero actor in a map.

The manifest format is one entry per line:

```text
ActorLabel(StaticMeshActor_UAID_full_id): C:/path/to/external-actor.uasset
```

The tool matches both the label and the full UAID. It traces down with `ECC_VISIBILITY`, ignores every `StaticMeshActor` so elevated props cannot occlude the terrain, and accepts only a `Landscape` hit. Applying moves only Z until the world bounds bottom reaches the impact point; XY, rotation, and scale remain authored. An optional `clamp_outside_xy=True` moves a target whose bounds lie outside the Landscape footprint to the nearest valid edge before tracing, and records that choice.

The returned summary includes one `package_paths` entry for each matched actor. SeaAbove uses World Partition external actors, so `save_current_level` alone is not sufficient: pass that exact array to Monolith `editor.save_packages` (and include the map package when it was changed), then reload the level and run the read-only audit again. This explicit package save and reload audit are the acceptance gate for placement work.

## Monolith calls

Run a read-only audit first:

```json
{
  "action": "run_python",
  "params": {
    "mode": "execute_statement",
    "unattended": true,
    "file_scope": "public",
    "command": "import sys; sys.path.append('C:/EnvironmentPortfolio/BS_GodFile/Content/Python'); import level_arrangement_tools as t; print(t.ground_static_mesh_manifest('C:/path/manifest.txt', apply=False, clamp_outside_xy=False, report_path='C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/arrangement_audit.json'))"
  }
}
```

Apply the reviewed set. Capture the returned `package_paths` array from the
summary and pass it to `editor.save_packages` as a second, explicit Monolith
call; the convenience map save inside the helper does not replace this step:

```json
{
  "action": "run_python",
  "params": {
    "mode": "execute_statement",
    "unattended": true,
    "file_scope": "public",
    "command": "import sys; sys.path.append('C:/EnvironmentPortfolio/BS_GodFile/Content/Python'); import level_arrangement_tools as t; print(t.ground_static_mesh_manifest('C:/path/manifest.txt', apply=True, clamp_outside_xy=True, report_path='C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/arrangement_applied.json'))"
  }
}
```

Run the same call again with `apply=False` and a separate `*_post.json` report. Acceptance is: `matched == manifest_entries`, `landscape_hits == matched`, `no_landscape_hit == 0`, `outside_landscape_xy == 0` when clamping is part of the manifest decision, and `candidate_delta_abs_cm.max <= 0.5`.

Example of the required scoped package save (use the exact array returned by
the apply call):

```json
{
  "action": "save_packages",
  "params": {
    "packages": ["/Game/__ExternalActors__/.../exact_package_from_summary"],
    "fail_on_unrequested_dirty": false,
    "dry_run": false
  }
}
```

For slopes, do not rotate every mesh automatically. First classify the asset as a plant, rock, architectural piece, or hero prop; slope alignment is an artistic/grouping pass after vertical contact. Do not use this utility on PCG ISM/HISM instances: those are owned by their graph's landscape raycast branch.

## SeaAbove evidence

The disk-verified 2026-09-04 manifest pass matched 184/184 geometry actors,
produced 184/184 Landscape hits, explicitly saved 184/184 external actor
packages, edge-clamped three north-edge ivy actors, and after a clean level
reload verified a maximum remaining delta of 0.15 cm. The exact report is
`Saved/Audit/sea_above_attached_mesh_grounding_disk_verified_2026-09-04.json`.
