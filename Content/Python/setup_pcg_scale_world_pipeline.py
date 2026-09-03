"""Create the additive UE 5.8 scale-world proof assets and manifest."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pcg_scale_world_pipeline as scale
import pcg_visual_chunk_builder as chunk_builder


def _proof_level_is_world_partitioned(unreal, level_path: str) -> bool:
    """Use both the on-disk OFPA marker and UE's live bounds query.

    A blank `.umap` can remain in the asset registry after a failed authoring
    pass, so checking only `does_asset_exist()` is not enough for the builder.
    """
    content_root = Path(unreal.Paths.project_content_dir()).resolve()
    relative = Path(level_path.removeprefix("/Game/").replace("/", "\\"))
    external_dir = content_root / "__ExternalActors__" / relative
    if external_dir.is_dir() and any(external_dir.rglob("*.uasset")):
        return True
    try:
        bounds = unreal.WorldPartitionBlueprintLibrary.get_editor_world_bounds()
        valid = getattr(bounds, "is_valid", False)
        return bool(valid() if callable(valid) else valid)
    except Exception:
        return False


def _recreate_stale_proof_level(unreal, level_editor, level_path: str) -> dict:
    """Recreate only the additive proof map when it is a stale non-WP package."""
    content_root = Path(unreal.Paths.project_content_dir()).resolve()
    relative = Path(level_path.removeprefix("/Game/").replace("/", "\\"))
    package_path = (content_root / relative).with_suffix(".umap").resolve()
    expected_parent = (content_root / "EnvSandbox" / "PCG" / "Musical" / "Hero").resolve()
    if package_path.parent != expected_parent:
        raise RuntimeError(f"refusing to recreate proof package outside the hero proof folder: {package_path}")

    scratch_path = f"{LEVEL_DIR}/_PCG_Hero_ScaleWorldScratch"
    if not unreal.EditorAssetLibrary.does_asset_exist(scratch_path):
        if not level_editor.new_level(scratch_path, is_partitioned_world=False):
            raise RuntimeError(f"could not park the editor on scratch level: {scratch_path}")
    else:
        if not level_editor.load_level(scratch_path):
            raise RuntimeError(f"could not load scratch level: {scratch_path}")

    deleted_asset = False
    if unreal.EditorAssetLibrary.does_asset_exist(level_path):
        deleted_asset = bool(unreal.EditorAssetLibrary.delete_asset(level_path))
    removed_files: list[str] = []
    if package_path.is_file():
        package_path.unlink()
        removed_files.append(str(package_path))
    external_dir = (content_root / "__ExternalActors__" / relative).resolve()
    external_root = (content_root / "__ExternalActors__").resolve()
    if external_dir.is_dir() and external_dir.is_relative_to(external_root):
        shutil.rmtree(external_dir)
        removed_files.append(str(external_dir))

    if not level_editor.new_level(level_path, is_partitioned_world=True):
        raise RuntimeError(f"could not recreate World Partition proof level: {level_path}")
    return {
        "recreated": True,
        "deleted_asset": deleted_asset,
        "removed_files": removed_files,
        "scratch_level": scratch_path,
        "world_partition": _proof_level_is_world_partitioned(unreal, level_path),
    }


def ensure_proof_pcg_volumes(unreal, actor_subsystem, level_path: str) -> list[dict]:
    """Author the four deterministic builder inputs in the additive proof map."""
    # The proof inputs are produced from the same reusable chunk planner used
    # by the endless-grid manifest. This keeps the proof triad honest: it is
    # instances of shared graph/profile bindings, not bespoke
    # graph copies.
    graph_specs = []
    for manifest in scale.build_chunk_grid(3900, radius=1):
        for spec in chunk_builder.chunk_volume_specs(manifest):
            # Keep every proof input visibly tied to the shared chunk planner,
            # including the xylophone landmark in chunk (0, 1).  The old
            # replacement list only normalized the origin row and made the
            # new instrument look like an unrelated one-off volume.
            label = spec["label"].replace("PCG Chunk ", "PCG ScaleWorld ", 1)
            graph_specs.append((
                label,
                spec["graph"],
                tuple(float(value) for value in spec["origin_cm"]),
                spec,
            ))
    existing = {actor.get_actor_label(): actor for actor in (actor_subsystem.get_all_level_actors() or [])}
    report: list[dict] = []
    for index, (label, graph_path, location, spec) in enumerate(graph_specs):
        graph = unreal.EditorAssetLibrary.load_asset(graph_path)
        if not graph:
            raise RuntimeError(f"scale proof graph missing: {graph_path}")
        volume = existing.get(label)
        if not volume:
            volume = actor_subsystem.spawn_actor_from_class(
                unreal.PCGVolume,
                unreal.Vector(*location),
                unreal.Rotator(0.0, 0.0, 0.0),
            )
            if not volume:
                raise RuntimeError(f"could not spawn scale proof PCG volume: {label}")
            volume.set_actor_label(label)
            existing[label] = volume
        else:
            volume.set_actor_location(unreal.Vector(*location), False, False)
        volume.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        tags = [str(tag) for tag in list(volume.tags or [])]
        if "PCG_ScaleWorld_ProofInput" not in tags:
            tags.append("PCG_ScaleWorld_ProofInput")
        volume.tags = tags
        try:
            volume.set_editor_property("is_spatially_loaded", False)
        except Exception:
            pass

        component = volume.get_component_by_class(unreal.PCGComponent)
        if not component:
            raise RuntimeError(f"scale proof volume has no PCG component: {label}")
        component.set_graph(graph)
        component.set_editor_property("activated", True)
        component.set_editor_property("is_component_partitioned", True)
        component.set_editor_property(
            "generation_trigger",
            unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND,
        )
        # The commandlet is explicitly allowed to include Normal mode as a
        # fallback; set the serialized mode when the reflected enum is exposed.
        dirty_mode = getattr(unreal, "PCGEditorDirtyMode", None)
        if dirty_mode is not None and hasattr(dirty_mode, "LOAD_AS_PREVIEW"):
            try:
                component.set_editor_property("serialized_editing_mode", dirty_mode.LOAD_AS_PREVIEW)
            except Exception:
                pass
        report.append({
            "label": label,
            "graph": graph_path,
            "profile": spec["profile"],
            "chunk": [spec["chunk_x"], spec["chunk_y"]],
            "biome_band": spec["biome_band"],
            "location": list(location),
            "partitioned": True,
            "generation_trigger": "GenerateOnDemand",
            "reusable_graph_binding": True,
            "curve_system": spec["curve_system"],
            "border_anchors": spec["border_anchors"],
        })
    return report


def build_scale_world_proof() -> dict:
    import importlib
    import unreal

    importlib.reload(scale)
    importlib.reload(chunk_builder)
    builder = scale.ensure_builder_settings_asset(unreal)
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_exists = unreal.EditorAssetLibrary.does_asset_exist(scale.SCALE_WORLD_PROOF_LEVEL)
    level_setup = {"recreated": False, "world_partition": False}
    if not level_exists:
        created = level_editor.new_level(scale.SCALE_WORLD_PROOF_LEVEL, is_partitioned_world=True)
        if not created:
            raise RuntimeError(f"could not create World Partition proof level: {scale.SCALE_WORLD_PROOF_LEVEL}")
        level_setup = {
            "created": True,
            "world_partition": _proof_level_is_world_partitioned(unreal, scale.SCALE_WORLD_PROOF_LEVEL),
        }
    elif not level_editor.load_level(scale.SCALE_WORLD_PROOF_LEVEL):
        raise RuntimeError(f"could not load World Partition proof level: {scale.SCALE_WORLD_PROOF_LEVEL}")
    elif not _proof_level_is_world_partitioned(unreal, scale.SCALE_WORLD_PROOF_LEVEL):
        level_setup = _recreate_stale_proof_level(unreal, level_editor, scale.SCALE_WORLD_PROOF_LEVEL)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    proof_inputs = ensure_proof_pcg_volumes(unreal, actor_subsystem, scale.SCALE_WORLD_PROOF_LEVEL)
    level_editor.save_current_level()
    world_partition_verified = _proof_level_is_world_partitioned(unreal, scale.SCALE_WORLD_PROOF_LEVEL)
    if not world_partition_verified:
        raise RuntimeError("scale proof level is still not a World Partition level after proof inputs were saved")
    root = Path(unreal.Paths.project_saved_dir()) / "Audit"
    report = scale.write_grid_report(root / "pcg_scale_world_chunk_grid.json")
    reusable_plan = chunk_builder.write_visual_world_plan(
        root / "pcg_visual_world_plan.json",
        world_seed=3900,
        radius=2,
    )
    result = {
        "proof_level": scale.SCALE_WORLD_PROOF_LEVEL,
        "level_setup": level_setup,
        "world_partition_verified": world_partition_verified,
        "builder_settings": builder,
        "proof_pcg_inputs": proof_inputs,
        "chunk_grid": report,
        "reusable_world_plan": reusable_plan,
        "scale_contract": scale.scale_contract(),
        "production_maps_touched": False,
    }
    unreal.log(f"[PCG Scale World] proof ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    import traceback

    report_path = Path(__file__).resolve().parents[1] / "Saved" / "Audit" / "pcg_scale_world_proof_setup.json"
    try:
        result = build_scale_world_proof()
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - persist the headless failure for the evaluator lane
        result = {
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "production_maps_touched": False,
        }
        unreal = None
        try:
            import unreal as _unreal
            unreal = _unreal
            unreal.log_error(f"[PCG Scale World] proof setup failed: {exc}")
        except Exception:
            pass
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    if not result.get("ok"):
        raise SystemExit(1)
