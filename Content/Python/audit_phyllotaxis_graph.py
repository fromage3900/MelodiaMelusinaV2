import unreal


PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisBiome"


def run():
    graph = unreal.EditorAssetLibrary.load_asset(PATH)
    if graph is None:
        raise RuntimeError(PATH)
    fields = [
        "grid_extents", "cell_size", "resolution", "distribution", "phi",
        "golden_ratio", "ray_direction", "ray_length", "b_unbounded",
        "select_landscape_hits", "keep_original_on_miss", "ignore_pcg_hits",
    ]
    rows = []
    for node in graph.nodes:
        settings = node.get_settings()
        row = {"node": node.get_name(), "class": settings.get_class().get_name() if settings else None}
        if settings:
            props = {}
            for field in fields:
                try:
                    props[field] = str(settings.get_editor_property(field))
                except Exception:
                    pass
            row["props"] = props
            if settings.get_class().get_name() == "PCGExCreateShapeFiblatSettings":
                row["fiblat_fields"] = [name for name in dir(settings) if not name.startswith("_") and any(k in name.lower() for k in ("gold", "phi", "ratio", "resol", "extent", "distrib", "scale"))]
        rows.append(row)
    return rows


if __name__ == "__main__":
    print(run())
