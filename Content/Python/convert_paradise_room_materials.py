"""
Convert Paradise room (Rooms_Paradise_*) material instances to Melodia masters.

Editor-bound: run via Tools/editor_run.py (Monolith editor_query run_python).
--dry-run inventories without editing.

Paradise_MATS mapping (from fix_library_paradise.py):
  Atlas_01_Mat      -> T_Atlas_01_Albedo
  Atlas_01_Trans_Mat-> T_Atlas_01_Trans
  Outliner_Mat      -> T_Atlas_01_Albedo
  Shadows_Mat       -> T_Seam_Shadows_01
  Seam_Floor_Mat    -> T_Seam_Floor_Albedo
  Seam_Sand_Mat     -> T_Seam_Sand_Albedo

Texture source: /Game/EnvSandbox/Textures/CrystalCrossroads/<TexName>

Output: Saved/Audit/paradise_room_conversion_run.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "paradise_room_conversion_run.json"

ENV_ROOT = "/Game/EnvSandbox/Meshes/Environment"
AVATAR_MAT_DIR = f"{ENV_ROOT}/AvatarGarden/Materials"
TEX_CR = "/Game/EnvSandbox/Textures/CrystalCrossroads"
MASTER_UNIVERSAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

PARADISE_MATS = {
    "Atlas_01_Mat":        "T_Atlas_01_Albedo",
    "Atlas_01_Trans_Mat":  "T_Atlas_01_Trans",
    "Outliner_Mat":        "T_Atlas_01_Albedo",
    "Shadows_Mat":         "T_Seam_Shadows_01",
    "Seam_Floor_Mat":      "T_Seam_Floor_Albedo",
    "Seam_Sand_Mat":       "T_Seam_Sand_Albedo",
}

PARADISE_TEX = {
    "T_Atlas_01_Albedo":   f"{TEX_CR}/T_Atlas_01_Albedo",
    "T_Atlas_01_Trans":    f"{TEX_CR}/T_Atlas_01_Trans",
    "T_Seam_Floor_Albedo": f"{TEX_CR}/T_Seam_Floor_Albedo",
    "T_Seam_Sand_Albedo":  f"{TEX_CR}/T_Seam_Sand_Albedo",
    "T_Seam_Shadows_01":   f"{TEX_CR}/T_Seam_Shadows_01",
}

PACK_MIC_NAMES = list(PARADISE_MATS.keys())
ART_INST_PREFIX = "MI_Rooms_Paradise_"
ART_INST_SUBDIR = AVATAR_MAT_DIR


def _load(path: str):
    try:
        import unreal
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception:
        return None

def _does_exist(path: str) -> bool:
    try:
        import unreal
        return unreal.EditorAssetLibrary.do_asset_exist(path)
    except Exception:
        return False

def _is_mic(obj) -> bool:
    if obj is None:
        return False
    try:
        import unreal
        return obj.get_class().get_name() == "MaterialInstanceConstant"
    except Exception:
        return False

def _read_parent(path: str) -> str:
    obj = _load(path)
    if obj is None:
        return "<MISSING>"
    try:
        p = obj.get_editor_property("parent")
        return p.get_path_name() if p is not None else "<NONE>"
    except Exception:
        return "<ERR>"

def _read_tex_overrides(path: str) -> list[str]:
    obj = _load(path)
    if obj is None:
        return []
    try:
        import unreal
        lib = unreal.MaterialEditingLibrary
        out = []
        for name in lib.get_texure_parameter_names(obj):
            if lib.is_mic_parameter_overridden(obj, name):
                out.append(name)
        return out
    except Exception:
        return []

def _list_assets(dir_path: str, prefix: str = "") -> list[str]:
    out = []
    try:
        import unreal
        for p in unreal.EditorAssetLibrary.list_assets(dir_path, recursive=False, include_folder=False):
            stem = Path(p).stem
            if prefix and stem.startswith(prefix):
                out.append(p)
            elif not prefix:
                out.append(p)
    except Exception:
        pass
    return sorted(out)

def _parse_pack_suffix(inst_name: str):
    parts = inst_name.split("_")
    for i in range(len(parts), 0, -1):
        cand = "_".join(parts[i-1:])
        if cand in PACK_MIC_NAMES:
            prop = "_".join(parts[:-1])
            return prop, cand
    return None, None

def _fix_mic(path: str, expect_tex_name: str | None, do_edit: bool) -> dict:
    name = Path(path).stem
    parent_before = _read_parent(path)
    obj = _load(path)
    if obj is None or not _is_mic(obj):
        return {"path": path, "status": "not_a_mic_or_missing", "parent_before": parent_before}

    changed = []
    cur_parent = parent_before
    want_parent = MASTER_UNIVERSAL

    if cur_parent != want_parent:
        if do_edit:
            try:
                import unreal
                p = _load(want_parent)
                if p is not None:
                    obj.set_editor_property("parent", p)
                    cur_parent = want_parent
                    changed.append(f"parent->{want_parent}")
            except Exception as e:
                return {"path": path, "status": "parent_fail", "error": str(e), "parent_before": parent_before}
        else:
            changed.append(f"WOULD parent->{want_parent} (was {cur_parent})")

    if expect_tex_name:
        tex_path = PARADISE_TEX.get(expect_tex_name)
        if tex_path and _does_exist(tex_path):
            overrides = _read_tex_overrides(path)
            if "Albedo" not in overrides:
                if do_edit:
                    try:
                        import unreal
                        tex_obj = _load(tex_path)
                        if tex_obj is not None:
                            unreal.MaterialEditingLibrary.set_mic_texture_param_value(obj, "Albedo", tex_obj)
                            changed.append(f"Albedo<-{expect_tex_name}")
                    except Exception as e:
                        changed.append(f"Albedo route FAIL: {e}")
                else:
                    changed.append(f"WOULD Albedo<-{expect_tex_name}")
            else:
                changed.append("Albedo already overridden")
        else:
            changed.append(f"tex MISSING: {expect_tex_name}")
    else:
        changed.append("no tex target (pure _Art, no pack suffix)")

    if do_edit:
        try:
            import unreal
            lib = unreal.MaterialEditingLibrary
            for scalar in ("TextureWeight", "LayerA_TextureWeight"):
                try:
                    lib.set_mic_scalar_param_value(obj, scalar, 1.0)
                    changed.append(f"{scalar}=1.0")
                except Exception:
                    pass
        except Exception:
            pass
    else:
        changed.append("WOULD set TextureWeight=1.0 + LayerA_TextureWeight=1.0")

    if do_edit:
        try:
            import unreal
            lib = unreal.MaterialEditingLibrary
            lib.set_mic_scalar_param_value(obj, "ShadowDreamStrength", 0.7)
            lib.set_mic_vec_param_value(obj, "ShadowDreamTint", unreal.LinearColor(0.541, 0.627, 0.839, 1.0))
            lib.set_mic_vec_param_value(obj, "ShadowFlowerColor", unreal.LinearColor(0.910, 0.627, 0.749, 1.0))
            lib.set_mic_scalar_param_value(obj, "ShadowFlowerStrength", 0.45)
            lib.set_mic_scalar_param_value(obj, "ShadowFlowerScale", 1.0)
            changed.append("ShadowDream set")
        except Exception as e:
            changed.append(f"ShadowDream FAIL: {e}")
    else:
        changed.append("WOULD set ShadowDream params")

    if do_edit:
        try:
            import unreal
            unreal.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False)
            changed.append("saved")
        except Exception as e:
            changed.append(f"save FAIL: {e}")

    return {"path": path, "parent_before": parent_before, "changed": changed, "status": "ok"}

def run_dry() -> dict:
    rows = []
    for name in PACK_MIC_NAMES:
        path = f"{ENV_ROOT}/{name}"
        rows.append({
            "kind": "pack_mic", "path": path,
            "parent": _read_parent(path),
            "tex_overrides": _read_tex_overrides(path),
            "tex_target": PARADISE_MATS.get(name),
        })
    art_paths = _list_assets(ART_INST_SUBDIR, prefix=ART_INST_PREFIX)
    art_rows = []
    for p in art_paths:
        name = Path(p).stem
        _, suffix_mic = _parse_pack_suffix(name)
        art_rows.append({
            "kind": "art_inst", "path": p, "name": name,
            "parent": _read_parent(p),
            "tex_overrides": _read_tex_overrides(p),
            "pack_suffix": suffix_mic,
            "tex_target": PARADISE_MATS.get(suffix_mic) if suffix_mic else None,
        })
    return {
        "dry_run": True,
        "pack_mics": rows, "art_insts": art_rows,
        "summary": {"pack_mics": len(rows), "art_insts": len(art_rows)},
    }

def run_edit() -> dict:
    rows = []
    for name in PACK_MIC_NAMES:
        path = f"{ENV_ROOT}/{name}"
        if not _does_exist(path):
            rows.append({"kind": "pack_mic", "path": path, "status": "missing"})
            continue
        tex_name = PARADISE_MATS.get(name)
        res = _fix_mic(path, tex_name, True)
        res["kind"] = "pack_mic"
        rows.append(res)
    art_paths = _list_assets(ART_INST_SUBDIR, prefix=ART_INST_PREFIX)
    art_rows = []
    for p in art_paths:
        name = Path(p).stem
        _, suffix_mic = _parse_pack_suffix(name)
        tex_name = PARADISE_MATS.get(suffix_mic) if suffix_mic else None
        res = _fix_mic(p, tex_name, True)
        res["kind"] = "art_inst"
        res["name"] = name
        res["pack_suffix"] = suffix_mic
        art_rows.append(res)
    return {
        "dry_run": False,
        "pack_mics": [r for r in rows if r.get("kind") == "pack_mic"],
        "art_insts": [r for r in rows if r.get("kind") == "art_inst"],
        "summary": {
            "pack_mics": len([r for r in rows if r.get("kind") == "pack_mic"]),
            "art_insts": len([r for r in rows if r.get("kind") == "art_inst"]),
            "ok": sum(1 for r in rows if r.get("status") == "ok"),
            "fail": sum(1 for r in rows if r.get("status") != "ok"),
        },
    }

def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    run = run_dry() if dry else run_edit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(run, indent=2, default=str), encoding="utf-8")
    print(json.dumps(run["summary"], indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
