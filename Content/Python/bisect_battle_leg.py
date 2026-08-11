"""bisect_battle_leg.py — READ-ONLY forensic probe for the JRPG/QuillScript battle loop (legs 4-5).

Diagnoses the current editor state WITHOUT mutating anything:

  1. Parent-class chain of every battle widget (stock + Melodia) — detects the
     08-04 reparent pattern (Melodia widget -> stock widget class).
  2. BindWidget-declared variables vs actual widget-tree entries per widget —
     flags reparent/orphaned-ref damage.
  3. E_BattleResult enum values (internal name -> display name).
  4. Live level: actors tagged Encounter_* / melodia_smoke_encounter and any
     actor exposing the stock battle contract (StartBattle + offLevelBattleData
     + OnBattleOver) — the bridge tag-match requirement.
  5. DA_MelodiaIntegrationConfig allowlists (EncounterIds is the battle gate).

Usage (read-only):
    Run inside the Unreal editor, e.g. via Monolith:
        editor_query run_python "Content/Python/bisect_battle_leg.py"
    No compile, no save, no asset/actor mutation. Every section is wrapped in
    try/except; a failure prints [SKIP] instead of aborting.
"""

import unreal

BATTLE_WIDGETS = [
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionsUI",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton",
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle",
    "/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI",
    "/Game/MelodiaIntegration/UI/BP_MelodiaActionsUI",
    "/Game/MelodiaIntegration/UI/BP_MelodiaActionButton",
    "/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt",
]

CONFIG_PATH = "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"
RESULT_ENUM_PATH = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/E_BattleResult"
CONTRACT_FUNCS = ("StartBattle",)
CONTRACT_PROPS = ("offLevelBattleData", "OnBattleOver")

SEC = "=" * 58


def section(title):
    unreal.log("")
    unreal.log(SEC)
    unreal.log(f"[BISECT] {title}")
    unreal.log(SEC)


def walk_widget_tree(widget, depth=0, out=None, max_depth=12):
    """Recursively collect widget names from a UMG tree (read-only)."""
    if out is None:
        out = []
    if widget is None or depth > max_depth:
        return out
    try:
        name = widget.get_name()
        out.append(name)
        if hasattr(widget, "get_editor_property"):
            slots = None
            try:
                slots = widget.get_editor_property("Slots")
            except Exception:
                slots = None
            if slots is not None:
                for slot in slots:
                    try:
                        content = slot.get_editor_property("Content")
                    except Exception:
                        content = None
                    if content is not None:
                        walk_widget_tree(content, depth + 1, out, max_depth)
    except Exception as e:
        unreal.log_warning(f"[BISECT] widget walk failed at {widget}: {e}")
    return out


def dump_widget(path):
    try:
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset is None:
            unreal.log(f"[BISECT] {path}: ASSET NOT FOUND")
            return
    except Exception as e:
        unreal.log(f"[BISECT] {path}: load failed: {e}")
        return

    unreal.log(f"--- {path} ---")

    # 1) Parent class chain.
    chain = []
    try:
        cls = asset.get_editor_property("GeneratedClass")
        while cls is not None:
            name = cls.get_name()
            chain.append(name)
            if name in ("Actor", "UserWidget", "Object"):
                break
            cls = cls.get_super_class()
    except Exception as e:
        unreal.log(f"[BISECT]   parent chain failed: {e}")
        chain = ["<unknown>"]
    unreal.log(f"  ParentClass chain: {' -> '.join(chain)}")

    # 2) NewVariables (Blueprint-declared) — look for BindWidget meta.
    bind_widget_vars = []
    all_vars = []
    try:
        new_vars = asset.get_editor_property("NewVariables")
        for var in new_vars:
            try:
                var_name = var.get_editor_property("VarName")
            except Exception:
                var_name = "<unnamed>"
            all_vars.append(str(var_name))
            try:
                meta = var.get_editor_property("MetaDataArray")
                for entry in meta:
                    key = str(entry.get_editor_property("DataKey"))
                    if key == "BindWidget":
                        bind_widget_vars.append(str(var_name))
            except Exception:
                pass
    except Exception as e:
        unreal.log(f"[BISECT]   NewVariables read failed: {e}")
    unreal.log(f"  NewVariables ({len(all_vars)}): {', '.join(all_vars) if all_vars else '(none)'}")
    unreal.log(f"  BindWidget-declared vars ({len(bind_widget_vars)}): "
               f"{', '.join(bind_widget_vars) if bind_widget_vars else '(none)'}")

    # 3) Widget tree contents.
    tree_names = []
    try:
        tree = asset.get_editor_property("WidgetTree")
        if tree is not None:
            root = tree.get_editor_property("RootWidget")
            tree_names = walk_widget_tree(root)
    except Exception as e:
        unreal.log(f"[BISECT]   WidgetTree read failed: {e}")
    unreal.log(f"  Widget tree entries ({len(tree_names)}): "
               f"{', '.join(tree_names) if tree_names else '(empty/none)'}")

    if bind_widget_vars:
        missing = [v for v in bind_widget_vars if v not in tree_names]
        if missing:
            unreal.log_warning(f"[BISECT]   !! BindWidget vars with NO tree widget: {missing}")
        else:
            unreal.log("  BindWidget vars all present in tree.")


def dump_result_enum():
    try:
        asset = unreal.EditorAssetLibrary.load_asset(RESULT_ENUM_PATH)
        if asset is None:
            unreal.log(f"[BISECT] E_BattleResult: ASSET NOT FOUND")
            return
        try:
            display_map = asset.get_editor_property("DisplayNameMap")
            for entry in display_map:
                internal = str(entry.get_editor_property("Key"))
                display = str(entry.get_editor_property("Value"))
                unreal.log(f"  {internal} -> '{display}'")
        except Exception:
            unreal.log(f"  DisplayNameMap unreadable; class = {asset.get_class().get_name()}")
    except Exception as e:
        unreal.log(f"[BISECT] E_BattleResult read failed: {e}")


def has_function(actor, name):
    try:
        return actor.find_function(name) is not None
    except Exception:
        return False


def has_property(actor, name):
    try:
        return actor.find_property(name) is not None
    except Exception:
        return False


def dump_level_actors():
    world = None
    try:
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor_subsystem.get_editor_world()
        level_name = world.get_name() if world else "<no world>"
        unreal.log(f"[BISECT] Current level: {level_name}")
    except Exception as e:
        unreal.log(f"[BISECT] No editor world: {e}")

    actors = []
    try:
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = actor_subsystem.get_all_level_actors()
    except Exception as e:
        unreal.log(f"[BISECT] EditorActorSubsystem unavailable: {e}")
        return

    unreal.log(f"[BISECT] {len(actors)} actors in level.")
    tagged = []
    contract = []
    for actor in actors:
        try:
            tags = [str(t) for t in actor.get_actor_tags()]
            label = actor.get_actor_label()
            cls = actor.get_class().get_name()
            if any(t.startswith("Encounter_") or t.startswith("melodia_") for t in tags):
                tagged.append(f"    {label} [{cls}] tags={tags}")
            if has_function(actor, CONTRACT_FUNCS[0]) and \
               all(has_property(actor, p) for p in CONTRACT_PROPS):
                contract.append(f"    {label} [{cls}] tags={tags}")
        except Exception:
            continue

    unreal.log("[BISECT] Tagged actors (Encounter_* / melodia_*):")
    for line in tagged:
        unreal.log(line)
    if not tagged:
        unreal.log("    (none)")
    unreal.log("[BISECT] Stock battle-contract actors (StartBattle+offLevelBattleData+OnBattleOver):")
    for line in contract:
        unreal.log(line)
    if not contract:
        unreal.log("    (none)")


def dump_allowlists():
    try:
        cfg = unreal.EditorAssetLibrary.load_asset(CONFIG_PATH)
        if cfg is None:
            unreal.log(f"[BISECT] DA_MelodiaIntegrationConfig: ASSET NOT FOUND")
            return
        for prop in ("EncounterIds", "QuestIds", "NarrativeFlagIds",
                     "TravelLevelIds", "DialogueRewardIds", "SocialStatIds"):
            try:
                value = cfg.get_editor_property(prop)
                names = [str(v) for v in value]
                unreal.log(f"  {prop}: {names}")
            except Exception as e:
                unreal.log(f"  {prop}: <unreadable> ({e})")
    except Exception as e:
        unreal.log(f"[BISECT] Config read failed: {e}")


def main():
    section("1. Battle widget parent chains + BindWidget vs widget tree")
    for path in BATTLE_WIDGETS:
        try:
            dump_widget(path)
        except Exception as e:
            unreal.log(f"[BISECT] {path}: unexpected failure {e}")

    section("2. E_BattleResult enum values")
    dump_result_enum()

    section("3. Current level: tagged actors + stock battle contract")
    dump_level_actors()

    section("4. DA_MelodiaIntegrationConfig allowlists")
    dump_allowlists()

    unreal.log("")
    unreal.log("[BISECT] Probe complete. No assets or actors were modified.")


if __name__ == "__main__":
    main()
