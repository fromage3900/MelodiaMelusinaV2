"""Sir Melodious KineFX intake probe (headless, hython) — AnimationDoctor lane.

Purpose: prove what Houdini 22 actually receives from the Sir Melodious v5 ARP
exports before any doctor/constraint work is built on top of it:

  Stage A (mesh)  — import SKM FBX; inventory pieces, points/prims, groups,
                    shop_materialpath materials, capture→captureoverride→
                    bonedeform chain presence, joint objects, bbox.
  Stage B (clip)  — import one animation-only FBX; inventory which nodes carry
                    keyframes and whether world motion is real between frames
                    (joint-trail viability for clip health checks).

Evidence lands as `Saved/Audit/sirmelodious_kinefx_doctor/intake_probe.json`
(schema melodia.sir_kinefx_intake.v1). Read-only staging: no source blend/FBX is
touched, nothing is exported, nothing goes to UE.

  hython Tools/Houdini/sir_kinefx/sir_intake_probe.py
  hython Tools/Houdini/sir_kinefx/sir_intake_probe.py --stage mesh|clip|all

Findings banked from the 2026-10-07 development probes (intake_probe.json /
node_tree_probe.json): hipFile.importFBX has no `suppress_warnings` kwarg on
H22; scene import wraps everything in one subnet; skin arrives as
capture/captureoverride/bonedeform per piece; `material` attrib is absent but
`shop_materialpath` exists on prim level; H22 Matrix4 exposes
`extractTranslates` (NOT `extractTrans` — the dev probe's empty animation
sample was this API bug, not an unanimated clip).
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import hou

REPO = Path(__file__).resolve().parents[3]
ARP = REPO / "Saved/Audit/SirMelodious_FlightUnit_20261003/exports/ue_arp"
DEFAULT_MESH = ARP / "SKM_SirMelodious_ARP_CrestTie_v5.fbx"
DEFAULT_CLIP = ARP / "A_Sir_Fly_Loop_v5_ARP.fbx"
OUT_DIR = REPO / "Saved/Audit/sirmelodious_kinefx_doctor"
SCHEMA = "melodia.sir_kinefx_intake.v1"


def walk(root: hou.Node, visitor, depth: int = 0) -> None:
    for child in root.children():
        visitor(child, depth)
        walk(child, visitor, depth + 1)


def collect(root: hou.Node, types: set[str]) -> list[hou.Node]:
    found: list[hou.Node] = []

    def v(n: hou.Node, _d: int) -> None:
        if n.type().name() in types:
            found.append(n)

    walk(root, v)
    return found


def stage_mesh(path: Path) -> dict:
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hipFile.importFBX(str(path))
    obj = hou.node("/obj")
    pieces: dict[str, dict] = {}
    geos = collect(obj, {"geo"})
    skin_chain: dict[str, list[str]] = {}

    def chain_v(n: hou.Node, _d: int) -> None:
        tn = n.type().name()
        if tn in ("capture", "captureoverride", "bonedeform"):
            parent = n.parent().name()
            skin_chain.setdefault(parent, []).append(f"{n.name()}={tn}")

    walk(obj, chain_v)
    for g in geos:
        disp = g.displayNode()
        if disp is None:
            pieces[g.name()] = {"error": "no display node"}
            continue
        geo = disp.geometry()
        if geo is None:
            pieces[g.name()] = {"error": "no geometry"}
            continue
        mats: dict[str, int] = {}
        mattr = geo.findPrimAttrib("shop_materialpath")
        if mattr is not None:
            for p in geo.prims():
                key = str(p.attribValue(mattr)) or "<empty>"
                mats[key] = mats.get(key, 0) + 1
        bbox = geo.boundingBox()
        pieces[g.name()] = {
            "points": len(geo.points()),
            "prims": len(geo.prims()),
            "prim_groups": [gr.name() for gr in geo.primGroups()],
            "point_groups": [gr.name() for gr in geo.pointGroups()],
            "point_attrs": [a.name() for a in geo.pointAttribs()],
            "prim_attrs": [a.name() for a in geo.primAttribs()],
            "materials": dict(sorted(mats.items(), key=lambda kv: -kv[1])),
            "skin_chain": skin_chain.get(g.name(), []),
            "bbox_min": [round(v, 3) for v in bbox.minvec()],
            "bbox_max": [round(v, 3) for v in bbox.maxvec()],
        }
    joints = sorted({n.name() for n in collect(obj, {"null", "bone"})})
    feather = [j for j in joints if "feather" in j and not j.endswith("_bone")]
    return {
        "fbx": str(path.relative_to(REPO)),
        "pieces": pieces,
        "joint_objects": len(joints),
        "joints": joints,
        "feather_joints": feather,
        "crest_joints": sorted(j for j in joints if j.startswith("cc_crest")),
        "tie_joints": sorted(j for j in joints if j.startswith("cc_tie")),
        "subnet": [c.name() for c in obj.children() if c.type().name() == "subnet"],
    }


def world_pos(node: hou.Node) -> list[float]:
    """World translation of a node on H22 (use extractTranslates, not extractTrans)."""
    return list(node.worldTransform().extractTranslates())


def stage_clip(path: Path, sample_frames: tuple[int, int] = (1, 10)) -> dict:
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hipFile.importFBX(str(path))
    obj = hou.node("/obj")
    keyed: dict[str, int] = {}
    chopnets: dict[str, int] = {}

    def key_v(n: hou.Node, _d: int) -> None:
        try:
            cnt = sum(len(p.keyframes()) for p in n.parms())
        except Exception:  # noqa: BLE001
            cnt = -1
        if cnt > 0:
            keyed[f"{n.path()}"] = cnt
        if n.type().name() == "chopnet":
            chopnets[n.path()] = len(list(n.children()))

    walk(obj, key_v)

    f0, f1 = sample_frames
    motion: dict[str, dict] = {}
    nodes = collect(obj, {"null", "bone"})
    hou.setFrame(f0)
    first = {n.name(): world_pos(n) for n in nodes}
    hou.setFrame(f1)
    for n in nodes:
        p0 = first.get(n.name())
        if p0 is None:
            continue
        p1 = world_pos(n)
        d = sum(abs(a - b) for a, b in zip(p0, p1))
        if d > 1e-4 and len(motion) < 40:
            motion[n.name()] = {
                "f{0}".format(f0): [round(v, 3) for v in p0],
                "f{0}".format(f1): [round(v, 3) for v in p1],
                "delta_l1": round(d, 3),
            }
    hou.setFrame(1)
    return {
        "fbx": str(path.relative_to(REPO)),
        "animated_nodes_scene": keyed,
        "animated_node_count": len(keyed),
        "chopnets": chopnets,
        "sample_frames": list(sample_frames),
        "world_motion_sample": motion,
        "motion_nodes_sampled": len(motion),
        "verdict": (
            "scene_keyframes" if keyed and motion
            else "chops_only" if chopnets and not motion
            else "no_animation_located"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Sir Melodious KineFX intake probe")
    ap.add_argument("--stage", choices=("mesh", "clip", "all"), default="all")
    ap.add_argument("--mesh", default=str(DEFAULT_MESH))
    ap.add_argument("--clip", default=str(DEFAULT_CLIP))
    ap.add_argument("--out", default=str(OUT_DIR / "intake_probe.json"))
    args = ap.parse_args()

    rep: dict = {
        "schema": SCHEMA,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "houdini": hou.applicationVersionString(),
        "stages_run": [],
    }
    try:
        if args.stage in ("mesh", "all"):
            rep["mesh"] = stage_mesh(Path(args.mesh))
            rep["stages_run"].append("mesh")
        if args.stage in ("clip", "all"):
            rep["clip"] = stage_clip(Path(args.clip))
            rep["stages_run"].append("clip")
        rep["status"] = "PASS"
    except Exception:  # noqa: BLE001
        rep["status"] = "EXCEPTION"
        rep["trace"] = traceback.format_exc()[-3000:]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1), encoding="utf-8")

    brief = {
        "status": rep.get("status"),
        "stages": rep.get("stages_run"),
        "out": str(out),
    }
    if "mesh" in rep:
        m = rep["mesh"]
        brief["pieces"] = {k: v.get("points") for k, v in m["pieces"].items()}
        brief["joints"] = m["joint_objects"]
        brief["feathers"] = len(m["feather_joints"])
        brief["crest"] = m["crest_joints"]
        brief["tie"] = m["tie_joints"]
        brief["materials"] = sorted({
            mat for p in m["pieces"].values() for mat in p.get("materials", {})
        })
    if "clip" in rep:
        brief["clip_verdict"] = rep["clip"]["verdict"]
        brief["clip_keyed_nodes"] = rep["clip"]["animated_node_count"]
        brief["clip_motion_sampled"] = rep["clip"]["motion_nodes_sampled"]
    print(json.dumps(brief, indent=1))
    return 0 if rep.get("status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
