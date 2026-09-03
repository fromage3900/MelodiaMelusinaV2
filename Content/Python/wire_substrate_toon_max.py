"""Max out the Substrate Toon BSDF on M_Master_Toon_Universal (UE 5.8 experimental).

The 5.8 Substrate Toon system = the Toon BSDF node (pins) + a **Toon Profile asset**
that centralizes ramp-based diffuse/specular, dithering, hatching self-shadow, and
GI-scale. Docs don't publish exact property names (experimental), so:

  1. discover()  - run FIRST on relaunch. Dumps the BSDF's real pins, whether a
     ToonProfile class exists in the `unreal` namespace + its editable properties,
     and any material settings related to toon. Grounds accurate wiring - do NOT
     guess-wire the Profile before running this.
  2. wire_anisotropy() - wires the CONFIRMED-safe anisotropic-spec pins
     (Anisotropy + Tangent), gated by ToonAnisotropy default 0 = zero change.
     Silk/water/lacquer streak highlights when dialed up. Safe on all 105 instances.

Run (Monolith run_python):
  import wire_substrate_toon_max as w
  print(w.discover())        # inspect output, then:
  w.wire_anisotropy()        # then verify is_compiled via get_compilation_stats

Verify is_compiled TRUE after wiring. If a landscape/water master ever gets this,
re-verify on an actual surface (preview-compile != renders, per the H incident).
"""
from __future__ import annotations

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
BSDF = "MaterialExpressionSubstrateToonBSDF_4"


def discover() -> str:
    import unreal
    MEL = unreal.MaterialEditingLibrary
    out = []
    m = unreal.EditorAssetLibrary.load_asset(MASTER)
    bsdf = next(e for e in MEL.get_material_expressions(m) if e.get_name() == BSDF)
    # dump BSDF editable properties (thresholds, toggles) + which pins are connected
    out.append("== BSDF editable properties ==")
    for p in ("use_metalness", "toon_profile", "profile", "specular_profile"):
        try:
            out.append(f"  {p} = {bsdf.get_editor_property(p)}")
        except Exception:
            pass
    ins = MEL.get_inputs_for_material_expression(m, bsdf)
    names = ["BaseColor", "Metallic", "Specular", "Roughness", "Normal",
             "EmissiveColor", "PatternUVs", "Anisotropy", "Tangent"]
    out.append("== BSDF pins (source or None) ==")
    for i, nm in enumerate(names):
        s = ins[i] if i < len(ins) else None
        out.append(f"  {nm}: {s.get_name() if s else 'UNCONNECTED'}")
    # ToonProfile class discovery
    out.append("== ToonProfile-ish classes in unreal namespace ==")
    for attr in dir(unreal):
        if "Toon" in attr or "NPR" in attr:
            out.append(f"  unreal.{attr}")
    msg = "\n".join(out)
    print(msg)
    return msg


def wire_anisotropy() -> str:
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.EditorAssetLibrary.load_asset(MASTER)
    E = MEL.get_material_expressions(m)
    bsdf = next(e for e in E if e.get_name() == BSDF)
    # skip if already wired
    if any(isinstance(e, unreal.MaterialExpressionScalarParameter)
           and str(e.get_editor_property("parameter_name")) == "ToonAnisotropy" for e in E):
        return "ToonAnisotropy already present - skipping"
    con = MEL.connect_material_expressions
    aniso = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 900)
    aniso.set_editor_property("parameter_name", "ToonAnisotropy")
    aniso.set_editor_property("default_value", 0.0)       # 0 = isotropic = no change
    aniso.set_editor_property("slider_min", -1.0)
    aniso.set_editor_property("slider_max", 1.0)
    aniso.set_editor_property("group", "10 | Nikki Iridescence & Sheen")
    con(aniso, "", bsdf, "Anisotropy")
    # Tangent left on the default vertex tangent (safe). To rotate highlights later,
    # feed a custom tangent vector here (e.g. a flow-map or WorldAligned direction).
    MEL.recompile_material(m)
    ok = unreal.EditorAssetLibrary.save_asset(MASTER, only_if_is_dirty=False)
    return f"ToonAnisotropy wired to BSDF.Anisotropy (default 0) | saved={ok}"


if __name__ == "__main__":
    discover()
