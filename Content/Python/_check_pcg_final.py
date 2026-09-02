import unreal
import json

# Check PCG volumes and their instances
actors = unreal.EditorLevelLibrary.get_all_level_actors()
pcg = [a for a in actors if type(a).__name__ == "PCGVolume"]

for vol in pcg:
    label = vol.get_actor_label()
    isms = vol.get_components_by_class(unreal.InstancedStaticMeshComponent)
    total = sum(ism.get_instance_count() for ism in isms)
    print(f"\n{label}: {total} instances")
    for ism in isms:
        count = ism.get_instance_count()
        if count > 0:
            mesh = ism.get_editor_property("static_mesh")
            mat = ism.get_editor_property("override_materials")
            mat_name = mat[0].get_name() if mat and mat[0] else "(none)"
            print(f"  {mesh.get_name()}: {count} instances, mat={mat_name}")
