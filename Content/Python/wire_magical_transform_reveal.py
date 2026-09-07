"""Author the Magical Transform reveal parameters used by the glide-outfit wing reveal.

WHAT THIS IS FOR
UMelodiaMagicalTransformComponent (MelodiaWardrobe plugin) animates a keyframed
0 -> 1 transformation on Melusina's accessory materials when the glide Resonant
Form's capability turns on. The wing is a MATERIAL SLOT on her existing body
mesh, not a new skeletal mesh, so the reveal is an opacity-mask animation. This
script creates the parameters that component writes. Without it every
SetScalarParameterValue call is a silent no-op -- UE does not error when you set
a parameter a material does not expose, so the feature would appear wired and do
nothing.

NAME AUTHORITY
Names mirror namespace MelodiaMagicalTransformParameter in
Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaMagicalTransformTypes.h.
That header is the single source of truth. Change a name there and here in the
same commit or the write lands on nothing.

WHY THE SHARED MASTER IS SAFE TO TOUCH
M_Master_Toon_Universal backs hundreds of instances. The whole block hangs off a
new static switch `bUseMagicalTransform` defaulting False and routing to the
pre-existing opacity path unchanged, so every existing instance compiles to the
identical shader it does today. This is the same additive pattern
converge_toon_universal.py used to land bUseOpacityMap (step1_opacity), which is
the sanctioned way to extend this master.

WHY MASKED AND NOT TRANSLUCENT
M_Master_Toon_Universal is BLEND_OPAQUE and its Substrate Toon BSDF has no
opacity input (probe 1 2026-08-17, recorded in wire_atlantis_opacity_master.py).
A translucent reveal would mean a new master and a new sort order on a character
that already ships 33 material slots. A masked dissolve routes through the
existing MP_OPACITY_MASK path, costs nothing extra, and is the look the reference
asset already uses (MI_Universal_HenshinDither). Blend mode is overridden
PER INSTANCE, matching converge_toon_universal.py:260-263.

RUN
  In the live editor:
      import wire_magical_transform_reveal as w; w.main()
  Headless:
      UnrealEditor-Cmd.exe BS_GodFile.uproject \
        -ExecutePythonScript="Content/Python/wire_magical_transform_reveal.py"

Manifest: Saved/Audit/magical_transform_reveal_wire.json
Idempotent: existing parameters are refreshed, never duplicated.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

MT = unreal.MaterialEditingLibrary
ASSETS = unreal.EditorAssetLibrary

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magical_transform_reveal_wire.json"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REVEAL_INSTANCE_DIR = "/Game/Melodia/Characters/Melusina/Materials"

MPC_CANDIDATES = [
    "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette",
    "/Game/EnvSandbox/Materials/MPC_Melodia_Palette",
]

GROUP = "MagicalTransform"

# Must equal namespace MelodiaMagicalTransformParameter in the C++ header.
P_PROGRESS = "MagicalTransformProgress"
P_DISSOLVE = "MagicalTransformDissolve"
P_BLOOM = "MagicalTransformBloom"
P_SPARKLE = "MagicalTransformSparkle"
P_BEAT = "MagicalTransformBeat"
P_TINT = "MagicalTransformTint"
P_OPACITY = "Opacity"
SWITCH = "bUseMagicalTransform"

# Existing opacity chain ported into this master by converge_toon_universal.py.
EXISTING_OPACITY_SWITCH = "bUseOpacityMap"

# Must equal namespace MelodiaMagicalTransformMPC in the C++ header.
MPC_SCALARS = [
    ("MagicalTransform", 0.0),       # progress mirror, 0 at rest
    ("MagicalTransformFlare", 0.0),  # wavefront intensity, 0 at rest
]

# Instances the reveal drives. Wing entries get their opacity mask animated;
# accessory entries only shimmer, so their opacity is left alone.
#
# Slot names come from Saved/Audit/melusina_slot_texture_sweep.json. The wing
# slot is authored ahead of the geometry on purpose: the component matches slot
# names case-insensitively by substring, so the MI is ready the moment the wing
# section lands in the mesh and no code changes when it does.
REVEAL_INSTANCES = [
    ("MI_Melusina_Wing_MagicalTransform", True),
    ("MI_Melusina_Bow_MagicalTransform", False),
]


def _find_param(mat, cls, name: str):
    """Locate an existing parameter expression by name, or None."""
    for expr in MT.get_material_expressions(mat) or []:
        try:
            if isinstance(expr, cls) and str(expr.get_editor_property("parameter_name")) == name:
                return expr
        except Exception:
            continue
    return None


def _param_names(mat, cls) -> list[str]:
    names = []
    for expr in MT.get_material_expressions(mat) or []:
        try:
            if isinstance(expr, cls):
                names.append(str(expr.get_editor_property("parameter_name")))
        except Exception:
            continue
    return sorted(names)


def ensure_mpc_scalars() -> dict:
    """Add the two MPC mirror scalars. Mirrors add_horizon_eater_mpc_params.py."""
    mpc = None
    mpc_path = None
    for candidate in MPC_CANDIDATES:
        asset = ASSETS.load_asset(candidate)
        if asset:
            mpc, mpc_path = asset, candidate
            break

    if not mpc:
        unreal.log_warning(
            "[MagicalTransform] MPC_Melodia_Palette not found in %s; the per-material "
            "reveal still works, only the world-side mirror is skipped." % MPC_CANDIDATES)
        return {"ok": False, "path": None, "added": [], "reason": "mpc_not_found"}

    scalars = list(mpc.get_editor_property("scalar_parameters"))
    existing = {s.get_editor_property("parameter_name") for s in scalars}

    added = []
    for name, default in MPC_SCALARS:
        if name in existing:
            continue
        param = unreal.CollectionScalarParameter()
        param.set_editor_property("parameter_name", name)
        param.set_editor_property("default_value", float(default))
        scalars.append(param)
        added.append(name)

    if added:
        mpc.set_editor_property("scalar_parameters", scalars)
        ASSETS.save_loaded_asset(mpc)

    final = {s.get_editor_property("parameter_name") for s in mpc.get_editor_property("scalar_parameters")}
    return {
        "ok": all(n in final for n, _ in MPC_SCALARS),
        "path": mpc_path,
        "added": added,
        "total_scalars": len(final),
    }


def ensure_transform_params(mat) -> dict:
    """Create the Magical Transform parameter block. Returns which were new."""
    created = []

    def scalar(name, default, x, y, desc):
        nonlocal created
        found = _find_param(mat, unreal.MaterialExpressionScalarParameter, name)
        if found:
            return found
        created.append(name)
        return lib.scalar_param(mat, name, GROUP, default, x, y, desc=desc)

    # Progress defaults to 1.0, not 0.0. An artist who enables the switch on an MI
    # and opens it should see the material, not an invisible one they will file as
    # broken. The runtime drives it to 0 immediately in BeginPlay via
    # SnapToPhase(Dormant), so the authoring default is never what ships.
    progress = scalar(
        P_PROGRESS, 1.0, -2100, 4200,
        "0=concealed 1=revealed. Driven by UMelodiaMagicalTransformComponent.")
    dissolve = scalar(
        P_DISSOLVE, 0.0, -2100, 4240,
        "Erosion band width at the dissolve edge. Widest mid-transition.")
    scalar(P_BLOOM, 0.0, -2100, 4280,
           "Emissive gain at the wavefront. May exceed 1.")
    scalar(P_SPARKLE, 0.0, -2100, 4320,
           "Sparkle-mote density through the transition.")
    scalar(P_BEAT, 0.0, -2100, 4360,
           "cos^2(BeatPhase*pi) forwarded per-MID so the wavefront lands on beat.")

    # `Opacity` is the name UMelodiaTraversalComponent::WingOpacityParameter
    # already defaults to, so an authored wing material predating this system
    # participates without being re-authored.
    opacity = scalar(
        P_OPACITY, 1.0, -2100, 4400,
        "Wing opacity multiplier. Same name as the traversal component's default.")

    if not _find_param(mat, unreal.MaterialExpressionVectorParameter, P_TINT):
        created.append(P_TINT)
        lib.vector_param(mat, P_TINT, GROUP, (1.0, 0.86, 0.62, 1.0), -2100, 4440,
                         desc="Wavefront colour.")

    switch = _find_param(mat, unreal.MaterialExpressionStaticSwitchParameter, SWITCH)
    if not switch:
        created.append(SWITCH)
        switch = lib.create_expression(
            mat, unreal.MaterialExpressionStaticSwitchParameter, -1300, 4200)
        switch.set_editor_property("parameter_name", SWITCH)
        switch.set_editor_property("group", GROUP)
        # False keeps every existing instance's shader byte-identical.
        switch.set_editor_property("default_value", False)

    return {
        "created": created,
        "progress": progress,
        "dissolve": dissolve,
        "opacity": opacity,
        "switch": switch,
    }


def build_dissolve_chain(mat, params) -> dict:
    """Build the dissolve mask and gate MP_OPACITY_MASK behind the new switch.

    mask = saturate((field - (1 - Progress) + band) / band) * Opacity
    where band = max(Dissolve * 0.35, 0.02) and field is a 0..1 noise field.

    The +band / /band form gives a soft leading edge whose width the designer
    controls, instead of the hard step a bare comparison produces. band is
    floored so a Dissolve of 0 is a crisp cut rather than a divide by zero --
    that would emit a NaN straight into the opacity mask and the whole slot would
    render as garbage for the rest of the frame.
    """
    wired = []

    # World-space noise field. Chosen over a texture so the reveal needs no new
    # asset and works on any slot regardless of its UV layout -- several of
    # Melusina's 33 slots share overlapping UVs, which would make a UV-space
    # dissolve tear across the seam.
    world_pos = lib.create_expression(
        mat, unreal.MaterialExpressionWorldPosition, -2100, 4520)
    noise = lib.create_expression(mat, unreal.MaterialExpressionNoise, -1850, 4520)
    lib.try_set_editor_property(noise, "scale", 0.35)
    lib.try_set_editor_property(noise, "levels", 3)
    lib.try_set_editor_property(noise, "output_min", 0.0)
    lib.try_set_editor_property(noise, "output_max", 1.0)
    lib.try_set_editor_property(noise, "turbulence", True)
    if lib.connect(world_pos, "", noise, "Position"):
        wired.append("WorldPosition->Noise.Position")

    # threshold = 1 - Progress. Progress 0 puts the threshold above every field
    # value, so nothing passes and the wing is fully concealed.
    one = lib.create_expression(mat, unreal.MaterialExpressionConstant, -1850, 4200)
    one.set_editor_property("r", 1.0)
    threshold = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -1700, 4200)
    lib.connect(one, "", threshold, "A")
    lib.connect(params["progress"], "", threshold, "B")

    # band = max(Dissolve * 0.35, 0.02)
    band_scale = lib.create_expression(mat, unreal.MaterialExpressionConstant, -1850, 4260)
    band_scale.set_editor_property("r", 0.35)
    band_raw = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -1700, 4260)
    lib.connect(params["dissolve"], "", band_raw, "A")
    lib.connect(band_scale, "", band_raw, "B")
    band_floor = lib.create_expression(mat, unreal.MaterialExpressionConstant, -1850, 4320)
    band_floor.set_editor_property("r", 0.02)
    band = lib.create_expression(mat, unreal.MaterialExpressionMax, -1560, 4260)
    lib.connect(band_raw, "", band, "A")
    lib.connect(band_floor, "", band, "B")

    # field - threshold + band
    delta = lib.create_expression(mat, unreal.MaterialExpressionSubtract, -1560, 4520)
    lib.connect(noise, "", delta, "A")
    lib.connect(threshold, "", delta, "B")
    biased = lib.create_expression(mat, unreal.MaterialExpressionAdd, -1440, 4520)
    lib.connect(delta, "", biased, "A")
    lib.connect(band, "", biased, "B")

    ramp = lib.create_expression(mat, unreal.MaterialExpressionDivide, -1320, 4520)
    lib.connect(biased, "", ramp, "A")
    lib.connect(band, "", ramp, "B")

    mask = lib.create_expression(mat, unreal.MaterialExpressionSaturate, -1200, 4520)
    lib.connect_unary(ramp, mask)

    # Multiply by Opacity so the component's own opacity write still has authority
    # over the finished mask -- that is the parameter a bespoke wing material
    # exposes, and it has to keep working here too.
    gated = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -1080, 4520)
    lib.connect(mask, "", gated, "A")
    lib.connect(params["opacity"], "", gated, "B")

    # Gate behind the switch. False routes the PRE-EXISTING opacity source, so
    # instances that never opt in are untouched.
    switch = params["switch"]
    existing_source = _find_param(
        mat, unreal.MaterialExpressionStaticSwitchParameter, EXISTING_OPACITY_SWITCH)

    if existing_source:
        # Insert ahead of the converged bUseOpacityMap chain rather than replacing
        # it: masked foliage and lace cutouts still need their own map.
        if lib.connect(existing_source, "", switch, "False"):
            wired.append(f"{EXISTING_OPACITY_SWITCH}->{SWITCH}.False")
        combine = lib.create_expression(mat, unreal.MaterialExpressionMultiply, -960, 4520)
        lib.connect(gated, "", combine, "A")
        lib.connect(existing_source, "", combine, "B")
        true_source = combine
        wired.append("dissolve * existing_opacity -> True")
    else:
        # No converged chain on this master yet. Fall back to the dissolve alone
        # and say so, rather than quietly wiring a half chain.
        fallback_one = lib.create_expression(
            mat, unreal.MaterialExpressionConstant, -1080, 4180)
        fallback_one.set_editor_property("r", 1.0)
        lib.connect(fallback_one, "", switch, "False")
        true_source = gated
        wired.append(f"WARNING {EXISTING_OPACITY_SWITCH} absent; False routes Constant 1.0")

    if lib.connect(true_source, "", switch, "True"):
        wired.append(f"dissolve->{SWITCH}.True")

    try:
        MT.connect_material_property(switch, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        wired.append(f"{SWITCH}->MP_OPACITY_MASK")
    except Exception as exc:
        wired.append(f"ERROR MP_OPACITY_MASK connect failed: {exc}")

    return {"wired": wired}


def ensure_reveal_instances(mat) -> list[dict]:
    """Create the wing/accessory MIs with the switch on and blend mode masked."""
    results = []
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    for name, is_wing in REVEAL_INSTANCES:
        path = f"{REVEAL_INSTANCE_DIR}/{name}"
        if ASSETS.does_asset_exist(path):
            mi = ASSETS.load_asset(path)
            action = "existing"
        else:
            mi = tools.create_asset(
                name, REVEAL_INSTANCE_DIR,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
            if mi:
                mi.set_editor_property("parent", mat)
            action = "created"

        if not mi:
            results.append({"name": name, "ok": False, "action": "create_failed"})
            continue

        lib.set_instance_static_switch(mi, SWITCH, True)

        # Only the wing dissolves. Turning the mask on for an accessory would
        # erode the accessory itself, which is not what "accessory wide" means --
        # accessories shimmer, the wing appears.
        if is_wing:
            # Per-instance blend override, matching converge_toon_universal.py.
            # The master stays BLEND_OPAQUE for everyone else.
            overrides = mi.get_editor_property("base_property_overrides")
            overrides.set_editor_property("override_blend_mode", True)
            overrides.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
            overrides.set_editor_property("override_two_sided", True)
            overrides.set_editor_property("two_sided", True)
            mi.set_editor_property("base_property_overrides", overrides)
            lib.set_instance_scalar(mi, P_PROGRESS, 0.0)  # ships concealed
            lib.set_instance_scalar(mi, P_OPACITY, 1.0)
        else:
            lib.set_instance_scalar(mi, P_PROGRESS, 1.0)

        ASSETS.save_loaded_asset(mi)
        results.append({"name": name, "ok": True, "action": action, "is_wing": is_wing})

    return results


def main() -> dict:
    mat = ASSETS.load_asset(MASTER)
    if not mat:
        report = {"ok": False, "error": f"master not loadable: {MASTER}"}
        print(json.dumps(report, indent=2))
        return report

    mpc = ensure_mpc_scalars()
    params = ensure_transform_params(mat)
    chain = build_dissolve_chain(mat, params)

    try:
        MT.recompile_material(mat)
        compile_ok, compile_err = True, None
    except Exception as exc:
        compile_ok, compile_err = False, str(exc)

    ASSETS.save_loaded_asset(mat, only_if_is_dirty=False)

    instances = ensure_reveal_instances(mat)

    # Re-read rather than trusting the writes. A parameter that failed to create
    # is the exact condition that makes the runtime silently no-op.
    scalars = _param_names(mat, unreal.MaterialExpressionScalarParameter)
    vectors = _param_names(mat, unreal.MaterialExpressionVectorParameter)
    switches = _param_names(mat, unreal.MaterialExpressionStaticSwitchParameter)

    required_scalars = [P_PROGRESS, P_DISSOLVE, P_BLOOM, P_SPARKLE, P_BEAT, P_OPACITY]
    missing = [n for n in required_scalars if n not in scalars]
    if P_TINT not in vectors:
        missing.append(P_TINT)
    if SWITCH not in switches:
        missing.append(SWITCH)

    errors = [w for w in chain["wired"] if w.startswith("ERROR")]
    warnings = [w for w in chain["wired"] if w.startswith("WARNING")]

    ok = (
        compile_ok
        and not missing
        and not errors
        and all(i["ok"] for i in instances)
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "mpc": mpc,
        "params_created": params["created"],
        "wired": chain["wired"],
        "warnings": warnings,
        "errors": errors,
        "missing_after_reread": missing,
        "compile_ok": compile_ok,
        "compile_error": compile_err,
        "instances": instances,
        "contract": (
            "UMelodiaMagicalTransformComponent is the sole runtime writer of "
            f"{GROUP} parameters and of MagicalTransform/MagicalTransformFlare on "
            "MPC_Melodia_Palette. Names mirror MelodiaMagicalTransformTypes.h."
        ),
        "follow_up": (
            f"{P_BLOOM}/{P_SPARKLE}/{P_TINT} exist and are written at runtime but are "
            "not yet wired to MP_EMISSIVE_COLOR on the shared master: doing so "
            "requires re-routing whatever currently drives emissive, which cannot "
            "be read back through MaterialEditingLibrary. Wire the wavefront "
            "emissive by hand in the material editor, or on a dedicated wing "
            "master. The opacity reveal is complete without it."
        ),
        "ok": ok,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)
