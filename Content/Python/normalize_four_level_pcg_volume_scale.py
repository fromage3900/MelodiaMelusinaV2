"""Normalize portfolio PCG volume footprint without changing authored locations."""
import unreal

LEVELS = [
    "/Game/EnvSandbox/Environments/L_EscherAscent",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/EnvSandbox/Environments/L_InfiniteScore",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
]

def run():
    report = {}
    for level in LEVELS:
        unreal.EditorLevelLibrary.load_level(level)
        changed = []
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if not actor.get_actor_label().startswith("PCG_"):
                continue
            before = actor.get_actor_scale3d()
            actor.set_actor_scale3d(unreal.Vector(25.0, 25.0, 5.0))
            component = actor.get_component_by_class(unreal.PCGComponent)
            if component:
                component.generate(True)
            changed.append({
                "label": actor.get_actor_label(),
                "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                "old_scale": [before.x, before.y, before.z],
                "new_scale": [25.0, 25.0, 5.0],
                "generated": bool(component),
            })
        unreal.EditorLevelLibrary.save_current_level()
        report[level] = changed
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
