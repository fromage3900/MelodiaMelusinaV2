"""Audit WP Pillar levels for ISM counts and compile status."""
from __future__ import annotations

import unreal

WP_LEVELS = [
    "/Game/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto",
    "/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery",
    "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream",
    "/Game/EnvSandbox/Environments/WP/L_WP_SpaceCathedral",
]

def main():
    unreal.log("[WP_Audit] Starting WP Pillar level audit...")
    results = {}
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    
    for level_path in WP_LEVELS:
        unreal.log(f"[WP_Audit] Loading {level_path}...")
        try:
            loaded = level_editor.load_level(level_path) if level_editor else False
            world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
            if not loaded or not world:
                results[level_path] = {"loaded": False, "error": "Failed to load"}
                continue
                
            actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
            ism_count = 0
            hism_count = 0

            # PCG often owns ISM/HISM components on generic PCG actors rather
            # than InstancedStaticMeshActor subclasses. Count components, not
            # actor class names, so the audit reflects generated geometry.
            for actor in actors:
                for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
                    count = component.get_instance_count()
                    if isinstance(component, unreal.HierarchicalInstancedStaticMeshComponent):
                        hism_count += count
                    else:
                        ism_count += count
            
            results[level_path] = {
                "loaded": True,
                "ism_instances": ism_count,
                "hism_instances": hism_count,
                "total_instances": ism_count + hism_count,
                "actor_count": len(actors)
            }
            unreal.log(f"[WP_Audit] {level_path}: ISM={ism_count}, HISM={hism_count}, Actors={len(actors)}")
            
        except Exception as e:
            results[level_path] = {"loaded": False, "error": str(e)}
            unreal.log_error(f"[WP_Audit] {level_path} failed: {e}")
    
    # Summary
    unreal.log("[WP_Audit] === SUMMARY ===")
    for path, data in results.items():
        if data.get("loaded"):
            unreal.log(f"  {path}: ISM={data['ism_instances']}, HISM={data['hism_instances']}, Total={data['total_instances']}")
        else:
            unreal.log(f"  {path}: FAILED - {data.get('error')}")
    
    return results


if __name__ == "__main__":
    main()
