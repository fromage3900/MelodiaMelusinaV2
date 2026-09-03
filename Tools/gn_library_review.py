# -*- coding: utf-8 -*-
"""Closed-editor (or post-construct) review of all Melodia GN builders.

Writes Saved/Audit/gn_review_<stamp>.md + .json with construct, preset,
STUDIO_LABELS, node count, fingerprint, and measured AAA checklist.

  python Tools/gn_library_review.py
  blender --factory-startup -b -P Saved/Audit/_gn_review_headless_2026-08-13.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"
MELODIA = DEPLOY / "surreal_arch" / "melodia_gn"
AUDIT = ROOT / "Saved" / "Audit"
CORE = MELODIA / "core.py"
PRESETS = MELODIA / "presets.py"
HEALTH = AUDIT / "gn_builder_health_last.json"
FINGERPRINT = AUDIT / "gn_fingerprint_baseline_2026-08-13.json"
STAMP = datetime.now().strftime("%Y-%m-%d")

KAWAII_DIR = ROOT / "Tools" / "BlenderAddons" / "blender_kawaii_gn"
BRUTALIST_DIR = ROOT / "Tools" / "BlenderAddons" / "blender_brutalist_gn"

CAT_LABEL = {
    "set_dressing": "Set Dressing",
    "castle": "Castle Kit",
    "music": "Musical Notation",
    "effects": "Magic Effects",
    "primitives": "Primitives",
    "mesh_tools": "Mesh Tools",
    "math_attrs": "Math and Attributes",
    "ornament": "Ornament",
    "profiles": "Profiles",
    "structures": "Structures",
    "filigree": "Filigree and Crests",
    "operations": "Operations",
}


def _parse_studio_labels(text: str) -> dict[str, str]:
    """Map MEL_* tree id -> STUDIO_LABELS key (first wins)."""
    out: dict[str, str] = {}
    current_key = None
    for line in text.splitlines():
        m = re.match(r'\s+"([A-Z0-9_]+)":\s*\{', line)
        if m and "STUDIO_LABELS" not in line:
            current_key = m.group(1)
        t = re.search(r'"mel_tree":\s*"(MEL_[^"]+)"', line)
        if t and current_key:
            out.setdefault(t.group(1), current_key)
            current_key = None
    return out


def _parse_preset_ids(text: str) -> dict[str, int]:
    """Builder id -> number of looks, from BUILDERS_PRESETS keys."""
    counts: dict[str, int] = {}
    current = None
    in_presets = False
    depth = 0
    for line in text.splitlines():
        m = re.match(r'\s+"(MEL_[^"]+)":\s*\{', line)
        if m and not in_presets:
            current = m.group(1)
            continue
        if current and '"presets":' in line and "{" in line:
            in_presets = True
            depth = line.count("{") - line.count("}")
            continue
        if in_presets and current:
            look = re.match(r'\s+"([A-Z0-9_]+)":\s*\{', line)
            if look:
                counts[current] = counts.get(current, 0) + 1
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                in_presets = False
                current = None
    return counts


def _parse_register_meta(path: Path) -> list[tuple[str, str, str]]:
    """(tree_name, label, category) from register_builder calls."""
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    # register_builder("MEL_x", fn, "Label", "...", "cat")
    # or keyword form
    for m in re.finditer(
        r'register_builder\(\s*"([^"]+)"\s*,\s*[^,]+,\s*"([^"]+)"'
        r'(?:\s*,\s*"[^"]*"\s*,\s*"([^"]+)")?',
        text,
    ):
        name, label, cat = m.group(1), m.group(2), m.group(3) or ""
        rows.append((name, label, cat))
    for m in re.finditer(
        r'register_builder\(\s*\n?\s*"([^"]+)"[\s\S]*?category\s*=\s*"([^"]+)"',
        text,
    ):
        name, cat = m.group(1), m.group(2)
        if not any(r[0] == name for r in rows):
            rows.append((name, name, cat))
    return rows


def _generator_ids(root: Path) -> list[str]:
    ids = []
    if not root.is_dir():
        return ids
    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'generator_id\s*=\s*"([^"]+)"', text):
            ids.append(m.group(1))
    return sorted(set(ids))


def load_health() -> dict[str, dict]:
    if not HEALTH.is_file():
        return {}
    data = json.loads(HEALTH.read_text(encoding="utf-8"))
    return {b["name"]: b for b in data.get("builders", [])}


def load_fingerprints() -> dict[str, dict]:
    if not FINGERPRINT.is_file():
        return {}
    data = json.loads(FINGERPRINT.read_text(encoding="utf-8"))
    return {t["name"]: t for t in data.get("trees", [])}


def _load_pure(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_rows() -> list[dict]:
    aaa = _load_pure("melodia_gn_aaa_quality", MELODIA / "aaa_quality.py")
    presets_mod = _load_pure("melodia_gn_presets", MELODIA / "presets.py")
    aaq_quality_checklist = aaa.aaq_quality_checklist
    BUILDERS_PRESETS = presets_mod.BUILDERS_PRESETS

    labels = _parse_studio_labels(CORE.read_text(encoding="utf-8", errors="replace"))
    health = load_health()
    fps = load_fingerprints()

    builders = {}
    for py in MELODIA.glob("*.py"):
        if py.name in ("__init__.py", "core.py", "stack.py", "bake.py",
                       "presets.py", "aaa_quality.py", "logging.py"):
            continue
        for name, label, cat in _parse_register_meta(py):
            builders[name] = {"label": label, "category": cat, "module": py.name}

    # Prefer live health (authoritative 165 + categories + node counts)
    if health:
        for name, rec in health.items():
            builders.setdefault(name, {})
            builders[name]["label"] = rec.get("label", builders[name].get("label", name))
            builders[name]["category"] = rec.get("category", builders[name].get("category", ""))
            builders[name]["nodes"] = rec.get("nodes")
            builders[name]["links"] = rec.get("links")
            builders[name]["construct"] = rec.get("status") == "pass"

    rows = []
    for name in sorted(builders):
        meta = builders[name]
        has_preset = name in BUILDERS_PRESETS and bool(BUILDERS_PRESETS[name].get("presets"))
        look_count = len(BUILDERS_PRESETS[name]["presets"]) if has_preset else 0
        has_label = name in labels
        has_fp = name in fps
        construct = meta.get("construct")
        if construct is None and name in health:
            construct = health[name].get("status") == "pass"
        node_count = meta.get("nodes")
        measured = {
            "construct": construct,
            "has_preset": has_preset,
            "has_label": has_label,
            "node_count": node_count,
            "has_fingerprint": has_fp,
        }
        checklist = aaq_quality_checklist(name, measured)
        open_gates = [
            g for g, info in checklist["gates"].items()
            if info.get("status") == "OPEN"
        ]
        rows.append({
            "name": name,
            "label": meta.get("label", name),
            "category": meta.get("category", ""),
            "category_label": CAT_LABEL.get(meta.get("category", ""), meta.get("category", "")),
            "construct": bool(construct) if construct is not None else None,
            "has_preset": has_preset,
            "preset_looks": look_count,
            "has_label": has_label,
            "studio_label_key": labels.get(name),
            "node_count": node_count,
            "link_count": meta.get("links"),
            "has_fingerprint": has_fp,
            "fingerprint_sha256": fps.get(name, {}).get("sha256"),
            "quality_gates_open": open_gates,
            "quality_checklist": checklist,
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    cats = Counter(r["category_label"] or r["category"] for r in rows)
    preset_cats = Counter(
        r["category_label"] or r["category"] for r in rows if r["has_preset"]
    )
    labeled = sum(1 for r in rows if r["has_label"])
    preset_n = sum(1 for r in rows if r["has_preset"])
    looks = sum(r["preset_looks"] for r in rows)
    construct_yes = sum(1 for r in rows if r["construct"] is True)
    construct_no = sum(1 for r in rows if r["construct"] is False)
    fp_n = sum(1 for r in rows if r["has_fingerprint"])
    nodes = [r["node_count"] for r in rows if isinstance(r["node_count"], int)]
    kawaii = _generator_ids(KAWAII_DIR)
    brutalist = _generator_ids(BRUTALIST_DIR)
    return {
        "date": STAMP,
        "registry_count": len(rows),
        "construct_pass": construct_yes,
        "construct_fail": construct_no,
        "preset_builders": preset_n,
        "preset_looks": looks,
        "preset_coverage": round(preset_n / len(rows), 4) if rows else 0,
        "studio_labels": labeled,
        "label_coverage": round(labeled / len(rows), 4) if rows else 0,
        "fingerprints": fp_n,
        "categories": dict(cats),
        "preset_by_category": dict(preset_cats),
        "node_min": min(nodes) if nodes else None,
        "node_max": max(nodes) if nodes else None,
        "node_median": sorted(nodes)[len(nodes) // 2] if nodes else None,
        "out_of_registry": {
            "kawaii_gn": {
                "path": "Tools/BlenderAddons/blender_kawaii_gn",
                "unique_generator_ids": len(kawaii),
                "ids": kawaii,
                "merged_into_GROUP_BUILDERS": False,
            },
            "brutalist_gn": {
                "path": "Tools/BlenderAddons/blender_brutalist_gn",
                "unique_generator_ids": len(brutalist),
                "ids": brutalist,
                "merged_into_GROUP_BUILDERS": False,
            },
        },
        "new_builders_this_pass": 0,
    }


def write_markdown(rows: list[dict], summary: dict, path: Path) -> None:
    lines = [
        f"# Melodia GN builder review - {summary['date']}",
        "",
        "Thesis: **stop adding Set Dressing volume.** Quality and thin-kit depth.",
        "Kawaii and Brutalist stay **standalone** (out of `GROUP_BUILDERS`).",
        "Zero new builders this pass.",
        "",
        f"- Registry: **{summary['registry_count']}**",
        f"- Construct: **{summary['construct_pass']} pass** / {summary['construct_fail']} fail",
        f"- Presets: **{summary['preset_builders']} / {summary['registry_count']}** "
        f"({summary['preset_coverage']*100:.1f}%), {summary['preset_looks']} looks",
        f"- STUDIO_LABELS: **{summary['studio_labels']} / {summary['registry_count']}** "
        f"({summary['label_coverage']*100:.1f}%)",
        f"- Fingerprints: **{summary['fingerprints']}** (12-tree heavy baseline)",
        f"- Node count: min {summary['node_min']} - median {summary['node_median']} - max {summary['node_max']}",
        "",
        "## Out of registry (do not merge)",
        "",
        f"- Kawaii GN: {summary['out_of_registry']['kawaii_gn']['unique_generator_ids']} unique ids - "
        f"`{summary['out_of_registry']['kawaii_gn']['path']}`",
        f"- Brutalist GN: {summary['out_of_registry']['brutalist_gn']['unique_generator_ids']} unique ids - "
        f"`{summary['out_of_registry']['brutalist_gn']['path']}`",
        "",
        "## Category mix",
        "",
        "| Category | Live | Presets | Labels |",
        "|----------|-----:|--------:|-------:|",
    ]
    for cat, n in sorted(summary["categories"].items(), key=lambda kv: (-kv[1], kv[0])):
        p = summary["preset_by_category"].get(cat, 0)
        lab = sum(1 for r in rows if (r["category_label"] or r["category"]) == cat and r["has_label"])
        lines.append(f"| {cat} | {n} | {p} | {lab} |")
    lines += [
        "",
        "## AAA quality gates",
        "",
        "`aaq_quality_checklist` now reads measured construct / preset / label / "
        "node count / fingerprint. Mesh, parameter-variety, output, pipeline, and "
        "cross-builder-consistency stay **OPEN** (unmeasured).",
        "",
        "## All builders",
        "",
        "| Builder | Category | Construct | Preset | Label | Nodes | Fingerprint | Open gates |",
        "|---------|----------|:---------:|:------:|:-----:|------:|:-----------:|------------|",
    ]
    for r in rows:
        cons = "yes" if r["construct"] else ("no" if r["construct"] is False else "?")
        preset = f"yes ({r['preset_looks']})" if r["has_preset"] else "no"
        label = "yes" if r["has_label"] else "no"
        nodes = r["node_count"] if r["node_count"] is not None else "-"
        fp = "yes" if r["has_fingerprint"] else "no"
        open_s = ", ".join(r["quality_gates_open"]) if r["quality_gates_open"] else "-"
        lines.append(
            f"| `{r['name']}` | {r['category_label'] or r['category']} | {cons} | "
            f"{preset} | {label} | {nodes} | {fp} | {open_s} |"
        )
    lines += ["", f"JSON: `{path.with_suffix('.json').name}`", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    summary = summarize(rows)
    payload = {"summary": summary, "builders": rows}
    json_path = AUDIT / f"gn_review_{STAMP}.json"
    md_path = AUDIT / f"gn_review_{STAMP}.md"
    # Keep a stable filename for this session as requested.
    json_path_fixed = AUDIT / "gn_review_2026-08-13.json"
    md_path_fixed = AUDIT / "gn_review_2026-08-13.md"
    json_path_fixed.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    write_markdown(rows, summary, md_path_fixed)
    print(f"Wrote {md_path_fixed}")
    print(f"Wrote {json_path_fixed}")
    print(
        f"builders={summary['registry_count']} presets={summary['preset_builders']} "
        f"labels={summary['studio_labels']} fingerprints={summary['fingerprints']}"
    )


if __name__ == "__main__":
    main()
