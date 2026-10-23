"""Native acceptance for the rounded-plan salon shell HDA.

Proves the packaged HDA (not just the standalone module) cooks through Houdini's
HDA path, that its gate passes for every plan shape, that geometry is
deterministic, that plan shape/tessellation actually change the mesh, and that
invalid portals are rejected. Native geometry only: no UE capsule, actor,
lighting or packaged claim.
"""
import argparse
import hashlib
import json
from pathlib import Path

import hou

TYPE = "melodia::room_shell_rounded::1.0"
SALON = dict(room_w=15.84, room_d=12.06, room_h=7.6, wall_t=0.24, engine_y_up=0, engine_flip=0)
PORTALS = [dict(id="salon_entry", theta=0.25, width=1.8, height=3.2),
           dict(id="salon_front", theta=0.75, width=2.4, height=3.2)]


def snapshot(node):
    node.cook(force=True)
    if node.errors():
        raise RuntimeError(str(node.errors()))
    geo = node.geometry()
    digest = hashlib.sha256()
    digest.update(repr(geo.pointFloatAttribValues("P")).encode())
    digest.update(repr(geo.vertexFloatAttribValues("uv")).encode())
    digest.update(repr([[v.point().number() for v in p.vertices()] for p in geo.prims()]).encode())
    payload = json.loads(geo.attribValue("sockets_json"))
    return dict(
        points=len(geo.points()),
        prims=len(geo.prims()),
        bbox=[list(geo.boundingBox().minvec()), list(geo.boundingBox().maxvec())],
        vertex_attributes=[a.name() for a in geo.vertexAttribs()],
        prim_attributes=[a.name() for a in geo.primAttribs()],
        geometry_sha256=digest.hexdigest(),
        gate=json.loads(geo.attribValue("gate_json")),
        sockets=payload,
        errors=list(node.errors()),
        warnings=list(node.warnings()),
    )


def main(source, candidate, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    canonical_sha = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    for path in (source, candidate):
        hou.hda.installFile(path)

    parent = hou.node("/obj").createNode("geo", "rounded_shell_verification")
    parent.deleteItems(parent.children())
    node = parent.createNode(TYPE, "rounded")

    report = dict(
        version=hou.applicationVersionString(),
        license=str(hou.licenseCategory()),
        source_hda=source,
        source_sha256=canonical_sha,
        candidate_hda=candidate,
        candidate_sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
        candidate_type=TYPE,
        checks={},
        variants={},
    )

    def configure(shape_idx, sides, expo, segs, portals=None):
        node.parm("plan_shape").set(shape_idx)
        node.parm("plan_sides").set(sides)
        node.parm("plan_exponent").set(expo)
        node.parm("plan_segments").set(segs)
        node.parm("openings_json").set(json.dumps(PORTALS if portals is None else portals))
        for key, value in SALON.items():
            node.parm(key).set(value)

    for name, (idx, sides, expo) in (("ellipse", (0, 16, 2.6)), ("superellipse", (1, 16, 2.6)), ("polygon", (2, 16, 2.6))):
        configure(idx, sides, expo, 96)
        report["variants"][name] = snapshot(node)

    # determinism: identical parms must reproduce identical geometry
    configure(0, 16, 2.6, 96)
    repeat = snapshot(node)
    report["checks"]["deterministic_repeat"] = repeat["geometry_sha256"] == report["variants"]["ellipse"]["geometry_sha256"]

    # plan shape and tessellation must actually change the mesh
    report["checks"]["shape_changes_geometry"] = (
        report["variants"]["ellipse"]["geometry_sha256"] != report["variants"]["polygon"]["geometry_sha256"])
    configure(0, 16, 2.6, 48)
    coarse = snapshot(node)
    report["variants"]["ellipse_coarse"] = coarse
    report["checks"]["tessellation_changes_geometry"] = coarse["geometry_sha256"] != report["variants"]["ellipse"]["geometry_sha256"]
    report["checks"]["coarse_still_gates"] = coarse["gate"]["all_pass"]

    # every variant must pass its own gate
    report["checks"]["all_variants_gate_pass"] = all(v["gate"]["all_pass"] for v in report["variants"].values())

    # the salon footprint must match the artist's room (15.84 x 12.06 x 7.6 AABB incl. wall thickness)
    ell = report["variants"]["ellipse"]
    lo, hi = ell["bbox"]
    report["checks"]["salon_footprint_exact"] = (
        abs(lo[0] + 0.24) < 1e-3 and abs(hi[0] - (15.84 + 0.24)) < 1e-3
        and abs(lo[1] + 0.24) < 1e-3 and abs(hi[1] - (12.06 + 0.24)) < 1e-3
        and abs(hi[2] - 7.78) < 1e-3)

    # named portals survive into the HDA payload
    ids = [q["id"] for q in ell["sockets"]["opening_sockets"]]
    report["checks"]["two_named_portals"] = ids == ["salon_entry", "salon_front"]
    report["checks"]["portals_are_native_cuts"] = all(q["native_cut"] for q in ell["sockets"]["opening_sockets"])
    report["checks"]["portals_floor_level"] = all(q["floor_z_m"] == 0.0 for q in ell["sockets"]["opening_sockets"])

    # contract attributes the UE side reads
    report["checks"]["uv_attribute_present"] = "uv" in ell["vertex_attributes"]
    report["checks"]["material_role_present"] = "material_role" in ell["prim_attributes"]
    report["checks"]["material_path_present"] = "shop_materialpath" in ell["prim_attributes"]

    # invalid portals must fail the cook, not silently fall back
    bad = [
        [dict(id="oob", theta=1.9, width=1.8, height=3.2)],
        [dict(id="tall", theta=0.25, width=1.8, height=9.0)],
        [dict(id="zero", theta=0.25, width=0.0, height=3.2)],
        [dict(id="dup", theta=0.25, width=1.8, height=3.2), dict(id="dup", theta=0.5, width=1.8, height=3.2)],
        [dict(id="ove", theta=0.25, width=1.8, height=3.2), dict(id="ove2", theta=0.27, width=1.8, height=3.2)],
        [dict(id="", theta=0.25, width=1.8, height=3.2)],
    ]
    rejected = []
    for records in bad:
        configure(0, 16, 2.6, 96, records)
        try:
            node.cook(force=True)
        except hou.OperationFailed:
            pass
        if node.errors():
            rejected.append(records)
    report["invalid_cases"] = len(bad)
    report["checks"]["invalid_portals_rejected"] = len(rejected) == len(bad)

    report["checks"]["canonical_hda_unchanged"] = canonical_sha == hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["all_pass"] = all(report["checks"].values())
    report["limits"] = ("Native packaged-HDA geometry only. UE import, capsule traversal, lighting, "
                        "dressing placement and the packaged route remain pending.")
    path = out / "room_shell_rounded_verify.json"
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(checks=report["checks"], all_pass=report["all_pass"],
                          prims=ell["prims"], points=ell["points"], evidence=str(path)), indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-hda", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raise SystemExit(main(a.source_hda, a.candidate, a.out))
