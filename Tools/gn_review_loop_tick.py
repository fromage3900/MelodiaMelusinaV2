# -*- coding: utf-8 -*-
"""One tick of the Melodia GN / ornament pipeline review loop.

  python Tools/gn_review_loop_tick.py [--scope melodia_gn|arch_types|pipelines]

Writes Saved/Audit/gn_review_loop/tick_NNN.json and updates gn_review_latest.json.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "Saved" / "Audit" / "gn_review_loop"
LATEST = ROOT / "Saved" / "Audit" / "gn_review_latest.json"
MELODIA_GN = ROOT / "deploy" / "surreal_arch" / "melodia_gn"
PIPELINES = ROOT / "my-site-clean" / "generated" / "geometry_nodes_pipelines.json"
CORE = MELODIA_GN / "core.py"

SCOPES = ("melodia_gn", "arch_types", "pipelines")
FIX_ARCH_TYPES = (
    "TORUS_KNOT_ORNAMENT",
    "FILIGREE_PANEL",
    "CORNICE",
    "ROSE_WINDOW",
    "BAROQUE_VAULT",
    "CUSPED_ARCH",
    "STAIRCASE",
    "TREBLE_CLEF",
)


def _next_tick() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    nums = []
    for p in AUDIT_DIR.glob("tick_*.json"):
        m = re.match(r"tick_(\d+)\.json$", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def _pick_scope(explicit: str | None, tick: int) -> str:
    if explicit in SCOPES:
        return explicit
    return SCOPES[(tick - 1) % len(SCOPES)]


def _scan_legacy_inputs(paths: list[Path]) -> list[dict]:
    hits = []
    pat = re.compile(r"tree\.inputs(?:\.new|\b)|tree\.outputs\.new")
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line) and "interface" not in line and "legacy" not in line.lower():
                # allow comments documenting the old API
                if line.strip().startswith("#") or '"""' in line or "removed tree.inputs" in line:
                    continue
                if "Yield input interface" in line:
                    continue
                hits.append({"file": str(path.relative_to(ROOT)), "line": i, "text": line.strip()[:160]})
    return hits


def _audit_melodia_gn() -> dict:
    modules = sorted(p.name for p in MELODIA_GN.glob("*.py") if p.name != "__init__.py")
    tree_types = []
    core_text = CORE.read_text(encoding="utf-8", errors="replace") if CORE.is_file() else ""
    in_list = False
    for line in core_text.splitlines():
        if "TREE_TYPES" in line and "=" in line:
            in_list = True
            continue
        if in_list:
            if line.strip().startswith("]"):
                break
            m = re.search(r'\("([^"]+)"\s*,\s*"([^"]+)"\)', line)
            if m:
                tree_types.append({"id": m.group(1), "label": m.group(2)})
    py_files = list(MELODIA_GN.glob("*.py"))
    legacy = _scan_legacy_inputs(py_files)
    interface_guard = "def make_group_input" in core_text and "tree.interface" in core_text
    return {
        "modules": modules,
        "tree_types_count": len(tree_types),
        "tree_types_sample": tree_types[:12],
        "interface_api_guard": interface_guard,
        "legacy_inputs_hits": legacy,
        "flags": []
        if interface_guard and not legacy
        else (["missing_interface_guard"] if not interface_guard else [])
        + ([f"legacy_inputs:{len(legacy)}"] if legacy else []),
    }


def _audit_arch_types() -> dict:
    # Search SurrealArch sources for fix-list builders
    roots = [
        ROOT / "deploy" / "surreal_architecture_gen.py",
        ROOT / "deploy" / "surreal_arch",
    ]
    found: dict[str, list[str]] = {k: [] for k in FIX_ARCH_TYPES}
    for root in roots:
        paths = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in paths:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(ROOT))
            for key in FIX_ARCH_TYPES:
                if key in text:
                    found[key].append(rel)
    missing = [k for k, v in found.items() if not v]
    return {
        "fix_arch_types": FIX_ARCH_TYPES,
        "locations": {k: sorted(set(v))[:5] for k, v in found.items()},
        "missing": missing,
        "flags": [f"missing_arch:{m}" for m in missing],
    }


def _audit_pipelines() -> dict:
    data = json.loads(PIPELINES.read_text(encoding="utf-8"))
    meshes = data.get("musical_meshes") or []
    statuses = {m.get("asset"): m.get("status") for m in meshes if isinstance(m, dict)}
    hand = [a for a, s in statuses.items() if s == "hand_remake"]
    tokens = [a for a, s in statuses.items() if s == "placeholder" or (a and "MelodyToken" in a)]
    flags = []
    if len(meshes) != 10:
        flags.append(f"musical_meshes_count:{len(meshes)}!=10")
    if "SM_Orn_TrebleClef" not in hand or "SM_Orn_MusicalCorner" not in hand:
        flags.append("hand_remake_incomplete")
    if len(tokens) < 3:
        flags.append("melody_tokens_incomplete")
    note = data.get("note") or ""
    if "10" not in note and "Melody Token" not in note:
        flags.append("note_stale")
    return {
        "musical_mesh_count": len(meshes),
        "statuses": statuses,
        "hand_remake": hand,
        "tokens": tokens,
        "lane_summary": next(
            (L.get("summary") for L in data.get("lanes") or [] if L.get("id") == "melody-musical-gn"),
            None,
        ),
        "flags": flags,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=SCOPES, default=None)
    args = ap.parse_args()
    tick = _next_tick()
    scope = _pick_scope(args.scope, tick)
    ts = datetime.now(timezone.utc).isoformat()

    if scope == "melodia_gn":
        body = _audit_melodia_gn()
    elif scope == "arch_types":
        body = _audit_arch_types()
    else:
        body = _audit_pipelines()

    payload = {
        "tick": tick,
        "scope": scope,
        "generated_at": ts,
        "result": body,
        "ok": not bool(body.get("flags")),
    }
    out = AUDIT_DIR / f"tick_{tick:03d}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    history = []
    if LATEST.is_file():
        try:
            prev = json.loads(LATEST.read_text(encoding="utf-8"))
            history = list(prev.get("history") or [])[-20:]
        except Exception:
            history = []
    history.append({"tick": tick, "scope": scope, "ok": payload["ok"], "flags": body.get("flags") or []})
    latest = {
        "updated_at": ts,
        "latest_tick": tick,
        "latest_scope": scope,
        "latest_ok": payload["ok"],
        "latest_flags": body.get("flags") or [],
        "next_scope": SCOPES[tick % len(SCOPES)],
        "history": history,
        "tick_path": str(out),
    }
    LATEST.parent.mkdir(parents=True, exist_ok=True)
    LATEST.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print(json.dumps({"tick": tick, "scope": scope, "ok": payload["ok"], "flags": body.get("flags") or [], "path": str(out)}, indent=2))


if __name__ == "__main__":
    main()
