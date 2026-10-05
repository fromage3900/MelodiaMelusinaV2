"""Stage Horizon Eater teaser in L_MelusinaMorning.

Sets UDS Time of Day to golden hour (1750), enables PPV_GoldenHour,
and sets HorizonEatAmount on MPC_Melodia_Palette for the teaser.

Run inside UE Editor via Monolith (editor_query:run_python):
  import stage_horizon_eater_teaser
  import importlib
  importlib.reload(stage_horizon_eater_teaser)
  stage_horizon_eater_teaser.stage()
"""
from __future__ import annotations

import unreal

UDS_TIME_GOLDEN_HOUR = 1750.0
HORIZON_EAT_AMOUNT = 0.6
HORIZON_TENSION = 0.8
DESTRUCTION_AMOUNT = 0.3


def _log(msg: str):
    unreal.log(f"[Horizon Teaser] {msg}")


def stage() -> dict:
    """Stage the Horizon Eater teaser in the current level."""
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world()
    if world is None:
        raise RuntimeError("No editor world loaded")

    level_name = world.get_name()
    _log(f"Staging in level: {level_name}")

    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    _log(f"Total actors: {len(actors)}")

    # 1. Set UDS Time of Day to golden hour
    uds_actors = [a for a in actors if "Ultra_Dynamic_Sky" in a.get_name()]
    uds_time_set = False
    if uds_actors:
        uds = uds_actors[0]
        # UDS uses a component property, not a direct actor property
        # Try to find the time-of-day property through the component
        try:
            # UDS stores time in the actor's root component or a sky component
            uds.set_editor_property("TimeOfDay", UDS_TIME_GOLDEN_HOUR)
            uds_time_set = True
            _log(f"UDS TimeOfDay set to {UDS_TIME_GOLDEN_HOUR}")
        except Exception as e:
            _log(f"Could not set UDS TimeOfDay directly: {e}")
            # Fallback: try to find the property through the component
            try:
                comp = uds.get_component_by_class(unreal.ActorComponent)
                if comp:
                    comp.set_editor_property("TimeOfDay", UDS_TIME_GOLDEN_HOUR)
                    uds_time_set = True
                    _log(f"UDS TimeOfDay set via component to {UDS_TIME_GOLDEN_HOUR}")
            except Exception as e2:
                _log(f"Could not set UDS TimeOfDay via component: {e2}")
    else:
        _log("No UDS actor found")

    # 2. Enable PPV_GoldenHour (already staged, just verify)
    ppvs = [a for a in actors if "PostProcess" in a.get_name() or "PPV" in a.get_name()]
    golden_hour_ppv = None
    for ppv in ppvs:
        pri = ppv.get_editor_property("Priority")
        if pri == 5.0:
            golden_hour_ppv = ppv
            ppv.set_editor_property("bEnabled", True)
            _log(f"Golden hour PPV enabled: {ppv.get_name()}")
            break

    if golden_hour_ppv is None:
        _log("Golden hour PPV not found (priority 5.0)")

    # 3. Set HorizonEatAmount on MPC_Melodia_Palette
    mpc_actors = [a for a in actors if "MPC_Melodia_Palette" in a.get_name() or "Melodia_Palette" in a.get_name()]
    mpc_set = False
    if mpc_actors:
        mpc = mpc_actors[0]
        try:
            mpc.set_editor_property("HorizonEatAmount", HORIZON_EAT_AMOUNT)
            mpc.set_editor_property("HorizonTension", HORIZON_TENSION)
            mpc.set_editor_property("DestructionAmount", DESTRUCTION_AMOUNT)
            mpc_set = True
            _log(f"MPC set: HorizonEatAmount={HORIZON_EAT_AMOUNT}, HorizonTension={HORIZON_TENSION}, DestructionAmount={DESTRUCTION_AMOUNT}")
        except Exception as e:
            _log(f"Could not set MPC properties: {e}")
    else:
        _log("MPC_Melodia_Palette actor not found")

    # 4. Report state
    result = {
        "level": level_name,
        "uds_time_set": uds_time_set,
        "uds_time": UDS_TIME_GOLDEN_HOUR if uds_time_set else None,
        "golden_hour_ppv": golden_hour_ppv.get_name() if golden_hour_ppv else None,
        "mpc_set": mpc_set,
        "horizon_eat_amount": HORIZON_EAT_AMOUNT if mpc_set else None,
    }

    _log(f"Staging complete: {result}")
    return result


if __name__ == "__main__":
    stage()
