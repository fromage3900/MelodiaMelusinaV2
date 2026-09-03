"""Probe UE 5.8 APIs for assigning Niagara sprite renderer materials."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "niagara_material_assign_probe.json"
SYSTEM = "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetals.NS_SakuraPetals"
MAT = "/Game/EnvSandbox/VFX/Materials/MI_Niagara_Petal.MI_Niagara_Petal"

out: dict = {"system": SYSTEM, "material": MAT, "attempts": []}


def attempt(label: str, fn) -> None:
    entry = {"label": label}
    try:
        entry["result"] = fn()
        entry["ok"] = True
    except Exception as exc:
        entry["ok"] = False
        entry["error"] = str(exc)
    out["attempts"].append(entry)
    flag = "OK" if entry.get("ok") else "FAIL"
    unreal.log(f"[ProbeMat] {flag} {label}: {entry.get('result', entry.get('error'))}")


if not unreal.EditorAssetLibrary.does_asset_exist(SYSTEM):
    out["error"] = "system missing"
else:
    system = unreal.load_asset(SYSTEM)
    material = unreal.load_asset(MAT) if unreal.EditorAssetLibrary.does_asset_exist(MAT) else None
    out["system_type"] = str(type(system))
    out["material_type"] = str(type(material))

    for name in dir(unreal):
        if "Niagara" in name and ("Editor" in name or "Toolset" in name):
            out.setdefault("niagara_classes", []).append(name)

    editor_lib = getattr(unreal, "NiagaraEditorLibrary", None)
    if editor_lib:
        for method in dir(editor_lib):
            if "material" in method.lower() or "renderer" in method.lower():
                out.setdefault("NiagaraEditorLibrary_methods", []).append(method)

    if system and material:
        attempt("NiagaraEditorLibrary.set_renderer_material", lambda: (
            unreal.NiagaraEditorLibrary.set_renderer_material(system, material) or "called"
        ) if editor_lib else (_ for _ in ()).throw(RuntimeError("no lib")))

        attempt("get_editor_property system", lambda: [
            p for p in ("emitters", "system_emitter", "editor_data", "editor_data_impl")
            if hasattr(system, "get_editor_property")
        ])

        for prop in ("emitters", "editor_data", "system_emitter"):
            try:
                val = system.get_editor_property(prop)
                out[f"prop_{prop}"] = str(type(val))
            except Exception as exc:
                out[f"prop_{prop}"] = f"error: {exc}"

        attempt("get_num_emitters", lambda: system.get_num_emitters())
        attempt("get_emitter_name 0", lambda: system.get_emitter_name(0))

        def try_emitter_props():
            count = system.get_num_emitters()
            hits = []
            for i in range(count):
                name = system.get_emitter_name(i)
                emitter = system.get_emitter_by_index(i)
                hits.append({"index": i, "name": name, "type": str(type(emitter))})
                if emitter:
                    for p in ("renderer_properties", "renderers", "versioned_renderer"):
                        try:
                            v = emitter.get_editor_property(p)
                            hits[-1][p] = str(type(v))
                        except Exception as exc:
                            hits[-1][p] = f"err:{exc}"
            return hits

        attempt("emitter introspection", try_emitter_props)

        def try_modify_renderer():
            emitter = system.get_emitter_by_index(0)
            props = emitter.get_editor_property("renderer_properties")
            changed = False
            for prop in props:
                cls = type(prop).__name__
                for field in ("material", "material_interface", "Material", "MaterialInterface"):
                    try:
                        prop.set_editor_property(field, material)
                        changed = True
                    except Exception:
                        pass
                if changed:
                    return f"changed via renderer_properties ({cls})"
            return "no change"

        attempt("emitter renderer_properties set", try_modify_renderer)

        attempt("NiagaraSystem.set_editor_property", lambda: "skipped")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(json.dumps(out, indent=2, default=str))
