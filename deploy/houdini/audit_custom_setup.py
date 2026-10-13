#!/usr/bin/env python3
"""Read-only inventory of local Houdini customization for Grandmaster Studio.

Compatible with normal Python (filesystem inventory) and Hython (live Houdini
package/shelf/HDA discovery). No preference, package, desktop, HDA, or HIP edits.
The generated report is intended to stay LOCAL: it may contain workstation
paths and names of private work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM_SUFFIXES = frozenset((".hda", ".hdalc", ".hdanc", ".hip", ".hiplc", ".hipnc", ".desk", ".shelf"))
SCRIPT_SUFFIXES = frozenset((".py", ".pyc", ".vfl", ".vex"))
SEARCH_DIRS = (
    "hda", "HDA", "otls", "OTLS", "hip", "HIP", "scenes", "Scenes",
    "desktop", "toolbar", "scripts", "Tools/Houdini", "houdini/otls",
)
SKIP_DIRS = frozenset((".git", "Binaries", "Intermediate", "__pycache__", ".venv", "node_modules", "DerivedDataCache"))
MAX_TOTAL = 300
MAX_DEPTH = 5


def safe_str(path: Path) -> str:
    return str(path.resolve())


def sha256(path: Path) -> str | None:
    try:
        if path.stat().st_size > 32 * 1024 * 1024:
            return None
        with path.open("rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def find_local_files(root: Path, max_files: int = MAX_TOTAL) -> list[dict]:
    """Bounded targeted scan: never traverses UE Content/, caches or all drives."""
    found: list[dict] = []
    seen: set[str] = set()
    folders = [root / rel for rel in SEARCH_DIRS]
    folders.append(root)  # root-level HIP/HDA/shelves
    for folder in folders:
        if not folder.is_dir():
            continue
        for current, dirs, files in os.walk(folder, followlinks=False):
            current_path = Path(current)
            depth = len(current_path.relative_to(folder).parts)
            dirs[:] = [] if folder == root or depth >= MAX_DEPTH else [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for filename in sorted(files):
                path = current_path / filename
                ext = path.suffix.lower()
                if ext not in CUSTOM_SUFFIXES and not (ext in SCRIPT_SUFFIXES and depth <= 2):
                    continue
                key = os.path.normcase(str(path.absolute()))
                if key in seen:
                    continue
                seen.add(key)
                found.append({
                    "kind": "hda" if ext in (".hda", ".hdalc", ".hdanc") else
                            "hip" if ext in (".hip", ".hiplc", ".hipnc") else
                            "desktop" if ext == ".desk" else
                            "shelf" if ext == ".shelf" else "script",
                    "path": safe_str(path),
                    "relative": path.relative_to(root).as_posix(),
                    "sha256": sha256(path) if ext in (".hda", ".hdalc", ".hdanc", ".desk", ".shelf") else None,
                })
                if len(found) >= max_files:
                    return found
    return found


def package_info(pref: Path | None) -> list[dict]:
    """Package names and path references only; never report env values or secrets."""
    if not pref:
        return []
    folder = pref / "packages"
    if not folder.is_dir():
        return []
    rows = []
    for file in sorted(folder.glob("*.json")):
        info = {"file": file.name, "path": safe_str(file)}
        try:
            data = json.loads(file.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
            info["package_path"] = data.get("package_path")
            info["hpath"] = data.get("hpath")
            info["env_keys"] = [
                k for ent in data.get("env", []) if isinstance(ent, dict) for k in ent.keys()
            ] if isinstance(data.get("env", []), list) else []
        except (OSError, ValueError, TypeError) as exc:
            info["parse_warning"] = str(exc)
        rows.append(info)
    return rows


def collect_hou(report: dict) -> None:
    """Only read HOM discovery APIs. Never install/override assets or change UI."""
    try:
        import hou
    except ImportError:
        report["houdini"] = {"available": False, "note": "use hython for live discovery"}
        return
    info = {"available": True, "version": hou.applicationVersionString()}
    try:
        info["license_category"] = hou.licenseCategory().name()
    except (AttributeError, hou.Error):
        info["license_category"] = "unknown"
    try:
        pref = Path(hou.homeHoudiniDirectory())
        info["user_pref_dir"] = safe_str(pref)
        report["packages"] = package_info(pref)
        for filetype in ("desktop", "toolbar"):
            d = pref / filetype
            info[f"user_{filetype}_files"] = sorted(str(p) for p in d.glob("*.desk" if filetype == "desktop" else "*.shelf")) if d.is_dir() else []
        desktop_report = {}
        for name in ("Melodia_Studio", "Melodia_KineFX"):
            local = pref / "desktop" / f"{name}.desk"
            expected = ROOT / "deploy" / "houdini" / "melodia_studio" / "desktop" / f"{name}.desk"
            try:
                resolved = hou.findFile(f"desktop/{name}.desk")
            except hou.Error:
                resolved = ""
            desktop_report[name] = {
                "resolved": resolved,
                "user_local_same_name": local.is_file(),
                "repo_backed": expected.is_file(),
                "local_sha256": sha256(local) if local.is_file() else None,
                "repo_sha256": sha256(expected) if expected.is_file() else None,
            }
        info["desktop_resolution"] = desktop_report
        report["warnings"].extend(
            f"Desktop shadow candidate: user-local {name}.desk; inspect before replacing or saving."
            for name, data in desktop_report.items() if data["user_local_same_name"]
        )
    except (OSError, AttributeError, hou.Error) as exc:
        info["pref_probe_warning"] = str(exc)
    try:
        registered = hou.shelves.shelves()
        info["shelf_names"] = sorted(registered.keys() if isinstance(registered, dict) else
                                     (x if isinstance(x, str) else x.name() for x in registered))
    except (AttributeError, hou.Error) as exc:
        info["shelf_probe_warning"] = str(exc)
    try:
        loaded = [p for p in hou.hda.loadedFiles() if "melodia" in str(p).lower() or "foundry" in str(p).lower()]
        info["loaded_melodia_hda_paths"] = sorted(loaded)[:100]
    except (AttributeError, hou.Error) as exc:
        info["hda_probe_warning"] = str(exc)
    report["houdini"] = info


def build_report(roots: list[Path]) -> dict:
    report = {
        "schema": "melodia.houdini_custom_setup_inventory.v1",
        "mode": "READ_ONLY",
        "repo_root": safe_str(ROOT),
        "custom_roots": [],
        "packages": [],
        "houdini": {"available": False},
        "warnings": [],
        "rules": [
            "Inventory only: never copy local settings into the repo.",
            "Duplicate HDA basenames with differing hashes require explicit artist selection.",
            "Never install user-local HDAs or load user-local HIPs automatically.",
            "Never replace an existing desktop/shelf/houdini.env or modify the user's open Houdini scene.",
        ],
    }
    canonical = ROOT / "hda"
    canonical_assets = {p.name.lower(): (safe_str(p), sha256(p)) for p in canonical.glob("*.hda*")} if canonical.is_dir() else {}
    inventory: list[dict] = []
    for root in roots:
        if not root.is_dir():
            report["warnings"].append(f"Custom root does not exist: {root}")
            continue
        items = find_local_files(root)
        report["custom_roots"].append({"path": safe_str(root), "files": items, "truncated": len(items) >= MAX_TOTAL})
        inventory.extend(items)
    for item in inventory:
        if item["kind"] != "hda":
            continue
        canonical_match = canonical_assets.get(Path(item["path"]).name.lower())
        if canonical_match and os.path.normcase(canonical_match[0]) != os.path.normcase(item["path"]):
            if canonical_match[1] == item["sha256"] and item["sha256"]:
                item["canonical_relation"] = "byte_identical"
            else:
                item["canonical_relation"] = "DIFFERENT_OR_UNVERIFIED"
                report["warnings"].append(f"Review custom-vs-canonical HDA: {item['relative']} (do not auto-install)")
    by_name: dict[str, list[dict]] = defaultdict(list)
    for item in inventory:
        if item["kind"] == "hda":
            by_name[Path(item["path"]).name.lower()].append(item)
    for name, matches in by_name.items():
        if len(set(x["sha256"] for x in matches)) > 1:
            report["warnings"].append(f"Multiple non-identical custom HDAs named {name}; choose manually")
    collect_hou(report)
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scan-root", action="append", type=Path, default=[],
                    help="additional existing custom Houdini workspaces; repeat as needed")
    ap.add_argument("--out", type=Path, help="optional LOCAL JSON report, never committed automatically")
    args = ap.parse_args(argv)
    roots = []
    for root in args.scan_root:
        norm = root.expanduser().resolve()
        if norm not in roots:
            roots.append(norm)
    report = build_report(roots)
    if args.out:
        out = args.out.expanduser().resolve()
        if out.exists():
            ap.error(f"Refusing to overwrite existing report: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Local inventory written to {out}")
    print("Houdini live:", report["houdini"]["available"],
          "| scanned roots:", len(report["custom_roots"]),
          "| custom files:", sum(len(x["files"]) for x in report["custom_roots"]),
          "| warnings:", len(report["warnings"]))
    for warning in report["warnings"][:25]:
        print("WARN:", warning)
    if not args.out:
        print("Tip: add --out Saved/Audit/houdini_studio/custom_setup_local.json to keep a local-only report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
