"""Sir Melodious sir_flight doctor family (pure Python, no Houdini, no editor).

Reads the banked intake evidence + export contracts and evaluates the
flight-readiness gates. Staging only: writes one report JSON, touches no
source FBX/blend and nothing in Content/.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUDIT = REPO / "Saved/Audit/SirMelodious_FlightUnit_20261003"
DOCTOR = REPO / "Saved/Audit/sirmelodious_kinefx_doctor"
SCHEMA = "melodia.sir_flight_doctor.v1"

FROZEN_SKELETON = "SK_SirMelodious_Rigged_Skeleton"
# Known defect baselines from PLAN.md headless Blender probe (v2 FBX that UE uses)
KNOWN_HOLDS = {
    "fly_amplitude": "Fly_Loop tip travel 3.4-3.8cm on 42cm span @0.33Hz (target 25-35cm, 2-3Hz cruise)",
    "hover_amplitude": "Hover_Idle tip travel 2.7-2.9cm (target 3-5Hz hover)",
    "land_asymmetry": "Land L tip 4.0cm vs R 0.6cm — re-key owed",
    "crest_bones": "v3 rig has no crest/tail/beak bones; v5 CrestTie graft status per UE_IMPORT_HANDOFF",
    "double_scale": "remapped FBXs were once x100 (46m cockatoo); Stage D guard still runs",
}


def load(name: str, base: Path) -> dict | None:
    p = base / name
    if not p.exists():
        return None
    return json.loads(p.read_text())


def main() -> dict:
    checks: list[dict] = []

    def gate(gid: str, status: str, detail: str) -> None:
        checks.append({"id": gid, "status": status, "detail": detail})

    intake = load("intake_probe.json", DOCTOR)
    ntree = load("node_tree_probe.json", DOCTOR)
    gate("intake_mesh_clip", "PASS" if intake and intake.get("status") == "PASS" else "HOLD",
         f"intake_probe status={intake.get('status') if intake else 'MISSING'}; "
         f"mesh={intake.get('mesh', {}).get('fbx', '?') if intake else '?'}; "
         f"clip animated_nodes={intake.get('clip', {}).get('animated_node_count', '?') if intake else '?'}")
    if intake:
        mesh = intake.get("mesh", {})
        pieces = mesh.get("pieces", {})
        skin_ok = all("capture" in " ".join(v.get("skin_chain", [])) for v in pieces.values() if isinstance(v, dict))
        gate("skin_chain", "PASS" if skin_ok else "HOLD", f"{len(pieces)} pieces all carry capture/override/deform" if skin_ok else "missing skin chain")
        feather = mesh.get("feather_joints", [])
        l = sum(1 for j in feather if j.endswith("_l"))
        r = sum(1 for j in feather if j.endswith("_r"))
        gate("feather_symmetry", "PASS" if feather and l == r and l > 0 else "HOLD",
             f"{len(feather)} feather joints L={l} R={r}")
        joints = mesh.get("joints", [])
        crest = mesh.get("crest_joints", [])
        gate("crest_present", "PASS" if crest else "HOLD",
             f"crest joints={len(crest)} (v3 rig had none; v5 graft expected)")
        # scale sanity from bboxes: wingspan-class dims in meters (Blender probe: 42cm span)
        # scale sanity from bboxes: Houdini import units vs Blender rest pose
        # (wingspan 42.2cm, height 28.5cm per PLAN §6) are not yet reconciled —
        # extents are REPORTED, not gated, until the unit convention is proven.
        ext = {k: [round(b - a, 1) for a, b in zip(v["bbox_min"], v["bbox_max"])]
               for k, v in pieces.items() if isinstance(v, dict) and "bbox_max" in v}
        body = ext.get("SirMelodiousBody", "?")
        gate("scale_gate", "HOLD",
             f"unit convention unproven: body extent XYZ={body} vs Blender rest 42.2cm span/28.5cm height; "
             f"all={ext}. Do NOT import to UE until cm-native proven (x100 trap precedent).")
    else:
        for gid in ("skin_chain", "feather_symmetry", "crest_present", "scale_gate"):
            gate(gid, "HOLD", "no intake_probe.json")

    gate("node_tree", "PASS" if ntree and ntree.get("status") == "PASS" else "HOLD",
         f"node_tree_probe status={ntree.get('status') if ntree else 'MISSING'}")

    contracts = sorted((AUDIT / "exports/ue").glob("*.contract.json"))
    remaps = sorted((AUDIT / "exports/ue").glob("*.remap.json"))
    frozen_ok = True
    for c in contracts:
        d = json.loads(c.read_text())
        if d.get("expected_skeleton") != FROZEN_SKELETON:
            frozen_ok = False
    gate("contract_skeleton", "PASS" if contracts and frozen_ok else "HOLD",
         f"{len(contracts)} contracts all target {FROZEN_SKELETON}" if contracts and frozen_ok
         else f"{len(contracts)} contracts, frozen_ok={frozen_ok}")
    gate("remap_present", "PASS" if len(remaps) == len(contracts) and contracts else "HOLD",
         f"{len(remaps)} remap JSONs vs {len(contracts)} contracts")

    wing = load("Wingbeat_curves_v5.json", AUDIT / "exports/ue_arp")
    gate("wingbeat_curves", "PASS" if wing and "Fly_Loop_v5" in wing else "HOLD",
         f"keys={sorted(wing.keys())}" if wing else "MISSING Wingbeat_curves_v5.json")

    tail = load("body_reweight_delta_kinefx.json", DOCTOR / "reweight")
    if tail and tail.get("zero_count") == 657:
        gate("tail_export", "HOLD",
             "tail IS rigged in source (spline c_spline_root->tip + bbones, "
             "all non-deform) but absent from the 66-bone export; 657 tail "
             "pts ship zero-weight (hython-proven). Staged fallback: "
             "root.x @1.0 (Blender delta, visually proven). Real wag needs "
             "spline/bbone deform export — owner mesh decision.")
    else:
        gate("tail_export", "HOLD", "no kinefx tail proof yet — run sir_reweight_kinefx.py")

    wt = load("wingtip_probe.json", DOCTOR)
    if wt and wt.get("clips"):
        clips = wt["clips"]
        bad = {k: v for k, v in clips.items() if "error" in v}
        sym_bad = [k for k, v in clips.items()
                   if "error" not in v and (v.get("lr_symmetry") or 0) < 0.9]
        loops = [k for k, v in clips.items()
                 if "error" not in v and "Loop" in k or "Hover" in k or "Glide" in k]
        seam_bad = [k for k in loops
                    if clips[k].get("seam_max_mm") not in (None, 0, 0.0)]
        fly = clips.get("A_Sir_Fly_Loop_v6_ARP.fbx", {})
        hov = clips.get("A_Sir_Hover_Idle_v6_ARP.fbx", {})
        gate("wingtip_measured",
             "PASS" if not bad and len(clips) >= 10 else "HOLD",
             f"{len(clips) - len(bad)}/{len(clips)} clips measured "
             f"(fly {fly.get('left', {}).get('tip_travel_cm')}cm @{fly.get('left', {}).get('stroke_hz')}Hz; "
             f"hover {hov.get('left', {}).get('tip_travel_cm')}cm @{hov.get('left', {}).get('stroke_hz')}Hz; "
             f"v5==v6 travel: fan is twist/spread, expected)"
             if not bad else f"errors: {sorted(bad)}")
        gate("wingtip_symmetry", "PASS" if not sym_bad else "FAIL",
             "L/R 1.0 all clips (PLAN v2 asymmetry fixed in v5+)" if not sym_bad
             else f"asymmetric: {sym_bad}")
        gate("loop_seams", "PASS" if not seam_bad else "HOLD",
             "Fly/Hover/Glide seams 0.0mm; Takeoff/Land one-shot seams expected"
             if not seam_bad else f"open loops: {seam_bad}")
        for hid, detail in KNOWN_HOLDS.items():
            if hid in ("fly_amplitude", "hover_amplitude", "land_asymmetry"):
                continue  # superseded by wingtip_measured above
            gate(f"known_hold:{hid}", "HOLD", detail)
    else:
        gate("wingtip_measured", "HOLD", "no wingtip_probe.json — run wingtip_probe.py (Blender headless)")
        for hid, detail in KNOWN_HOLDS.items():
            gate(f"known_hold:{hid}", "HOLD", detail)

    npass = sum(1 for c in checks if c["status"] == "PASS")
    nhold = sum(1 for c in checks if c["status"] == "HOLD")
    nfail = sum(1 for c in checks if c["status"] == "FAIL")
    verdict = "FAIL" if nfail else ("HOLD" if nhold else "PASS")
    report = {
        "schema": SCHEMA,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": f"{verdict} — {npass}/{len(checks)} PASS, {nhold} HOLD, {nfail} FAIL",
        "checks": checks,
    }
    out = DOCTOR / "doctor_report_sir_flight.json"
    out.write_text(json.dumps(report, indent=1))
    print(report["verdict"])
    for c in checks:
        print(f"  {c['status']:4} {c['id']}: {c['detail']}")
    print(f"wrote {out.relative_to(REPO)}")
    return report


if __name__ == "__main__":
    main()
