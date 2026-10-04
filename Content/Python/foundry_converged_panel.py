"""Foundry converged panel -- one read-only front door over existing owners.

Converges (not replaces):
  - Material Instance inspector  : Content/Python/material_instance_widget_panel.py
  - World Compiler apply console : Content/Python/world_compiler_panel.py
                                    (compile stays CLI: Tools/world_compiler.py)
  - Houdini Foundry contract gate: Tools/Houdini/foundry/houdini_foundry.py
  - Universe Foundry compiler    : Tools/universe_foundry.py

Authority: this module never cooks, never compiles, never writes MPCs, never
imports ``hou`` or ``unreal`` at import time. Every action delegates to the
owning module above; editor-only paths degrade to HOLD offline instead of
tracebacks. Schemas/recipes stay canonical under specs/ + recipes/.

Usage (offline-safe):
  python Content/Python/foundry_converged_panel.py status
  python Content/Python/foundry_converged_panel.py mi --instance <path>
  python Content/Python/foundry_converged_panel.py wc-status [--bundle <dir>]
  python Content/Python/foundry_converged_panel.py foundry-validate <recipe...>
  python Content/Python/foundry_converged_panel.py foundry-plan <recipe>
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

ROOT = Path(__file__).resolve().parents[2]
HOUDINI_FOUNDRY_DIR = ROOT / "Tools" / "Houdini" / "foundry"
TOOLS_DIR = ROOT / "Tools"
for _p in (str(HOUDINI_FOUNDRY_DIR), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEFAULT_RECIPE = ROOT / "recipes" / "houdini_foundry" / "field_atlas_sea_above_test_tile.v1.json"


def _mod(name: str, rel: str):
    """Lazy import one owner module by repo-relative path (no unreal/hou)."""
    import importlib.util

    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {rel}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


def inspect_material(instance_path: str | None = None) -> dict[str, Any]:
    mi = _mod("material_instance_widget_panel", "Content/Python/material_instance_widget_panel.py")
    try:
        state = mi.MaterialInstanceWidgetPanel.inspect_instance(instance_path)
        return {"ok": True, **asdict(state)}
    except Exception as exc:  # offline-safe: never traceback the panel
        return {"ok": False, "status": "HOLD", "error": str(exc)}


def set_material_scalar(instance_path: str, param_name: str, value: float) -> dict[str, Any]:
    mi = _mod("material_instance_widget_panel", "Content/Python/material_instance_widget_panel.py")
    return mi.MaterialInstanceWidgetPanel.set_scalar_parameter(instance_path, param_name, float(value))


def wc_status(bundle: str | None = None) -> dict[str, Any]:
    wcp = _mod("world_compiler_panel", "Content/Python/world_compiler_panel.py")
    try:
        return {"ok": True, **wcp.status(bundle)}
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "error": str(exc)}


def _wc_editor_only(op: str, bundle: str | None = None) -> dict[str, Any]:
    try:
        wcp = _mod("world_compiler_panel", "Content/Python/world_compiler_panel.py")
        fn = {"cleanup": wcp.cleanup, "apply": wcp.apply_field, "capture": wcp.capture}[op]
        return {"ok": True, "op": op, "result": fn(bundle)}
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "op": op,
                "error": f"editor/UE path unavailable: {exc}"}


def foundry_validate(paths: list[str]) -> dict[str, Any]:
    hf = _mod("houdini_foundry", "Tools/Houdini/foundry/houdini_foundry.py")
    out: dict[str, Any] = {"ok": True, "files": {}}
    for p in paths:
        try:
            data = hf.load_json(Path(p))
            if data.get("schema") == hf.REQUEST_SCHEMA:
                errors = hf.validate_request(data)
            else:
                errors = hf.validate_recipe(data)
            out["files"][p] = {"ok": not errors, "errors": errors}
        except Exception as exc:
            out["files"][p] = {"ok": False, "errors": [str(exc)]}
    out["ok"] = all(f["ok"] for f in out["files"].values())
    return out


def foundry_plan(recipe: str) -> dict[str, Any]:
    hf = _mod("houdini_foundry", "Tools/Houdini/foundry/houdini_foundry.py")
    try:
        data = hf.load_json(Path(recipe))
        errors = hf.validate_recipe(data)
        if errors:
            return {"ok": False, "recipe": recipe, "errors": errors}
        return {"ok": True, "recipe": recipe, "plan": hf.build_plan(data)}
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "recipe": recipe, "error": str(exc)}


def foundry_verify(manifest: str) -> dict[str, Any]:
    hf = _mod("houdini_foundry", "Tools/Houdini/foundry/houdini_foundry.py")
    try:
        errors = hf.verify_manifest(Path(manifest))
        return {"ok": not errors, "manifest": manifest, "errors": errors}
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "manifest": manifest, "error": str(exc)}


def foundry_probe(timeout_s: int = 60) -> dict[str, Any]:
    hf = _mod("houdini_foundry", "Tools/Houdini/foundry/houdini_foundry.py")
    try:
        return hf.probe(timeout_s)
    except Exception as exc:
        return {"status": "HOLD", "reason": f"probe unavailable: {exc}"}


def universe_validate(genome: str, delta: str) -> dict[str, Any]:
    uf = _mod("universe_foundry", "Tools/universe_foundry.py")
    try:
        g = uf._load(Path(genome))
        d = uf._load(Path(delta))
        errors = uf.validate_genome(g) + uf.validate_delta(d, g.get("world_id"))
        return {"ok": not errors, "genome": genome, "delta": delta, "errors": errors}
    except Exception as exc:
        return {"ok": False, "status": "HOLD", "error": str(exc)}


def _mi_default_recipes() -> list[str]:
    return sorted(str(p).replace("\\", "/") for p in (ROOT / "recipes" / "houdini_foundry").glob("*.json"))


def menu_status_summary(bundle: str | None = None, recipe: str | None = None,
                        instance: str | None = None) -> str:
    """Compact multi-line summary for a menu click (Output Log friendly)."""
    snap = status(bundle, recipe, instance)
    lines = ["[Foundry] MI + WorldCompiler + Foundry status"]
    m, w, f = snap["material"], snap["world_compiler"], snap["foundry_recipe"]
    if m.get("ok"):
        lines.append(f"  MI: {m.get('instance')} (parent {m.get('parent')}, overrides {m.get('overrides')})")
    else:
        lines.append(f"  MI: HOLD ({m.get('error')})")
    if w.get("ok"):
        lines.append(f"  WC bundle: {w.get('bundle')} last_step={w.get('last_step')}")
    else:
        lines.append(f"  WC: HOLD ({w.get('error')})")
    bad = [p for p, r in (f.get("files") or {}).items() if not r.get("ok")]
    lines.append(f"  Foundry recipe: {'PASS' if f.get('ok') else 'FAIL: ' + '; '.join(bad)}")
    lines.append("  Compile stays CLI: Tools/world_compiler.py + Tools/world_compiler_ue_driver.py")
    return "\n".join(lines)


def menu_mi_summary(instance: str | None = None) -> str:
    state = inspect_material(instance)
    if not state.get("ok"):
        return f"[Foundry] MI inspect HOLD ({state.get('error')})"
    lines = [f"[Foundry] MI {state['instance_name']} (parent {state['parent_master']}, "
             f"overrides {state['override_count']}/{state['total_parameters']})"]
    for grp, items in state["groups"].items():
        overridden = [i["name"] for i in items if i.get("is_overridden")][:12]
        extra = "" if len([i for i in items if i.get("is_overridden")]) <= 12 else " ..."
        lines.append(f"  {grp}: {len(items)} params" +
                     (f" | overridden: {', '.join(overridden)}{extra}" if overridden else ""))
    return "\n".join(lines)


def menu_foundry_validate_summary(paths: list[str] | None = None) -> str:
    result = foundry_validate(paths or _mi_default_recipes())
    lines = ["[Foundry] recipe validation"]
    for p, r in result["files"].items():
        name = p.rsplit("/", 1)[-1]
        lines.append(f"  {'PASS' if r['ok'] else 'FAIL'} {name}" +
                     ("" if r["ok"] else f" -- {'; '.join(r['errors'][:3])}"))
    return "\n".join(lines)


def menu_foundry_plan_summary(recipe: str | None = None) -> str:
    result = foundry_plan(recipe or str(DEFAULT_RECIPE))
    if not result.get("ok"):
        detail = result.get("errors") or result.get("error")
        return f"[Foundry] plan HOLD ({detail})"
    plan = result["plan"]
    tiles = plan.get("tiles", [])
    lines = [f"[Foundry] plan {plan.get('recipe_id')} (seed {plan.get('seed')}, "
             f"{len(tiles)} tile(s) -> {plan.get('output_dir')})"]
    for t in tiles[:6]:
        lines.append(f"  {t['tile_id']} seed={t['seed']} bake_bounds={t['bake_bounds_cm']}")
    if len(tiles) > 6:
        lines.append(f"  ... +{len(tiles) - 6} more")
    lines.append(f"  UE target: {plan['ue_target']['consumer']} {plan['ue_target']['asset_path_prefix']}")
    return "\n".join(lines)


def status(bundle: str | None = None, recipe: str | None = None,
           instance: str | None = None) -> dict[str, Any]:
    """One combined read-only snapshot: MI + World Compiler + Foundry recipe."""
    mi = inspect_material(instance)
    wc = wc_status(bundle)
    fv = foundry_validate([recipe or str(DEFAULT_RECIPE)])
    return {
        "schema": "melodia.foundry_converged_status.v1",
        "compile_stays_cli": ("python Tools/world_compiler.py compile <recipe> && "
                              "python Tools/world_compiler_ue_driver.py <bundle> --lookdev"),
        "material": {"ok": mi.get("ok", False),
                     "instance": mi.get("instance_name"),
                     "parent": mi.get("parent_master"),
                     "overrides": mi.get("override_count"),
                     "error": mi.get("error")},
        "world_compiler": {"ok": wc.get("ok", False),
                           "bundle": wc.get("bundle"),
                           "last_step": (wc.get("last_step") or {}).get("step"),
                           "error": wc.get("error")},
        "foundry_recipe": {"ok": fv.get("ok", False), "files": fv.get("files")},
    }


def webm_encode_mi_loops(only: str | None = None, fps: int = 30) -> dict[str, Any]:
    """Encode MRQ MI-loop PNG sequences to .webm (ffmpeg libvpx-vp9).

    Consumes Saved/Portfolio/Renders/MaterialLoops/<mi_id>/<mi_id>_NNNN.png as
    written by run_mi_preview_mrq.py; writes <mi_id>.webm beside the frames.
    Pure post-production: no editor, no scene mutation.
    """
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return {"ok": False, "status": "HOLD", "error": "ffmpeg not on PATH"}
    root = ROOT / "Saved" / "Portfolio" / "Renders" / "MaterialLoops"
    if not root.is_dir():
        return {"ok": False, "status": "HOLD", "error": f"no loops dir yet: {root}"}
    dirs = [d for d in sorted(root.iterdir()) if d.is_dir()]
    if only:
        dirs = [d for d in dirs if d.name == only]
        if not dirs:
            return {"ok": False, "error": f"no loop dir for '{only}'"}
    out: dict[str, Any] = {"ok": True, "encoded": [], "skipped": []}
    for d in dirs:
        frames = sorted(d.glob(f"{d.name}_*.png")) or sorted(d.glob("frame_*.png"))
        frames = [f for f in frames if f.stat().st_size > 0]
        if not frames:
            out["skipped"].append(f"{d.name} (no encodable PNG frames)")
            continue
        dest = d / f"{d.name}.webm"
        stage = d / "_webm_stage"
        if stage.exists():
            import shutil as _sh
            _sh.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True)
        for i, f in enumerate(frames):
            (stage / f"f_{i:04d}.png").write_bytes(f.read_bytes())
        cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i", str(stage / "f_%04d.png"),
               "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
               "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", str(dest)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        import shutil as _sh2
        _sh2.rmtree(stage, ignore_errors=True)
        if proc.returncode != 0 or not dest.is_file():
            out["ok"] = False
            (out.setdefault("errors", {})[d.name]) = proc.stderr[-800:]
        else:
            out["encoded"].append(f"{d.name}.webm ({len(frames)} frames)")
    if not out["encoded"] and not out.get("errors"):
        out["ok"] = False
    return out


def menu_webm_summary(only: str | None = None) -> str:
    result = webm_encode_mi_loops(only=only)
    if result.get("status") == "HOLD":
        return f"[Foundry] webm HOLD ({result.get('error')})"
    lines = ["[Foundry] MI-loop .webm encode"]
    lines += [f"  OK {e}" for e in result.get("encoded", [])]
    lines += [f"  SKIP {s}" for s in result.get("skipped", [])]
    for name, err in (result.get("errors") or {}).items():
        lines.append(f"  FAIL {name}: {err.splitlines()[-1] if err else 'unknown'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Foundry converged panel (delegating front door)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="combined MI + World Compiler + Foundry snapshot")
    p.add_argument("--bundle", default=None)
    p.add_argument("--recipe", default=None)
    p.add_argument("--instance", default=None)

    p = sub.add_parser("mi", help="inspect one Material Instance (delegates to MI panel)")
    p.add_argument("--instance", default=None)

    p = sub.add_parser("mi-set-scalar", help="editor-only clamped scalar set (delegates to MI panel)")
    p.add_argument("instance")
    p.add_argument("param")
    p.add_argument("value", type=float)

    p = sub.add_parser("wc-status", help="World Compiler bundle status (delegates to WC panel)")
    p.add_argument("--bundle", default=None)

    for op in ("wc-apply", "wc-cleanup", "wc-capture"):
        p = sub.add_parser(op, help=f"editor-only World Compiler {op[3:]} (delegates to WC panel)")
        p.add_argument("--bundle", default=None)

    p = sub.add_parser("foundry-validate", help="offline Foundry recipe/request validation")
    p.add_argument("paths", nargs="+")

    p = sub.add_parser("foundry-plan", help="offline deterministic tile/output plan")
    p.add_argument("recipe")

    p = sub.add_parser("foundry-verify", help="re-derive hashes of a bake manifest")
    p.add_argument("manifest")

    p = sub.add_parser("foundry-probe", help="hython/license probe with hard timeout")
    p.add_argument("--timeout", type=int, default=60)

    p = sub.add_parser("universe-validate", help="offline genome+delta validation")
    p.add_argument("genome")
    p.add_argument("delta")

    p = sub.add_parser("webm", help="encode MI-loop PNG sequences to .webm (ffmpeg)")
    p.add_argument("--only", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "status":
        print(json.dumps(status(args.bundle, args.recipe, args.instance), indent=2, default=str))
    elif args.cmd == "mi":
        print(json.dumps(inspect_material(args.instance), indent=2, default=str))
    elif args.cmd == "mi-set-scalar":
        print(json.dumps(set_material_scalar(args.instance, args.param, args.value), indent=2, default=str))
    elif args.cmd == "wc-status":
        print(json.dumps(wc_status(args.bundle), indent=2, default=str))
    elif args.cmd.startswith("wc-"):
        print(json.dumps(_wc_editor_only(args.cmd[3:], args.bundle), indent=2, default=str))
    elif args.cmd == "foundry-validate":
        result = foundry_validate(args.paths)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1
    elif args.cmd == "foundry-plan":
        result = foundry_plan(args.recipe)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1
    elif args.cmd == "foundry-verify":
        result = foundry_verify(args.manifest)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1
    elif args.cmd == "foundry-probe":
        print(json.dumps(foundry_probe(args.timeout), indent=2, default=str))
    elif args.cmd == "universe-validate":
        result = universe_validate(args.genome, args.delta)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1
    elif args.cmd == "webm":
        result = webm_encode_mi_loops(only=args.only)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
