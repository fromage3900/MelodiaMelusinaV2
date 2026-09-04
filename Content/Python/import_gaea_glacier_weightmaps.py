"""Import the Gaea Glacier weightmaps and wire them into the landscape material.

WHY THIS EXISTS
---------------
`Saved/GaeaStaging/Glacier/` holds a complete Gaea export for the SeaAbove landscape.
Its `contract.json` declares:

    layers      : ["Base", "Snow", "Water", "Rock"]
    weightmaps  : ["W_Glacier_Snow.png", "W_Glacier_Water.png", "W_Glacier_Rock.png"]
    scale       : { xy: 495.5401306152344, z: 244.453125 }

The four COLOUR maps from that export were imported and are bound on
`MI_Glacier_Landscape_Layered` (T_Glacier_ColorErosion / Combine / GroundTexture / SatMap).
The three WEIGHTMAPS were never imported -- no `W_Glacier_*` asset exists in Content.

That is why `bUseGaeaMasks` is false and the `Gaea_*Mask` slots still hold placeholder
gradient textures: the layer-blend data never reached UE. This script closes that gap.

SLOT NAMING MISMATCH -- READ BEFORE EXTENDING
---------------------------------------------
`M_Master_Nikki_Landscape` exposes three Gaea mask slots:

    Gaea_SlopeMask / Gaea_SlopeWeight
    Gaea_WaterMask / Gaea_WaterWeight
    Gaea_FlowMask  / Gaea_FlowWeight

The Gaea contract's layers are Snow / Water / Rock. Only Water matches by name.

  Water -> Gaea_WaterMask   exact match, bound here.
  Rock  -> Gaea_SlopeMask   defensible: rock is the steep-slope layer, and the master's
                            SlopeSharpness drives the same blend. Bound here.
  Snow  -> (no slot)        NOT bound. "Flow" is an erosion-flow concept, not snow, and
                            binding snow to it would make the parameter name lie about
                            its contents. The master already has a full snow layer
                            (Snow_Albedo, Snow_NormalMap, SnowTint, SnowStrength) but no
                            Gaea_SnowMask to drive it. Adding that slot is a master-graph
                            change and is deliberately left for a human decision.

The Snow weightmap IS imported regardless, so the asset is ready the moment a slot exists.

USAGE
-----
Run from the editor Python console:

    import import_gaea_glacier_weightmaps as g; g.main()

Idempotent: re-importing overwrites in place, re-binding is a no-op if already correct.
"""

import os

import unreal

STAGING = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/GaeaStaging/Glacier"
DEST_PATH = "/Game/Gaea/Glacier/Textures"
LANDSCAPE_MI = "/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered"
CONTENT_ROOT = r"C:/EnvironmentPortfolio/BS_GodFile/Content"

# Gaea weightmap -> master mask slot. Snow intentionally absent; see module docstring.
MASK_BINDINGS = [
    ("W_Glacier_Rock.png", "Gaea_SlopeMask", "Gaea_SlopeWeight", 1.0),
    ("W_Glacier_Water.png", "Gaea_WaterMask", "Gaea_WaterWeight", 1.0),
]
# Imported but not bound -- no matching slot on the master yet.
IMPORT_ONLY = ["W_Glacier_Snow.png"]


def _clear_readonly(package_path):
    """git-lfs marks *.uasset lockable, so saves silently fail while read-only."""
    disk = CONTENT_ROOT + package_path.replace("/Game", "") + ".uasset"
    try:
        os.chmod(disk, 0o666)
    except OSError:
        pass  # not yet on disk (first import) is fine


def import_weightmaps():
    """Import the weightmaps as linear masks. Returns {filename: asset_path}."""
    tasks = []
    for filename in [b[0] for b in MASK_BINDINGS] + IMPORT_ONLY:
        source = os.path.join(STAGING, filename)
        if not os.path.isfile(source):
            unreal.log_error("[Gaea] missing export: %s" % source)
            continue
        task = unreal.AssetImportTask()
        task.filename = source
        task.destination_path = DEST_PATH
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append((filename, task))

    if not tasks:
        return {}

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t for _, t in tasks])

    imported = {}
    for filename, task in tasks:
        paths = list(task.get_editor_property("imported_object_paths"))
        if not paths:
            unreal.log_error("[Gaea] import produced no asset: %s" % filename)
            continue
        imported[filename] = paths[0]
    return imported


def configure_as_mask(asset_path):
    """Weightmaps are DATA, not colour: linear, masks compression, no sRGB.

    Imported as sRGB the blend weights are gamma-curved and every layer boundary
    lands in the wrong place.
    """
    texture = unreal.load_asset(asset_path)
    if texture is None:
        return False
    _clear_readonly(asset_path.split(".")[0])
    texture.set_editor_property("srgb", False)
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_asset(asset_path.split(".")[0], only_if_is_dirty=False)
    return True


def bind_to_material(imported):
    """Bind masks, set weights, enable bUseGaeaMasks. Reads every value back."""
    mi = unreal.load_asset(LANDSCAPE_MI)
    if mi is None:
        unreal.log_error("[Gaea] landscape MI not found: %s" % LANDSCAPE_MI)
        return False

    _clear_readonly(LANDSCAPE_MI)
    lib = unreal.MaterialEditingLibrary

    for filename, mask_param, weight_param, weight in MASK_BINDINGS:
        asset_path = imported.get(filename)
        if not asset_path:
            unreal.log_warning("[Gaea] not imported, skipping bind: %s" % filename)
            continue
        texture = unreal.load_asset(asset_path)
        lib.set_material_instance_texture_parameter_value(mi, mask_param, texture)
        lib.set_material_instance_scalar_parameter_value(mi, weight_param, weight)
        bound = lib.get_material_instance_texture_parameter_value(mi, mask_param)
        got = lib.get_material_instance_scalar_parameter_value(mi, weight_param)
        print("  %-18s -> %-28s  %s = %.3f"
              % (mask_param, bound.get_name() if bound else None, weight_param, got))

    lib.set_material_instance_static_switch_parameter_value(mi, "bUseGaeaMasks", True)
    print("  bUseGaeaMasks      -> %s"
          % lib.get_material_instance_static_switch_parameter_value(mi, "bUseGaeaMasks"))

    saved = unreal.EditorAssetLibrary.save_asset(LANDSCAPE_MI, only_if_is_dirty=False)
    print("  saved: %s" % saved)
    return saved


def main():
    print("[Gaea] importing Glacier weightmaps from %s" % STAGING)
    imported = import_weightmaps()
    for filename, asset_path in imported.items():
        ok = configure_as_mask(asset_path)
        print("  %-22s -> %s  (mask/linear: %s)" % (filename, asset_path, ok))

    if not imported:
        print("[Gaea] nothing imported; aborting before material changes")
        return 1

    print("[Gaea] binding to %s" % LANDSCAPE_MI)
    bind_to_material(imported)

    print("[Gaea] Snow weightmap imported but NOT bound -- the master has no Gaea_SnowMask "
          "slot. See module docstring.")
    return 0


if __name__ == "__main__":
    main()
