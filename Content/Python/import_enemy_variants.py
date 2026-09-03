from __future__ import annotations

import glob
import json
import os

import unreal
from pathlib import Path

ASSET_PATH = "/Game/Melodia/Data/Enemies/DA_MelodiaEnemyCatalog"
DIR = Path(unreal.Paths.project_content_dir()) / ".." / "Imports" / "Data" / "EnemyVariants"

ELEMENT_MAP = {
    "arcane": unreal.MelodiaSpellElement.ARCANE,
    "arcane_element": unreal.MelodiaSpellElement.ARCANE,
    "forte": unreal.MelodiaSpellElement.FORTE,
    "forte_element": unreal.MelodiaSpellElement.FORTE,
    "gale": unreal.MelodiaSpellElement.GALE,
    "gale_element": unreal.MelodiaSpellElement.GALE,
    "wind": unreal.MelodiaSpellElement.GALE,
    "wind_element": unreal.MelodiaSpellElement.GALE,
    "radiant": unreal.MelodiaSpellElement.RADIANT,
    "radiant_element": unreal.MelodiaSpellElement.RADIANT,
    "stone": unreal.MelodiaSpellElement.STONE,
    "stone_element": unreal.MelodiaSpellElement.STONE,
    "tide": unreal.MelodiaSpellElement.TIDE,
    "tide_element": unreal.MelodiaSpellElement.TIDE,
    "water": unreal.MelodiaSpellElement.TIDE,
    "water_element": unreal.MelodiaSpellElement.TIDE,
    "umbral": unreal.MelodiaSpellElement.UMBRAL,
    "umbral_element": unreal.MelodiaSpellElement.UMBRAL,
}

TIER_BOSS = {"unique", "boss", "miniboss", "elite_boss"}


def _resolve_element(raw: str) -> unreal.MelodiaSpellElement:
    key = raw.strip().lower().replace(" ", "_")
    return ELEMENT_MAP.get(key, unreal.MelodiaSpellElement.FORTE)


def _load_or_create_asset():
    asset = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    if asset:
        unreal.log(f"  [load] {ASSET_PATH}")
        return asset
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.DataAssetFactory()
    asset = tools.create_asset(
        "DA_MelodiaEnemyCatalog",
        "/Game/Melodia/Data/Enemies",
        unreal.MelodiaEnemyDataAsset,
        factory,
    )
    if not asset:
        unreal.log_error("  [FAILED] Could not create data asset")
        return None
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    asset = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    unreal.log(f"  [create] {ASSET_PATH}")
    return asset


def _populate_enemy_def(data: dict) -> unreal.MelodiaEnemyDef:
    enemy = unreal.MelodiaEnemyDef()
    stats = data.get("stats", {})
    intents = data.get("intents", [])

    enemy.set_editor_property("enemy_id", data.get("id", ""))
    enemy.set_editor_property("display_name", unreal.Text.from_string(data.get("display_name", "")))
    enemy.set_editor_property("max_hp", stats.get("max_hp", 300.0))
    enemy.set_editor_property("max_toughness", stats.get("toughness", 100.0))
    enemy.set_editor_property("base_damage", stats.get("base_damage", 15.0))
    enemy.set_editor_property("speed", stats.get("speed", 80))
    enemy.set_editor_property("element", _resolve_element(data.get("element", "forte")))
    enemy.set_editor_property("bpm_override", stats.get("bpm", 0.0))
    enemy.set_editor_property("mesh_scale", 1.0)

    tier = (data.get("tier") or "").strip().lower()
    enemy.set_editor_property("b_is_boss", tier in TIER_BOSS)

    if intents:
        enemy.set_editor_property("primary_intent_name",
                                  unreal.Text.from_string(intents[0].get("name", "")))
        enemy.set_editor_property("primary_intent_damage_multiplier",
                                  intents[0].get("damage_mult", 1.0))

    return enemy


def import_variants():
    asset = _load_or_create_asset()
    if not asset:
        return

    existing_map: dict[str, int] = {}
    for i, e in enumerate(asset.get_editor_property("enemies")):
        eid = e.get_editor_property("enemy_id")
        if eid:
            existing_map[eid] = i

    files = sorted(glob.glob(os.path.join(DIR, "*.json")))
    count_new = 0
    count_updated = 0
    count_skipped = 0
    enemies = list(asset.get_editor_property("enemies"))

    for fp in files:
        name = os.path.basename(fp)
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            unreal.log_warning(f"  [skip] {name}: {exc}")
            count_skipped += 1
            continue

        eid = data.get("id", "")
        if not eid:
            unreal.log_warning(f"  [skip] {name}: missing 'id'")
            count_skipped += 1
            continue

        enemy = _populate_enemy_def(data)

        if eid in existing_map:
            enemies[existing_map[eid]] = enemy
            count_updated += 1
        else:
            enemies.append(enemy)
            existing_map[eid] = len(enemies) - 1
            count_new += 1

    asset.set_editor_property("enemies", enemies)
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)

    unreal.log(
        f"import_enemy_variants: {count_new} new, {count_updated} updated, "
        f"{count_skipped} skipped from {len(files)} files"
    )


if __name__ == "__main__":
    import_variants()
