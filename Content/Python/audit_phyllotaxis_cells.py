import unreal


def run():
    rows = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not actor.get_actor_label().startswith("PCG_East_Phyllotaxis"):
            continue
        points = []
        count = 0
        for ism in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            n = ism.get_instance_count()
            count += n
            for index in range(n):
                try:
                    transform = ism.get_instance_transform(index, True)
                    p = transform.translation
                    points.append((p.x, p.y, p.z))
                except Exception:
                    pass
        if points:
            rows.append({
                "label": actor.get_actor_label(),
                "location": str(actor.get_actor_location()),
                "scale": str(actor.get_actor_scale3d()),
                "instances": count,
                "world_extent_cm": [
                    round(max(p[0] for p in points) - min(p[0] for p in points), 2),
                    round(max(p[1] for p in points) - min(p[1] for p in points), 2),
                    round(max(p[2] for p in points) - min(p[2] for p in points), 2),
                ],
                "z_range_cm": [round(min(p[2] for p in points), 2), round(max(p[2] for p in points), 2)],
            })
    return rows


if __name__ == "__main__":
    print(run())

