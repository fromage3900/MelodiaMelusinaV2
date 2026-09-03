"""Build L_SakuraPath: dusk lighting rig + toon/bloom post + CineCamera + greybox blockout.

Greybox uses engine BasicShapes (replace with the CC0 kit later). Assigns MI_Sakura_*
materials if they exist (run setup_sakura_instances.py first).

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_sakura_scene.py"

Headless:
  python Content/Python/setup_sakura_scene.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sakura_scene.json"

LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
MIROOT = "/Game/EnvSandbox/Materials/Instances/Sakura"
LANDSCAPEROOT = "/Game/EnvSandbox/Materials/Instances/Landscape"
WATERROOT = "/Game/EnvSandbox/Materials/Instances/Water"
CUBE = "/Engine/BasicShapes/Cube.Cube"
PLANE = "/Engine/BasicShapes/Plane.Plane"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _set_tag(actor, tag: str) -> None:
    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _pcg_audit_from_level() -> dict:
    """Read PCG volume + ISM state from the loaded level."""
    import unreal
    import pcg_validate_helpers as vh

    volumes: list[str] = []
    ism_counts: dict[str, int] = {}
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []:
        label = actor.get_actor_label()
        if label.startswith("PCG_"):
            volumes.append(label)
            try:
                ism_counts[label] = vh.count_ism(actor)
            except Exception:
                ism_counts[label] = 0
    return {
        "pcg_preset": "showcase",
        "pcg_volumes": volumes,
        "ism_counts": ism_counts,
    }


def _audit_from_assets() -> dict:
    """Scene audit JSON without mutating the level (headless validate path)."""
    import unreal

    def _mi_exists(name: str, root: str) -> bool:
        return unreal.EditorAssetLibrary.does_asset_exist(f"{root}/{name}.{name}")

    pond_name = "MI_GrandWater_SakuraPond" if _mi_exists("MI_GrandWater_SakuraPond", WATERROOT) else None
    if not pond_name and _mi_exists("MI_Sakura_Water", MIROOT):
        pond_name = "MI_Sakura_Water"
    terrain_name = "MI_Landscape_SakuraGarden" if _mi_exists("MI_Landscape_SakuraGarden", LANDSCAPEROOT) else None
    bank_name = "MI_Landscape_PondBank" if _mi_exists("MI_Landscape_PondBank", LANDSCAPEROOT) else None
    base = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": LEVEL,
        "koi_pond_material": pond_name,
        "landscape_mi": terrain_name,
        "pond_bank_mi": bank_name,
        "grand_water_available": _mi_exists("MI_GrandWater_SakuraPond", WATERROOT),
        "landscape_available": _mi_exists("MI_Landscape_SakuraGarden", LANDSCAPEROOT),
        "stone_path_mi": _mi_exists("MI_Sakura_StonePath", MIROOT),
    }
    for mi_name, root in (
        ("MI_Landscape_SakuraGarden", LANDSCAPEROOT),
        ("MI_Landscape_PondBank", LANDSCAPEROOT),
        ("MI_Sakura_StonePath", MIROOT),
    ):
        path = f"{root}/{mi_name}.{mi_name}"
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            try:
                mi = unreal.load_asset(path)
                base[f"{mi_name}_shadow_flower"] = mi.get_scalar_parameter_value("ShadowFlowerStrength")
            except Exception:
                base[f"{mi_name}_shadow_flower"] = None
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.L_SakuraPath"):
            les.load_level(LEVEL)
            base.update(_pcg_audit_from_level())
    except Exception:
        base.update({"pcg_preset": None, "pcg_volumes": [], "ism_counts": {}})
    return base


def refresh_audit() -> dict:
    report = _audit_from_assets()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build(*, force_new: bool = False) -> str:
    """Create or rebuild the SakuraPath greybox level."""
    import unreal

    force_new = force_new or os.environ.get("BS_SAKURA_FORCE", "").lower() in ("1", "true", "yes")
    force_new = force_new or any("force" in str(a).lower() for a in sys.argv)
    validate_only = os.environ.get("BS_SAKURA_VALIDATE", "").lower() in ("1", "true", "yes")

    if validate_only:
        refresh_audit()
        unreal.log(f"[Sakura] audit refreshed (validate-only) -> {REPORT}")
        return LEVEL

    level_asset = f"{LEVEL}.L_SakuraPath"
    if not force_new and unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        unreal.log(f"[Sakura] reusing existing level {LEVEL}")
        refresh_audit()
        return LEVEL

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if force_new and unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        unreal.EditorAssetLibrary.delete_asset(level_asset)
    if unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        les.load_level(LEVEL)
        for actor in eas.get_all_level_actors() or []:
            try:
                actor.destroy_actor()
            except Exception:
                pass
    else:
        les.new_level(LEVEL)

    def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0)):
        try:
            return eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))
        except Exception as e:
            unreal.log_warning(f"spawn {cls}: {e}")
            return None

    def mi(name, root=MIROOT):
        for p in (f"{root}/{name}", f"{root}/{name}.{name}"):
            if unreal.EditorAssetLibrary.does_asset_exist(p):
                return unreal.load_asset(p)
        return None

    def landscape_mi(name):
        return mi(name, LANDSCAPEROOT)

    def pond_water_mi():
        """Grand water on koi pond; Universal glass fallback if specialist MI missing."""
        return mi("MI_GrandWater_SakuraPond", WATERROOT) or mi("MI_Sakura_Water")

    def greybox(mesh_path, loc, scale, mat=None, label=""):
        a = spawn(unreal.StaticMeshActor, loc)
        if not a:
            return
        a.set_actor_scale3d(unreal.Vector(*scale))
        if label:
            a.set_actor_label(label)
        c = a.static_mesh_component
        c.set_static_mesh(unreal.load_asset(mesh_path))
        if mat:
            c.set_material(0, mat)
        return a

    # ---- lighting: UDS when available, else dusk fallback ----
    import portfolio_scene_integration as scene

    uds_info = scene.ensure_uds_actors(eas, time_of_day=1750.0, spawn_weather=True)
    if not uds_info.get("sky"):
        sun = spawn(unreal.DirectionalLight, (0, 0, 900), (-11, 38, 0))
        if sun:
            sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
            if sc:
                sc.set_editor_property("light_color", unreal.Color(255, 198, 162))
                sc.set_editor_property("intensity", 3.2)
        spawn(unreal.SkyAtmosphere)
        spawn(unreal.SkyLight, (0, 0, 500))
    else:
        scene.disable_manual_sun_if_uds(eas)

    fog = spawn(unreal.ExponentialHeightFog, (0, 0, 60))
    if fog:
        fc = fog.component
        fc.set_editor_property("fog_density", 0.012)
        try:
            fc.set_editor_property("volumetric_fog", True)
        except Exception:
            pass

    # ---- post: bloom + toon/storybook outline stack ----
    import material_lib as lib

    ppv = scene.find_or_spawn_ppv(eas, (0, 0, 300))
    if ppv:
        s = ppv.get_editor_property("settings")
        lib.try_set_editor_property(s, "b_override_bloom_intensity", True)
        lib.try_set_editor_property(s, "bloom_intensity", 1.5)
        lib.try_set_editor_property(s, "b_override_auto_exposure_method", True)
        lib.try_set_editor_property(s, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        lib.try_set_editor_property(s, "b_override_auto_exposure_bias", True)
        lib.try_set_editor_property(s, "auto_exposure_bias", 11.0)
        ppv.set_editor_property("settings", s)
        scene.apply_post_process_stack(ppv)

    # ---- greybox blockout ----
    ground = greybox(PLANE, (0, 0, 0), (60, 60, 1), mi("MI_Sakura_Moss"), "Ground")
    if ground:
        _set_tag(ground, "PCG_Ground")
    for i in range(7):
        stone = greybox(
            CUBE,
            (-1400 + i * 230, -60 + (i % 2) * 50, 6),
            (1.4, 1.0, 0.12),
            mi("MI_Sakura_StonePath"),
            f"PathStone_{i}",
        )
        if stone:
            _set_tag(stone, "PCG_Path")
    red = mi("MI_Sakura_ToriiRed")
    greybox(CUBE, (300, -260, 280), (0.4, 0.4, 5.6), red, "Torii_PillarL")
    greybox(CUBE, (300, 260, 280), (0.4, 0.4, 5.6), red, "Torii_PillarR")
    greybox(CUBE, (300, 0, 560), (0.5, 6.2, 0.4), red, "Torii_TopBeam")
    greybox(CUBE, (300, 0, 470), (0.4, 5.6, 0.28), red, "Torii_Tie")
    torii_pad = greybox(CUBE, (300, 0, 20), (2.2, 2.2, 0.15), red, "Torii_Pad")
    if torii_pad:
        _set_tag(torii_pad, "PCG_Path")
    greybox(CYL, (-600, 360, 90), (0.5, 0.5, 1.8), mi("MI_Sakura_Lantern"), "Lantern")
    bark = mi("MI_Sakura_Bark")
    for x, y in ((-900, -520), (-300, 560), (600, -600), (1000, 500)):
        greybox(CYL, (x, y, 320), (0.7, 0.7, 6.4), bark, f"Trunk_{x}_{y}")
    # koi pond plane (west side) — grand water specialist, not Universal glass
    pond_mat = pond_water_mi()
    pond = greybox(PLANE, (600, -400, 4), (4.0, 3.0, 1.0), pond_mat, "KoiPond")
    if pond:
        _set_tag(pond, "PCG_Pond")
    pond_mi_name = pond_mat.get_name() if pond_mat else "none"
    unreal.log(f"[Sakura] KoiPond material: {pond_mi_name}")
    print(f"SAKURA_POND_MI {pond_mi_name}")

    # Pond bank ring — landscape specialist shore preset (mesh proxy until terrain)
    bank_mat = landscape_mi("MI_Landscape_PondBank")
    if bank_mat:
        greybox(PLANE, (600, -400, 3), (4.6, 3.4, 1.0), bank_mat, "PondBankRing")
    terrain_mat = landscape_mi("MI_Landscape_SakuraGarden")
    terrain_mi_name = terrain_mat.get_name() if terrain_mat else None
    if terrain_mat:
        greybox(PLANE, (0, 0, 1), (55, 55, 1), terrain_mat, "TerrainProxy_SakuraGarden")

    spawn(unreal.CineCameraActor, (-1500, -260, 240), (0, -7, 14))

    pcg_result: dict = {}
    try:
        import setup_pcg_greybox as grey_pcg
        import pcg_portfolio_standards as pcg_std

        pcg_result = grey_pcg.apply_greybox_pcg(
            LEVEL,
            preset="showcase",
            generate=True,
            grass_mi=pcg_std.MI_SAKURA_GRASS,
        )
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in eas.get_all_level_actors():
            if actor.get_actor_label() == pcg_std.ACTOR_GROUND_COVER:
                actor.set_actor_label(pcg_std.ACTOR_SAKURA_VOLUME)
    except Exception as exc:
        unreal.log_warning(f"[Sakura] PCG showcase apply failed: {exc}")
        pcg_result = {"passed": False, "error": str(exc)}

    les.save_current_level()

    water_result: dict = {}
    try:
        import setup_ue_water_simulation as water_sim

        water_result = water_sim.build_all()
    except Exception as exc:
        water_result = {"passed": False, "error": str(exc)}
        unreal.log_warning(f"[Sakura] water sim hook failed: {exc}")

    report = _audit_from_assets()
    report["uds"] = uds_info
    report["koi_pond_material"] = pond_mi_name
    report["landscape_mi"] = terrain_mi_name
    report["pond_bank_mi"] = bank_mat.get_name() if bank_mat else None
    report["pcg_apply"] = pcg_result
    report["water_sim"] = water_result
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Sakura] scene built: {LEVEL} -> {REPORT}")
    return LEVEL


def main() -> int:
    if _in_ue():
        build()
        print(f"SAKURA_SCENE built {LEVEL}")
        return 0
    if not UE_CMD.exists():
        print(f"ERROR: UE not found at {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "setup_sakura_scene.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_sakura_scene.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
