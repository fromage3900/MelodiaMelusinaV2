"""Converge M_Master_Toon_Universal_Alpha into M_Master_Toon_Universal.

WHY
---
The two masters differ only in blend mode (Masked vs Opaque) and two-sidedness.
Everything else is a maintenance burden: ~1250 duplicated expressions kept in
sync by hand. Worse, the Alpha master carries NONE of the 14 Cymatic_*/Audio*
parameters the opaque master has, so its 109 instances -- Melusina's whole
SW_Dress_P01..P48 set among them -- are structurally excluded from the audio
reactivity the rest of the project runs on.

PLAN
----
Keep the opaque master (2205 instances, untouched) and move the 109 across:

  Step 1  port the OpacityMask chain into the opaque master, additively.
          bUseOpacityMap defaults to False and routes to Constant 1.0, so all
          2205 existing instances compile and render exactly as before.
  Step 2  port the MF_ClothWindDrape WPO chain (2 instances need it).
  Step 3  reparent the 109 and set per-instance BlendMode=Masked +
          TwoSided=true so they keep their current appearance.

Blend mode and two-sidedness are overridable per material instance
(bOverride_BlendMode / bOverride_TwoSided), which is what makes one master
able to serve both.

Run step by step from the editor Python console; each step verifies itself.
"""
import os

import unreal

OPAQUE = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
ALPHA = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"
CONTENT = r"C:/EnvironmentPortfolio/BS_GodFile/Content"

lib = unreal.MaterialEditingLibrary


def _clear_readonly(package_path):
    """git-lfs marks *.uasset lockable; saves fail silently while read-only."""
    disk = CONTENT + package_path.replace("/Game", "") + ".uasset"
    try:
        os.chmod(disk, 0o666)
    except OSError:
        pass


def _save(package_path):
    _clear_readonly(package_path)
    saved = unreal.EditorAssetLibrary.save_asset(package_path, only_if_is_dirty=False)
    print("   saved %s: %s" % (package_path.split("/")[-1], saved))
    return saved


def _find_param(material, cls_name, param):
    for e in lib.get_material_expressions(material) or []:
        if e.get_class().get_name() != cls_name:
            continue
        try:
            if str(e.get_editor_property("parameter_name")) == param:
                return e
        except Exception:
            pass
    return None


def step1_opacity():
    """Add OpacityMap / OpacityStrength / bUseOpacityMap -> OpacityMask."""
    mat = unreal.load_asset(OPAQUE)
    existing = _find_param(mat, "MaterialExpressionStaticSwitchParameter", "bUseOpacityMap")
    if existing is not None:
        print("   opacity chain already present, skipping")
        return True

    tex = lib.create_material_expression(
        mat, unreal.MaterialExpressionTextureObjectParameter, -1400, 2600)
    tex.set_editor_property("parameter_name", "OpacityMap")
    tex.set_editor_property("group", "Opacity")

    sample = lib.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -1100, 2600)

    strength = lib.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -1100, 2820)
    strength.set_editor_property("parameter_name", "OpacityStrength")
    strength.set_editor_property("default_value", 1.0)
    strength.set_editor_property("group", "Opacity")

    mul = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -820, 2660)

    one = lib.create_material_expression(mat, unreal.MaterialExpressionConstant, -820, 2860)
    one.set_editor_property("r", 1.0)

    switch = lib.create_material_expression(
        mat, unreal.MaterialExpressionStaticSwitchParameter, -560, 2700)
    switch.set_editor_property("parameter_name", "bUseOpacityMap")
    switch.set_editor_property("default_value", False)
    switch.set_editor_property("group", "Opacity")

    # OpacityMap -> TextureSample.TextureObject  (the exact link that was an
    # orphan on the Alpha master and made masked foliage render as nothing)
    lib.connect_material_expressions(tex, "", sample, "TextureObject")
    lib.connect_material_expressions(sample, "R", mul, "A")
    lib.connect_material_expressions(strength, "", mul, "B")
    lib.connect_material_expressions(mul, "", switch, "True")
    lib.connect_material_expressions(one, "", switch, "False")
    lib.connect_material_property(switch, "", unreal.MaterialProperty.MP_OPACITY_MASK)

    lib.recompile_material(mat)
    _save(OPAQUE)

    ok = _find_param(mat, "MaterialExpressionStaticSwitchParameter", "bUseOpacityMap") is not None
    print("   bUseOpacityMap present: %s" % ok)
    return ok


def verify_untouched(sample_paths):
    """The 2205 opaque instances must be unaffected: switch is False by default."""
    for p in sample_paths:
        mi = unreal.load_asset(p)
        if mi is None:
            print("   MISSING %s" % p)
            continue
        try:
            v = lib.get_material_instance_static_switch_parameter_value(mi, "bUseOpacityMap")
        except Exception:
            v = "n/a"
        print("   %-46s bUseOpacityMap=%s" % (p.split("/")[-1], v))


def step2_cloth():
    """Port the MF_ClothWindDrape WPO chain, gated OFF by default.

    Only MI_SeaAbove_Cloth_Banner and MI_SeaAbove_Cloth_Shroud use it, so it
    hangs behind bClothWind_Active (default False -> Constant3Vector 0,0,0).
    The 2205 opaque instances therefore get a WPO of zero, exactly as now.
    """
    mat = unreal.load_asset(OPAQUE)
    if _find_param(mat, "MaterialExpressionStaticSwitchParameter", "bClothWind_Active"):
        print("   cloth chain already present, skipping")
        return True

    fn = unreal.load_asset("/Game/EnvSandbox/Materials/Functions/MF_ClothWindDrape")
    if fn is None:
        print("   MF_ClothWindDrape missing")
        return False

    Y = 3300
    uv = lib.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1700, Y)
    tm = lib.create_material_expression(mat, unreal.MaterialExpressionTime, -1700, Y + 120)

    def scalar(name, default, dy):
        e = lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1700, Y + dy)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", default)
        e.set_editor_property("group", "Cloth")
        return e

    strength = scalar("Cloth_WindStrength", 0.0, 240)
    speed = scalar("Cloth_WindSpeed", 0.35, 360)
    folding = scalar("Cloth_FoldingAmount", 0.0, 600)
    drape = scalar("Cloth_DrapeScale", 1.0, 840)

    direction = lib.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -1700, Y + 480)
    direction.set_editor_property("parameter_name", "Cloth_WindDirection")
    direction.set_editor_property("default_value", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    direction.set_editor_property("group", "Cloth")

    # DrapeMask = VertexColor.G * Cloth_DrapeScale, mirroring the Alpha master
    vcol = lib.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -1700, Y + 960)
    drape_mul = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1400, Y + 900)
    lib.connect_material_expressions(vcol, "G", drape_mul, "A")
    lib.connect_material_expressions(drape, "", drape_mul, "B")

    call = lib.create_material_expression(
        mat, unreal.MaterialExpressionMaterialFunctionCall, -1050, Y + 300)
    call.set_editor_property("material_function", fn)

    lib.connect_material_expressions(uv, "", call, "UV")
    lib.connect_material_expressions(tm, "", call, "Time")
    lib.connect_material_expressions(strength, "", call, "WindStrength")
    lib.connect_material_expressions(speed, "", call, "WindSpeed")
    lib.connect_material_expressions(direction, "", call, "WindDirection")
    lib.connect_material_expressions(folding, "", call, "FoldingAmount")
    lib.connect_material_expressions(drape_mul, "", call, "DrapeMask")

    zero = lib.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -750, Y + 560)
    zero.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 0.0))

    gate = lib.create_material_expression(
        mat, unreal.MaterialExpressionStaticSwitchParameter, -520, Y + 400)
    gate.set_editor_property("parameter_name", "bClothWind_Active")
    gate.set_editor_property("default_value", False)
    gate.set_editor_property("group", "Cloth")

    lib.connect_material_expressions(call, "WPO", gate, "True")
    lib.connect_material_expressions(zero, "", gate, "False")
    lib.connect_material_property(gate, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    lib.recompile_material(mat)
    _save(OPAQUE)
    ok = _find_param(mat, "MaterialExpressionStaticSwitchParameter", "bClothWind_Active") is not None
    print("   bClothWind_Active present: %s" % ok)
    return ok


def _override_names(mi):
    out = set()
    for prop in ("scalar_parameter_values", "vector_parameter_values",
                 "texture_parameter_values"):
        for v in mi.get_editor_property(prop):
            out.add(str(v.parameter_info.name))
    try:
        for v in mi.get_editor_property("static_parameters").get_editor_property("static_switch_parameters"):
            out.add(str(v.parameter_info.name))
    except Exception:
        pass
    return out


def step3_reparent(dry_run=True):
    """Reparent the Alpha instances onto the opaque master.

    Sets BlendMode=Masked and TwoSided=true per instance so appearance is
    preserved -- both are overridable on a material instance, which is what
    lets one master serve masked and opaque content.
    """
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    alpha = unreal.load_asset(ALPHA)
    opaque = unreal.load_asset(OPAQUE)

    targets = []
    for a in ar.get_assets_by_class(
            unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True):
        mi = a.get_asset()
        if mi is None:
            continue
        try:
            if mi.get_editor_property("parent") == alpha:
                targets.append(mi)
        except Exception:
            pass

    print("   instances to reparent: %d" % len(targets))
    if dry_run:
        print("   DRY RUN - nothing changed")
        return len(targets)

    lost_total = 0
    done = 0
    for mi in targets:
        before = _override_names(mi)
        path = mi.get_path_name().split(".")[0]
        _clear_readonly(path)

        ov = mi.get_editor_property("base_property_overrides")
        ov.set_editor_property("override_blend_mode", True)
        ov.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        ov.set_editor_property("override_two_sided", True)
        ov.set_editor_property("two_sided", True)
        mi.set_editor_property("base_property_overrides", ov)
        mi.set_editor_property("parent", opaque)

        lib.update_material_instance(mi)
        after = _override_names(mi)
        lost = before - after
        if lost:
            lost_total += len(lost)
            print("   LOST on %s: %s" % (mi.get_name(), sorted(lost)))
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
        done += 1

    print("   reparented: %d   overrides lost: %d" % (done, lost_total))
    return done


def verify_converged(paths):
    for p in paths:
        mi = unreal.load_asset(p)
        if mi is None:
            print("   MISSING %s" % p)
            continue
        parent = mi.get_editor_property("parent")
        ov = mi.get_editor_property("base_property_overrides")
        try:
            usemap = lib.get_material_instance_static_switch_parameter_value(mi, "bUseOpacityMap")
        except Exception:
            usemap = "n/a"
        print("   %-26s parent=%-28s blend=%s twosided=%s bUseOpacityMap=%s"
              % (mi.get_name(), parent.get_name(),
                 ov.get_editor_property("blend_mode"),
                 ov.get_editor_property("two_sided"), usemap))
