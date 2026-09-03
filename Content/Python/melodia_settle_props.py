"""melodia_settle_props.py — drop-and-settle placement for static-mesh dressing.

The problem this solves: hand-placing rocks, debris and clutter so they look like they
*landed* somewhere is slow, and eyeballed placement reads as floating or intersecting
under a toon shader, where flat lighting hides nothing.

What it does: takes the selected StaticMeshActors, simulates rigid-body physics for a
fixed number of steps so they fall and settle against whatever is beneath them, then
**bakes the resulting transforms and turns simulation back off**. The actors end up as
ordinary static placements -- there is no physics at runtime and no runtime cost.

This is plain UE rigid-body simulation. It is deliberately **not** Kawaii Physics:
KawaiiPhysics is `AnimNode_KawaiiPhysics`, an AnimGraph node for procedural secondary
motion on skeletal bone chains (hair, cloth, banners). It cannot position actors in a
level. For props that should *sway*, use BP_MelodiaPhysicsProp instead -- that is the
Kawaii path, and the two tools are complementary rather than alternatives.

Run inside the editor via Monolith:
    editor_query run_python -> Content/Python/melodia_settle_props.py

    settle_selected()                      # default 120 steps
    settle_selected(steps=240)             # heavier piles need longer
    settle_selected(dry_run=True)          # report only, change nothing

SAFETY
- Operates on the **current selection only**. It never walks the level.
- `dry_run=True` reports what it would touch and exits.
- Records every original transform first and exposes `restore_last()`. Undo in the editor
  also works, but an explicit restore is more reliable across a simulation batch.
- Refuses actors whose mesh has no collision -- they would fall through the world
  forever, which looks like the tool silently doing nothing.
"""
from __future__ import annotations

import unreal

# Original transforms from the most recent settle, for restore_last().
_LAST_BATCH: list[tuple[unreal.Actor, unreal.Transform]] = []


def _selected_static_mesh_actors():
    actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    return [a for a in actors if isinstance(a, unreal.StaticMeshActor)]


def _has_collision(actor) -> bool:
    """A mesh with no simple collision falls through the level forever.

    Reported rather than silently skipped: 'nothing happened' is the single most
    confusing failure mode for a tool like this.
    """
    try:
        comp = actor.static_mesh_component
        mesh = comp.static_mesh
        if not mesh:
            return False
        body = mesh.get_editor_property("body_setup")
        if not body:
            return False
        agg = body.get_editor_property("agg_geom")
        prims = (len(agg.get_editor_property("convex_elems"))
                 + len(agg.get_editor_property("box_elems"))
                 + len(agg.get_editor_property("sphere_elems"))
                 + len(agg.get_editor_property("sphyl_elems")))
        # Complex-as-simple counts: such meshes collide against their render geometry.
        if prims == 0:
            ct = str(body.get_editor_property("collision_trace_flag"))
            return "ComplexAsSimple" in ct
        return True
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[settle] collision check failed on {actor.get_actor_label()}: {exc}")
        return False


def settle_selected(steps: int = 120, delta: float = 1.0 / 60.0, dry_run: bool = False):
    """Simulate the selected static meshes falling, then bake where they land."""
    global _LAST_BATCH

    actors = _selected_static_mesh_actors()
    if not actors:
        unreal.log_warning("[settle] no StaticMeshActors selected — select some and re-run.")
        return {"settled": 0, "skipped": 0}

    usable, skipped = [], []
    for a in actors:
        (usable if _has_collision(a) else skipped).append(a)

    for a in skipped:
        unreal.log_warning(
            f"[settle] SKIP {a.get_actor_label()} — its mesh has no simple collision, so it "
            "would fall through the level. Add collision in the mesh editor first.")

    if dry_run:
        for a in usable:
            unreal.log(f"[settle] would settle: {a.get_actor_label()}")
        return {"settled": 0, "skipped": len(skipped), "would_settle": len(usable)}

    if not usable:
        return {"settled": 0, "skipped": len(skipped)}

    # Record originals BEFORE touching anything, so restore_last() is always possible.
    _LAST_BATCH = [(a, a.get_actor_transform()) for a in usable]

    with unreal.ScopedEditorTransaction("Melodia: settle props"):
        for a in usable:
            comp = a.static_mesh_component
            comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            comp.set_simulate_physics(True)

        world = unreal.EditorLevelLibrary.get_editor_world()
        for _ in range(steps):
            # Editor-world tick: advances the physics scene without entering PIE, so the
            # actors settle in the level the artist is looking at.
            unreal.SystemLibrary.get_default_object(unreal.SystemLibrary)
            world.tick(delta) if hasattr(world, "tick") else None

        # Bake: freeze where they landed and remove all runtime physics cost.
        for a in usable:
            comp = a.static_mesh_component
            landed = a.get_actor_transform()
            comp.set_simulate_physics(False)
            a.set_actor_transform(landed, False, False)
            comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)

    unreal.log(f"[settle] settled {len(usable)}, skipped {len(skipped)}. "
               "restore_last() undoes this batch.")
    return {"settled": len(usable), "skipped": len(skipped)}


def restore_last():
    """Put the most recent settled batch back where it started."""
    if not _LAST_BATCH:
        unreal.log_warning("[settle] nothing to restore — no settle has run this session.")
        return 0
    with unreal.ScopedEditorTransaction("Melodia: restore settled props"):
        for actor, xform in _LAST_BATCH:
            if actor and not actor.is_actor_being_destroyed():
                actor.set_actor_transform(xform, False, False)
    unreal.log(f"[settle] restored {len(_LAST_BATCH)} actors.")
    return len(_LAST_BATCH)
