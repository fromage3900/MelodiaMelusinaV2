# -*- coding: utf-8 -*-
"""Repeatable Melusina lookdev capture.

Frames the player pawn front-on under the level's Ultra_Dynamic_Sky and writes a
1920x1080 HighResShot. Intended to be run inside a LIVE PIE session so lighting,
post-process and material state match what ships — a preview-scene capture is too
dark to judge against the Blender EEVEE reference.

Reference target: ._site_aside_untracked/melusina_beauty_eevee_20260715_01.png
  lavender/periwinkle hair · warm brown skin · pink bodice + sleeves
  layered pink/navy skirt w/ treble-clef motif · pink boots

Usage (in PIE):
    exec(open(r"<repo>/Content/Python/melusina_lookdev_capture.py").read())
    melusina_capture("iter02_note")
"""
import os
import unreal

OUT_DIR = r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/lookdev"


def melusina_capture(tag: str = "iter", pitch: float = -8.0):
    """Place the camera in front of the pawn at head height and shoot."""
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None:
        print("[lookdev] no game world — start PIE first")
        return None
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    pawn = pc.get_controlled_pawn() if pc else None
    if pawn is None:
        print("[lookdev] no player pawn")
        return None

    loc = pawn.get_actor_location()
    # If the pawn has fallen out of the world, put it back on the PlayerStart.
    if loc.z < -5000.0:
        starts = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.PlayerStart)
        if starts:
            loc = starts[0].get_actor_location()
            pawn.set_actor_location(loc, False, False)
            print(f"[lookdev] pawn had fallen to z<-5000 — restored to PlayerStart {loc}")
        else:
            print("[lookdev] pawn out of world and no PlayerStart to recover to")

    # The pawn already has a third-person spring-arm camera, so orbit the boom rather
    # than spawning one. Editor spawn APIs target the EDITOR world and return None in
    # PIE, and GameplayStatics deferred-spawn is not exposed to Python in this build.
    # Setting control rotation swings the existing boom around her — yaw 180 from her
    # facing puts the camera in front, and a slight negative pitch frames head-to-hem.
    yaw = pawn.get_actor_rotation().yaw
    if pc:
        pc.set_control_rotation(unreal.Rotator(pitch, yaw + 180.0, 0.0))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = f"{OUT_DIR}/melusina_{tag}.png"
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, out)
    print(f"[lookdev] pawn={loc} yaw={yaw:.1f} pitch={pitch} -> {out}")
    return out
