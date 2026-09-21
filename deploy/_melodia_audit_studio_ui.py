"""Static UI census for the Melodia Studio / Surreal Architecture addon family.

A0 audit (read-only). Never imports bpy, never touches the live install, never
writes anything outside Saved/Audit/. Complements deploy/_melodia_health_gn_builders.py
(which verifies the builder registry under bpy) by answering the UI-side question:

    which panels, operators, pie menus, keymaps and N-tab categories does each
    addon surface declare, and where do they collide?

Scanned surfaces (ADDON_AUTHORITY_2026-09-03.md plus siblings):
  - deploy/surreal_architecture_gen.py            (the monolith)
  - deploy/surreal_arch/**/*.py                   (overhaul package, melodia_gn)
  - deploy/surreal_world, surreal_os, surreal_greybox
  - Tools/BlenderAddons/**/*.py                   (melodia_studio + friends)

Findings per file (via ast, no bpy import):
  - Panel / Operator / Menu / AddonPreferences class declarations with
    bl_idname, bl_label, bl_category, bl_parent_id, bl_space_type, bl_region_type
  - dynamically-generated classes (nested in functions) - flagged via "dynamic"
  - keymap registrations (keymap_items.new)
  - bl_info dicts in __init__.py entry points
  - draw hooks (.draw patches, context-menu appends) that reach into other modules

Output: Saved/Audit/melodia_studio_ui_census_<date>.json + a collision summary on
stdout. Exit code 0 always - this is a census, not a gate. Gate decisions are
human + Tools/verify_addon.py per the freeze doc.

Usage:
        python deploy/_melodia_audit_studio_ui.py [--out PATH] [--repo ROOT]
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import date
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk upward from *start* to locate the repo root (contains .git/.gitattributes).

    Portable regardless of call-site depth, so the tool keeps working if moved
    from Tools/ to deploy/ or run from an IDE working dir.
    """
    p = start
    for _ in range(8):
        if p.name == ".git" or (p / ".git").exists() or (p / ".gitattributes").exists():
            return p
        nxt = p.parent
        if nxt == p:
            break
        p = nxt
    return start  # fallback: caller dir


DEFAULT_REPO = _find_repo_root(Path(__file__).resolve().parent)

# Surfaces scanned, relative to repo root. Each entry: (rel_path, surface_name)
SURFACES = [
    ("deploy/surreal_architecture_gen.py", "monolith"),
    ("deploy/surreal_arch", "surreal_arch_package"),
    ("deploy/surreal_greybox", "surreal_greybox"),
    ("deploy/surreal_world", "surreal_world"),
    ("deploy/surreal_os", "surreal_os"),
    ("Tools/BlenderAddons", "tools_blenderaddons"),
]

BASE_CLASSES = {"Panel", "Operator", "Menu", "AddonPreferences"}


def _const_str(node: ast.AST) -> str:
    """Best-effort string value from an AST node (handles a few forms)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _const_str(node.func)
    if isinstance(node, ast.JoinedStr):  # f-string - not a stable id
        return "<fstring>"
    return ""


def _kw_str(node: ast.Call, name: str) -> str:
    for kw in node.keywords:
        if kw.arg == name:
            return _const_str(kw.value)
    return ""


def _attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        parent = _attr_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return _attr_name(node.func)
    if isinstance(node, ast.Subscript):
        return _attr_name(node.value)
    return ""


def _annotations(node: ast.ClassDef) -> dict[str, str]:
    """Map annotated names (bpy.props.* assignments) to their annotation source."""
    out = {}
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            out[stmt.target.id] = _attr_name(stmt.annotation)
    return out


def _walk_scoped(classes_out: list, node: ast.ClassDef, file_rel: str, surface: str,
                 inside_fn: bool) -> None:
    kind = None
    for base in node.bases:
        nm = _attr_name(base)
        if nm.rsplit(".", 1)[-1] in BASE_CLASSES:
            kind = nm.rsplit(".", 1)[-1]
            break
    body_stmts = []
    anns = _annotations(node)
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id.startswith("bl_"):
                    body_stmts.append((t.id, _const_str(stmt.value)))
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body_stmts.append((stmt.name, "<method>"))
    entry = {
        "kind": kind or "Unknown",
        "class": node.name,
        "file": file_rel,
        "surface": surface,
        "line": node.lineno,
        "dynamic": inside_fn,
        "props": {k: v for k, v in anns.items() if "props" in v},
        "bl_idname": "", "bl_label": "", "bl_category": "", "bl_parent_id": "",
        "bl_space_type": "", "bl_region_type": "",
        "methods": [n for n, v in body_stmts if v == "<method>"],
    }
    for name, val in body_stmts:
        if name in entry and name.startswith("bl_"):
            entry[name] = val
    if kind is None and not any(n.startswith("bl_") for n, _ in body_stmts):
        return  # not UI-relevant
    classes_out.append(entry)


def _scan_calls(tree: ast.AST, file_rel: str) -> tuple[list, list]:
    """Flat pass over every node: keymap registrations, draw-hook calls and
    panel-rewrite assignments (works at any nesting depth)."""
    keymaps: list[dict] = []
    draw_hooks: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = _attr_name(node.func)
            if fn.endswith("keymap_items.new"):
                keymaps.append({
                    "file": file_rel,
                    "idname": (node.args[0].value if node.args
                               and isinstance(node.args[0], ast.Constant) else ""),
                    "key": (node.args[1].value if len(node.args) > 1
                            and isinstance(node.args[1], ast.Constant) else ""),
                    "mods": [f"{kw.arg}={_const_str(kw.value) or kw.arg}"
                             for kw in node.keywords],
                    "line": node.lineno,
                })
            elif fn.endswith(("append", ".draw")):
                txt = ast.unparse(node)
                if ".draw" in txt or "context_menu.append" in txt:
                    draw_hooks.append({"file": file_rel, "call": txt[:200],
                                       "line": node.lineno})
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Attribute) and t.attr in (
                        "draw", "poll", "execute", "bl_category",
                        "bl_parent_id", "bl_label", "bl_order"):
                    # e.g. monolith.SURREAL_ARCH_PT_arch_picker.draw = _picker_draw
                    # or cls.bl_category = N_PANEL_CATEGORY (branding unify pass)
                    txt = ast.unparse(node)
                    if "PT_" in txt or "panel" in txt.lower() or "bl_" in txt:
                        draw_hooks.append({
                            "file": file_rel, "call": txt[:200],
                            "line": node.lineno, "kind": "rewrite"})
    return keymaps, draw_hooks


def scan_file(path: Path, file_rel: str, surface: str) -> dict:
    try:
        src = path.read_text(encoding="utf-8-sig", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        return {"file": file_rel, "surface": surface, "error": f"syntax: {exc}",
                "classes": [], "keymaps": [], "draw_hooks": [], "bl_info": None}

    classes: list[dict] = []
    bl_info: dict | None = None

    def _visit_body(body, inside_fn: bool):
        nonlocal bl_info
        for stmt in body:
            if isinstance(stmt, ast.ClassDef):
                _walk_scoped(classes, stmt, file_rel, surface, inside_fn)
                _visit_body(stmt.body, inside_fn)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _visit_body(stmt.body, True)
            elif isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    if isinstance(t, ast.Name) and t.id == "bl_info":
                        try:
                            bl_info = ast.literal_eval(stmt.value)
                        except (ValueError, SyntaxError):
                            bl_info = {"<unparsed>": True}

    _visit_body(tree.body, False)
    keymaps, draw_hooks = _scan_calls(tree, file_rel)
    return {"file": file_rel, "surface": surface, "classes": classes,
            "keymaps": keymaps, "draw_hooks": draw_hooks, "bl_info": bl_info}


def scan_surface(root: Path, rel: str, surface: str) -> list[dict]:
    p = root / rel
    results = []
    if p.is_file():
        results.append(scan_file(p, rel, surface))
    elif p.is_dir():
        for f in sorted(p.rglob("*.py")):
            if "__pycache__" in f.parts:
                continue
            results.append(scan_file(f, str(f.relative_to(root)).replace("\\", "/"), surface))
    return results


def summarize(all_results: list[dict]) -> dict:
    panels = [c for r in all_results for c in r["classes"] if c["kind"] == "Panel"]
    prefs = [c for r in all_results for c in r["classes"]
             if c["kind"] == "AddonPreferences"]
    menus = [c for r in all_results for c in r["classes"] if c["kind"] == "Menu"]
    ops = [c for r in all_results for c in r["classes"] if c["kind"] == "Operator"]
    by_cat: dict[str, list] = {}
    for p in panels:
        by_cat.setdefault(p["bl_category"] or "<none>", []).append(p["class"])
    dup_labels: dict[str, list] = {}
    for p in panels:
        if p["bl_label"]:
            dup_labels.setdefault(p["bl_label"], []).append(
                f"{p['class']}@{p['file']}:{p['line']}")
    dup_labels = {k: v for k, v in dup_labels.items() if len(v) > 1}
    monolith_panels = [p for p in panels if p["surface"] == "monolith"]
    pkg_panels = [p for p in panels if p["surface"] == "surreal_arch_package"]
    keymaps = [k for r in all_results for k in r["keymaps"]]
    hooks = [h for r in all_results for h in r["draw_hooks"]]
    return {
        "counts": {
            "files_scanned": len(all_results),
            "errors": sum(1 for r in all_results if "error" in r),
            "panels": len(panels),
            "menus": len(menus),
            "operators": len(ops),
            "addon_preferences": len(prefs),
            "keymap_registrations": len(keymaps),
            "draw_hooks": len(hooks),
        },
        "panel_categories": {k: len(v) for k, v in sorted(by_cat.items())},
        "duplicate_panel_labels": dup_labels,
        "monolith_panel_classes": [p["class"] for p in monolith_panels],
        "package_panel_classes": [p["class"] for p in pkg_panels],
        "monolith_panel_count": len(monolith_panels),
        "package_panel_count": len(pkg_panels),
        "keymaps": keymaps,
        "draw_hooks": hooks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.repo).resolve()

    all_results: list[dict] = []
    for rel, surface in SURFACES:
        all_results.extend(scan_surface(root, rel, surface))

    summary = summarize(all_results)
    payload = {
        "tool": "Tools/audit_melodia_studio_ui.py",
        "date": str(date.today()),
        "repo": str(root),
        "summary": summary,
        "files": [r for r in all_results if r["classes"] or r.get("bl_info")
                  or "error" in r],
    }
    out = Path(args.out) if args.out else root / "Saved" / "Audit" / (
        f"melodia_studio_ui_census_{date.today().strftime('%Y-%m-%d')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    c = summary["counts"]
    print(f"census -> {out}")
    print(f"files scanned: {c['files_scanned']}  ({c['errors']} errors)")
    print(f"panels: {c['panels']}  menus: {c['menus']}  operators: {c['operators']}  "
          f"prefs: {c['addon_preferences']}")
    print(f"keymaps: {c['keymap_registrations']}  draw-hooks: {c['draw_hooks']}")
    print("-- panel categories --")
    for cat, n in summary["panel_categories"].items():
        print(f"  {n:3d}  {cat}")
    print(f"-- monolith panels ({summary['monolith_panel_count']}) --")
    for cls in summary["monolith_panel_classes"]:
        print(f"  {cls}")
    print(f"-- package panels ({summary['package_panel_count']}) --")
    for cls in summary["package_panel_classes"][:40]:
        print(f"  {cls}")
    if summary["duplicate_panel_labels"]:
        print("-- duplicate panel labels --")
        for lbl, locs in summary["duplicate_panel_labels"].items():
            print(f"  '{lbl}': {locs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
