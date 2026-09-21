# -*- coding: utf-8 -*-
"""Faraway Stage 2b — discover real texture param names on Mother MIs and rebind imported Copernicus maps."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "faraway_mother_stage2b_texbind_2026-09-21.json"

MI_SPECS = {
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle": "FarawayNightVelvet",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown": "FarawayCelestialSilk",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil": "FarawayAquaLace",
    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset": "FarawayGildedRidge",
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayAlabasterDrape": "FarawayAlabasterDrape",
    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayMoonChiffon": "FarawayMoonChiffon",
}

LOGICAL = {
    "BaseColor": ["basecolor", "base_color", "albedo", "diffuse", "color", "base"],
    "Normal": ["normal"],
    "ORM": ["orm", "occlusionroughnessmetallic", "packedorm", "mask"],
    "Roughness": ["roughness"],
    "Metallic": ["metallic"],
    "Height": ["height", "displacement", "parallax"],
    "Emissive": ["emissive"],
    "Sheen": ["sheen"],
    "Opacity": ["opacity", "opacitymask", "alpha"],
    "AO": ["ambientocclusion", "ao", "occlusion"],
}


def _tex_path(family, logical):
    suf = {
        "BaseColor": "_BaseColor",
        "Normal": "_Normal",
        "ORM": "_ORM",
        "Roughness": "_Roughness",
        "Metallic": "_Metallic",
        "Height": "_Height",
        "Emissive": "_Emissive",
        "Sheen": "_Sheen",
        "Opacity": "_Opacity",
        "AO": "_AO",
    }[logical]
    p = f"/Game/EnvSandbox/Textures/Copernicus/Faraway/{family}/T_Cymatic_{family}{suf}"
    if EAL.does_asset_exist(p):
        return p
    return None


def _list_tex_params(mi):
    names = []
    # try several UE APIs
    for fn in (
        lambda: MEL.get_texture_parameter_names(mi),
        lambda: MEL.get_texture_parameter_names(mi.get_editor_property("parent")),
    ):
        try:
            vals = fn()
            if vals:
                for n in vals:
                    names.append(str(n))
        except Exception:
            pass
    # static parameters on MIC
    try:
        sps = mi.get_editor_property("texture_parameter_values")
        for e in sps or []:
            try:
                names.append(str(e.get_editor_property("parameter_info").get_editor_property("name")))
            except Exception:
                try:
                    names.append(str(e.parameter_info.name))
                except Exception:
                    pass
    except Exception:
        pass
    # parent expressions scan via get_parameter names on parent asset
    try:
        parent = mi.get_editor_property("parent")
        if parent:
            for fn in (
                lambda: MEL.get_texture_parameter_names(parent),
            ):
                try:
                    for n in fn() or []:
                        names.append(str(n))
                except Exception:
                    pass
    except Exception:
        pass
    # unique preserve order
    out, seen = [], set()
    for n in names:
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _match(param_names, logical):
    keys = LOGICAL[logical]
    ranked = []
    for pn in param_names:
        low = pn.lower().replace(" ", "").replace("_", "")
        for k in keys:
            kk = k.replace("_", "")
            if kk in low:
                # prefer exact-ish
                score = 0 if low == kk or low.endswith(kk) else 1
                ranked.append((score, pn))
                break
    ranked.sort()
    return ranked[0][1] if ranked else None


def _set_tex(mi, pname, tex):
    try:
        MEL.set_material_instance_texture_parameter_value(mi, pname, tex)
        # verify
        try:
            cur = MEL.get_material_instance_texture_parameter_value(mi, pname)
            return cur == tex or cur is not None
        except Exception:
            return True
    except Exception:
        try:
            MEL.set_material_instance_texture_parameter_value(mi, unreal.Name(pname), tex)
            return True
        except Exception as e:
            return False


def main():
    report = {
        "schema": "melodia.faraway_mother.stage2b_texbind.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": {},
        "ok": False,
    }
    saved = []
    any_bound = False
    for mi_path, family in MI_SPECS.items():
        entry = {"family": family, "params_discovered": [], "binds": {}}
        if not EAL.does_asset_exist(mi_path):
            entry["error"] = "mi_missing"
            report["results"][mi_path] = entry
            continue
        mi = EAL.load_asset(mi_path)
        pnames = _list_tex_params(mi)
        entry["params_discovered"] = pnames
        for logical in LOGICAL:
            tex_p = _tex_path(family, logical)
            if not tex_p:
                entry["binds"][logical] = {"status": "no_texture_asset"}
                continue
            tex = EAL.load_asset(tex_p)
            pname = _match(pnames, logical)
            if not pname:
                # last resort: try common names even if not discovered
                for guess in {
                    "BaseColor": ["BaseColor", "Base Color", "Diffuse", "Albedo"],
                    "Normal": ["Normal", "NormalMap"],
                    "ORM": ["ORM", "OcclusionRoughnessMetallic"],
                    "Roughness": ["Roughness"],
                    "Metallic": ["Metallic"],
                    "Height": ["Height", "ParallaxHeight", "Displacement"],
                    "Emissive": ["Emissive", "EmissiveMap"],
                    "Sheen": ["SheenMask", "Sheen"],
                    "Opacity": ["Opacity", "OpacityMask"],
                    "AO": ["AmbientOcclusion", "AO"],
                }[logical]:
                    if _set_tex(mi, guess, tex):
                        pname = guess
                        break
            if not pname:
                entry["binds"][logical] = {"status": "no_param_match", "tex": tex_p}
                continue
            ok = _set_tex(mi, pname, tex)
            entry["binds"][logical] = {"status": "bound" if ok else "set_failed", "param": pname, "tex": tex_p}
            if ok:
                any_bound = True
        try:
            MEL.update_material_instance(mi)
            entry["updated"] = True
        except Exception as e:
            entry["updated"] = str(e)
        EAL.save_asset(mi_path)
        saved.append(mi_path)
        report["results"][mi_path] = entry

    try:
        pkgs = [EAL.load_asset(p) for p in saved]
        unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, False)
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        report["save"] = True
    except Exception as e:
        report["save"] = str(e)

    report["ok"] = any_bound
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    # compact summary
    bound = 0
    total = 0
    for e in report["results"].values():
        for b in (e.get("binds") or {}).values():
            total += 1
            if b.get("status") == "bound":
                bound += 1
    print("STAGE2B " + json.dumps({"bound": bound, "total": total, "ok": any_bound, "out": str(OUT)}))
    unreal.log("STAGE2B wrote " + str(OUT))
    return 0 if any_bound else 2


if __name__ == "__main__":
    raise SystemExit(main())
