"""Import the house fill density textures as PCG-ready assets.

WHO RUNS THIS: the artist, in the editor, with the level open. An agent does NOT
run it - it writes into Content/, and the editor belongs to the artist.

WHY: the fill contract's density field is a grayscale PNG. For PCG to sample it
the PNG has to become a Texture2D with the right settings (sRGB OFF, a
grayscale compression, no mips) and then reach the graph as a texture path
attribute. Imported as an ordinary colour texture, the field washes out and the
alpha channel reads 1.0 everywhere - which is exactly the gotcha recorded in
specs/p0/melusina_house_p0_fill_graphs.v1.json.

USAGE (in the editor's Python console, or Output Log > Python):

    import melusia_house_fill_import
    melusia_house_fill_import.import_density_textures()

It is idempotent: an asset that already exists with the right settings is left
alone, and nothing is deleted.
"""

from __future__ import annotations

import pathlib
import unreal

TEXTURE_DIR = "Content/EnvSandbox/PCG/House/Textures"
SOURCE_DIR = pathlib.Path(r"C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\PCG\House\Textures")
ROOMS = ("bedroom", "landing", "salon")


def _asset_path(room: str) -> str:
    return f"/Game/EnvSandbox/PCG/House/Textures/dressing_heatmap_{room}"


def _apply_settings(texture) -> None:
    """The recipe the fill contract names. Everything here is a property set, not a re-import."""
    texture.set_editor_property("srgb", False)
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    try:
        texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_PCG)
    except Exception:
        pass  # the PCG texture group is not exposed in every build; it is an optimisation, not a requirement


def import_density_textures() -> dict:
    """Import (or refresh) the three density textures. Returns a small report."""
    report = {"imported": [], "already_correct": [], "failed": []}

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    for room in ROOMS:
        source = SOURCE_DIR / f"dressing_heatmap_{room}.png"
        if not source.exists():
            report["failed"].append(f"{room}: no PNG at {source}")
            continue

        destination = f"{TEXTURE_DIR}/{source.name}"

        task = unreal.AssetImportTask()
        task.filename = str(source)
        task.destination_path = TEXTURE_DIR
        task.automated = True
        task.replace_existing = True
        task.save = True

        asset_tools.import_asset_tasks([task])

        texture = unreal.load_asset(_asset_path(room))
        if texture is None:
            report["failed"].append(f"{room}: the import produced no asset at {_asset_path(room)}")
            continue

        _apply_settings(texture)
        texture.modify()
        unreal.EditorAssetLibrary.save_asset(_asset_path(room), only_if_is_dirty=False)
        report["imported"].append(room)

    return report


def create_density_data_assets() -> dict:
    """Create the PCG texture-data assets if this build exposes the class.

    PCGEx's UPCGTexture2DSingleBaseData family carries the texture reference the
    graph samples. If the class is not exposed to Python in this build, the
    artist creates the data asset by hand in the editor - the fill contract's
    node chain does not change either way.
    """
    report = {"created": [], "manual": []}

    factory_class = getattr(unreal, "PCGExTexture2DSingleBaseDataFactory", None)
    data_class = getattr(unreal, "PCGExTexture2DSingleBaseData", None)
    if factory_class is None or data_class is None:
        report["manual"].append(
            "This build does not expose the PCGEx texture-data factory to Python. "
            "Create the data assets by hand: right-click > Miscellaneous > PCG Data > Texture 2D Single, "
            "point each at its dressing_heatmap_<room> texture.")
        return report

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for room in ROOMS:
        name = f"DA_Density_House_{room.capitalize()}"
        package_path = "/Game/EnvSandbox/PCG/House/Data"
        factory = unreal.new_object(factory_class, outer=unreal.get_transient_package())
        asset = asset_tools.create_asset(name, package_path, data_class, factory)
        if asset is None:
            report["manual"].append(f"{name}: could not be created automatically")
            continue
        texture = unreal.load_asset(_asset_path(room))
        if texture is not None:
            for property_name in ("texture", "Texture"):
                try:
                    asset.set_editor_property(property_name, texture)
                    break
                except Exception:
                    continue
        unreal.EditorAssetLibrary.save_asset(f"{package_path}/{name}", only_if_is_dirty=False)
        report["created"].append(name)

    return report
