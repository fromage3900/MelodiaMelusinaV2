"""Fix redirectors in /Game/EnvSandbox/Materials after Melodia migration.

Run: Tools -> Execute Python Script, or Output Log:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_migration_redirectors.py"
"""
import unreal

TARGET = "/Game/EnvSandbox/Materials"

def fix_redirectors(root: str = TARGET) -> bool:
    paths = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
    redirectors = [p for p in paths if unreal.EditorAssetLibrary.does_asset_exist(p)
                   and str(unreal.EditorAssetLibrary.find_asset_data(p).asset_class) == "ObjectRedirector"]
    unreal.log(f"[Redirectors] {root}: {len(redirectors)} redirector(s)")
    if not redirectors:
        unreal.log(f"[Redirectors] OK — no redirectors under {root}")
        return True
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for name in ("fix_up_redirectors", "fixup_referencers", "fix_up_referencers"):
        fn = getattr(asset_tools, name, None)
        if not callable(fn):
            continue
        try:
            fn(root) if fn.__code__.co_argcount >= 2 else fn(redirectors)
            unreal.EditorAssetLibrary.save_directory(root, only_if_is_dirty=False, recursive=True)
            unreal.log(f"[Redirectors] {name} OK — saved {root}")
            return True
        except Exception as exc:
            unreal.log_error(f"[Redirectors] {name} failed: {exc}")
    # UE 5.8: AssetTools batch APIs may be missing; per-asset Fixup via EditorAssetLibrary
    fixed = 0
    for path in redirectors:
        try:
            if hasattr(unreal.EditorAssetLibrary, "fix_up_redirector"):
                unreal.EditorAssetLibrary.fix_up_redirector([path])
                fixed += 1
            elif hasattr(unreal.EditorAssetLibrary, "consolidate_assets"):
                break
        except Exception as exc:
            unreal.log_warning(f"[Redirectors] per-asset fix failed {path}: {exc}")
    if fixed:
        unreal.EditorAssetLibrary.save_directory(root, only_if_is_dirty=False, recursive=True)
        unreal.log(f"[Redirectors] fixed {fixed}/{len(redirectors)} via EditorAssetLibrary")
        return True
    unreal.log_warning(
        "[Redirectors] No Python fix_up API — UE 5.8 manual: enable Filters > "
        "Other Filters > Show Redirectors (or Miscellaneous > Redirectors), "
        "right-click redirector -> Fixup, then Save All. "
        "See Docs/UE58_REDIRECTOR_CLEANUP.md. Root=%s Found=%s"
        % (root, ", ".join(redirectors) or "none"))
    return False


def fix_common_roots() -> None:
    """Clean portfolio roots agents used to describe as Fix Up Redirectors."""
    for root in (
        "/Game/EnvSandbox",
        "/Game/EnvSandbox/Materials",
        "/Game/Characters/Melusina",
        "/Game/Melodia/Characters/Melusina",
    ):
        try:
            fix_redirectors(root)
        except Exception as exc:
            unreal.log_error(f"[Redirectors] skip {root}: {exc}")


if __name__ == "__main__":
    fix_common_roots()
