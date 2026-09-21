"""Param-wiring TRIAGE - a static guess, not a verdict. Read this before using.

THE AUTHORITY IS `_melodia_health_gn_param_wiring.py`, which builds every tree in
Blender and reads the real answer: a Group Input socket with no outgoing link is
unwired, and no preset or slider can move geometry through it.

THIS script is a cheap heuristic that OVER-REPORTS, badly and predictably. It
cannot see wiring that goes through:

  * loop variables   - paris_wall_detail wires `Show Cornice` via a `specs` tuple
                       list, so the name is never a literal at the call site and
                       this script calls it dead when it is in fact wired;
  * computed names   - civic_kit builds param names from BUILDER_PARAM_DEFAULTS
                       (`nm.replace('_',' ').title()`), so it declares nothing
                       this script can see at all;
  * module helpers   - partially covered (one level of inlining), not in general.

On 2026-09-20 it reported 226 of 359 builders with dead params and 1162 dead
sockets. That number is not credible and is mostly false positive; the runtime
audit is what settled the real cases (civic_kit's fountain, GN_PARIS_SlabTrim).

It is kept because a ranked list of candidates is still useful for triage - you
look at the top of the list first - and it exits 0 ALWAYS so it can never be
mistaken for a gate. Do not wire it into CI. Do not act on a single hit without
confirming it in Blender.

Usage:
    python deploy/_melodia_param_wiring_audit.py [--json]
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

GN_DIR = Path(__file__).resolve().parent / "surreal_arch" / "melodia_gn"

_PARAM_FUNCS = {
    "add_float_param", "add_int_param", "add_bool_param",
    "add_vector_param", "add_string_param",
    # paris_wall_detail.py declares its params with a local sock() helper:
    #   sock(t, 'CORNICE_STYLE', 'NodeSocketInt', 1)
    "sock",
}


def _declared_params(fn: ast.AST) -> list[str]:
    """Param NAMES declared inside a builder function.

    The house signature is add_*_param(tree, name, default, ...) - the name is
    the first STRING argument, not the first argument. Taking args[0] returned
    the tree variable for every builder, so the first run of this audit reported
    "0 builders with params / 595 without" on a library where nearly every
    builder declares them. Scan the args for the first string literal instead.
    """
    names: list[str] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if fname not in _PARAM_FUNCS:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                names.append(arg.value)
                break
    return names


def _group_input_names(fn: ast.AST) -> set[str]:
    """Variables bound to the group-input node, under any name.

    The house names it `gin`, but paris_wall_detail uses `gin2`, and some
    builders take it from N(t, 'NodeGroupInput'). Missing the alias is how a
    wired builder gets reported as fully dead.
    """
    gi: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            call = node.value
            f = getattr(call, "func", None)
            fname = ""
            if f is not None:
                fname = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            # tree, gin, gout = new_geometry_tree(...)
            if fname == "new_geometry_tree" and len(node.targets) == 1:
                tgt = node.targets[0]
                if isinstance(tgt, ast.Tuple) and len(tgt.elts) >= 2:
                    second = tgt.elts[1]
                    if isinstance(second, ast.Name):
                        gi.add(second.id)
            # gin2 = N(t, 'NodeGroupInput', ...)
            if any(isinstance(a, ast.Constant) and a.value == "NodeGroupInput"
                   for a in getattr(call, "args", []) or []):
                if isinstance(node.targets[0], ast.Name):
                    gi.add(node.targets[0].id)
    return gi


def _wired_names(fn: ast.AST, module_funcs: dict | None = None) -> set[str]:
    """Names this builder actually reads out of its group input.

    Two idioms exist and both must be counted, or the verdict is wrong:
      * `gin.outputs['Name']`            (subscript)
      * `L(t, gin2, 'Name', node, 'in')` (name passed as a string ARGUMENT)
    Wiring may also live one call deeper, in a module-level helper the builder
    calls (paris_wall_detail's _gothic_branch), so those bodies are inlined one
    level down.
    """
    bodies = [fn]
    gi = _group_input_names(fn)
    if module_funcs:
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            helper = module_funcs.get(nm)
            if helper is not None and helper is not fn:
                bodies.append(helper)
                gi |= _group_input_names(helper)

    wired: set[str] = set()
    for body in bodies:
        for node in ast.walk(body):
            if isinstance(node, ast.Subscript):
                val = node.value
                if (isinstance(val, ast.Attribute) and val.attr == "outputs"
                        and isinstance(val.value, ast.Name) and val.value.id in gi):
                    sl = node.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        wired.add(sl.value)
            elif isinstance(node, ast.Call):
                args = list(node.args) + [k.value for k in node.keywords]
                if any(isinstance(a, ast.Name) and a.id in gi for a in args):
                    for a in args:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            wired.add(a.value)
    return wired


def audit() -> dict:
    report = {"modules": 0, "builders": 0, "fully_wired": 0, "with_dead": [],
              "no_params": 0}
    for path in sorted(GN_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        report["modules"] += 1
        module_funcs = {n.name: n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef)}
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("build_"):
                continue
            declared = _declared_params(fn)
            if not declared:
                report["no_params"] += 1
                continue
            report["builders"] += 1
            wired = _wired_names(fn, module_funcs)
            # 'Geometry' is the passthrough, never a user-facing param.
            wanted = [d for d in declared if d != "Geometry"]
            dead = [d for d in wanted if d not in wired]
            if not dead:
                report["fully_wired"] += 1
            else:
                report["with_dead"].append(
                    {"module": path.name, "builder": fn.name, "line": fn.lineno,
                     "declared": len(wanted), "dead": dead,
                     "wired": sorted(set(wanted) & wired)})
    return report


def main(argv: list[str]) -> int:
    report = audit()
    if "--json" in argv:
        print(json.dumps(report, indent=2))
    else:
        print("[param-wiring audit] which declared params the geometry never reads")
        print(f"  modules scanned: {report['modules']}")
        print(f"  builders with params: {report['builders']}")
        print(f"    fully wired: {report['fully_wired']}")
        print(f"    with DEAD params: {len(report['with_dead'])}")
        print(f"  (builders declaring no literals at all: {report['no_params']} - "
              f"includes those that build param names dynamically)")
        dead_total = sum(len(d["dead"]) for d in report["with_dead"])
        print(f"  dead param sockets in total: {dead_total}")
        for d in report["with_dead"]:
            pct = f"{len(d['dead'])}/{d['declared']}"
            print(f"    {d['module']}:{d['line']} {d['builder']} dead={pct} "
                  f"-> {d['dead'][:6]}")
    return 0   # triage only - never a gate (see module docstring)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
