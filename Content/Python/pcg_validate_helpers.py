"""PCG validation helpers — generate wait, ISM counts, bounds."""
from __future__ import annotations

import time

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore


def pump_editor(_delta: float = 0.016) -> None:
    if unreal is None:
        return
    try:
        unreal.SystemLibrary.execute_console_command(None, "obj gc", None)
    except Exception:
        pass


def is_generating(comp) -> bool:
    if hasattr(comp, "is_generating"):
        try:
            return bool(comp.is_generating())
        except Exception:
            pass
    return False


def generate_and_wait(comp, force: bool = True, max_wait: float = 60.0) -> None:
    import pcg_graph_builder as gb

    gb.configure_pcg_component(comp, activated=True)
    comp.generate(force=force)
    deadline = time.time() + max_wait
    idle = 0
    while time.time() < deadline:
        if not is_generating(comp):
            idle += 1
            if idle >= 6:
                break
        else:
            idle = 0
        pump_editor()
        time.sleep(0.05)


def count_ism(actor) -> int:
    if unreal is None:
        return 0
    total = 0
    for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            total += int(comp.get_instance_count())
        except Exception:
            pass
    return total


def count_world_ism() -> int:
    if unreal is None:
        return 0
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    total = 0
    for actor in eas.get_all_level_actors():
        total += count_ism(actor)
    return total


def within_bounds(count: int, minimum: int, maximum: int) -> bool:
    return minimum <= count <= maximum


SCATTER_CHAIN_META_KEYS = frozenset({
    "surface_sampler",
    "density_filter",
    "spacing_prune",
    "pcgex_exclusion",
    "transform_jitter",
})


def scatter_chain_meta_valid(meta: dict | None) -> bool:
    """Static check that wire_scatter_chain metadata is complete."""
    if not meta:
        return False
    return SCATTER_CHAIN_META_KEYS.issubset(meta.keys())
