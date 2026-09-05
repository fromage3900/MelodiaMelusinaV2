"""Repair existing Sea Above Oceanology bounds; run in the editor via Monolith.

Writes a before/after report and disk backups, but leaves package saving explicit.
Does not move the ocean, create actors, or edit the false-ocean presentation.
"""
import datetime
import json
import math
from pathlib import Path
import shutil
import stat

import unreal


def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    expected = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
    if world.get_path_name().split(".")[0] != expected:
        raise RuntimeError("Load LV_SeaAbove_Prototype before applying this repair")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    volumes = [a for a in actors if a.get_class().get_name() == "OceanologyWaterVolume"]
    if len(volumes) != 1:
        raise RuntimeError(f"Expected one authored OceanologyWaterVolume, got {len(volumes)}")
    volume = volumes[0]
    ocean = volume.get_editor_property("oceanology_water")
    if not ocean or ocean.get_class().get_name() != "OceanologyInfiniteOcean":
        raise RuntimeError("The authored volume must reference the infinite ocean")
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = root / "Saved/Audit" / f"oceanology_volume_{stamp}"
    out.mkdir(parents=True, exist_ok=False)

    def snapshot():
        quad = ocean.get_editor_property("quad_tree_settings")
        return {
            "volume_location": volume.get_actor_location().to_tuple(),
            "volume_scale": volume.get_actor_scale3d().to_tuple(),
            "volume_bounds": [v.to_tuple() for v in volume.get_actor_bounds(False)],
            "ocean_location": ocean.get_actor_location().to_tuple(),
            "far_mesh_extent_cm": quad.get_editor_property("far_distance_mesh_extent"),
            "use_far_mesh": quad.get_editor_property("use_far_mesh"),
            "water_volume": volume.get_editor_property("water_volume"),
        }

    packages = [a.get_package().get_name() for a in (volume, ocean)]
    for package in packages:
        if not package.startswith("/Game/__ExternalActors__/"):
            raise RuntimeError(f"Expected isolated external actor package: {package}")
        disk = root / "Content" / (package.removeprefix("/Game/") + ".uasset")
        if disk.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
            raise RuntimeError(f"Acquire the asset lock before writing: {disk}")
        shutil.copy2(disk, out / disk.name)
    report = {"map": expected, "packages": packages, "before": snapshot(), "saved": False}
    report_path = out / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Keep the existing dense near grid; extend only its inexpensive far mesh.
    # The physical bounds cover the authored 6 km horizon region, 50 m below
    # the actual surface. Oceanology is already an APhysicsVolume; no second
    # water/swimming authority is needed.
    quad = ocean.get_editor_property("quad_tree_settings")
    far_extent = max(600000.0, quad.get_editor_property("far_distance_mesh_extent"))
    origin = ocean.get_actor_location()
    with unreal.ScopedEditorTransaction("Repair Sea Above Oceanology water bounds"):
        ocean.modify()
        quad.set_editor_property("far_distance_mesh_extent", far_extent)
        quad.set_editor_property("use_far_mesh", True)
        ocean.set_editor_property("quad_tree_settings", quad)
        volume.modify()
        volume.set_actor_rotation(unreal.Rotator(), False)
        volume.set_actor_scale3d(unreal.Vector(far_extent / 100.0, far_extent / 100.0, 25.0))
        volume.set_actor_location(unreal.Vector(origin.x, origin.y, origin.z - 2500.0), False, False)

    report["after"] = snapshot()
    center, extent = volume.get_actor_bounds(False)
    report["checks"] = {
        "top_matches_ocean": math.isclose(center.z + extent.z, origin.z, abs_tol=0.1),
        "covers_horizon_xy": extent.x >= far_extent and extent.y >= far_extent,
        "ocean_transform_preserved": report["before"]["ocean_location"] == report["after"]["ocean_location"],
        "native_water_volume": bool(volume.get_editor_property("water_volume")),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not all(report["checks"].values()):
        raise RuntimeError(f"Volume verification failed; inspect {report_path}")
    print(json.dumps({"report": str(report_path), **report}))


if __name__ == "__main__":
    run()
