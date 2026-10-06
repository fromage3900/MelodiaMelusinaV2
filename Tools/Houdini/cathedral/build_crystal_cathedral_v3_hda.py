"""build_crystal_cathedral_v3_hda.py — converged builder for CrystalCathedralV3 (hython).

v3 converges the v2 attempt (cathedral + corridor in one geo network) with the
2026-10-06 probe findings and the hda_verify lane contract. Convergence is done
by IMPORTING the proven builders, not by copying them:

  * the entire cathedral side is v2.build_cathedral(), which is call-for-call
    identical to build_crystal_cathedral_hda.py (V1, Gate 2 verified at
    9278/8641 / 1032/288 / 1682/1608 — verify() asserts exactly those);
  * cathedral controls come from v1.CONTROLS_PARMS via v1._build_controls(),
    which includes wall_thickness — v2's table omitted it although both stages
    read chs("../controls/wall_thickness"), so v2 cooked a broken dist channel;
  * corridor VEX and the corridor parameter table come verbatim from
    build_crystal_cathedral_v2_hda.py (authored content, provenance kept).

What this file authors itself — the corridor STAGE — fixes, each verified
against the live Houdini 22.0.368 install:

  * polyreduce percentage is a 0-100 KEEP scale (default 100). v2 chained tiers
    at 0.25-0.1*i, i.e. "keep 0.25% of the PREVIOUS tier", which compunds to an
    empty mesh. v3 builds SIBLINGS off the beveled mesh (the authored comment
    already said "simplified mesh copies") keeping 25/15/5 percent; the fog
    rasters the lowest tier. verify() asserts the tiers strictly reduce.
  * volume.type is the voxel DATA type (Float/Integer) — v2's "1 = fog" comment
    was wrong; density fog needs Float, so type keeps its default. The node is a
    Houdini Volume, not a VDB (vdbfromgeometry does not exist in this build),
    hence the honest corridor_fog_* names.
  * the corridor chain creates no primitive groups, so v2's group pattern "poly*"
    matched nothing and thicken/bevel were silent no-ops; empty group = all
    primitives.
  * OUT_Corridor never set outputidx (v2), colliding with OUT_Cathedral at
    index 0; it is now output index 3 of 4.
  * all corridor parm sets go through v1._set() (warn, never crash) — the v2
    build died on a direct .parm(...).set() on a missing parm.
  * chain_type and lod_count stay on the inner controls null as BUILD-time
    config (the builder bakes the tier count from lod_count). They are NOT
    promoted: a dialog knob that does nothing at cook is the defect this lane
    exists to catch. The 18 live controls are promoted via
    Tools/Houdini/hda_promote_controls.py — stage1 before createDigitalAsset
    (instance content locks afterwards), stage2 moves the spares onto the
    definition so every fresh instance and UE's panel exposes them.
  * the .hda is written to Saved/HDA_build/ and copied to hda/, so rebuilds
    never drop network-bearing copies into hda/backup/ (a Gate 0 contract zone
    that must only hold empty stubs).

outputs: OUT_Cathedral (0) | OUT_Rose (1) | OUT_Collision (2) | OUT_Corridor (3)

Known content note (not fixed here): the corridor VEX runs its bays along +Z
from the origin, which in this network is the cathedral's up axis, so the chain
interpenetrates the nave. Geometry placement is an art pass, not builder work —
registry counts pin current behavior.

Run:
    hython Tools/Houdini/cathedral/build_crystal_cathedral_v3_hda.py
    hython Tools/Houdini/cathedral/build_crystal_cathedral_v3_hda.py --verify
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import hou  # noqa: F401  (hython-only file, like its v2 predecessor)

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "CrystalCathedralV3.hda"
BUILD_TMP_DIR = PROJECT_ROOT / "Saved" / "HDA_build"

# v1 = the Gate 2 verified cathedral builder; v2 = the authored v2 attempt.
# Both live in this directory. Promotion helper lives one level up.
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
import hda_promote_controls as promote
import build_crystal_cathedral_hda as v1
import build_crystal_cathedral_v2_hda as v2

NODE_TYPE = "CrystalCathedralV3"

# chain_type / lod_count are read ONCE by this builder, never at cook time.
BUILD_TIME_PARMS = ("chain_type", "lod_count")
CATHEDRAL_PARMS = [c[0] for c in v1.CONTROLS_PARMS]                     # 14, all live
CORRIDOR_LIVE_PARMS = [c[0] for c in v2.CORRIDOR_CONTROLS_PARMS
                       if c[0] not in BUILD_TIME_PARMS]                 # 4
LIVE_PARMS = CATHEDRAL_PARMS + CORRIDOR_LIVE_PARMS                      # 18, promoted


def _build_controls(template):
    """controls null = V1's 14 cathedral parms + the 6 corridor parms."""
    controls = v1._build_controls(hou, template)
    group = controls.parmTemplateGroup()
    for name, label, ncomp, default, lo, hi in v2.CORRIDOR_CONTROLS_PARMS:
        if isinstance(default[0], float):
            group.append(hou.FloatParmTemplate(name, label, ncomp,
                                               default_value=default, min=lo, max=hi))
        else:
            group.append(hou.IntParmTemplate(name, label, ncomp,
                                             default_value=default, min=lo, max=hi))
    controls.setParmTemplateGroup(group)
    return controls


def build_corridor(template, controls):
    """Box-chain -> weld -> thicken/bevel -> sibling LOD tiers -> fog volume.

    The authored chain from build_crystal_cathedral_v2_hda.py, with the stage
    fixes listed in the module docstring. Node names are corridor_-prefixed so
    they cannot collide with the cathedral's wall_thicken/edge_bevel.
    """
    seed = v1._seed_point(hou, template, "corridor_seed")

    build = template.createNode("attribwrangle", "corridor_build")
    build.parm("class").set(0)
    build.parm("snippet").set(v2.CORRIDOR_VEX)
    build.setInput(0, seed)
    build.setNextInput(controls)

    weld = template.createNode("fuse", "weld_corridor_seams")
    v1._set(weld, "tol3d", 0.0001)
    weld.setInput(0, build)
    weld.setNextInput(controls)

    # No primitive groups exist in the corridor chain, so v2's "poly*" pattern
    # matched nothing; an empty group selects every primitive.
    thicken = template.createNode("polyextrude", "corridor_wall_thicken")
    v1._set(thicken, "group", "")
    v1._set(thicken, "dist", None, 'chs("../controls/wall_thickness")')
    v1._set(thicken, "outputfront", 1)
    v1._set(thicken, "outputback", 1)
    v1._set(thicken, "outputside", 1)
    v1._set(thicken, "splittype", 1)
    thicken.setInput(0, weld)
    thicken.setNextInput(controls)

    bevel = template.createNode("polybevel::2.0", "corridor_edge_bevel")
    v1._set(bevel, "group", "")
    v1._set(bevel, "offset", None, 'chs("../controls/bevel_width")')
    v1._set(bevel, "offsetmode", 1)
    v1._set(bevel, "divisions", None, 'chs("../controls/bevel_segments")')
    v1._set(bevel, "commonlimit", 1)
    v1._set(bevel, "groupflatangle", 30.0)
    bevel.setInput(0, thicken)
    bevel.setNextInput(controls)

    # LOD tiers as SIBLINGS off the beveled mesh. Chained percentages compound
    # (each tier keeps 25/15/5% of the PREVIOUS tier) and collapse to nothing.
    # percentage is a 0-100 keep scale. The corridor mesh is small (each bay
    # cooks as its own closed shell: 36-72 prims at the default 6 bays), so a
    # 5% bottom tier rounds to ZERO prims and the fog would raster an empty
    # mesh — measured 2026-10-06: 25/15/5 -> [8, 5, 0], 40/25/15 -> [14, 8, 5].
    lod_count = int(controls.parm("lod_count").eval())
    lowest = bevel
    for i in range(lod_count):
        lr = template.createNode("polyreduce", "lod_remove_%d" % i)
        lr.setInput(0, bevel)                  # sibling, not chained
        v1._set(lr, "decimationcontrol", 1)    # FolderSet: use the custom controls
        v1._set(lr, "percentage", max(15.0, 40.0 - 15.0 * i))
        v1._set(lr, "boundaryweight", 1.0)
        lowest = lr                            # fog rasters the lowest tier

    # Houdini Volume SOP, not VDB (vdbfromgeometry does not exist here).
    # volume.type = voxel DATA type (Float/Integer); density fog = Float default.
    fog = template.createNode("volume", "corridor_fog_volume")
    fog.setInput(0, lowest)
    v1._set(fog, "samplediv", 20)

    lit = template.createNode("volumevop", "corridor_fog_light")
    lit.setInput(0, fog)

    out = template.createNode("output", "OUT_Corridor")
    out.setInput(0, lit)
    out.parm("outputidx").set(3)


def build_hda(out: Path):
    obj = hou.node("/obj")
    template = obj.createNode("geo", "CH_CrystalCathedralV3_Template")
    for child in template.children():
        try:
            child.destroy()
        except Exception:
            pass

    controls = _build_controls(template)

    # stage1 MUST run before createDigitalAsset: instance content locks and the
    # inner expressions can no longer be added (hda_promote_controls.py).
    pairs = promote.stage1_promote(controls, template, LIVE_PARMS)
    promote.stage1_wire(controls, pairs)

    v2.build_cathedral(template, controls)     # V1-faithful cathedral side
    build_corridor(template, controls)
    template.layoutChildren()

    # Write the .hda into Saved/HDA_build/ and copy the bytes to the final path.
    # Writing directly to hda/ on a REBUILD makes Houdini drop network-bearing
    # copies into hda/backup/, which fails Gate 0's empty-stub contract.
    BUILD_TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BUILD_TMP_DIR / out.name
    if tmp.exists():
        tmp.unlink()

    asset = template.createDigitalAsset(
        name=NODE_TYPE,
        hda_file_name=str(tmp),
        description="Melodia Crystal Cathedral V3: vault + rose + collision + corridor LOD fog",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    # stage2: move the promoted spares from the instance onto the definition, so
    # every fresh instance (and UE's parameter panel) exposes them.
    promote.stage2_promote_definition(asset, pairs, tmp)

    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tmp, out)
    print(f"[v3] wrote {out} ({out.stat().st_size} bytes, tmp={tmp})")
    return asset


def _instance(out_path: Path):
    """Create an instance of the built type, installing from disk if needed."""
    obj = hou.node("/obj")
    try:
        return obj.createNode(NODE_TYPE, "verify_v3")
    except hou.Error:
        hou.hda.installFile(str(out_path))
        return obj.createNode(NODE_TYPE, "verify_v3")


def verify(out_path: Path) -> int:
    """Assert promotion, V1's golden counts, LOD reduction, and clean cooks."""
    fails = []

    inst = _instance(out_path)

    # 1) every live control must exist on the HDA type (promotion contract)
    unpromoted = [n for n in LIVE_PARMS
                  if inst.parm(n) is None and inst.parm(n + "_ctrl") is None]
    if unpromoted:
        fails.append("unpromoted parameter(s): " + ", ".join(unpromoted))
    else:
        print(f"PASS promoted: {len(LIVE_PARMS)} control(s) on the {NODE_TYPE} type")

    # 2) cathedral outputs must equal V1's golden pins — this side is imported
    #    from v2.build_cathedral (V1-identical), so any drift is a real bug.
    golden = {
        "OUT_Cathedral": (9278, 8641),
        "OUT_Rose": (1032, 288),
        "OUT_Collision": (1682, 1608),
    }
    measured = {}
    for child in inst.allSubChildren():
        if child.type().name() != "output":
            continue
        geo = child.geometry()
        pts, prims = len(geo.points()), len(geo.prims())
        measured[child.name()] = (pts, prims)
        want = golden.get(child.name())
        if want is None:
            # OUT_Corridor: first-run measurement, no golden to hold it to
            status = "FAIL" if (pts == 0 or prims == 0) else "INFO"
            if status == "FAIL":
                fails.append(f"{child.name()} is empty")
            print(f"{status} {child.name()}: {pts}/{prims}")
        elif (pts, prims) != want:
            fails.append(f"{child.name()} = {pts}/{prims}, "
                         f"expected {want[0]}/{want[1]} (V1 golden)")
            print(f"FAIL {child.name()}: {pts}/{prims} expected {want[0]}/{want[1]}")
        else:
            print(f"PASS {child.name()}: {pts}/{prims} (V1 golden)")

    expected_outputs = set(golden) | {"OUT_Corridor"}
    missing = expected_outputs - set(measured)
    if missing:
        fails.append("missing output(s): " + ", ".join(sorted(missing)))

    # 3) LOD tiers must actually reduce (percentage-unit regression guard)
    tiers = sorted((c for c in inst.allSubChildren()
                    if c.name().startswith("lod_remove_")),
                   key=lambda c: c.name())
    counts = [len(tier.geometry().prims()) for tier in tiers]
    if counts:
        if counts != sorted(set(counts), reverse=True) or counts[-1] == 0:
            fails.append(f"LOD tiers are not strictly reducing or the lowest "
                         f"tier (fog source) is empty: {counts}")
        else:
            print(f"PASS LOD tiers reduce (lowest tier non-empty): {counts}")

    # 4) no node inside the instance may report an error
    errors = []
    for child in inst.allSubChildren():
        try:
            errs = child.errors()
        except Exception:
            errs = ()
        errors += [f"{child.name()}: {str(e).strip().splitlines()[0]}"
                   for e in errs]
    if errors:
        fails.append("node error(s): " + "; ".join(errors[:5]))
    else:
        print("PASS node errors: none")

    inst.destroy()
    if fails:
        for f in fails:
            print(f"FAIL {f}")
        return 1
    print(f"VERIFY {NODE_TYPE}: PASS ({out_path})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="build CrystalCathedralV3 (hython)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="where the final .hda is copied")
    parser.add_argument("--verify", action="store_true",
                        help="verify an existing .hda instead of building")
    args = parser.parse_args()

    out = args.out.resolve()
    if not args.verify:
        build_hda(out)
    return verify(out)


if __name__ == "__main__":
    sys.exit(main())
