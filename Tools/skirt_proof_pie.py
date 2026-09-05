import json
import traceback
import unreal

RESULT = {"checks": [], "screenshots": []}
COSMETIC = "Cos_Skirt_MelusinaV2"
GRANT_ID = "proof_skirt_grant_20260903"
EXPECTED_MESH = "SK_Melusina_V2_Skirt"


def check(name, ok, detail=""):
    RESULT["checks"].append({"name": name, "ok": bool(ok),
                             "detail": str(detail)[:300]})
    unreal.log(f"[SKIRTPROOF] {'PASS' if ok else 'FAIL'} {name} :: {detail}")


try:
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_game_world()
    if world is None:
        RESULT["error"] = "NO_PIE: no game world; start PIE first"
    else:
        check("pie_world_present", True, world.get_name())
        w = unreal.MelodiaWardrobeSubsystem.get(world)
        check("subsystem_resolved", w is not None,
              type(w).__name__ if w else "None")

        if w is not None:
            owned_pre = w.is_owned(COSMETIC)
            check("owned_pre_state", True, f"IsOwned={owned_pre}")

            granted = w.grant_cosmetic(COSMETIC, GRANT_ID)
            check("grant_accepted", granted is True,
                  f"GrantCosmetic -> {granted}")

            pawn_cls = unreal.load_class(
                None,
                "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.BP_MelusinaJRPGCharacter_C")
            check("pawn_class_loaded", pawn_cls is not None, str(pawn_cls))
            pawn = unreal.GameplayStatics.get_actor_of_class(world, pawn_cls)
            check("pawn_found", pawn is not None, str(pawn))

            ward_cls = unreal.load_class(
                None, "/Script/MelodiaWardrobe.MelodiaWardrobeComponent")
            ward = pawn.get_component_by_class(ward_cls) if pawn else None
            check("wardrobe_component_found", ward is not None, str(ward))

            if ward is not None:
                eq = ward.equip_cosmetic(COSMETIC)
                check("equip_accepted", eq is True, f"EquipCosmetic -> {eq}")

                slot_eq = ward.is_slot_equipped(unreal.MelodiaWardrobeSlot.SKIRT)
                check("readback_true", slot_eq is True,
                      f"IsSlotEquipped(Skirt)={slot_eq}")

                sc = ward.get_slot_component(unreal.MelodiaWardrobeSlot.SKIRT)
                mesh_name = None
                if sc is not None:
                    m = sc.get_editor_property("skeletal_mesh_asset")
                    mesh_name = m.get_name() if m is not None else None
                check("mesh_identity", mesh_name == EXPECTED_MESH,
                      f"slot component mesh = {mesh_name}")

                ward.unequip_slot(unreal.MelodiaWardrobeSlot.SKIRT)
                neg = ward.is_slot_equipped(unreal.MelodiaWardrobeSlot.SKIRT)
                check("unequip_readback_false", neg is False,
                      f"after UnequipSlot -> {neg}")

                reeq = ward.equip_cosmetic(COSMETIC)
                reeq_state = ward.is_slot_equipped(
                    unreal.MelodiaWardrobeSlot.SKIRT)
                check("reequip_accepted",
                      reeq is True and reeq_state is True,
                      f"EquipCosmetic -> {reeq}, IsSlotEquipped -> {reeq_state}")
                sc2 = ward.get_slot_component(unreal.MelodiaWardrobeSlot.SKIRT)
                m2 = sc2.get_editor_property("skeletal_mesh_asset") if sc2 else None
                check("mesh_identity_after_reequip",
                      (m2.get_name() if m2 else None) == EXPECTED_MESH,
                      f"{m2}")

                shot_path = (r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit"
                             r"\p0_real_input_run\05_skirt_equipped.png")
                try:
                    unreal.AutomationLibrary.take_high_res_screenshot(
                        1920, 1080, shot_path)
                    import time as _t
                    _t.sleep(2.5)
                    import os as _os
                    RESULT["screenshots"].append(
                        {"path": shot_path,
                         "exists": _os.path.isfile(shot_path)})
                except Exception as se:
                    check("screenshot", False, str(se))
except Exception:
    RESULT["error"] = traceback.format_exc()[-1200:]
finally:
    print("[SKIRTPROOF-JSON]" + json.dumps(RESULT))
