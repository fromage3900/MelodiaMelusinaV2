import unreal


def run():
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    counts = {}
    static = []
    landscapes = []
    for actor in actors:
        cls = actor.get_class().get_name()
        counts[cls] = counts.get(cls, 0) + 1
        if cls == "StaticMeshActor":
            origin, extent = actor.get_actor_bounds(False, False)
            static.append({
                "label": actor.get_actor_label(),
                "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
                "bounds_origin": [origin.x, origin.y, origin.z],
                "bounds_extent": [extent.x, extent.y, extent.z],
            })
        if cls == "Landscape":
            origin, extent = actor.get_actor_bounds(False, False)
            landscapes.append({
                "label": actor.get_actor_label(),
                "bounds_origin": [origin.x, origin.y, origin.z],
                "bounds_extent": [extent.x, extent.y, extent.z],
            })
    return {
        "total_actors": len(actors),
        "static_mesh_actors": len(static),
        "landscapes": landscapes,
        "class_counts": sorted(counts.items(), key=lambda item: -item[1]),
        "static_meshes": static,
    }


if __name__ == "__main__":
    print(run())
