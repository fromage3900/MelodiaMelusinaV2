from pathlib import Path

try:
    from .common import ToolsPackageBase
except ImportError:
    ToolsPackageBase = object


class AssetHelper:
    assets_dir = Path(__file__).parent.parent.parent.parent / "assets"

    @classmethod
    def list_local_model_assets(cls) -> dict[str]:
        assets = {}
        assets_dir = cls.assets_dir / "models"
        for asset_cat in assets_dir.iterdir():
            if not asset_cat.is_dir():
                continue
            for asset in asset_cat.glob("*.blend"):
                assets.setdefault(asset_cat.stem, []).append(asset.stem)
        return assets

    @classmethod
    def load_model_into(cls, asset_path: str) -> dict:
        import bpy
        from mathutils import Vector

        old_objects = set(bpy.data.objects)
        with bpy.data.libraries.load(asset_path) as (data_from, data_to):
            data_to.objects = data_from.objects
        new_objects = set(bpy.data.objects) - old_objects
        loaded_object_info = {}
        for o in new_objects:
            bpy.context.scene.collection.objects.link(o)
            loaded_object_info[o.name] = {
                "translation": tuple(o.location),
                "bound_box": [tuple(o.matrix_world @ Vector(v)) for v in o.bound_box],
            }
        return {
            "asset_name": asset_path,
            "load_status": "success",
            "loaded_objects": [o.name for o in new_objects],
            "loaded_object_info": loaded_object_info,
        }


class AssetTools(ToolsPackageBase):
    """
    Custom Asset Tools.
    """

    def list_local_model_assets() -> dict[str, list[str]]:
        """
        List local model assets, descripted by their category and name.
        If user wants to create scene or object, you should use custom assets first if possible.

        Returns: dict[asset_cat, list[asset_name]] like this
        {
            "Building": ["School", "House"],
            "Plant": ["Tree", "Bush"],
        }
        """
        assets = AssetHelper.list_local_model_assets()
        return assets

    # def get_model_info(asset_name: str) -> dict[str]:
    #     """
    #     Get model Info, such as bound box, file path

    #     Args:
    #     - asset_name: Asset Name to Query
    #     """
    #     object_info = AssetHelper.load_model_into(asset_name)

    #     return object_info.get("loaded_object_info")

    def load_model(asset_cat: str, asset_name: str) -> dict:
        """
        Load Asset to Blender.

        Args:
        - asset_cat: Asset Category.
        - asset_name: Asset Name to Load
        """
        asset_path = AssetHelper.assets_dir / "models" / asset_cat / f"{asset_name}.blend"
        if not asset_path.exists():
            raise FileNotFoundError(f"Asset {asset_name} not found in {asset_cat}")
        return AssetHelper.load_model_into(asset_path.as_posix())


if __name__ == "__main__":
    assets = AssetTools.list_local_model_assets()
    print(assets)
