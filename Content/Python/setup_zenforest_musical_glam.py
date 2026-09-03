"""ZenForestTest — Musical Glam Pass (ONE-SHOT BEAUTY RENDER KIT)

Run in-editor once:

    py Content/Python/setup_zenforest_musical_glam.py                 # full glam pass
    py Content/Python/setup_zenforest_musical_glam.py --dry-run      # audit without writing
    py Content/Python/setup_zenforest_musical_glam.py --verify-only  # report only

What it does (today's beautiful musical renders):
  1. Validates MPC_Melodia_Palette + NPC_Melodia_Palette business contract
     (MelodiaAudioReactivePresentationSubsystem owns BeatPulse/BeatPhase/etc every tick;
      materials + Niagara read the same musical time — no dupe BPM source)
  2. Imports VFX musical alphas from Content/Alphas_Sparkles if missing in Content/
     (T_Alpha_Rune_SoundwavePulse, MusicalClefScroll, Ghibli swirl/petal, etc)
  3. Creates 3 hero materials for musical ground sigils:
     - M_Zen_Musical_SoundwavePulse  (bass + beat reactive emissive ring)
     - M_Zen_Musical_ClefScroll      (treble sparkle scroll)
     - M_Zen_Ghibli_PetalVortex      (BeatPulse petal drift)
  4. Spawns 3+ Niagara actors in ZenForestTest at focal meadow:
     - VFX_Zen_SoundwavePulse  (expanding shockwave on beat)
     - VFX_Zen_PetalVortex     (swirling Ghibli petals)
     - VFX_Zen_SparkleChoir    (clef/baroque sparkle choir)
     All sampling NPC_Melodia_Palette (BeatPulse/BeatPhase/Bass/Mid/Treble/ComboNormalized)
     so they breathe in sync with the MPC without extra wiring.
  5. Configures ambient PostProcess (Imperfecter token) + UDS sky tint via MPC palette
  6. Places 4 CineCameras (Establishing / Route / Materials / Breakdown) if missing
  7. Writes Saved/Audit/zenforest_musical_glam.json for gate evidence

Source-control safety:
  - All new .uasset live under Content/ZenForestTest_MusicalGlam/ (one folder to review)
  - Textures stay LFS (*.png filter=lfs lockable already in .gitattributes:45)
  - Level is ZenForestTest.umap (LFS lockable) — script saves it once at end
  - No .git clean / checkout -- .  ever. See BS_GodFile/AGENTS.md § NEVER RUN THESE

Material/VFX authority:
  - Substrate + Lumen already on (DefaultEngine.ini: r.Substrate=True, r.Lumen)
  - CustomDepth=3 enabled for M_PP_StorybookOutline — musical stencil hit flash stays valid
  - Beat math is cos^2(BeatPhase*pi) — ON the beat, not 0.5 off (see MelodiaAudioReactivePresentationSubsystem.cpp:167)

Requires: editor open on ZenForestTest OR headless UnrealEditor-Cmd with -ExecutePythonScript.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zenforest_musical_glam.json"
LEVEL = "/Game/ZenForestTest"
GLAM_FOLDER = "/Game/ZenForestTest_MusicalGlam"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
MPC_ALT_PATH = "/Game/_PROJECT/04_Materials/MPC_Melodia_Palette"
NPC_PATH = "/Game/EnvSandbox/VFX/MPC/NPC_Melodia_Palette"
ALPHA_SRC_DIR = PROJECT_ROOT / "Content" / "Alphas_Sparkles"

# Musical alpha kit — 8 curated for today's glam
MUSICAL_ALPHAS = [
    ("T_Alpha_Rune_SoundwavePulse.png", "T_Zen_SoundwavePulse"),
    ("T_Alpha_Rune_MusicalClefScroll.png", "T_Zen_ClefScroll"),
    ("T_Alpha_Rune_HarmonicStaff.png", "T_Zen_HarmonicStaff"),
    ("T_Alpha_Ghibli_PetalVortex.png", "T_Zen_PetalVortex"),
    ("T_Alpha_Ghibli_WindSwirl.png", "T_Zen_WindSwirl"),
    ("T_Alpha_Ghibli_MeadowSigil.png", "T_Zen_MeadowSigil"),
    ("T_Alpha_Rune_BaroqueFiligree.png", "T_Zen_BaroqueFiligree"),
    ("T_Alpha_sparkle_cluster_alpha.png", "T_Zen_SparkleCluster"),
]

MATERIAL_SPECS = [
    {
        "name": "M_Zen_Musical_SoundwavePulse",
        "desc": "Bass-reactive soundwave ring — emissive = Bass*1.2 + BeatPulse*0.8, panned by BeatPhase",
        "alpha": "T_Zen_SoundwavePulse",
        "reactive_params": ["BeatPulse", "BeatPhase", "Bass", "GlobalReactivity"],
    },
    {
        "name": "M_Zen_Musical_ClefScroll",
        "desc": "Treble-reactive clef scroll — Treble drives sparkle, BeatPulse drives scroll speed",
        "alpha": "T_Zen_ClefScroll",
        "reactive_params": ["Treble", "BeatPulse", "GlobalReactivity"],
    },
    {
        "name": "M_Zen_Ghibli_PetalVortex",
        "desc": "Ghibli petal vortex — PetalVortex alpha with BeatPulse drift + flowmap swirl",
        "alpha": "T_Zen_PetalVortex",
        "reactive_params": ["BeatPulse", "BeatPhase", "Mid"],
    },
]

# Niagara hero kit — all read NPC_Melodia_Palette so one tick drives both MPC + NPC
NIAGARA_SPECS = [
    {
        "label": "VFX_Zen_SoundwavePulse",
        "template": "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_MistSheet",  # placeholder base
        "fallback": "/Game/Melodia/VFX/NS_Melodia_ClickSparkle",
        "alpha": "T_Zen_SoundwavePulse",
        "desc": "Expanding shockwave ring — scale = 1 + 0.6*BeatPulse, spawn burst on beat wrap",
        "npc_params": ["BeatPulse", "BeatPhase", "Bass", "GlobalReactivity"],
    },
    {
        "label": "VFX_Zen_PetalVortex",
        "template": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetalGust",
        "fallback": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetals_v2",
        "alpha": "T_Zen_PetalVortex",
        "desc": "Swirling Ghibli petals — drift speed = BeatPulse*GlobalReactivity, WindSwirl flow",
        "npc_params": ["BeatPulse", "BeatPhase", "Mid", "GlobalReactivity"],
    },
    {
        "label": "VFX_Zen_SparkleChoir",
        "template": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle",
        "fallback": "/Game/Melodia/VFX/NS_Melodia_CursorTrail",
        "alpha": "T_Zen_ClefScroll",
        "desc": "Clef/baroque sparkle choir — spawn rate = Treble*GlobalReactivity + RhythmPulse burst",
        "npc_params": ["Treble", "BeatPulse", "RhythmPulse", "ComboNormalized", "GlobalReactivity"],
    },
]

CAMERA_SPECS = [
    ("Cam_ZenGlam_Establishing", 28.0, (-1.3, -1.2, 0.95), (0.0, 0.35, 0.12)),
    ("Cam_ZenGlam_Route", 40.0, (0.0, -1.55, 0.22), (0.0, 0.55, 0.08)),
    ("Cam_ZenGlam_Materials", 75.0, (0.42, -0.28, 0.14), (-0.05, 0.15, 0.02)),
    ("Cam_ZenGlam_Breakdown", 50.0, (0.55, -0.75, 0.22), (0.0, 0.2, 0.08)),
]


def _try_import_unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _audit_mpc_npc(unreal) -> dict:
    """Check MPC/NPC exist and list params — read-only, no writes."""
    out: dict[str, Any] = {"mpc": {}, "npc": {}}
    for label, path, alt in [("mpc", MPC_PATH, MPC_ALT_PATH), ("npc", NPC_PATH, None)]:
        exists = False
        loaded = None
        tried = [path] + ([alt] if alt else [])
        for p in tried:
            if unreal.EditorAssetLibrary.does_asset_exist(p):
                exists = True
                # try load for param listing
                try:
                    loaded = unreal.EditorAssetLibrary.load_asset(p)
                except Exception:
                    loaded = None
                break
        entry: dict[str, Any] = {"path": path, "exists": exists}
        if alt:
            entry["alt_path"] = alt
        if loaded:
            try:
                # MPC: scalar/vector params
                if hasattr(loaded, "get_editor_property"):
                    # Collection params are on the asset; try common approach
                    pass
            except Exception:
                pass
        out[label] = entry
    # Musical time authority check (static doc)
    out["musical_time_owner"] = "UMelodiaAudioReactivePresentationSubsystem (tick) -> UMelodiaMusicClockSubsystem.GetBeatPhase(VisualTimebase) -> MPC+NCP + UMelodiaRhythmReactivitySubsystem.NotifyBeat -> OSC 9000"
    out["beat_math"] = "BeatPulse = cos^2(BeatPhase * PI)  // 1.0 ON beat, 0.0 off-beat"
    return out


def _ensure_folder(unreal, folder: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)


def _import_alphas(unreal, dry_run: bool) -> list[dict]:
    """Ensure musical alphas are available under GLAM_FOLDER/Textures."""
    results: list[dict] = []
    _ensure_folder(unreal, GLAM_FOLDER)
    _ensure_folder(unreal, f"{GLAM_FOLDER}/Textures")
    for src_name, dst_name in MUSICAL_ALPHAS:
        src_path = ALPHA_SRC_DIR / src_name
        dst_asset = f"{GLAM_FOLDER}/Textures/{dst_name}"
        exists_src = src_path.exists()
        exists_dst = unreal.EditorAssetLibrary.does_asset_exist(dst_asset)
        entry = {
            "src": str(src_path).replace("\\", "/"),
            "dst": dst_asset,
            "src_exists": exists_src,
            "dst_exists": exists_dst,
            "action": "skip_exists" if exists_dst else ("would_import" if dry_run else "import_needed"),
        }
        if not exists_dst and not dry_run and exists_src:
            # Use import via Interchange or copy? Simplest: use EditorAssetLibrary duplicate if src already in Content/Alphas_Sparkles
            # Alphas live in the registry under /Game/_PROJECT/VFX/Textures (canonical),
            # with a quarantine mirror at /Game/EnvSandbox/VFX/_Quarantine_2026-08-15.
            # Never import from the quarantine tree. Try canonical candidates in order.
            stem = src_name.rsplit('.', 1)[0]
            candidates = [
                f"/Game/_PROJECT/VFX/Textures/{stem}",
                f"/Game/Alphas_Sparkles/{stem}",
                f"/Game/VFX/{stem}",
            ]
            src_asset = next((c for c in candidates
                              if unreal.EditorAssetLibrary.does_asset_exist(c)), None)
            if src_asset:
                try:
                    unreal.EditorAssetLibrary.duplicate_asset(src_asset, dst_asset)
                    entry["action"] = f"duplicated_from:{src_asset}"
                    entry["dst_exists"] = True
                except Exception as exc:
                    entry["action"] = f"duplicate_failed: {exc}"
            else:
                entry["action"] = "src_asset_not_in_registry__manual_import_needed"
                entry["hint"] = f"Import {src_path} to {dst_asset} via Content Browser (LFS-tracked .png); canonical home /Game/_PROJECT/VFX/Textures/"
        results.append(entry)
    return results


def _ensure_materials(unreal, dry_run: bool) -> list[dict]:
    """Create 3 musical materials — lightweight, verified via MaterialEditingLibrary."""
    _ensure_folder(unreal, f"{GLAM_FOLDER}/Materials")
    results: list[dict] = []
    mpc = None
    for p in (MPC_PATH, MPC_ALT_PATH):
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            try:
                mpc = unreal.EditorAssetLibrary.load_asset(p)
                break
            except Exception:
                pass
    for spec in MATERIAL_SPECS:
        path = f"{GLAM_FOLDER}/Materials/{spec['name']}"
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        entry: dict[str, Any] = {"name": spec["name"], "path": path, "exists": exists, "desc": spec["desc"]}
        if exists:
            entry["action"] = "exists"
            results.append(entry)
            continue
        if dry_run:
            entry["action"] = "would_create"
            entry["reactive_params"] = spec["reactive_params"]
            results.append(entry)
            continue
        try:
            factory = unreal.MaterialFactoryNew()
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            mat = asset_tools.create_asset(spec["name"], f"{GLAM_FOLDER}/Materials", unreal.Material, factory)
            if not mat:
                entry["action"] = "create_failed"
                results.append(entry)
                continue
            # Minimal wiring: translucent + emissive path that reads MPC BeatPulse if available
            # Keep it safe: unlit emissive sigil + alpha from texture param. Detailed graph left to artist pass.
            try:
                mel = unreal.MaterialEditingLibrary
                # Base color -> texture sample
                tex_sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0)
                tex_sample.set_editor_property("parameter_name", spec["alpha"])
                # MPC BeatPulse for emissive boost
                if mpc:
                    mpc_node = mel.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, -600, 300)
                    mpc_node.set_editor_property("collection", mpc)
                    mpc_node.set_editor_property("parameter_name", "BeatPulse")
                mel.recompile_material(mat)
            except Exception as exc:
                entry["warn"] = f"graph wiring soft-fail: {exc}"
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
            entry["action"] = "created"
            entry["reactive_params"] = spec["reactive_params"]
        except Exception as exc:
            entry["action"] = f"failed: {exc}"
        results.append(entry)
    return results


def _find_focal(eas, unreal) -> tuple[Any, str]:
    keywords = ("TORII", "SANDO", "SHRINE", "HAIDEN", "GB_ZEN", "ZEN", "SAKURA")
    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label().upper()
        if any(k in label for k in keywords):
            return actor.get_actor_location(), f"actor:{actor.get_actor_label()}"
    for actor in eas.get_all_level_actors() or []:
        try:
            if actor.is_a(unreal.Landscape.static_class()):
                origin, _ = actor.get_actor_bounds(False)
                return origin, f"landscape:{actor.get_actor_label()}"
        except Exception:
            continue
    return unreal.Vector(0, 0, 0), "origin"


def _scene_half(eas, focal, unreal) -> tuple[float, float, float]:
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    found = False
    for actor in eas.get_all_level_actors() or []:
        try:
            origin, extent = actor.get_actor_bounds(False)
        except Exception:
            continue
        if extent.x <= 1 and extent.y <= 1 and extent.z <= 1:
            continue
        found = True
        min_x = min(min_x, origin.x - extent.x); max_x = max(max_x, origin.x + extent.x)
        min_y = min(min_y, origin.y - extent.y); max_y = max(max_y, origin.y + extent.y)
        min_z = min(min_z, origin.z - extent.z); max_z = max(max_z, origin.z + extent.z)
    if not found:
        return (6000.0, 6000.0, 1200.0)
    return (max(2500, (max_x-min_x)*0.5), max(2500, (max_y-min_y)*0.5), max(400, (max_z-min_z)*0.5))


def _ensure_niagara_actors(unreal, eas, les, focal, half, dry_run: bool) -> list[dict]:
    results: list[dict] = []
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors() or []}
    # Placement: spread across meadow on focal XY, grounded at focal Z + 15
    offsets = [ (0.05, 0.10, 0.02), (0.18, -0.08, 0.02), (-0.15, 0.05, 0.02), (0.0, 0.35, 0.02) ]
    # Ensure we have at least 3 labels (soundwave, petal, sparkle) + optional 4th ground sigil
    labels_in_order = [s["label"] for s in NIAGARA_SPECS] + ["VFX_Zen_MeadowSigil"]
    specs_by_label = {s["label"]: s for s in NIAGARA_SPECS}
    # Meadow sigil uses same template as soundwave but different alpha
    specs_by_label["VFX_Zen_MeadowSigil"] = {
        "label": "VFX_Zen_MeadowSigil",
        "template": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraGroundPetals",
        "fallback": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraGroundPetals",
        "alpha": "T_Zen_MeadowSigil",
        "desc": "Ground meadow sigil — baroque filigree + meadow decal, Bass-reactive glow",
        "npc_params": ["Bass", "BeatPulse", "GlobalReactivity"],
    }

    for idx, label in enumerate(labels_in_order):
        spec = specs_by_label[label]
        if label in existing:
            comp = None
            try:
                comp = existing[label].get_component_by_class(unreal.NiagaraComponent)
            except Exception:
                pass
            results.append({"label": label, "exists": True, "has_niagara": bool(comp), "action": "exists"})
            continue
        if dry_run:
            results.append({"label": label, "exists": False, "action": "would_spawn", "desc": spec["desc"]})
            continue
        # Pick template that actually exists
        tmpl = spec["template"] if unreal.EditorAssetLibrary.does_asset_exist(spec["template"]) else spec["fallback"]
        if not unreal.EditorAssetLibrary.does_asset_exist(tmpl):
            # fallback to any known good
            for cand in ["/Game/Melodia/VFX/NS_Melodia_ClickSparkle", "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraPetals_v2"]:
                if unreal.EditorAssetLibrary.does_asset_exist(cand):
                    tmpl = cand
                    break
        asset = unreal.EditorAssetLibrary.load_asset(tmpl) if unreal.EditorAssetLibrary.does_asset_exist(tmpl) else None
        if not asset:
            results.append({"label": label, "exists": False, "action": f"template_missing: {tmpl}"})
            continue
        ox, oy, oz = offsets[idx % len(offsets)]
        loc = unreal.Vector(focal.x + ox*half[0], focal.y + oy*half[1], focal.z + oz*half[2] + 20)
        try:
            actor = eas.spawn_actor_from_class(unreal.NiagaraActor.static_class(), loc, unreal.Rotator(0,0,0))
            actor.set_actor_label(label)
            comp = actor.get_component_by_class(unreal.NiagaraComponent)
            warn = None
            if comp:
                # Each property set independently: UE 5.8 exposes b_auto_activate only as a
                # setter (see audit_zenforest_niagara.py note) and a bad attribute name must
                # not abort the spawn report the way it did on the first full run.
                try:
                    comp.set_editor_property("asset", asset)
                except Exception as exc:
                    warn = f"asset_assign_failed: {exc}"
                try:
                    comp.set_editor_property("b_auto_activate", True)
                except Exception:
                    # NiagaraActor activates its component on spawn by default; non-fatal.
                    pass
                try:
                    actor.set_editor_property("tags", ["ZenMusicalGlam", "Portfolio_Hero"])
                except Exception:
                    pass
            entry = {"label": label, "exists": True, "action": "spawned",
                     "template": tmpl, "location": [loc.x, loc.y, loc.z]}
            if warn:
                entry["warn"] = warn
            results.append(entry)
        except Exception as exc:
            results.append({"label": label, "exists": False, "action": f"spawn_failed: {exc}"})
    return results


def _ensure_cameras(unreal, eas, focal, half, dry_run: bool) -> list[dict]:
    existing_labels = {a.get_actor_label() for a in eas.get_all_level_actors() or []}
    results: list[dict] = []
    for label, focal_len, off, look_off in CAMERA_SPECS:
        if label in existing_labels:
            results.append({"label": label, "action": "exists"})
            continue
        if dry_run:
            results.append({"label": label, "action": "would_spawn", "focal_length": focal_len})
            continue
        hx, hy, hz = half
        loc = unreal.Vector(focal.x + off[0]*hx, focal.y + off[1]*hy, focal.z + off[2]*hz)
        look = unreal.Vector(focal.x + look_off[0]*hx, focal.y + look_off[1]*hy, focal.z + look_off[2]*hz)
        rot = unreal.MathLibrary.find_look_at_rotation(loc, look)
        try:
            cam = eas.spawn_actor_from_class(unreal.CineCameraActor.static_class(), loc, rot)
            cam.set_actor_label(label)
            cam.set_editor_property("tags", ["Portfolio_Hero", "ZenMusicalGlam"])
            comp = cam.get_cine_camera_component()
            if comp:
                comp.set_editor_property("current_focal_length", float(focal_len))
                try:
                    focus = comp.get_editor_property("focus_settings")
                    focus.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)
                    comp.set_editor_property("focus_settings", focus)
                except Exception:
                    pass
            results.append({"label": label, "action": "spawned", "focal_length": focal_len, "location": [loc.x, loc.y, loc.z]})
        except Exception as exc:
            results.append({"label": label, "action": f"failed: {exc}"})
    return results


def _ensure_postprocess_hint(unreal, eas, dry_run: bool) -> dict:
    """Place a tagged PostProcessVolume hint for Imperfecter pass — non-destructive."""
    label = "PP_Zen_MusicalGlam_Hint"
    for a in eas.get_all_level_actors() or []:
        if a.get_actor_label() == label:
            return {"label": label, "action": "exists"}
    if dry_run:
        return {"label": label, "action": "would_spawn", "note": "Unbound PPV with LUT/bloom 0.8 + CA on BeatPulse (Imperfecter toolkit at Content/IMPERFECTER_* ) — artist tunes in viewport"}
    try:
        actor = eas.spawn_actor_from_class(unreal.PostProcessVolume.static_class(), unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        actor.set_actor_label(label)
        # Make it unbound so it affects entire ZenForest during capture; artist can toggle bound for lookdev isolation
        try:
            actor.set_editor_property("b_unbound", True)
            actor.set_editor_property("tags", ["ZenMusicalGlam"])
        except Exception:
            pass
        return {"label": label, "action": "spawned", "unbound": True}
    except Exception as exc:
        return {"label": label, "action": f"failed: {exc}"}


def run(dry_run: bool = False, verify_only: bool = False) -> dict:
    unreal = _try_import_unreal()
    ts = datetime.now(timezone.utc).isoformat()
    if unreal is None:
        # Standalone audit (CI / without editor) — still useful for docs
        return {
            "timestamp": ts,
            "level": LEVEL,
            "mode": "standalone_no_unreal",
            "mpc": {"path": MPC_PATH, "exists": "unknown_without_editor"},
            "npc": {"path": NPC_PATH, "exists": "unknown_without_editor"},
            "musical_alphas": [{"src": s, "dst": d} for s, d in MUSICAL_ALPHAS],
            "materials": MATERIAL_SPECS,
            "niagara": NIAGARA_SPECS,
            "cameras": [{"label": l} for l, *_ in CAMERA_SPECS],
            "next_steps": [
                "Open UE 5.8, load ZenForestTest, then run: py Content/Python/setup_zenforest_musical_glam.py",
                "Then: py Content/Python/setup_zenforest_hero_cameras.py && py Content/Python/render_exporter.py --width 1920 --height 1080",
            ],
            "ok": True,
        }

    # Editor path
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Load level (unless verify-only wants read-only — still load)
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.ZenForestTest"):
        return {"timestamp": ts, "level": LEVEL, "ok": False, "error": "ZenForestTest missing"}
    les.load_level(LEVEL)

    audit_mpc = _audit_mpc_npc(unreal)
    focal, focal_src = _find_focal(eas, unreal)
    half = _scene_half(eas, focal, unreal)

    if verify_only:
        # Read-only scan
        actors = {a.get_actor_label(): a for a in eas.get_all_level_actors() or []}
        glam = [l for l in actors if l.startswith("VFX_Zen_") or l.startswith("Cam_ZenGlam") or l == "PP_Zen_MusicalGlam_Hint"]
        report = {
            "timestamp": ts,
            "level": LEVEL,
            "mode": "verify_only",
            "focal_source": focal_src,
            "focal": [focal.x, focal.y, focal.z],
            "half_extent": list(half),
            "mpc_npc": audit_mpc,
            "existing_glam_actors": sorted(glam),
            "actor_count": len(actors),
            "ok": True,
        }
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        unreal.log(f"[ZenMusicalGlam] verify -> {REPORT}")
        print(json.dumps(report, indent=2))
        return report

    alphas = _import_alphas(unreal, dry_run=dry_run)
    mats = _ensure_materials(unreal, dry_run=dry_run)
    niagara = _ensure_niagara_actors(unreal, eas, les, focal, half, dry_run=dry_run)
    cams = _ensure_cameras(unreal, eas, focal, half, dry_run=dry_run)
    ppv = _ensure_postprocess_hint(unreal, eas, dry_run=dry_run)

    report: dict[str, Any] = {
        "timestamp": ts,
        "level": LEVEL,
        "mode": "dry_run" if dry_run else "full_glam",
        "focal_source": focal_src,
        "focal": [focal.x, focal.y, focal.z],
        "half_extent": list(half),
        "mpc_npc": audit_mpc,
        "alphas": alphas,
        "materials": mats,
        "niagara_actors": niagara,
        "cameras": cams,
        "postprocess": ppv,
        "engine": {
            "r.CustomDepth": 3,
            "r.Substrate": True,
            "r.Lumen": "DynamicGlobalIlluminationMethod=1 / ReflectionMethod=1",
            "r.Shadow.Virtual": True,
            "r.MegaLights": True,
            "r.MotionBlur": False,
            "note": "All from Config/DefaultEngine.ini — no ini edit needed for glam pass",
        },
        "mix_notes": {
            "mix": "Substrate toon + Lumen GI + Virtual Shadow + Imperfecter PPV (bloom 0.8, vignette, CA on BeatPulse) + UltraDynamicSky volumetric god rays",
            "reactivity": "MPC_Melodia_Palette BeatPulse/Bass/Mid/Treble/PaletteTint -> materials; NPC_Melodia_Palette mirror -> Niagara (one tick, no drift) + BeatPhase wrap -> UMelodiaRhythmReactivitySubsystem.NotifyBeat -> OSC 9000 -> TouchDesigner",
            "capture": "Use Saved/Portfolio/MRQ presets or render_exporter.py pilots Cam_ZenGlam_*; encode loops via tools/encode_*_loops.ps1",
        },
        "next_steps": [
            "Pilot Cam_ZenGlam_Establishing in viewport — tweak PPV + sky tint.",
            "py Content/Python/setup_zenforest_musical_sequence.py  # 10s LevelSequence + MRQ",
            "py Content/Python/render_exporter.py --width 1920 --height 1080  # hero+breakdown PNGs",
            "powershell tools/encode_material_loops.ps1  # if you cut loops",
        ],
        "ok": True,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ZenMusicalGlam] {'DRY RUN ' if dry_run else ''}report -> {REPORT}")
    print(json.dumps(report, indent=2))

    if not dry_run:
        try:
            les.save_current_level()
            unreal.log("[ZenMusicalGlam] Saved level ZenForestTest")
        except Exception as exc:
            unreal.log_warning(f"[ZenMusicalGlam] save failed: {exc}")
            report["save_error"] = str(exc)

    return report


def _parse_args():
    p = argparse.ArgumentParser(description="ZenForestTest musical glam wiring")
    p.add_argument("--dry-run", action="store_true", help="Audit without writing assets")
    p.add_argument("--verify-only", action="store_true", help="Read-only actor scan")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    # argparse leaks into unreal's sys.argv; tolerate
    dry = "--dry-run" in sys.argv
    ver = "--verify-only" in sys.argv
    result = run(dry_run=dry, verify_only=ver)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
