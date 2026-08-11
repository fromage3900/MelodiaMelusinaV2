"""One-shot post-module-reload build for the interactive PCG piano."""

from __future__ import annotations


def build_all(force: bool = True) -> dict:
    import build_piano_assets
    import build_pcg_piano
    import setup_pcg_piano_level
    import audit_pcg_piano

    assets = build_piano_assets.build_assets()
    graph = build_pcg_piano.build_piano_graph(force=force, create_profile=True)
    level = setup_pcg_piano_level.build_level()
    audit = audit_pcg_piano.audit()
    result = {"assets": assets, "graph": graph, "level": level, "audit": audit}

    try:
        import unreal

        unreal.log(f"[PCG Piano] one-shot build complete: {result}")
    except Exception:
        pass
    return result


if __name__ == "__main__":
    print(build_all())
