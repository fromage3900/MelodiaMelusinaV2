# -*- coding: utf-8 -*-
"""Stage 1 v2 — restore editor world, create Faraway prototype from Gaea Sakura template, keep Landscape + PlayerStart only."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
TEMPLATE = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/L_Gaea_SakuraTerrace_WP"
SAFE_BOOT = "/Game/ZenForestTest"
LAND_LABEL = "LM_FarawayMother_Terrain"
PLAYER_LABEL = "FM_PlayerStart"
AUDIT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\faraway_mother")
OUT = AUDIT / "stage1_landscape_verify.json"
SEED = 20260829

EAL = unreal.EditorAssetLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log(f"[FM-Stage1] {m}")


def world_path():
    w = UES.get_editor_world()
    return w.get_path_name() if w else None


def ensure_world():
    w = world_path()
    if w:
        log(f"world already {w}")
        if "MelusinaMorning" in w:
            raise RuntimeError("refused: editor on MelusinaMorning")
        return w
    # boot a safe level (not Morning)
    for cand in (SAFE_BOOT, TEMPLATE):
        if EAL.does_asset_exist(cand):
            ok = LES.load_level(cand)
            log(f"boot load {cand} ok={ok} world={world_path()}")
            if world_path():
                return world_path()
    raise RuntimeError("cannot obtain editor world")


def ensure_dirs():
    for d in [
        "/Game/EnvSandbox/Monoliths/FarawayMother",
        "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype",
        "/Game/EnvSandbox/Landscapes/FarawayMother",
    ]:
        if not EAL.does_directory_exist(d):
            EAL.make_directory(d)


def create_level_from_template():
    ensure_dirs()
    if EAL.does_asset_exist(LVL):
        ok = LES.load_level(LVL)
        log(f"loaded existing Faraway ok={ok}")
        return "loaded_existing"
    if not EAL.does_asset_exist(TEMPLATE):
        # blank new level
        LES.new_level(LVL)
        LES.save_current_level()
        log("created blank new_level")
        return "blank"
    # duplicate template asset then open
    try:
        LES.new_level_from_template(LVL, TEMPLATE)
        log("new_level_from_template")
        LES.save_current_level()
        return "from_template"
    except Exception as e:
        log(f"new_level_from_template failed: {e}")
        # Asset duplicate
        ok = EAL.duplicate_asset(TEMPLATE, LVL)
        log(f"duplicate_asset ok={ok}")
        if not ok and not EAL.does_asset_exist(LVL):
            LES.new_level(LVL)
            LES.save_current_level()
            return "blank_fallback"
        LES.load_level(LVL)
        LES.save_current_level()
        return "duplicated_template"


def find_landscapes():
    out = []
    for a in EAS.get_all_level_actors():
        try:
            if isinstance(a, (unreal.Landscape, unreal.LandscapeProxy)):
                out.append(a)
        except Exception:
            pass
    return out


def strip_non_stage1():
    """Remove PCG/dress/volumes except Landscape, PlayerStart, WorldSettings, Brush."""
    keep_types = (
        unreal.Landscape,
        unreal.LandscapeProxy,
        unreal.PlayerStart,
        unreal.WorldSettings,
        unreal.DefaultPhysicsVolume,
        unreal.LevelBounds,
    )
    removed = []
    for a in list(EAS.get_all_level_actors()):
        try:
            if isinstance(a, keep_types):
                continue
            cls = a.get_class().get_name()
            lab = a.get_actor_label() or ""
            # keep directional light + sky for basic visibility
            if cls in ("DirectionalLight", "SkyAtmosphere", "SkyLight", "ExponentialHeightFog", "PostProcessVolume"):
                continue
            # destroy PCG / static mesh clutter from template
            EAS.destroy_actor(a)
            removed.append(lab or cls)
        except Exception as e:
            log(f"skip destroy {e}")
    return removed


def label_landscape_and_player():
    lands = find_landscapes()
    land = lands[0] if lands else None
    if land:
        try:
            land.set_actor_label(LAND_LABEL)
            land.tags = list({str(t) for t in (land.tags or [])} | {"FarawayMother", "Stage1", f"seed_{SEED}"})
        except Exception:
            pass
    # player start
    ps = None
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or (a.get_actor_label() or "") == PLAYER_LABEL:
            ps = a
            break
    if not ps:
        ps = EAS.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
    if ps:
        ps.set_actor_label(PLAYER_LABEL)
        # lift above landscape if we can
        try:
            loc = ps.get_actor_location()
            ps.set_actor_location(unreal.Vector(loc.x, loc.y, max(loc.z, 300)), False, True)
        except Exception:
            pass
    return land, ps


def save_reload_verify():
    LES.save_current_level()
    LES.save_all_dirty_levels()
    ok = LES.load_level(LVL)
    lands = find_landscapes()
    ps = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == PLAYER_LABEL or isinstance(a, unreal.PlayerStart):
            ps = a
            break
    return {
        "reload_ok": bool(ok),
        "world": world_path(),
        "lvl_exists": EAL.does_asset_exist(LVL),
        "landscape_count": len(lands),
        "landscape_label": (lands[0].get_actor_label() if lands else None),
        "player_start": bool(ps),
        "actor_count": len(list(EAS.get_all_level_actors())),
        "not_morning": "MelusinaMorning" not in (world_path() or ""),
    }


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "melodia.faraway_mother.stage1_landscape.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": LVL,
        "template": TEMPLATE,
        "seed": SEED,
        "steps": [],
        "ok": False,
        "pcg_spawned": False,
    }
    boot = ensure_world()
    report["steps"].append({"boot_world": boot})
    mode = create_level_from_template()
    report["steps"].append({"create": mode, "world": world_path()})
    if "MelusinaMorning" in (world_path() or ""):
        report["error"] = "refused_on_morning"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("STAGE1_FAIL morning")
        return 1

    removed = strip_non_stage1()
    report["steps"].append({"stripped": len(removed), "sample": removed[:20]})
    land, ps = label_landscape_and_player()
    report["steps"].append({
        "landscape": bool(land),
        "player": bool(ps),
        "land_class": land.get_class().get_name() if land else None,
    })

    # If no landscape in template, fail clearly — do not fake with StaticMesh
    if not land:
        report["error"] = "no_landscape_in_level_after_template"
        report["notes"] = [
            "Template may be mesh-terrain WP without Landscape actor.",
            "Need manual Landscape create in editor OR different template.",
        ]
        LES.save_current_level()
        OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print("STAGE1_FAIL no_landscape")
        return 1

    verify = save_reload_verify()
    report["verify"] = verify
    report["ok"] = bool(
        verify.get("lvl_exists")
        and verify.get("landscape_count", 0) >= 1
        and verify.get("player_start")
        and verify.get("not_morning")
    )
    report["notes"] = [
        "Stage 1 only — no PCG",
        "Morning untouched",
        "MA: wire landscape MIs + Faraway Copernicus next",
    ]
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("STAGE1 " + json.dumps({
        "ok": report["ok"],
        "world": verify.get("world"),
        "landscapes": verify.get("landscape_count"),
        "player": verify.get("player_start"),
        "lvl_exists": verify.get("lvl_exists"),
        "stripped": len(removed),
    }))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
