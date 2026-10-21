"""Tune ABP_Melusina_Current AnimGraphNode_KawaiiPhysics_0:
- Bind DA_Melusina_SkirtBoneConstraints if present
- Exclude duplicate child branches c_kilt_main_* and c_kilt_row_* so only the 16 radial c_kilt_01..08 chains simulate cleanly
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())


def main():
    abp_path = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
    abp = unreal.load_asset(abp_path)
    klass = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    if not abp or not klass:
        print("SKIRT_KAWAII_ERR=missing_abp_or_class")
        return 1
    nodes = list(abp.get_nodes_of_class(klass))
    if not nodes:
        print("SKIRT_KAWAII_ERR=no_kawaii_nodes")
        return 1
    graph_node = nodes[0]
    node = graph_node.get_editor_property("node")

    # Bind DA_Melusina_SkirtBoneConstraints if available
    bc_da = unreal.load_asset("/Game/Melodia/Characters/Melusina/Physics/DA_Melusina_SkirtBoneConstraints")
    bc_bound = False
    if bc_da:
        for prop_name in ("bone_constraints_data_asset", "constraints_data_asset"):
            try:
                node.set_editor_property(prop_name, bc_da)
                bc_bound = True
                break
            except Exception:
                pass

    # Exclude secondary branch chains c_kilt_main_* and c_kilt_row_* from double-simulation
    exclude_names = [
        "c_kilt_row_01_x", "c_kilt_row_02_x", "c_kilt_row_03_x", "c_kilt_row_04_x",
        "c_kilt_main_03_02_l", "c_kilt_main_03_03_l", "c_kilt_main_03_04_l",
        "c_kilt_main_03_02_r", "c_kilt_main_03_03_r", "c_kilt_main_03_04_r",
        "c_kilt_main_05_02_l", "c_kilt_main_05_03_l", "c_kilt_main_05_04_l",
        "c_kilt_main_05_02_r", "c_kilt_main_05_03_r", "c_kilt_main_05_04_r",
        "c_kilt_main_07_02_l", "c_kilt_main_07_03_l", "c_kilt_main_07_04_l",
        "c_kilt_main_07_02_r", "c_kilt_main_07_03_r", "c_kilt_main_07_04_r",
    ]
    excluded_set = 0
    try:
        excl = []
        for bname in exclude_names:
            ref = unreal.BoneReference()
            ref.set_editor_property("bone_name", bname)
            excl.append(ref)
        node.set_editor_property("exclude_bones", excl)
        excluded_set = len(excl)
    except Exception as exc:
        print("EXCLUDE_BONES_NOTE=", exc)

    settings = node.get_editor_property("physics_settings")
    settings.damping = 0.35
    settings.stiffness = 0.22
    settings.world_damping_location = 0.82
    settings.world_damping_rotation = 0.85
    settings.limit_angle = 32.0
    settings.radius = 2.8
    node.set_editor_property("physics_settings", settings)
    graph_node.set_editor_property("node", node)

    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    disk = PROJECT / "Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset"
    if disk.is_file():
        os.chmod(disk, stat.S_IWRITE)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(abp, False))
    print("SKIRT_KAWAII_FIX=" + json.dumps({
        "asset": abp_path,
        "bone_constraints_bound": bc_bound,
        "excluded_secondary_branches": excluded_set,
        "saved": saved,
        "settings": {
            "damping": float(settings.damping),
            "stiffness": float(settings.stiffness),
            "limit_angle": float(settings.limit_angle),
            "radius": float(settings.radius),
        }
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
