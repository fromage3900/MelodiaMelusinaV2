"""
Import Design Tokens JSON to UE Data Asset (UMelodiaDesignTokens).
Loads Saved/Audit/melodia_design_tokens_ue.json and populates DA_MelodiaDesignTokens.
"""

import json
import re
from pathlib import Path

import unreal

TOKENS_JSON_PATH = unreal.SystemLibrary.get_project_directory() + "Saved/Audit/melodia_design_tokens_ue.json"
DATA_ASSET_PATH = "/Game/Melodia/Data/DA_MelodiaDesignTokens"


def load_tokens_json():
    json_path = Path(TOKENS_JSON_PATH)
    if not json_path.exists():
        unreal.log_error(f"Tokens JSON not found: {json_path}")
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def hex_to_linear_color(hex_string):
    if not isinstance(hex_string, str):
        return unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
    s = hex_string.strip()
    if s.startswith("{") and s.endswith("}"):
        unreal.log_warning(f"Unresolved token ref left in Hex: {s}")
        return unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
    raw = s.lstrip("#")
    if len(raw) == 6:
        return unreal.LinearColor(int(raw[0:2], 16) / 255.0, int(raw[2:4], 16) / 255.0, int(raw[4:6], 16) / 255.0, 1.0)
    if len(raw) == 8:
        return unreal.LinearColor(
            int(raw[0:2], 16) / 255.0, int(raw[2:4], 16) / 255.0, int(raw[4:6], 16) / 255.0, int(raw[6:8], 16) / 255.0
        )
    if s.startswith("rgba("):
        match = re.match(r"rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", hex_string)
        if match:
            return unreal.LinearColor(
                int(match.group(1)) / 255.0,
                int(match.group(2)) / 255.0,
                int(match.group(3)) / 255.0,
                float(match.group(4)),
            )
    return unreal.LinearColor(1.0, 1.0, 1.0, 1.0)


def resolve_data_asset():
    asset = unreal.EditorAssetLibrary.load_asset(DATA_ASSET_PATH)
    if not asset:
        unreal.log_error(f"Missing asset: {DATA_ASSET_PATH}")
        return None
    if asset.get_class().get_name() == "MelodiaDesignTokens":
        return asset
    if hasattr(asset, "generated_class"):
        gen = asset.generated_class()
        if gen:
            cdo = unreal.get_default_object(gen)
            unreal.log(f"Using Blueprint CDO: {cdo}")
            return cdo
    unreal.log_warning(f"Loaded type {asset.get_class().get_name()} — attempting direct use")
    return asset


def make_color_token(hex_value, description=""):
    linear = hex_to_linear_color(hex_value)
    try:
        tok = unreal.MelodiaColorToken()
        tok.set_editor_property("Hex", str(hex_value) if isinstance(hex_value, str) else "#FFFFFF")
        tok.set_editor_property("LinearColor", linear)
        tok.set_editor_property("Description", description or "")
        return tok
    except Exception as e:
        unreal.log_warning(f"MelodiaColorToken unavailable ({e}); using dict fallback")
        return {"Hex": hex_value, "LinearColor": linear, "Description": description or ""}


def populate_colors(data_asset, colors):
    unreal.log(f"Populating {len(colors)} color tokens...")
    colors_map = {}
    unresolved = 0
    for key, color_data in colors.items():
        hex_value = color_data.get("Hex", "#FFFFFF")
        if isinstance(hex_value, str) and hex_value.startswith("{"):
            unresolved += 1
        colors_map[key] = make_color_token(hex_value, color_data.get("Description", ""))
    try:
        data_asset.set_editor_property("Colors", colors_map)
        unreal.log(f"Colors map set ({len(colors_map)} entries, unresolved_refs={unresolved})")
    except Exception as e:
        unreal.log_error(f"Failed to set Colors: {e}")


def populate_spacing(data_asset, spacing):
    unreal.log(f"Populating {len(spacing)} spacing tokens...")
    spacing_map = {}
    for key, spacing_data in spacing.items():
        try:
            tok = unreal.MelodiaSpacingToken()
            tok.set_editor_property("Value", float(spacing_data.get("Value", 0)))
            tok.set_editor_property("Description", spacing_data.get("Description", "") or "")
            spacing_map[key] = tok
        except Exception:
            spacing_map[key] = {
                "Value": float(spacing_data.get("Value", 0)),
                "Description": spacing_data.get("Description", ""),
            }
    try:
        data_asset.set_editor_property("Spacing", spacing_map)
        unreal.log("Spacing map set")
    except Exception as e:
        unreal.log_warning(f"Could not set Spacing: {e}")


def populate_linear_map(data_asset, prop_name, mapping):
    if not mapping:
        return
    out = {key: hex_to_linear_color(hex_value) for key, hex_value in mapping.items()}
    try:
        data_asset.set_editor_property(prop_name, out)
        unreal.log(f"{prop_name} set ({len(out)})")
    except Exception as e:
        unreal.log_warning(f"Could not set {prop_name}: {e}")


def main():
    unreal.log("=== Importing Design Tokens to UE Data Asset (fixed) ===")
    tokens = load_tokens_json()
    if not tokens:
        return
    data_asset = resolve_data_asset()
    if not data_asset:
        return

    populate_colors(data_asset, tokens.get("Colors", {}))
    populate_spacing(data_asset, tokens.get("Spacing", {}))
    populate_linear_map(data_asset, "GameColors", tokens.get("GameColors", {}))
    populate_linear_map(data_asset, "KeybindColors", tokens.get("KeybindColors", {}))

    package_asset = unreal.EditorAssetLibrary.load_asset(DATA_ASSET_PATH)
    try:
        package_asset.modify()
    except Exception:
        pass
    ok = unreal.EditorAssetLibrary.save_asset(DATA_ASSET_PATH, only_if_is_dirty=False)
    unreal.log(f"save_asset({DATA_ASSET_PATH}) -> {ok}")
    unreal.log("Done. Spot-check DA_MelodiaDesignTokens Colors map in editor.")


if __name__ == "__main__":
    main()
