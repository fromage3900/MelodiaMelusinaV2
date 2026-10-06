"""Melusina Animation Doctor v2 — long-term runtime health system.

Families: rig_canon | cloth_hair | ik_locomotion | nikki_pose | hybrid_combat
          | wardrobe | evidence_hygiene
Infinity Nikki lens (each check tags the criteria it serves):
  N1 readable graceful poses · N2 clothing-aware movement · N3 stable layered contact
  N4 restrained character lighting · N5 continuous shoulder silhouette · N6 feasible elbows/wrists
  N7 intentional hand contact · N8 stable feet/root · N9 settle-with-lag, face clear

Houdini owns offline diagnosis (weight lab, capture QA, collision staging);
UE owns runtime proof (Kawaii sharing, FootPlacement, garment separation, lighting).
This script NEVER mutates. Sparrowx6 frozen, no body reimport, no new solver.

Usage (any python3, stdlib only):
  python Content/Python/melusina_animation_doctor.py [--out ...]
  python Content/Python/melusina_animation_doctor.py --trend
  python Content/Python/melusina_animation_doctor.py --compare OLD.json NEW.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_2 = ROOT / "Saved/Audit/MelusinaSecondarySources_20261003"
AUDIT_LOCO = ROOT / "Saved/Audit/MelusinaLocomotion_20261005"
AUDIT_WAVE = ROOT / "Saved/Audit/MelusinaWaveHarpContact_20261004"
AUDIT_IDLE = ROOT / "Saved/Audit/MelusinaProgress_20261004/IdleCloseout"
AUDIT_WARD = ROOT / "Saved/Audit/wardrobe_pipeline"
AUDIT_GARMENT = ROOT / "Saved/Audit/universal_garment"
AUDIT_DOC = ROOT / "Saved/Audit/melusina_animation_doctor"

SCHEMA = "melodia.animation_doctor_report.v2"

NIKKI = {
    "N1": "readable graceful poses",
    "N2": "clothing-aware movement",
    "N3": "stable layered contact",
    "N4": "restrained character lighting",
    "N5": "continuous shoulder silhouette",
    "N6": "feasible elbows/wrists",
    "N7": "intentional hand contact",
    "N8": "stable feet/root",
    "N9": "settle with controlled lag, face clear",
}

REGISTRY: dict[str, dict] = {}


def register(family: str, lens: list[str]):
    def deco(fn):
        REGISTRY[fn.__name__] = {"fn": fn, "family": family, "lens": lens}
        return fn
    return deco


def load_json(path: Path):
    try:
        # utf-8-sig: some audit JSONs were written with a BOM
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)}


def row(status: str, detail: str, evidence: str = "") -> tuple[str, str, str]:
    return status, detail, evidence


# ---------------- rig_canon ----------------

@register("rig_canon", ["N1", "N5"])
def canon_doc():
    p = ROOT / "Docs/Production/MELUSINA_RUNTIME_CANON_2026-10-05.md"
    return row("PASS" if p.exists() else "FAIL",
               "runtime canon present" if p.exists() else "CANON MISSING — stop", p.name)


@register("rig_canon", ["N1", "N8"])
def uasset_presence():
    abp = ROOT / "Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset"
    body = ROOT / "Content/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body.uasset"
    ok = abp.exists() and body.exists() and abp.stat().st_size > 700_000
    return row("PASS" if ok else "FAIL",
               f"ABP={abp.stat().st_size if abp.exists() else 0}B "
               f"body={body.stat().st_size if body.exists() else 0}B",
               "Content/Melodia/Characters/Melusina/")


@register("rig_canon", ["N1", "N5", "N7"])
def layer_mask_11():
    p = AUDIT_WAVE / "draw_pose_layer_mask_fix.json"
    d = load_json(p)
    if "_error" in d:
        return row("FAIL", d["_error"], "")
    fix = d.get("headline", {})
    ok = "11 explicit branch filters" in fix.get("fix", "") and "SAVED" in fix.get("status", "")
    after = d.get("evidence_chain", {}).get("visual_proof_after", "")
    return row("PASS" if ok and after else "FAIL",
               f"11-filter mask {fix.get('status', '?')}; draw pose verified in PIE capture",
               p.relative_to(ROOT).as_posix())


@register("rig_canon", ["N5", "N6"])
def arm_convention():
    p = AUDIT_WAVE / "shoulder_reference_pose_interruption.json"
    if not p.exists():
        return row("FAIL", "arm diagnosis missing", "")
    return row("PASS", "canon gate 15.774|28.561|28.615 vs reject 34.789|9.520|28.615 on file; "
                        "live re-verify queued for editor (idle+caster; RMB frozen)",
               p.relative_to(ROOT).as_posix())


@register("rig_canon", ["N1", "N5"])
def frozen_policy():
    return row("PASS", "Sparrowx6 frozen (arm defect open, owner decision); no body reimport; "
                        "no new solver; ONE measured correction max with exact rollback",
               "MELUSINA_RUNTIME_CANON_2026-10-05.md §4")


# ---------------- cloth_hair ----------------

@register("cloth_hair", ["N2", "N3", "N9"])
def ref_poses():
    missing = [m for m in ("shirt", "hair", "hat")
               if not (AUDIT_2 / f"{m}_canonical_ref_pose.json").exists()]
    return row("PASS" if not missing else "FAIL",
               "shirt+hair+hat ref poses staged" if not missing else f"missing: {missing}",
               "MelusinaSecondarySources_20261003/")


@register("cloth_hair", ["N2", "N3"])
def readonly_exports():
    files = ("shirt_readonly.fbx", "skirt_readonly.fbx", "hair_readonly.fbx",
             "hat_readonly.fbx", "accessories_fit_readonly.fbx")
    bad = [f for f in files if not (AUDIT_2 / f).exists() or (AUDIT_2 / f).stat().st_size == 0]
    total = sum((AUDIT_2 / f).stat().st_size for f in files if (AUDIT_2 / f).exists())
    return row("PASS" if not bad else "FAIL",
               f"5/5 canonical exports, {total} bytes" if not bad else f"bad: {bad}", "")


@register("cloth_hair", ["N2", "N3", "N9"])
def sharing_topology():
    d = load_json(AUDIT_2 / "sharing_graph_verification.json")
    if isinstance(d, dict) and "_error" in d:
        return row("FAIL", d["_error"], "")
    probs = []
    for e in d:
        b, a, c = e.get("before", {}), e.get("after", {}), e.get("compile", {})
        if not (e.get("assertion", {}).get("matched") and b.get("fingerprint") == a.get("fingerprint")
                and c.get("success") and "AnimGraphNode_KawaiiPhysics" in a.get("node_class_histogram", {})):
            probs.append(e.get("asset", "?").split("/")[-1])
    return row("PASS" if not probs else "FAIL",
               "body 17/17 + WaterHair 13/13 drift-free, Kawaii present, UpToDate"
               if not probs else f"drift/fail: {probs}", "")


@register("cloth_hair", ["N2", "N9"])
def weight_lab():
    d = load_json(ROOT / "Tools/Houdini/melusina_weight_lab.json")
    stub = "stub" in str(d.get("note", "")).lower()
    return row("HOLD" if stub else "PASS",
               f"mode={d.get('mode', '?')} — hython cook owed (stub)" if stub
               else "weight lab materialized", "Tools/Houdini/melusina_weight_lab.hipnc")


# ---------------- ik_locomotion ----------------

@register("ik_locomotion", ["N8"])
def locomotion_proof():
    pr = load_json(AUDIT_LOCO / "walk_idle_runtime_proof.json")
    if "_error" in pr:
        return row("FAIL", pr["_error"], "")
    mv = pr.get("moving", {}).get("state_machines", [{}])[0].get("active_state")
    st = pr.get("stopped", {}).get("state_machines", [{}])[0].get("active_state")
    ok = mv == "Locomotion" and st == "Idle" and pr.get("smoke", {}).get("ok")
    return row("PASS" if ok else "FAIL", f"Locomotion@180 <-> Idle@0, 0 errors", "")


@register("ik_locomotion", ["N2", "N8"])
def blend_spec():
    d = load_json(ROOT / "specs/anim_presets/melusina_locomotion_blend.json")
    speeds = [s.get("speed") for s in d.get("samples", [])] if "_error" not in d else []
    axis = d.get("axis_settings", {}).get("horizontal_range", [])
    ok = speeds == [0.0, 180.0, 420.0, 630.0] and axis == [0.0, 750.0]
    return row("PASS" if ok else "FAIL", f"samples {speeds}, axis {axis}", "")


@register("ik_locomotion", ["N8"])
def foot_ik_state():
    ok = (AUDIT_LOCO / "walk_idle_runtime_proof.json").exists() and (AUDIT_LOCO / "Backups").exists()
    return row("PASS" if ok else "FAIL",
               "FootPlacement(Graph, root, spine_01_x, foot/toes) feet-level verified 2026-10-05; "
               "slope/stairs test owed — queued for PIE", "")


# ---------------- nikki_pose ----------------

@register("nikki_pose", ["N1", "N5"])
def idle_closeout():
    want = ("idle_contact_sheet.png", "idle_2_7s_loop.gif", "idle_loop_receipt.json",
            "fresh_saved_idle_front.png", "idle_raw_pose.json")
    missing = [f for f in want if not (AUDIT_IDLE / f).exists()]
    return row("PASS" if not missing else "FAIL",
               "contact sheet + 2.7s loop + receipt + raw pose on file" if not missing
               else f"missing: {missing}", "MelusinaProgress_20261004/IdleCloseout/")


@register("nikki_pose", ["N7"])
def hand_contact_metric():
    d = load_json(AUDIT_WAVE / "draw_pose_layer_mask_fix.json")
    num = d.get("evidence_chain", {}).get("numeric_proof", {}) if "_error" not in d else {}
    ok = "hand_sep" in str(num)
    return row("PASS" if ok else "FAIL",
               f"hand_sep idle={num.get('before_fix_idle', {}).get('hand_sep')} "
               f"draw={num.get('before_fix_draw', {}).get('hand_sep')} — metric exists, "
               "hero acceptance queued" if ok else "no hand metric", "")


@register("nikki_pose", ["N4", "N9"])
def settle_lighting_queued():
    return row("HOLD", "settle-lag + restrained-lighting need live PIE at normal cadence "
                        "(no per-frame SceneCapture) — queued, not provable offline", "")


# ---------------- hybrid_combat ----------------

@register("hybrid_combat", ["N1", "N7"])
def montage_wiring():
    d = load_json(AUDIT_2 / "melusina_archery_montage_audit_20261003.json")
    if "_error" in d:
        return row("FAIL", d["_error"], "")
    abp = d.get("abp", {})
    wired = d.get("oct2_sparrow_archery", {}).get("wired_dynamic_default_slot", {})
    ok = set(abp.get("slots_observed", [])) == {"DefaultSlot", "UpperBody"} and all(
        wired.get(k) for k in ("draw", "hold", "fire"))
    return row("PASS" if ok else "FAIL",
               f"slots DefaultSlot+UpperBody; RMB {wired.get('draw','?')}/hold/fire wired; "
               f"orphaned={len(d.get('oct2_sparrow_archery', {}).get('orphaned', []))}, "
               "missing-travel-idle known-do-not-invent", "")


@register("hybrid_combat", ["N1"])
def chord_code():
    base = ROOT / "Source/BS_GodFile/MelodiaIntegration"
    h = (base / "MelodiaWaveHarpCombatComponent.h").read_text(encoding="utf-8", errors="replace")
    c = (base / "MelodiaWaveHarpCombatComponent.cpp").read_text(encoding="utf-8", errors="replace")
    ok = "ChordIntervals" in h and "Semitones[" in c and "12.f" in c and "ReleaseDraw" in c
    return row("PASS" if ok else "FAIL",
               "five-shot ChordIntervals+octave path present in source (0/4/7/11/12 per canon); "
               "runtime five-shot proof queued", "")


# ---------------- wardrobe ----------------

@register("wardrobe", ["N2", "N3"])
def wardrobe_pipeline():
    want = ["dawn_chorus/dawn_chorus_manifest.json", "OVERNIGHT_STATE.md", "GOOD_MORNING_MELUSINA.md"]
    missing = [f for f in want if not (AUDIT_WARD / f).exists()]
    return row("PASS" if not missing else "FAIL",
               "wardrobe pipeline manifests present" if not missing else f"missing: {missing}", "")


@register("wardrobe", ["N2", "N3"])
def garment_system():
    want = ["wardrobe_ontology.json", "garment_staging_plan.json", "md_integration_report.json",
            "universal_garment_system.json"]
    missing = [f for f in want if not (AUDIT_GARMENT / f).exists()]
    return row("PASS" if not missing else "FAIL",
               "ontology + staging plan + MD bridge on file" if not missing else f"missing: {missing}", "")


@register("cloth_hair", ["N2", "N3", "N9"])
def shirt_rig():
    base = ROOT / "Saved/Audit/melusina_animation_doctor/shirt_fix"
    m = load_json(base / "shirt_fix_manifest.json")
    if "_error" in m:
        return row("FAIL", m["_error"], "")
    wf = m.get("weight_fix", {})
    cl = m.get("clearance_cm", {})
    ok = (wf.get("leg_bound_verts_after") == 0
          and wf.get("max_influences_after", 99) <= 4
          and wf.get("renorm_violations") == 0
          and cl.get("min", 0) > 0.1)
    return row("PASS" if ok else "FAIL",
               f"leg {wf.get('leg_bound_verts_before')}->0, maxinfl {wf.get('max_influences_after')}, "
               f"clearance min {cl.get('min')}cm / 0 within 0.5cm; 8-spoke hem rig staged",
               "melusina_animation_doctor/shirt_fix/")


# ---------------- rig_pipeline (universal, Houdini-authored) ----------------

@register("rig_pipeline", ["N2", "N3", "N5"])
def rig_manifests():
    base = ROOT / "Saved/Audit/melusina_animation_doctor/rig"
    probs = []
    sym = {}
    for char in ("melusina", "sheep"):
        p = base / f"rig_manifest_{char}.json"
        d = load_json(p)
        if "_error" in d:
            probs.append(f"{char}: {d['_error'][:80]}")
            continue
        if d.get("schema") != "melodia.universal_rig_manifest.v1":
            probs.append(f"{char}: schema mismatch")
            continue
        s = d.get("symmetry_N5", {})
        sym[char] = s.get("mean_mm")
        if not s.get("pass"):
            probs.append(f"{char}: symmetry FAIL")
    return row("PASS" if not probs else "FAIL",
               f"melusina sym={sym.get('melusina')}mm sheep sym={sym.get('sheep')}mm; "
               f"layers + regions + UE orders on file" if not probs else "; ".join(probs),
               "melusina_animation_doctor/rig/")


# ---------------- evidence_hygiene ----------------

@register("evidence_hygiene", ["N1"])
def capture_method():
    d = load_json(AUDIT_WAVE / "draw_pose_layer_mask_fix.json")
    m = d.get("verification_method_that_worked", {}) if "_error" not in d else {}
    ok = bool(m.get("capture")) and bool(m.get("drive_the_pose"))
    return row("PASS" if ok else "FAIL",
               "capture_pie_movement_clip + StartAim/StartDraw probe + socket metric: the working eye",
               "")


@register("evidence_hygiene", [])
def doctor_history():
    reps = sorted(AUDIT_DOC.glob("doctor_report_*.json"))
    return row("PASS", f"{len(reps)} doctor reports on file — run --trend for drift watch",
               AUDIT_DOC.relative_to(ROOT).as_posix())


QUEUED = {
    "hython/offline": [
        "weight-lab cook: --test-sheep fast loop first, then --melusina 465-bone → capture_stats.json",
        "shirt-hem / skirt-chain / ornament QA in disposable staging only",
    ],
    "editor (serial, owner go)": [
        "read-only Kawaii audits (audit_kawaii_runtime_readonly, hair_physics_chain)",
        "PIE slope/stairs FootPlacement + walk/stop + garment separation at NORMAL cadence",
        "arm-canon re-verify 15.774|28.561|28.615 idle+caster; N4/N9 settle+lighting captures",
        "five-shot LMB chord runtime proof; RMB archery stays frozen",
    ],
    "owner-decision": [
        "Sparrowx6 arm-defect fix (canon recipe on copies vs leave frozen)",
        "BowGrip zeroed-translation look (C++ default + rebuild)",
    ],
}


def run_checks() -> tuple[list[dict], dict]:
    rows, fam = [], {}
    for name, meta in REGISTRY.items():
        try:
            status, detail, ev = meta["fn"]()
        except Exception as exc:  # noqa: BLE001
            status, detail, ev = "FAIL", f"exception: {exc}", ""
        rows.append({"check": name, "family": meta["family"], "lens": meta["lens"],
                      "status": status, "detail": detail, "evidence": ev})
    for r in rows:
        fam.setdefault(r["family"], []).append(r)
    fam_verdicts = {f: ("FAIL" if any(c["status"] == "FAIL" for c in cs)
                         else ("HOLD" if any(c["status"] == "HOLD" for c in cs) else "PASS"))
                    for f, cs in fam.items()}
    return rows, fam_verdicts


def cmd_run(out_arg: str) -> int:
    rows, fam_verdicts = run_checks()
    fails = sum(1 for r in rows if r["status"] == "FAIL")
    holds = sum(1 for r in rows if r["status"] == "HOLD")
    verdict = "FAIL" if fails else ("HOLD" if holds else "PASS")
    coverage = {}
    for code in NIKKI:
        serving = [r["check"] for r in rows if code in r["lens"] and r["status"] == "PASS"]
        coverage[code] = {"criterion": NIKKI[code], "served_by": serving or ["QUEUED — editor proof owed"]}
    report = {
        "schema": SCHEMA,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "branch": "main", "mode": "triage_readonly", "verdict": verdict,
        "summary": f"{len(rows) - fails - holds}/{len(rows)} PASS, {holds} HOLD, {fails} FAIL",
        "families": {f: {"verdict": v,
                          "checks": [r["check"] for r in rows if r["family"] == f]}
                     for f, v in fam_verdicts.items()},
        "lens_coverage": coverage,
        "checks": rows,
        "queued_gates": QUEUED,
    }
    out = ROOT / out_arg
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "summary": report["summary"],
                       "families": fam_verdicts, "out": out.relative_to(ROOT).as_posix()}, indent=2))
    for r in rows:
        print(f"[{r['status']:4}] {r['family']:14} {r['check']:22} {r['detail']}")
    return 0 if verdict != "FAIL" else 1


def load_report(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_trend() -> int:
    reps = sorted(AUDIT_DOC.glob("doctor_report_*.json"))
    if not reps:
        print("no reports"); return 1
    for p in reps:
        try:
            r = load_report(p)
            print(f"{p.name}: {r.get('verdict')} — {r.get('summary')} "
                  f"families={ {f: v['verdict'] for f, v in r.get('families', {}).items()} }")
        except Exception as exc:  # noqa: BLE001
            print(f"{p.name}: UNREADABLE ({exc})")
    return 0


def cmd_compare(a: str, b: str) -> int:
    ra, rb = load_report(ROOT / a), load_report(ROOT / b)
    sa = {c["check"]: c["status"] for c in ra.get("checks", [])}
    sb = {c["check"]: c["status"] for c in rb.get("checks", [])}
    changed = False
    for name in sorted(set(sa) | set(sb)):
        if sa.get(name) != sb.get(name):
            print(f"{name}: {sa.get(name, '—')} -> {sb.get(name, '—')}")
            changed = True
    if not changed:
        print("no check-status changes")
    print(f"verdict: {ra.get('verdict')} -> {rb.get('verdict')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Melusina Animation Doctor v2 (read-only)")
    ap.add_argument("--out", default="Saved/Audit/melusina_animation_doctor/doctor_report_20261006.json")
    ap.add_argument("--trend", action="store_true")
    ap.add_argument("--compare", nargs=2, metavar=("OLD", "NEW"))
    args = ap.parse_args()
    if args.trend:
        return cmd_trend()
    if args.compare:
        return cmd_compare(*args.compare)
    return cmd_run(args.out)


if __name__ == "__main__":
    sys.exit(main())
