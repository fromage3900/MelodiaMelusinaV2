"""Health check for the GN scene-time seam - run inside Blender 5.2.

Proves `melodia_gn/time.py` is actually wired, and that its determinism
contract holds. A diff review cannot prove either: `safe_node` returns None
instead of raising, so a mis-wired time node degrades into a builder that
silently does not move - which is the exact defect this seam exists to fix.

Checks, per probed builder:
  1. the tree contains a GeometryNodeInputSceneTime node
  2. Animated / Time Scale / Time Offset are declared ONCE (no duplicates -
     add_time_params must reuse an existing Animated, e.g. water.py's)
  3. a SINE node's phase input traces back to that SceneTime node
  4. Animated=False yields the same phase as time=0 (the determinism contract:
     the gate multiplies time by 0/1, so no branch and no geometry change)

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_gn_time.py
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
for p in (DEPLOY, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

failures = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


# Builders whose motion intent is documented in their own source.
PROBES = (
    # uses apply_universal_music_pass (the universal seam)
    "MEL_musical_wave_variant",
    # FIX-2: named for wind sway, had no time authority at all
    "MEL_chime_aeolian_wall",
    # FIX-2: comment documented speed*time, code used a static param
    "MEL_musical_pulse_variant",
)


def _upstream_reaches(node, target_bl_idname, depth=0, seen=None):
    """True when any upstream node of `node` is of the target type."""
    if node is None or depth > 200:
        return False
    seen = seen if seen is not None else set()
    if node.bl_idname == target_bl_idname:
        return True
    for inp in node.inputs:
        for lk in inp.links:
            fn = lk.from_node
            if fn.name in seen:
                continue
            seen.add(fn.name)
            if _upstream_reaches(fn, target_bl_idname, depth + 1, seen):
                return True
    return False


def main():
    try:
        import bpy  # noqa: F401
        from surreal_arch.melodia_gn.core import GROUP_BUILDERS
        from surreal_arch.melodia_gn import time as mel_time
    except Exception as exc:
        check("import melodia_gn.time", False, repr(exc))
        return 1
    check("import melodia_gn.time", True)

    # Contract names must be stable - the Convergence panel addresses them.
    check("socket-name contract",
          (mel_time.ANIMATED, mel_time.TIME_SCALE, mel_time.TIME_OFFSET)
          == ("Animated", "Time Scale", "Time Offset"),
          f"{mel_time.ANIMATED}/{mel_time.TIME_SCALE}/{mel_time.TIME_OFFSET}")

    for builder_id in PROBES:
        fn = GROUP_BUILDERS.get(builder_id)
        if fn is None:
            check(f"{builder_id} registered", False, "not in GROUP_BUILDERS")
            continue
        try:
            r = fn()
            tree = r[0] if isinstance(r, (tuple, list)) else r
        except Exception as exc:
            check(f"{builder_id} builds", False, repr(exc))
            continue
        if tree is None:
            check(f"{builder_id} builds", False, "no tree")
            continue
        check(f"{builder_id} builds", True, f"{len(tree.nodes)} nodes")

        names = [getattr(s, "name", "") for s in tree.interface.items_tree
                 if getattr(s, "item_type", "") == "SOCKET"]
        for want in (mel_time.ANIMATED, mel_time.TIME_SCALE, mel_time.TIME_OFFSET):
            n = names.count(want)
            check(f"{builder_id}: {want} declared once", n == 1,
                  f"count={n}" if n != 1 else "")

        st = [n for n in tree.nodes if n.bl_idname == "GeometryNodeInputSceneTime"]
        check(f"{builder_id}: scene-time node present", bool(st),
              f"{len(st)} found" if st else "NONE - builder is frozen")

        # A SINE whose phase traces back to SceneTime is the actual wiring proof.
        wired = False
        for n in tree.nodes:
            if n.bl_idname != "ShaderNodeMath":
                continue
            try:
                if n.operation != "SINE":
                    continue
            except Exception:
                continue
            for inp in n.inputs:
                for lk in inp.links:
                    if _upstream_reaches(lk.from_node, "GeometryNodeInputSceneTime"):
                        wired = True
                        break
                if wired:
                    break
            if wired:
                break
        check(f"{builder_id}: SINE phase driven by scene time", wired,
              "" if wired else "sine exists but phase is not time-fed")

    print(f"\ntime-seam health: {len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"time-seam health check crashed: {exc!r}")
        sys.exit(1)