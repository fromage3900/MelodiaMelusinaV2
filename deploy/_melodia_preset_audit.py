"""Preset library audit — shadowed keys, duplicate assignments, brand refs.

Read-only. Pure Python (no bpy): parses `presets.py` as an AST so it can see
keys Python has ALREADY silently discarded at runtime.

Why this exists: on 2026-09-20 a census of BUILDERS_PRESETS found two entries
defined twice in the same dict literal. Python keeps the last and throws the
rest away, so the earlier curated set was invisible to every runtime consumer
(the apply operator, the N-panel, the JSON export, Studio Health). No dump of
the live dict can ever find this — the key exists, the data does not. It is the
presets-layer twin of `core.link_failures()`: a silent no-op with a green light.

Also resolves the Maison Impossible brand packs, so a pack that points at a
renamed builder or a deleted preset is caught here instead of at click time.

Usage:
    python deploy/_melodia_preset_audit.py            # human report
    python deploy/_melodia_preset_audit.py --json     # machine-readable

Exit code 1 if shadowed keys or broken brand refs exist, else 0.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRESETS_PATH = ROOT / "surreal_arch" / "melodia_gn" / "presets.py"


def _dict_literal_keys(tree: ast.AST) -> list[dict]:
    """Every key defined inside a `BUILDERS_PRESETS = {...}` literal.

    Handles BOTH Assign and AnnAssign: the library's main literal is annotated
    (`BUILDERS_PRESETS: dict[str, dict[str, Any]] = {`), and only matching
    plain Assign silently skipped the whole dict — a false "0 shadowed keys"
    on the very file that has two. Caught 2026-09-20.
    """
    found: list[dict] = []
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if value is None or not isinstance(value, ast.Dict):
            continue
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if "BUILDERS_PRESETS" not in names:
            continue
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                found.append({"id": key.value, "line": key.lineno})
    return found


def _post_hoc_assignments(tree: ast.AST) -> list[dict]:
    """Every `BUILDERS_PRESETS["id"] = {...}` assignment (overwrites silently)."""
    found: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Subscript):
            continue
        base = tgt.value
        if not (isinstance(base, ast.Name) and base.id == "BUILDERS_PRESETS"):
            continue
        sl = tgt.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            found.append({"id": sl.value, "line": node.lineno})
    return found


def _load_presets():
    """Import presets.py standalone (it has no module-level bpy imports)."""
    spec = importlib.util.spec_from_file_location("_mi_presets", PRESETS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def audit() -> dict:
    report: dict = {
        "path": str(PRESETS_PATH),
        "shadowed_keys": [],
        "post_hoc_overwrites": [],
        "builder_count": 0,
        "preset_count": 0,
        "brands": [],
        "brand_orphans": [],
    }
    if not PRESETS_PATH.is_file():
        report["error"] = f"presets.py not found at {PRESETS_PATH}"
        return report

    tree = ast.parse(PRESETS_PATH.read_text(encoding="utf-8"))
    seen: dict[str, int] = {}
    for entry in _dict_literal_keys(tree):
        bid, line = entry["id"], entry["line"]
        if bid in seen:
            report["shadowed_keys"].append(
                {"id": bid, "first_line": seen[bid], "shadowed_by_line": line}
            )
        else:
            seen[bid] = line

    assigned: dict[str, list[int]] = {}
    for entry in _post_hoc_assignments(tree):
        assigned.setdefault(entry["id"], []).append(entry["line"])
    for bid, lines in assigned.items():
        if len(lines) > 1:
            report["post_hoc_overwrites"].append({"id": bid, "lines": lines})

    try:
        mod = _load_presets()
    except Exception as exc:
        report["error"] = f"import failed: {type(exc).__name__}: {exc}"
        return report

    lib = getattr(mod, "BUILDERS_PRESETS", {})
    report["builder_count"] = len(lib)
    report["preset_count"] = sum(len(e.get("presets", {})) for e in lib.values())

    for brand_id, brand in (getattr(mod, "BRANDS", {}) or {}).items():
        for pack_id, pack in (brand.get("packs") or {}).items():
            refs = pack.get("refs") or []
            resolved = 0
            pending = 0
            for ref in refs:
                bid = ref.get("builder")
                pname = ref.get("preset")
                if ref.get("pending"):
                    pending += 1
                    continue
                entry = lib.get(bid)
                if entry is None:
                    report["brand_orphans"].append(
                        {"brand": brand_id, "pack": pack_id, "builder": bid,
                         "preset": pname, "reason": "builder has no preset entry"}
                    )
                    continue
                if pname not in entry.get("presets", {}):
                    report["brand_orphans"].append(
                        {"brand": brand_id, "pack": pack_id, "builder": bid,
                         "preset": pname, "reason": "preset not defined for builder"}
                    )
                    continue
                resolved += 1
            report["brands"].append(
                {"brand": brand_id, "pack": pack_id,
                 "label": pack.get("label", pack_id),
                 "refs": len(refs), "resolved": resolved, "pending": pending}
            )
    return report


def main(argv: list[str]) -> int:
    report = audit()
    if "--json" in argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"[Maison Impossible / preset audit] {report['path']}")
        if report.get("error"):
            print(f"  ERROR: {report['error']}")
            return 1
        print(f"  builders with presets: {report['builder_count']}")
        print(f"  total presets: {report['preset_count']}")
        shadowed = report["shadowed_keys"]
        print(f"  SHADOWED keys (dead data): {len(shadowed)}")
        for s in shadowed:
            print(f"    {s['id']}: defined line {s['first_line']}, "
                  f"silently REPLACED by line {s['shadowed_by_line']}")
        overwritten = report["post_hoc_overwrites"]
        if overwritten:
            print(f"  post-hoc overwrites: {len(overwritten)}")
            for o in overwritten:
                print(f"    {o['id']}: assigned at {o['lines']}")
        print(f"  brand packs: {len(report['brands'])}")
        for b in report["brands"]:
            pend = f", {b['pending']} pending" if b["pending"] else ""
            print(f"    {b['brand']}/{b['pack']} ({b['label']}): "
                  f"{b['resolved']}/{b['refs']} refs resolved{pend}")
        orphans = report["brand_orphans"]
        print(f"  brand ORPHANS: {len(orphans)}")
        for o in orphans:
            print(f"    {o['brand']}/{o['pack']}: {o['builder']} "
                  f"-> {o['preset']} ({o['reason']})")

    failed = bool(report.get("error") or report["shadowed_keys"]
                  or report["brand_orphans"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

