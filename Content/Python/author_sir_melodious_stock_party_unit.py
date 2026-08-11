"""Create the stock-JRPG party-unit child used for Sir Melodious recruitment.

Run only in an open UE Editor after the native bridge has been rebuilt. This
duplicates the stock player-unit contract; it does not edit stock template
assets, alter party state, or place actors in a level.
"""
from __future__ import annotations

import unreal

SOURCE = "/Game/TurnBasedJRPGTemplate/Blueprints/Units/PlayerUnits/BP_SwordsmanPlayerUnit"
DESTINATION = "/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit"


def main() -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(DESTINATION):
        unreal.log("MELUSINA_SIR_PARTY_UNIT_EXISTS path=" + DESTINATION)
        return

    source_asset = unreal.EditorAssetLibrary.load_asset(SOURCE)
    if not source_asset:
        raise RuntimeError("Stock player-unit source is missing: " + SOURCE)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    duplicate = asset_tools.duplicate_asset(
        "BP_SirMelodiousPlayerUnit", "/Game/MelodiaIntegration/Party", source_asset
    )
    if not duplicate:
        raise RuntimeError("Could not create Sir Melodious stock party-unit child")

    unreal.EditorAssetLibrary.save_loaded_asset(duplicate)
    unreal.log("MELUSINA_SIR_PARTY_UNIT_CREATED path=" + DESTINATION)
    unreal.log("NEXT: assign Sir's unit display, battle mesh, abilities, and portrait in the new child; do not modify the stock parent.")


main()
