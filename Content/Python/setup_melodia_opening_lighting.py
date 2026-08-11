"""Add reversible, story-led lighting beats to the two opening maps."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
REPORT = ROOT / "Saved" / "Melodia" / "opening_lighting_setup.json"
LEVELS = {
    "dream": "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate",
    "morning": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
}


def _clear(eas, prefix="LT_Melodia_"):
    for actor in list(eas.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            eas.destroy_actor(actor)


def _light_color(color):
    """LightColor is an FColor in UE 5.8's Python bridge, not LinearColor."""
    return unreal.Color(*(max(0, min(255, round(channel * 255))) for channel in color[:3]), 255)


def _point(eas, label, location, color, intensity, radius, tags):
    actor = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    if not actor:
        raise RuntimeError(f"Could not spawn point light {label}")
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_property("light_color", _light_color(color))
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("cast_shadows", True)
    actor.tags = [unreal.Name(tag) for tag in tags]
    return actor


def _spot(eas, label, location, rotation, color, intensity, radius, tags):
    actor = eas.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*location), unreal.Rotator(*rotation))
    if not actor:
        raise RuntimeError(f"Could not spawn spot light {label}")
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.SpotLightComponent)
    component.set_editor_property("light_color", _light_color(color))
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("cast_shadows", True)
    actor.tags = [unreal.Name(tag) for tag in tags]
    return actor


def _dream(eas):
    _clear(eas)
    made = []
    # Cool approach rhythm; the middle is deliberately more unstable/purple.
    for index, x in enumerate((-600, -220, 220, 600)):
        color = (0.22, 0.42, 1.0, 1.0) if abs(x) > 300 else (0.72, 0.28, 1.0, 1.0)
        made.append(_point(eas, f"LT_Melodia_Dream_Pillar_{index}", (x, 0, 300), color, 1400.0, 900.0, ("Melodia", "Dreamstate", "Lighting")))
    made.append(_spot(eas, "LT_Melodia_Dream_Wake", (900, 0, 450), (-65, 180, 0), (0.68, 0.78, 1.0, 1.0), 2400.0, 1300.0, ("Melodia", "Dreamstate", "Wake")))
    made.append(_point(eas, "LT_Melodia_Dream_Dissonance", (0, 220, 180), (0.92, 0.12, 0.52, 1.0), 900.0, 650.0, ("Melodia", "Dreamstate", "Dissonance")))
    return [actor.get_actor_label() for actor in made]


def _morning(eas):
    _clear(eas)
    made = []
    made.append(_point(eas, "LT_Melodia_Morning_Bed", (-180, -90, 220), (1.0, 0.55, 0.30, 1.0), 950.0, 650.0, ("Melodia", "Bedroom", "Wake")))
    made.append(_point(eas, "LT_Melodia_Morning_Sir", (160, 130, 230), (1.0, 0.78, 0.34, 1.0), 1250.0, 620.0, ("Melodia", "Bedroom", "SirMelodious")))
    made.append(_spot(eas, "LT_Melodia_Morning_Exit", (0, 300, 350), (-62, 0, 0), (0.48, 0.65, 1.0, 1.0), 1100.0, 900.0, ("Melodia", "Bedroom", "Exit")))
    return [actor.get_actor_label() for actor in made]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results = {}
    for name, path in LEVELS.items():
        if not levels.load_level(path):
            raise RuntimeError(f"Could not load {path}")
        labels = _dream(eas) if name == "dream" else _morning(eas)
        levels.save_current_level()
        results[name] = {"level": path, "lights": labels}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaLighting] Built opening lighting -> {REPORT}")


if __name__ == "__main__":
    main()
