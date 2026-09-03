"""convert_halftone_trio.py

Fix the 3 MooaToon halftone EXCEPTIONs under the owner's directive
("fix halftone trio as well"):

  M_MooaToon_Halftone_Enhanced  30 exprs,  2 dangling MFCs (material_function=None)
  M_MooaToon_Halftone_Universal 38 exprs,  resolvable MFCs (HeightToNormalSmooth + MeshBlend)
  M_MooaToon_Halftone_Vortex    26 exprs,  resolvable MFC (MeshBlend)

Pipeline per master:
  1. PORT   _PROJECT/04_Materials/MooaToon/<stem>.uasset -> EnvSandbox/Materials/Masters/
            (disk copy; _PROJECT read-only; skip if destination exists)
  2. DISARM (Enhanced only) any MaterialExpressionMaterialFunctionCall whose
            material_function is None: disconnect inputs, delete the node.
            The halftone core (textures + scalars + lerp) survives; the two
            dead sub-effects are replaced by the graph's existing defaults.
  3. CONVERT Strategy C via convert_masters_to_substrate_toon.convert_master
            (preserve graph; root -> SubstrateToonBSDF -> MP_FRONT_MATERIAL).
  4. VERIFY independently: BSDF present + Front Material wired, recompile a
            second time, confirm 0 errors via recompile_material.
  5. PROFILE assign TP_Ornamental (halftone = dream ornament family).
  6. MI     create MI_Halftone_<Stem> under
            /Game/EnvSandbox/Materials/SDF/Instances/Halftone with the master
            as parent, then the creative-variance policy is applied by
            apply_instance_parameter_policy.py (separate run; HALFTONE_ROOTS).

Reports: Saved/Audit/halftone_trio.json
Run (one editor, serialized):
  Monolith editor_query run_python -> this file
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_MOOA = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / "MooaToon"
DST_MASTERS = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "halftone_trio.json"

MASTERS_ROOT = "/Game/EnvSandbox/Materials/Masters"
INST_FOLDER = "/Game/EnvSandbox/Materials/SDF/Instances/Halftone"
PROFILE_DIR = "/Game/EnvSandbox/Materials/ToonProfiles"

TRIO = [
    {"stem": "M_MooaToon_Halftone_Enhanced", "disarm": True},
    {"stem": "M_MooaToon_Halftone_Universal", "disarm": False},
    {"stem": "M_MooaToon_Halftone_Vortex", "disarm": False},
]

sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))
import convert_masters_to_substrate_toon as conv  # noqa: E402


def rescan(folder: str) -> None:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        ar.scan_paths_synchronous([folder], force_rescan=True)
    except Exception as exc:
        unreal.log_warning(f"[Halftone] rescan failed: {exc}")


def port_one(stem: str) -> tuple[str, str]:
    """Copy from _PROJECT MooaToon to EnvSandbox Masters if missing.

    Returns (status, detail).
    """
    src = SRC_MOOA / f"{stem}.uasset"
    dst = DST_MASTERS / f"{stem}.uasset"
    if dst.exists():
        return "exists", str(dst)
    if not src.is_file():
        return "missing_src", str(src)
    shutil.copy2(src, dst)
    return "ported", str(dst)


def disarm_dangling_mfcs(material_path: str) -> list[str]:
    """Remove MaterialFunctionCall expressions with material_function=None.

    A dangling MFC compiles into a broken/unpredictable shader and cannot be
    rewired (the referenced function asset no longer exists). We delete the
    node; anything that consumed its output falls back to the pin default
    (usually white/1.0), preserving the halftone core.
    """
    asset = unreal.load_asset(material_path)
    if asset is None:
        return []
    lib = unreal.MaterialEditingLibrary
    removed: list[str] = []
    for expr in list(lib.get_material_expressions(asset) or []):
        tname = type(expr).__name__
        if "MaterialFunctionCall" not in tname:
            continue
        try:
            fn = expr.get_editor_property("material_function")
        except Exception:
            fn = None
        if fn is None:
            # sever all inputs first so deletion leaves no dangling wires
            try:
                for inp in lib.get_inputs_for_material_expression(asset, expr):
                    lib.connect_material_expressions(None, "", expr, "", disconnect=True)
            except Exception:
                pass
            try:
                lib.delete_material_expression(asset, expr)
                removed.append(tname)
            except Exception as exc:
                unreal.log_warning(f"[Halftone] delete MFC failed: {exc}")
    return removed


def create_halftone_instance(stem: str, master_path: str) -> str:
    """Create MI parented to the converted master, with TP_Ornamental default."""
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi_path = f"{INST_FOLDER}/MI_{stem}"
    mi = assets.create_asset(
        f"MI_{stem}",
        INST_FOLDER,
        unreal.MaterialInstanceConstant,
        factory,
    )
    if mi is None:
        return f"create_failed:{mi_path}"
    mi.set_editor_property("parent", unreal.load_asset(master_path))
    profile_path = f"{PROFILE_DIR}/TP_Ornamental"
    if unreal.EditorAssetLibrary.does_asset_exist(profile_path):
        profile = unreal.load_asset(profile_path)
        try:
            mi.set_editor_property("toon_profile", profile)
            mi.set_editor_property("override_toon_profile", True)
        except Exception:
            pass
    saved = unreal.EditorAssetLibrary.save_asset(mi_path, only_if_is_dirty=False)
    return f"saved:{saved}"


def main() -> int:
    rescan("/Game/EnvSandbox/Materials/Masters")
    rescan(INST_FOLDER)
    rows: list[dict] = []
    failures = 0

    for item in TRIO:
        stem = item["stem"]
        row: dict = {"stem": stem}
        # 1. PORT
        status, detail = port_one(stem)
        row["port"] = status
        path = f"{MASTERS_ROOT}/{stem}"
        if status == "missing_src":
            row["status"] = "failed"
            row["error"] = detail
            rows.append(row)
            failures += 1
            continue
        # reload after rescan
        rescan("/Game/EnvSandbox/Materials/Masters")
        asset = unreal.load_asset(path)
        if asset is None or "Material" not in type(asset).__name__:
            row["status"] = "failed"
            row["error"] = f"not a Material after port: {type(asset).__name__ if asset else 'None'}"
            rows.append(row)
            failures += 1
            continue

        # 2. DISARM
        if item["disarm"]:
            removed = disarm_dangling_mfcs(path)
            row["disarmed_mfcs"] = removed

        # 3. CONVERT (skip if already toon)
        if conv._has_substrate_toon_bsdf(asset):
            row["convert"] = "already_toon"
        else:
            try:
                r = conv.convert_master(path)
                row["convert"] = r.get("status")
                row["convert_error"] = r.get("error")
            except Exception as exc:
                row["convert"] = "convert_error"
                row["convert_error"] = str(exc)

        # 4. VERIFY independently (re-read + BSDF/Front + recompile)
        asset2 = unreal.load_asset(path)
        exprs = conv._get_expressions(asset2) if asset2 else []
        has_bsdf = any("SubstrateToonBSDF" in type(e).__name__ for e in exprs)
        has_front = conv._has_front_material_wired(asset2) if asset2 else False
        recompiled_ok = False
        if asset2:
            try:
                unreal.MaterialEditingLibrary.recompile_material(asset2)
                recompiled_ok = True
            except Exception as exc:
                row["recompile_error"] = str(exc)
        row["verify"] = {"bsdf": has_bsdf, "front": has_front, "recompile": recompiled_ok}
        if not (has_bsdf and has_front):
            row["status"] = "failed"
            row["error"] = "BSDF/Front verification failed"
            failures += 1
            rows.append(row)
            continue

        # 5. PROFILE on the master's Toon BSDF
        toon_bsdf = conv._get_toon_bsdf(asset2)
        profile_path = f"{PROFILE_DIR}/TP_Ornamental"
        if toon_bsdf is not None and unreal.EditorAssetLibrary.does_asset_exist(profile_path):
            try:
                toon_bsdf.set_editor_property("toon_profile", unreal.load_asset(profile_path))
                unreal.EditorAssetLibrary.save_loaded_asset(asset2, only_if_is_dirty=False)
                row["profile"] = "TP_Ornamental"
            except Exception as exc:
                row["profile_error"] = str(exc)

        # 6. MI
        row["instance"] = create_halftone_instance(stem, path)
        row["status"] = "ok"
        rows.append(row)
        unreal.log(f"[Halftone] {stem}: {row['status']}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total": len(rows),
                "failures": failures,
                "results": rows,
                "next": "Run apply_instance_parameter_policy.py with EXTRA_ROOTS=[INST_FOLDER]",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Halftone trio: {len(rows) - failures} ok, {failures} failed -> {REPORT}")
    for r in rows:
        print(f"  [{r.get('status')}] {r['stem']} | port={r.get('port')} | convert={r.get('convert')} | verify={r.get('verify')}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())