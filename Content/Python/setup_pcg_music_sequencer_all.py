"""One-shot build for the second interactable musical PCG graph."""

from __future__ import annotations


def build_all(force: bool = True) -> dict:
    import build_pcg_music_sequencer
    import setup_pcg_music_sequencer_level
    import audit_pcg_music_sequencer

    graph = build_pcg_music_sequencer.build_sequencer_graph(force=force, create_profile=True)
    level = setup_pcg_music_sequencer_level.build_level()
    audit = audit_pcg_music_sequencer.audit()
    result = {"graph": graph, "level": level, "audit": audit}
    try:
        import unreal

        unreal.log(f"[PCG Music Sequencer] one-shot build complete: {result}")
    except Exception:
        pass
    return result


if __name__ == "__main__":
    print(build_all())
