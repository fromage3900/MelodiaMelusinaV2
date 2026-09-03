"""Per-pillar lighting/exposure pass so hero plates stop reading as silhouettes.

Root problem (seen on all 2026-07-09 plates): the Sun sits behind the terrain
relative to Cam_Hero_Establishing, so the terrain is backlit black. This turns
each Sun toward the camera azimuth (front-lit at a pleasing ~35deg offset),
bumps intensity slightly, and clamps PPV auto-exposure so the sky can't drive
the terrain into shadow.

Run per pillar IN THE EDITOR (kick), then verify/capture in later calls:
    import wp_lighting_pass; wp_lighting_pass.apply('SakuraDream')
"""
from __future__ import annotations

import json
import math

# camera azimuths are ~41-45deg (cameras sit SW of origin looking NE);
# sun yaw should be ~camera yaw +/- offset so light comes over the shoulder.
PILLAR_LIGHT = {
    # yaw, pitch, intensity, exposure (min, max)
    "SakuraDream":    {"yaw": 75.0,  "pitch": -38.0, "intensity": 8.0, "exposure": (0.9, 1.15)},
    "SpaceCathedral": {"yaw": 70.0,  "pitch": -28.0, "intensity": 6.5, "exposure": (0.8, 1.1)},
    "BaroqueGrotto":  {"yaw": 80.0,  "pitch": -32.0, "intensity": 5.5, "exposure": (0.85, 1.1)},
    "CosmicOrrery":   {"yaw": 85.0,  "pitch": -22.0, "intensity": 3.5, "exposure": (0.7, 1.05)},
}


def apply(pillar: str) -> dict:
    import unreal

    cfg = PILLAR_LIGHT[pillar]
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(f"/Game/EnvSandbox/Environments/WP/L_WP_{pillar}")
    wpbl = unreal.WorldPartitionBlueprintLibrary
    wpbl.load_actors([d.guid for d in wpbl.get_actor_descs()])
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report = {"pillar": pillar, "sun": False, "ppv": False}
    for a in eas.get_all_level_actors() or []:
        label = a.get_actor_label()
        if label == "Sun":
            r = unreal.Rotator()
            r.set_editor_property("yaw", cfg["yaw"])
            r.set_editor_property("pitch", cfg["pitch"])
            r.set_editor_property("roll", 0.0)
            a.set_actor_rotation(r, False)
            lc = a.get_component_by_class(unreal.DirectionalLightComponent)
            if lc:
                lc.set_editor_property("intensity", cfg["intensity"])
            report["sun"] = {"yaw": cfg["yaw"], "pitch": cfg["pitch"], "intensity": cfg["intensity"]}
        elif label.startswith("PPV"):
            pc = a.get_component_by_class(unreal.PostProcessComponent) or a
            try:
                settings = (pc if isinstance(pc, unreal.PostProcessComponent) else a).get_editor_property("settings")
                settings.set_editor_property("override_auto_exposure_min_brightness", True)
                settings.set_editor_property("override_auto_exposure_max_brightness", True)
                settings.set_editor_property("auto_exposure_min_brightness", cfg["exposure"][0])
                settings.set_editor_property("auto_exposure_max_brightness", cfg["exposure"][1])
                (pc if isinstance(pc, unreal.PostProcessComponent) else a).set_editor_property("settings", settings)
                report["ppv"] = {"exposure": cfg["exposure"]}
            except Exception as exc:  # noqa: BLE001
                report["ppv"] = f"err:{str(exc)[:80]}"
    report["saved"] = les.save_current_level()
    print(json.dumps(report))
    return report
