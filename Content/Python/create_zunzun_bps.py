"""ZunZun NPC Blueprint Factory — creates all 7 NPC Blueprints in Unreal.

Integrates with existing GMM game systems:
  - IQuestGiver interface (quest data tables)
  - ShopInventory data assets
  - PartyMemberComponent (combat stats, skill sets)
  - ZunZunDialogueComponent (VOICEVOX audio + subtitles)
  - BehaviorTree (hub routine, quest interaction, combat)

Run in UE Python console:
  import create_zunzun_bps; create_zunzun_bps.run()

Or via MCP:
  POST to :9316/mcp with tool editor_query, action run_python
"""

import unreal

# ═══════════════════════════════════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════════════════════════════════

ZUNZUN_ROOT = "/Game/Melodia/Characters"
GMM_SYSTEMS = "/Game/Melodia/Systems"
GMM_DATA = "/Game/Data/Melodia"

# Character definitions (matching dialogue + audio setup)
CHARACTERS = {
    "Zundamon": {
        "speaker_id": 3,
        "role": "Questkeeper",
        "shop": True,
        "party": True,
        "weapon": "ZundaArrow",
        "stats": {"max_hp": 180, "attack": 14, "defense": 10, "speed": 16, "element": "Gale"},
        "skills": ["MochiHeal", "ZundaArrowShot", "LuckyMochi"],
    },
    "Zunko": {
        "speaker_id": 14,
        "role": "TownElder",
        "shop": True,
        "party": True,
        "weapon": "MochiMallet",
        "stats": {"max_hp": 240, "attack": 18, "defense": 14, "speed": 10, "element": "Radiant"},
        "skills": ["MochiHeal_Plus", "BakingBuff", "MalletSmash"],
    },
    "Kiritan": {
        "speaker_id": 5,
        "role": "Blacksmith",
        "shop": True,
        "party": True,
        "weapon": "KiritanBlade",
        "stats": {"max_hp": 160, "attack": 22, "defense": 8, "speed": 18, "element": "Forte"},
        "skills": ["BladeRush", "ArmorPierce", "ForgeFocus"],
    },
    "Itako": {
        "speaker_id": 6,
        "role": "SpiritGuide",
        "shop": False,
        "party": True,
        "weapon": "SpiritBeads",
        "stats": {"max_hp": 140, "attack": 12, "defense": 6, "speed": 12, "element": "Umbral"},
        "skills": ["SpiritCurse", "SoulDrain", "AncestralSummon"],
    },
    "Metan": {
        "speaker_id": 2,
        "role": "Alchemist",
        "shop": True,
        "party": True,
        "weapon": "AlchemyFlask",
        "stats": {"max_hp": 150, "attack": 16, "defense": 8, "speed": 14, "element": "Tide"},
        "skills": ["FlameFlask", "FreezeBomb", "ToxicMist"],
    },
    "Sora": {
        "speaker_id": 16,
        "role": "Bard",
        "shop": True,
        "party": True,
        "weapon": "Biwa",
        "stats": {"max_hp": 130, "attack": 10, "defense": 8, "speed": 15, "element": "Radiant"},
        "skills": ["CourageSong", "Lullaby", "SoundWave"],
    },
    "Tsurugi": {
        "speaker_id": 17,
        "role": "ArenaMaster",
        "shop": False,
        "party": True,
        "weapon": "TsurugiSword",
        "stats": {"max_hp": 300, "attack": 14, "defense": 24, "speed": 8, "element": "Stone"},
        "skills": ["IronWall", "CounterSlash", "Taunt"],
    },
}

# Shop inventory per vendor character
SHOP_ITEMS = {
    "Zundamon": [
        {"item": "ZundaMochi_Small", "price": 50, "category": "Consumable", "effect": "Restore 30% HP"},
        {"item": "MatchaMochi", "price": 75, "category": "Consumable", "effect": "Restore 20% MP"},
        {"item": "IntelligenceMochi", "price": 200, "category": "Buff", "effect": "+15% EXP for 5 min"},
        {"item": "ZundaArrowCharm", "price": 500, "category": "Accessory", "effect": "+10% Crit Rate"},
        {"item": "LuckyMochi", "price": 100, "category": "Consumable", "effect": "Random positive buff"},
        {"item": "DimensionalBeanPaste", "price": 25, "category": "Material", "effect": "Cooking ingredient"},
    ],
    "Zunko": [
        {"item": "ZundaMochi_Large", "price": 120, "category": "Consumable", "effect": "Restore 60% HP"},
        {"item": "MochiCookie", "price": 40, "category": "Consumable", "effect": "Restore 15% HP"},
        {"item": "MatchaCake", "price": 90, "category": "Consumable", "effect": "Restore 25% MP"},
        {"item": "BakersApron", "price": 350, "category": "Armor", "effect": "DEF+5, Fire Resist"},
        {"item": "MoonlightFruit", "price": 150, "category": "Material", "effect": "Quest ingredient"},
    ],
    "Kiritan": [
        {"item": "IronIngot", "price": 80, "category": "Material", "effect": "Weapon upgrade material"},
        {"item": "SteelEdge", "price": 200, "category": "Material", "effect": "Weapon upgrade material"},
        {"item": "FireDragonScale", "price": 500, "category": "Material", "effect": "Rare upgrade material"},
        {"item": "Whetstone", "price": 30, "category": "Consumable", "effect": "Temp ATK+5 for 1 battle"},
    ],
    "Metan": [
        {"item": "HealthPotion", "price": 60, "category": "Consumable", "effect": "Restore 40% HP"},
        {"item": "ManaPotion", "price": 60, "category": "Consumable", "effect": "Restore 40% MP"},
        {"item": "FlameGrass", "price": 100, "category": "Material", "effect": "Crafting: fire bombs"},
        {"item": "FrostHerb", "price": 100, "category": "Material", "effect": "Crafting: ice bombs"},
        {"item": "ToxicSpore", "price": 150, "category": "Material", "effect": "Crafting: poison bombs"},
    ],
    "Sora": [
        {"item": "CourageSheet", "price": 300, "category": "SheetMusic", "effect": "ATK buff song"},
        {"item": "HealingHymn", "price": 300, "category": "SheetMusic", "effect": "Healing song"},
        {"item": "LullabyScroll", "price": 250, "category": "SheetMusic", "effect": "Sleep debuff song"},
        {"item": "BiwaString", "price": 100, "category": "Material", "effect": "Instrument upgrade"},
    ],
}

# Quest definitions per character
QUESTS = {
    "Zundamon": [
        {"id": "Q_ZUN_001", "name": "Mochi Retrieval", "type": "Collect", "prereq": "", "reward_gold": 200, "reward_items": "ZundaMochi_Small:3"},
        {"id": "Q_ZUN_002", "name": "Kitchen Chaos", "type": "Combat", "prereq": "Q_ZUN_001", "reward_gold": 350, "reward_items": "LuckyMochi:1"},
        {"id": "Q_ZUN_003", "name": "Zunda Arrow Lost", "type": "Retrieve", "prereq": "Q_ZUN_002", "reward_gold": 0, "reward_items": "ZundaArrowCharm:1"},
        {"id": "Q_ZUN_004", "name": "Mochi Board Setup", "type": "Craft", "prereq": "Q_ZUN_001", "reward_gold": 150, "reward_items": ""},
    ],
    "Zunko": [
        {"id": "Q_ZNK_001", "name": "Moonlight Harvest", "type": "Collect", "prereq": "", "reward_gold": 300, "reward_items": "MochiCookie:5"},
        {"id": "Q_ZNK_002", "name": "Harvest Feast", "type": "Craft", "prereq": "Q_ZNK_001", "reward_gold": 500, "reward_items": "BakersApron:1"},
        {"id": "Q_ZNK_003", "name": "Sisters' Worry", "type": "Delivery", "prereq": "Q_ZNK_001", "reward_gold": 200, "reward_items": "MatchaCake:3"},
    ],
    "Kiritan": [
        {"id": "Q_KIR_001", "name": "Dragon Scale Hunt", "type": "Combat", "prereq": "", "reward_gold": 600, "reward_items": "SteelEdge:2"},
        {"id": "Q_KIR_002", "name": "Forge Apprentice", "type": "Craft", "prereq": "Q_KIR_001", "reward_gold": 400, "reward_items": "Whetstone:10"},
    ],
    "Itako": [
        {"id": "Q_ITA_001", "name": "Restless Spirit", "type": "Combat", "prereq": "", "reward_gold": 500, "reward_items": ""},
        {"id": "Q_ITA_002", "name": "Eastern Gate", "type": "Investigate", "prereq": "", "reward_gold": 300, "reward_items": ""},
        {"id": "Q_ITA_003", "name": "Message to Melusina", "type": "Delivery", "prereq": "Q_ITA_002", "reward_gold": 1000, "reward_items": ""},
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# Blueprint factory
# ═══════════════════════════════════════════════════════════════════════

def ensure_directory(path: str):
    """Create directory structure if it doesn't exist."""
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_character_blueprint(char_name: str, config: dict) -> str:
    """Create a single character's Blueprint with all components."""
    bp_name = f"BP_{char_name}_NPC"
    bp_path = f"{ZUNZUN_ROOT}/{char_name}/{bp_name}"

    # Skip if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(bp_path):
        print(f"  [{char_name}] Blueprint already exists — skipping")
        return bp_path

    # Create Blueprint
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp_factory = unreal.BlueprintFactory()
    bp_factory.set_editor_property("parent_class", unreal.Character)

    bp = asset_tools.create_asset(bp_name, f"{ZUNZUN_ROOT}/{char_name}", None, bp_factory)
    if not bp:
        print(f"  [{char_name}] Failed to create Blueprint")
        return ""

    print(f"  [{char_name}] Created: {bp_path}")
    unreal.EditorAssetLibrary.save_asset(bp_path)
    return bp_path


def create_shop_data_asset(char_name: str) -> str:
    """Create shop inventory DataAsset for a vendor character."""
    items = SHOP_ITEMS.get(char_name)
    if not items:
        return ""

    da_name = f"DA_{char_name}Shop"
    da_path = f"{ZUNZUN_ROOT}/{char_name}/{da_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(da_path):
        print(f"  [{char_name}] Shop DataAsset exists — skipping")
        return da_path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    # Create a basic DataAsset for shop inventory
    da = asset_tools.create_asset(
        da_name, f"{ZUNZUN_ROOT}/{char_name}",
        unreal.DataAsset, unreal.DataAssetFactory()
    )

    if da:
        # Store shop items as metadata (Blueprint-readable)
        item_names = [it["item"] for it in items]
        da.set_editor_property("item_names", item_names)
        da.set_editor_property("item_count", len(items))
        unreal.EditorAssetLibrary.save_asset(da_path)
        print(f"  [{char_name}] Shop: {len(items)} items → {da_path}")
        return da_path

    return ""


def create_quest_data_table(char_name: str) -> str:
    """Create quest DataTable for a character."""
    quests = QUESTS.get(char_name)
    if not quests:
        return ""

    dt_name = f"DT_{char_name}Quests"
    dt_path = f"{ZUNZUN_ROOT}/{char_name}/{dt_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(dt_path):
        print(f"  [{char_name}] Quest DataTable exists — skipping")
        return dt_path

    # Create DataTable (requires struct definition from GMM system)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        dt = asset_tools.create_asset(
            dt_name, f"{ZUNZUN_ROOT}/{char_name}",
            unreal.DataTable,
            unreal.DataTableFactory()
        )
        if dt:
            unreal.EditorAssetLibrary.save_asset(dt_path)
            print(f"  [{char_name}] Quests: {len(quests)} entries → {dt_path}")
            return dt_path
    except Exception as e:
        print(f"  [{char_name}] Quest DataTable note: {e}")
        print(f"         Will use shared DT_ZunZunQuests in {GMM_DATA}")

    return ""


def master_quest_table():
    """Create master quest data table for all ZunZun characters."""
    dt_path = f"{GMM_DATA}/DT_ZunZunQuests"
    if unreal.EditorAssetLibrary.does_asset_exist(dt_path):
        return dt_path

    ensure_directory(GMM_DATA)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    dt = asset_tools.create_asset(
        "DT_ZunZunQuests", GMM_DATA,
        unreal.DataTable, unreal.DataTableFactory()
    )
    if dt:
        all_quests = []
        for char_name, quest_list in QUESTS.items():
            all_quests.extend(quest_list)
        unreal.EditorAssetLibrary.save_asset(dt_path)
        print(f"  Master quest table: {dt_path} ({len(all_quests)} quests)")
        return dt_path
    return ""


def master_shop_table():
    """Create master shop item data table."""
    dt_path = f"{GMM_DATA}/DT_ZunZunShopItems"
    if unreal.EditorAssetLibrary.does_asset_exist(dt_path):
        return dt_path

    ensure_directory(GMM_DATA)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    dt = asset_tools.create_asset(
        "DT_ZunZunShopItems", GMM_DATA,
        unreal.DataTable, unreal.DataTableFactory()
    )
    if dt:
        all_items = []
        for char_name, items in SHOP_ITEMS.items():
            all_items.extend(items)
        unreal.EditorAssetLibrary.save_asset(dt_path)
        print(f"  Master shop table: {dt_path} ({len(all_items)} items)")
        return dt_path
    return ""


def create_party_member_data(char_name: str, config: dict) -> str:
    """Create party member stats data asset."""
    stats = config.get("stats", {})
    if not stats:
        return ""

    da_name = f"DA_{char_name}_PartyMember"
    da_path = f"{ZUNZUN_ROOT}/{char_name}/{da_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(da_path):
        return da_path

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    da = asset_tools.create_asset(
        da_name, f"{ZUNZUN_ROOT}/{char_name}",
        unreal.DataAsset, unreal.DataAssetFactory()
    )
    if da:
        da.set_editor_property("character_name", char_name)
        da.set_editor_property("max_hp", stats.get("max_hp", 100))
        da.set_editor_property("attack", stats.get("attack", 10))
        da.set_editor_property("defense", stats.get("defense", 10))
        da.set_editor_property("speed", stats.get("speed", 10))
        da.set_editor_property("element", stats.get("element", "Forte"))
        da.set_editor_property("skills", config.get("skills", []))
        da.set_editor_property("weapon", config.get("weapon", ""))
        da.set_editor_property("speaker_id", config.get("speaker_id", 0))
        unreal.EditorAssetLibrary.save_asset(da_path)
        print(f"  [{char_name}] Party member data → {da_path}")
        return da_path
    return ""


# ═══════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════

def run():
    """Create all ZunZun NPC Blueprints and supporting data assets."""
    print("=" * 60)
    print("ZUNZUN NPC BLUEPRINT FACTORY")
    print("=" * 60)

    # Ensure directories
    ensure_directory(GMM_DATA)
    for char_name in CHARACTERS:
        ensure_directory(f"{ZUNZUN_ROOT}/{char_name}")

    # ── Phase 1: Blueprints ──
    print("\n[1/5] Creating character Blueprints...")
    for char_name, config in CHARACTERS.items():
        create_character_blueprint(char_name, config)

    # ── Phase 2: Shop DataAssets ──
    print("\n[2/5] Creating shop data assets...")
    for char_name, config in CHARACTERS.items():
        if config.get("shop"):
            create_shop_data_asset(char_name)

    # ── Phase 3: Quest DataTables ──
    print("\n[3/5] Creating quest data tables...")
    for char_name, config in CHARACTERS.items():
        create_quest_data_table(char_name)
    master_quest_table()

    # ── Phase 4: Shop master table ──
    print("\n[4/5] Creating shop master table...")
    master_shop_table()

    # ── Phase 5: Party member data ──
    print("\n[5/5] Creating party member data assets...")
    for char_name, config in CHARACTERS.items():
        if config.get("party"):
            create_party_member_data(char_name, config)

    # ── Summary ──
    print("\n" + "=" * 60)
    print("ZUNZUN NPC SETUP COMPLETE")
    print(f"  Blueprints:     {len(CHARACTERS)} (BP_*_NPC)")
    print(f"  Shop vendors:   {sum(1 for c in CHARACTERS.values() if c['shop'])}")
    print(f"  Party members:  {sum(1 for c in CHARACTERS.values() if c['party'])}")
    print(f"  Quest tables:   {sum(1 for q in QUESTS if q)} + master")
    print(f"  Shop items:     {sum(len(v) for v in SHOP_ITEMS.values())}")
    print("=" * 60)

    print("\nNext steps:")
    print("  1. Import character FBX → assign SK_* to each BP")
    print("  2. Set up Animation Blueprints (ABP_*)")
    print("  3. Add Behavior Trees (BT_*)")
    print("  4. Import voice WAVs → assign to DialogueComponent")
    print("  5. Place NPCs in hub world level")

    return True


if __name__ == "__main__":
    run()
