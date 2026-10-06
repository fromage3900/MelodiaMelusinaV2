"""hda_verify.py - Gate 2: install, inspect and COOK every active HDA (hython).

Answers what Gate 0 cannot: does the definition actually load, does the asset
instantiate, does it cook without node errors, and does the geometry it emits
match the numbers pinned in the registry?

    hython Tools/Houdini/hda_verify/hda_verify.py --out-dir Saved/Audit/hda_verify/<run>
    hython Tools/Houdini/hda_verify/hda_verify.py --only melodia_crystal_cathedral

Per entry (status=active in hda_registry.v1.json):
  install     -> hou.hda.installFile + a definition must be found
  create      -> /obj can instantiate node_type
  parms       -> expect.parms must exist on the instance (declared on the HDA type)
  outputs     -> every expect.outputs entry must cook with >= min_points/min_prims
                 (and == points/prims when an exact pin is given)
  drive       -> expect.parm_drive sets a parameter, re-cooks, requires the
                 geometry to move (points/prims must differ from the default cook
                 and match any pin, or bbox must move when the pin uses differ_bbox
                 for outputs whose counts are constant (a single Volume primitive),
                 then restores the value and re-proves the
                 default cook against expect.outputs
  errors      -> no node inside the instance may report an error

Entries with status=missing are reported as OWED (warn, exit stays 0) so the
known debt stays visible without blocking the gate. Measured counts are always
written to the receipt so pinning exact numbers is a copy/paste, not a guess.

Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = environment/registry problem.
Receipt: <out-dir>/hda_verify_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = Path(__file__).with_name("hda_registry.v1.json")

try:
    import hou  # noqa: F401  (only available under hython)
except ImportError:
    hou = None


# --------------------------------------------------------------------- helpers
def load_registry(path: Path) -> dict:
    # utf-8-sig: PowerShell's Set-Content writes a BOM and a BOM must not
    # turn into "ENVIRONMENT FAIL: JSONDecodeError".
    with path.open("r", encoding="utf-8-sig") as fh:
        reg = json.load(fh)
    if reg.get("schema") != "melodia.hda_registry.v1":
        raise ValueError(f"unexpected registry schema: {reg.get('schema')!r}")
    return reg


def custom_parm_names(node) -> tuple[list[str], str]:
    """Names of the parameters the HDA *type* declares (what UE's panel shows).

    The definition's own DialogScript is the honest source: Object-context nodes
    inherit tx/ty/tz/scale/... from the transform category (so 'every parm' would
    falsely look parameterised) while spareParms() may list package spares that no
    consumer ever sees. Both remain as fallbacks for builds that cannot answer.
    """
    try:
        definition = node.type().definition()
    except Exception:
        definition = None
    if definition is not None:
        try:
            names = [t.name() for t in definition.parmTemplateGroup().parmTemplates()
                     if not isinstance(t, hou.FolderParmTemplate)]
            return sorted(names), "definition"
        except Exception:
            pass
    meth = getattr(node, "spareParms", None)
    if meth is not None:
        try:
            return sorted(t.name() for t in meth()), "spareParms"
        except Exception:
            pass
    try:
        return sorted(p.name() for p in node.parms()), "parms(fallback)"
    except Exception:
        return [], "unavailable"


def output_problems(got: dict | None, want: dict, base: dict | None = None) -> list[str]:
    """Registry pin comparison for one cooked output. [] means it matched.

    `base` is the default cook of the same output; when given, `want["differ"]`
    requires the measured counts to have MOVED — that is what proves a parameter
    actually drives the cook instead of merely existing on the dialog. For
    outputs whose primitive count cannot move (a rasterized Volume is always one
    primitive / one point), `want["differ_bbox"]` compares the bounding box
    instead — still a real cook change, just measured on bounds.
    """
    if got is None:
        return ["output node not found"]
    if "cook_error" in got:
        return [got["cook_error"]]
    problems = []
    if "min_points" in want and got["points"] < want["min_points"]:
        problems.append(f"points {got['points']} < {want['min_points']}")
    if "min_prims" in want and got["prims"] < want["min_prims"]:
        problems.append(f"prims {got['prims']} < {want['min_prims']}")
    if "points" in want and got["points"] != want["points"]:
        problems.append(f"points {got['points']} != {want['points']}")
    if "prims" in want and got["prims"] != want["prims"]:
        problems.append(f"prims {got['prims']} != {want['prims']}")
    if want.get("differ") and base and "points" in base:
        if (got["points"], got["prims"]) == (base["points"], base["prims"]):
            problems.append(
                f"unchanged from the default cook ({got['points']}/{got['prims']}) "
                "- the parameter does not drive the cook")
    if want.get("differ_bbox") and base and base.get("bbox") and got.get("bbox"):
        if got["bbox"] == base["bbox"]:
            problems.append(
                f"bbox unchanged from the default cook ({got['bbox']}) "
                "- the parameter does not drive the cook")
    return problems


def cook_outputs(inst) -> tuple[dict, list, list, float]:
    """Force-cook every output SOP under the instance. Returns geometry stats."""
    outputs: dict[str, dict] = {}
    errors: list[str] = []
    warnings: list[str] = []
    started = time.time()

    children = list(inst.allSubChildren())
    for child in children:
        try:
            errs = child.errors()
        except Exception:
            errs = ()
        for e in errs:
            errors.append(f"{child.path()}: {str(e).strip().splitlines()[0]}")
        try:
            warns = child.warnings()
        except Exception:
            warns = ()
        for w in warns:
            warnings.append(f"{child.path()}: {str(w).strip().splitlines()[0]}")

    for child in children:
        if child.type().name() != "output":
            continue
        rec: dict = {"node": child.name()}
        try:
            geo = child.geometry()  # cooks this branch
            rec["points"] = len(geo.points())
            rec["prims"] = len(geo.prims())
            rec["bbox"] = [round(v, 3) for v in geo.boundingBox().sizevec()]
        except Exception as exc:
            rec["cook_error"] = f"{type(exc).__name__}: {exc}"
        outputs[child.name()] = rec

    return outputs, errors, warnings, time.time() - started


def verify_entry(project_root: Path, entry: dict) -> dict:
    """Install + cook one entry. Never raises: problems become FAIL checks."""
    import hou as _hou

    rec: dict = {
        "id": entry.get("id"),
        "status": entry.get("status"),
        "path": entry.get("path"),
        "node_type": entry.get("node_type"),
        "checks": [],
        "result": "PASS",
    }

    def check(name: str, ok: bool, detail: str = "", level: str = "FAIL") -> None:
        rec["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if ok:
            return
        if level == "FAIL":
            rec["result"] = "FAIL"
        elif rec["result"] == "PASS":
            rec["result"] = "WARN"

    if entry.get("status") == "missing":
        check("file_present", False,
              f"OWED: {entry['path']} (builder: {entry.get('builder') or 'none'})",
              level="WARN")
        return rec

    path = (project_root / entry["path"]).resolve()
    if not path.is_file():
        check("file_present", False, f"missing: {entry['path']}")
        return rec
    check("file_present", True, f"{path.stat().st_size} bytes")

    # ---- install -----------------------------------------------------------
    try:
        _hou.hda.installFile(str(path))
    except Exception as exc:
        check("install", False, f"{type(exc).__name__}: {exc}")
        return rec

    definitions = list(_hou.hda.definitionsInFile(str(path)))
    check("definition_found", bool(definitions),
          "; ".join(f"{d.nodeTypeName()} ({d.description()})" for d in definitions))
    if not definitions:
        return rec
    disabled = False
    probe = getattr(definitions[0], "isDisabled", None)
    if probe is not None:
        try:
            disabled = bool(probe())
        except Exception:
            disabled = False
    rec["definition"] = {
        "node_type": definitions[0].nodeTypeName(),
        "description": definitions[0].description(),
        "disabled": disabled,
    }

    node_type = entry.get("node_type") or definitions[0].nodeTypeName()
    obj = _hou.node("/obj")
    inst = None
    try:
        inst = obj.createNode(node_type, f"verify_{entry['id']}")
    except Exception as exc:
        check("create_node", False, f"{node_type}: {type(exc).__name__}: {exc}")
        return rec
    check("create_node", True, node_type)

    try:
        # ---- parameters ---------------------------------------------------
        names, source = custom_parm_names(inst)
        rec["parms"] = {"source": source, "names": names, "count": len(names)}
        required = entry.get("expect", {}).get("parms") or []
        missing_p = [p for p in required if inst.parm(p) is None]
        check("parms_required", not missing_p,
              f"source={source}; missing={missing_p or '[]'}; required={required}")

        # ---- cook ----------------------------------------------------------
        outputs, errors, warnings, seconds = cook_outputs(inst)
        network = [{"path": c.path().replace(inst.path() + "/", ""),
                    "type": c.type().nameWithCategory()}
                   for c in inst.allSubChildren()]
        rec["network"] = network
        rec["cook"] = {
            "seconds": round(seconds, 3),
            "outputs": outputs,
            "node_errors": errors,
            "node_warnings": warnings[:20],
            "node_warning_count": len(warnings),
        }

        # No declared parameters is legal but worth stating out loud: the asset
        # can only ever cook at its internal defaults (from UE's panel too).
        check("parms_exposed", rec["parms"]["count"] > 0,
              f"{rec['parms']['count']} parameter(s) declared on the HDA type - "
              "0 means the controls still live only on an inner node, so the "
              "asset cooks at defaults only",
              level="WARN")

        expect_outputs = entry.get("expect", {}).get("outputs") or {}
        for out_name, want in expect_outputs.items():
            got = outputs.get(out_name)
            problems = output_problems(got, want)
            check(f"output:{out_name}", not problems,
                  "; ".join(problems) or
                  f"points={got['points']} prims={got['prims']} "
                  f"bbox={got.get('bbox')}")

        if not expect_outputs:
            check("outputs_declared", False,
                  "registry lists no expect.outputs for this entry - pin the "
                  "measured counts from this receipt", level="WARN")

        # ---- parameter drive probe -------------------------------------
        # Proves the exposed parameters are not decoration: set one, re-cook,
        # require the geometry to move, then restore the value and re-prove the
        # default cook. A drive test that only checks "it changed" would pass a
        # broken restore, so the golden pins are re-checked afterwards too.
        drive_probes = entry.get("expect", {}).get("parm_drive") or []
        drive_records = []
        for probe in drive_probes:
            pname = probe.get("parm")
            want_value = probe.get("value")
            parm = inst.parm(pname) if pname else None
            if parm is None:
                check(f"drive:{pname}", False, "parameter not found on instance")
                continue
            try:
                previous = parm.eval()
                parm.set(want_value)
                driven_outputs, driven_errors, _, driven_seconds = cook_outputs(inst)
                problems = []
                if driven_errors:
                    problems.append(
                        f"{len(driven_errors)} node error(s): {driven_errors[:2]}")
                for out_name, spec in (probe.get("outputs") or {}).items():
                    sub = output_problems(driven_outputs.get(out_name), spec,
                                          outputs.get(out_name))
                    problems.extend(f"{out_name}: {p}" for p in sub)
                drive_records.append({
                    "parm": pname, "set_to": want_value, "previous": previous,
                    "problems": problems,
                    "outputs": {k: {kk: vv for kk, vv in v.items() if kk in ("points", "prims")}
                                for k, v in driven_outputs.items()},
                })
                check(f"drive:{pname}={want_value}", not problems,
                      "; ".join(problems) or
                      f"driven cook {round(driven_seconds, 3)}s: " + ", ".join(
                          f"{n}={o.get('points')}/{o.get('prims')}"
                          for n, o in driven_outputs.items()))

                # restore and re-prove the golden cook
                parm.set(previous)
                restored_outputs, restored_errors, _, _ = cook_outputs(inst)
                restore_problems = []
                if restored_errors:
                    restore_problems.append(
                        f"{len(restored_errors)} node error(s): {restored_errors[:2]}")
                for out_name, want in expect_outputs.items():
                    sub = output_problems(restored_outputs.get(out_name), want)
                    restore_problems.extend(f"{out_name}: {p}" for p in sub)
                check(f"restore_after_drive:{pname}", not restore_problems,
                      "; ".join(restore_problems) or
                      "golden cook restored: " + ", ".join(
                          f"{n}={o.get('points')}/{o.get('prims')}"
                          for n, o in restored_outputs.items()
                          if o.get("points") is not None))
            except Exception as exc:
                check(f"drive:{pname}", False, f"{type(exc).__name__}: {exc}")
        if drive_records:
            rec["drive"] = drive_records

        if entry.get("expect", {}).get("node_errors") == "none":
            check("node_errors", not errors,
                  f"{len(errors)} error(s): {errors[:3]}")
    finally:
        try:
            inst.destroy()
        except Exception:
            pass

    return rec


def run_verify(project_root: Path, registry_path: Path, out_dir: Path,
               only: list[str] | None = None) -> dict:
    import hou as _hou

    registry = load_registry(registry_path)
    entries = [e for e in registry["entries"]
               if not only or e.get("id") in only]
    results = []
    for entry in entries:
        started = time.time()
        try:
            rec = verify_entry(project_root, entry)
        except Exception as exc:  # a crashing entry must not hide the others
            rec = {"id": entry.get("id"), "status": entry.get("status"),
                   "path": entry.get("path"), "result": "FAIL",
                   "checks": [{"name": "verify_entry", "ok": False,
                               "detail": f"{type(exc).__name__}: {exc}"}]}
        rec["wall_seconds"] = round(time.time() - started, 3)
        results.append(rec)

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        counts[r["result"]] = counts.get(r["result"], 0) + 1

    report = {
        "schema": "melodia.hda_verify_report.v1",
        "gate": 2,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "houdini_version": str(_hou.applicationVersionString()),
        "license": str(_hou.licenseCategory()),
        "project_root": str(project_root),
        "registry": str(registry_path),
        "counts": counts,
        "entries": results,
        "overall": "FAIL" if counts.get("FAIL") else
                   ("WARN" if counts.get("WARN") else "PASS"),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hda_verify_report.json"
    with out_path.open("w", encoding="utf-8") as fh:
        # default=str keeps hou enums/tuples from ever crashing the receipt.
        json.dump(report, fh, indent=2, default=str)
    report["_receipt"] = str(out_path)
    return report


def main(argv: list[str] | None = None) -> int:
    if hou is None:
        print("[hda_verify] hou unavailable - run under hython", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description="HDA Gate 2: install + cook verifier")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--only", action="append", default=None,
                    help="verify just this entry id (repeatable)")
    args = ap.parse_args(argv)

    out_dir = args.out_dir or (PROJECT_ROOT / "Saved" / "Audit" / "hda_verify"
                               / datetime.now().strftime("%Y%m%d_%H%M%S"))
    try:
        report = run_verify(args.project_root.resolve(), args.registry, out_dir,
                            args.only)
    except Exception as exc:
        print(f"[hda_verify] ENVIRONMENT FAIL: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2

    for e in report["entries"]:
        print(f"{e['result']:4} {e['id']}")
        for c in e["checks"]:
            mark = "ok" if c["ok"] else "!!"
            print(f"       {mark} {c['name']}: {c['detail']}")
        cook = e.get("cook")
        if cook:
            print(f"       cook {cook['seconds']}s, "
                  f"{cook['node_warning_count']} warning(s)")
    print(f"[hda_verify] {report['counts']} | Houdini {report['houdini_version']} "
          f"({report['license']})")
    print(f"[hda_verify] receipt: {report['_receipt']}")
    return 1 if report["overall"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
