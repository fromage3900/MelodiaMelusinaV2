"""Re-stage the BowStage bow-test corner in L_MelusinaMorning (2026-09-19).

Run inside the editor via Monolith editor_query run_python:
  exec(open(r'C:/EnvironmentPortfolio/BS_GodFile/Tools/stage_bow_test_room.py', encoding='utf-8').read())

Idempotent: existing BowStage labels are skipped, never duplicated.
Camera: reuse WC_Lookdev_waterline_dolly (-3100, 200, 180, yaw 8.5) - do not move it.
Evidence: Saved/Audit/BowStage_20260919/bow_stage_cast.json
"""
import json

CARD = {
    "bow": ("SM_BowStage_Bow", "/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Bow_R07",
            (-2900.0, 185.0, 165.0), (0.0, 8.5, 0.0), (1.0, 1.0, 1.0)),
    "rack": ("SM_BowStage_ArrowRack", "/Game/Cinematics/Shorewake/HERO01/WaveHarp_R07/SM_ME_WaveHarp_Arrow_R07",
             (-2890.0, 150.0, 150.0), (0.0, 8.5, 0.0), (1.0, 1.0, 1.0)),
    "catcher": ("SM_BowStage_Catcher", "/Engine/BasicShapes/Cube",
                (-2100.0, 250.0, 170.0), (0.0, 0.0, 0.0), (0.5, 3.0, 3.0)),
}
MIST = ("FX_BowStage_PondMist", "/Game/Melodia/VFX/NS_Morning_PondMist", (-2500.0, 200.0, 60.0))
LIGHT = ("L_BowStage_CoolLight", (-2700.0, 200.0, 300.0))

have = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if a.get_folder_path() == "BowStage":
            have[a.get_actor_label()] = True
    except Exception:
        pass

made, skipped = [], []
for _key, (label, mesh_path, loc, rot, scale) in CARD.items():
    if label in have:
        skipped.append(label)
        continue
    mesh = unreal.load_asset(mesh_path)
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
    a.set_actor_label(label)
    a.set_folder_path("BowStage")
    a.static_mesh_component.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(*scale))
    made.append(label)

label, mist_path, loc = MIST
if label not in have:
    fx = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.NiagaraActor, unreal.Vector(*loc), unreal.Rotator(0.0, 0.0, 0.0))
    fx.set_actor_label(label)
    fx.set_folder_path("BowStage")
    fx.get_components_by_class(unreal.NiagaraComponent)[0].set_asset(unreal.load_asset(mist_path))
    made.append(label)
else:
    skipped.append(label)

label, loc = LIGHT
if label not in have:
    lt = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(*loc), unreal.Rotator(0.0, 0.0, 0.0))
    lt.set_actor_label(label)
    lt.set_folder_path("BowStage")
    comp = lt.get_components_by_class(unreal.PointLightComponent)[0]
    comp.set_editor_property("light_color", unreal.LinearColor(0.55, 0.75, 1.0, 1.0))
    comp.set_editor_property("intensity", 750.0)
    made.append(label)
else:
    skipped.append(label)

print("BOWSTAGE_RESTAGE:" + json.dumps({"made": made, "skipped": skipped}))
