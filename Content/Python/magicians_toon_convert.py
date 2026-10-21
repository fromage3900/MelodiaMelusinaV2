"""magicians_toon_convert.py — bring pack meshes onto the Universal toon master.

Creates one material instance per mesh, parented to M_Master_Toon_Universal, with
the pack's own Base/Normal/AO textures bound, and assigns it to the mesh slot.
Mirrors the house pattern verified on MI_M_Box (2026-08-14 route_library_mi_textures):
    Albedo   -> T_<stem>_Base
    NormalMap-> T_<stem>_Normal
    ORM      -> T_<stem>_AO   (or _OcclusionRoughnessMetallic / _ORM)
    RoughnessMap/MetallicMap/HeightMap/EmissiveMap -> neutral utility maps
    LayerA_TextureWeight = 1.0

Texture matching is fuzzy: the pack has real quirks (T_Polygotn2_* for Polygon2,
T_GlassBottle6_OcclusionRoughnessMetallic instead of _AO, Floor1F holding nine
meshes in one folder).

Modes (arg 1, default "plan"):
    plan     - report only, no mutation
    apply   - create MIs, assign slots, save
    save    - create MIs, assign slots, save, and resave the touched meshes

Usage: run via Monolith editor_query run_python (execute_file) with this path,
optionally followed by " apply".
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_toon_convert.json"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
NEUTRAL = "/Game/EnvSandbox/Textures/Utility"
ROOTS = [
    "/Game/MagicianLabatory/Source/Building",
    "/Game/MagicianLabatory/Source/Props",
]
SKIP_FOLDERS = ("/BP/", "/Map/", "/Demo/")

ROLE_SUFFIX = {
    "base": ("_base", "_basecolor", "_albedo", "_diffuse", "_color"),
    "normal": ("_normal", "_norm", "_normalmap"),
    "ao": ("_ao", "_orm", "_occlusionroughnessmetallic", "_ambientocclusion"),
}

# Meshes whose texture set is named after a sibling, not after themselves.
# SM_Wick is the candle wick and ships inside Props/Candle with T_Candle_*.
TEXTURE_SET_OVERRIDE = {
    "SM_Wick": "Candle",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def role_of(texture_name: str):
    n = texture_name.lower()
    for role, suffixes in ROLE_SUFFIX.items():
        for suf in suffixes:
            if n.endswith(suf):
                return role
    return None


def core_name(texture_name: str):
    """'T_Floor_1_Base' -> 'Floor_1'   (role suffix + T_ prefix stripped)."""
    core = texture_name
    role = role_of(core)
    if role:
        for suf in ROLE_SUFFIX[role]:
            if core.lower().endswith(suf):
                core = core[: -len(suf)]
                break
    if core[:2].upper() == "T_":
        core = core[2:]
    return core


def find_textures(folder: str, stem: str):
    """-> {role: texture path}. Exact core-name match first, fuzzy only as fallback.

    The pack has real naming quirks the fuzzy path must survive:
      T_Polygotn2_Base      (typo for Polygon2)
      T_GlassBottle6_OcclusionRoughnessMetallic   (ORM instead of _AO)
    """
    pool = []
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        role = role_of(name)
        if role:
            pool.append((role, core_name(name), name, p))
    if not pool:
        return {}
    target = norm(stem)
    out = {}
    for role in ("base", "normal", "ao"):
        cands = [c for c in pool if c[0] == role]
        if not cands:
            continue
        exact = [c for c in cands if norm(c[1]) == target]
        if exact:
            out[role] = exact[0][3]
            continue
        # prefix rule: 'Roof_WindowBar_DefaultMaterial' belongs to 'Roof_WindowBar'
        pref = [c for c in cands if norm(c[1]).startswith(target)]
        if len(pref) == 1:
            out[role] = pref[0][3]
            continue
        scored = sorted(
            ((difflib.SequenceMatcher(None, target, norm(c[1])).ratio(), c) for c in cands),
            key=lambda x: -x[0])
        if not scored:
            continue
        best_score, best = scored[0]
        runner_up = scored[1][0] if len(scored) > 1 else 0.0
        if best_score >= 0.75 and best_score - runner_up >= 0.05:
            out[role] = best[3]
    return out


def make_mi_name(mesh_name: str) -> str:
    stem = mesh_name[3:] if mesh_name.startswith("SM_") else mesh_name
    return "MI_M_" + stem


def mi_set_texture(mi, param, texture_path):
    if not texture_path:
        return False
    tex = unreal.load_asset(texture_path)
    if tex is None:
        return False
    try:
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, param, tex)
        return True
    except Exception:
        return False


def build_mi(mi_path, folder, stem, textures):
    """Create (or fetch) the MI and bind textures. -> dict"""
    existing = unreal.load_asset(mi_path)
    if existing is None:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            mi_path.rsplit("/", 1)[-1], folder, unreal.MaterialInstanceConstant, factory)
        if mi is None:
            return {"status": "create_failed"}
        mi.set_editor_property("parent", unreal.load_asset(MASTER))
    else:
        mi = existing
        if mi.get_editor_property("parent").get_path_name() != MASTER:
            mi.set_editor_property("parent", unreal.load_asset(MASTER))

    bound = {}
    for param, role in (("Albedo", "base"), ("NormalMap", "normal"), ("ORM", "ao")):
        if mi_set_texture(mi, param, textures.get(role)):
            bound[param] = role
    for param, tex in (
            ("RoughnessMap", NEUTRAL + "/T_Neutral_Roughness"),
            ("MetallicMap", NEUTRAL + "/T_Neutral_Metallic"),
            ("HeightMap", NEUTRAL + "/T_Neutral_Height")):
        mi_set_texture(mi, param, tex)
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "LayerA_TextureWeight", 1.0)
    except Exception:
        pass
    return {"status": "ok", "bound": bound, "mi": mi_path}


def set_slot(mesh, mi):
    slots = list(mesh.get_editor_property("static_materials") or [])
    changed = False
    for i, s in enumerate(slots):
        cur = s.get_editor_property("material_interface")
        if cur is None or cur.get_path_name() == mi.get_path_name():
            continue
        s.set_editor_property("material_interface", mi)
        changed = True
    if changed:
        mesh.set_editor_property("static_materials", slots)
    return changed


def main() -> int:
    mode = "plan"
    if len(sys.argv) > 1:
        mode = sys.argv[1].strip().lower()
    if mode not in ("plan", "apply", "save"):
        mode = "plan"
    # optional "start:end" slice over the sorted mesh list, for chunked runs
    lo, hi = 0, 10 ** 9
    if len(sys.argv) > 2 and ":" in sys.argv[2]:
        try:
            a, b = sys.argv[2].split(":")
            lo, hi = int(a), int(b)
        except ValueError:
            lo, hi = 0, 10 ** 9

    rows = []
    counters = Counter()
    targets = []
    for root in ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            counters["root_missing"] += 1
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if any(s in p for s in SKIP_FOLDERS):
                continue
            name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if not (name.startswith("SM_") or name == "candle1_L"):
                continue
            targets.append(p)
    targets.sort()
    targets = targets[lo:hi]

    for p in targets:
            name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            folder = "/".join(p.split("/")[:-1])
            stem = name[3:] if name.startswith("SM_") else name
            mi_name = make_mi_name(name)
            mi_path = "%s/%s" % (folder, mi_name)
            textures = find_textures(folder, TEXTURE_SET_OVERRIDE.get(name, stem))
            has_all = all(k in textures for k in ("base", "normal"))
            row = {"mesh": p, "folder": folder, "mi": mi_path,
                   "textures": textures, "has_base_normal": has_all}
            if mode != "plan":
                mesh = unreal.load_asset(p)
                if mesh is None:
                    row["result"] = "mesh_load_failed"
                    counters["mesh_load_failed"] += 1
                    rows.append(row)
                    continue
                res = build_mi(mi_path, folder, stem, textures)
                row["result"] = res.get("status")
                row["bound"] = res.get("bound")
                if res.get("status") == "ok":
                    mi = unreal.load_asset(mi_path)
                    changed = set_slot(mesh, mi)
                    row["slot_changed"] = changed
                    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
                    if changed or mode == "save":
                        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
                    counters["created_or_updated"] += 1
                    if not has_all:
                        counters["missing_base_or_normal"] += 1
                else:
                    counters["mi_" + res.get("status", "error")] += 1
            else:
                row["result"] = "planned"
                counters["planned"] += 1
                if not has_all:
                    counters["missing_base_or_normal"] += 1
            rows.append(row)

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "slice": "%d:%d" % (lo, hi),
        "master": MASTER,
        "roots": ROOTS,
        "counters": dict(counters),
        "rows": rows,
    }
    out_path = REPORT if (lo == 0 and hi == 10 ** 9) else REPORT.with_name(
        "magicians_toon_convert_%d_%d.json" % (lo, min(hi, 10 ** 9)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("TOON|%s|%s|%s" % (mode, json.dumps(dict(counters)), out_path.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
