"""Shorewake 48-material Substance Painter builder — self-removing startup module.

Builds ONE .spp from the night-package slotted mesh (48 material slots
SW_Dress_P01..P48 -> 48 texture sets) and wires the baked maps from the
2026-08-31 bake-of-record into every set (shared dress-space UV layout):

  BaseColor  T_DressShorewake_Painterly_Drape_4K.png   (projected through these UVs)
  Normal     SM_.._low_normal-from-mesh.png  (4K sbsbaker, DirectX Y+)
  Height     T_Shorewake_Painterly_Height.png
  Roughness  T_Shorewake_PearlWeave_Roughness.png

Extra kit maps (PanelID, FoamCrest, ChladniWeave_N, PearlSheen, bake AO /
curvature / thickness / position) are imported as project resources for
hand-paint masking; they are NOT wired to channels (Emissive/AO channels are
not enabled by default on texture sets — see pipeline doc §6).

Writes painter_build_done.json + painter_build_steps.log, then DELETES ITSELF
only on full success. Master copy: Tools/Houdini/sea_above_reef/this file.
"""
import json
import os
import traceback
from pathlib import Path

from substance_painter import project, resource, textureset, layerstack
from substance_painter import colormanagement as _cm

PKG = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/bake/night_pkg_2026-08-31")
BAKE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/bake")
STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/substance_staging/Shorewake48")
SPP = STAGE / "spp"
MESH = PKG / "SM_ShorewakeDress_48MAT_v2_slotted.fbx"
DONE = STAGE / "painter_build_done.json"
STEPLOG = STAGE / "painter_build_steps.log"

VARIANTS = ["Shorewake48"]

# shared dress-space UV layout -> same map on all 48 sets
CHANNEL_MAP = {
    "BaseColor": PKG / "T_DressShorewake_Painterly_Drape_4K.png",
    "Normal": BAKE / "sbs" / "SM_ShorewakeDress_48MAT_v2_low_normal-from-mesh.png",
    "Height": PKG / "T_Shorewake_Painterly_Height.png",
    "Roughness": PKG / "T_Shorewake_PearlWeave_Roughness.png",
}
# imported for hand-paint use, not wired
EXTRA_RESOURCES = [
    PKG / "T_DressShorewake_PanelID_4K.png",
    PKG / "T_DressShorewake_FoamCrest_Mask_4K.png",
    PKG / "T_Shorewake_ChladniWeave_N.png",
    PKG / "T_Shorewake_PearlSheen_Iridescence.png",
    PKG / "T_Shorewake_PearlSheen_Strength.png",
    PKG / "T_Shorewake_PearlWeave_Normal.png",
    PKG / "T_Shorewake_PearlWeave_Height.png",
    PKG / "T_Shorewake_PearlWeave_AO.png",
    BAKE / "T_DressShorewake_AO.png",
    BAKE / "T_DressShorewake_Curvature.png",
    BAKE / "T_DressShorewake_Thickness.png",
    BAKE / "T_DressShorewake_Position.png",
    BAKE / "T_DressShorewake_Normal.png",
]

_FS_SCHEDULED = False


def step(msg):
    try:
        with open(STEPLOG, "a", encoding="utf-8") as f:
            f.write(f"[step] {msg}\n")
    except Exception:
        pass


def wire_all_sets(rid_by_name, log):
    """Wire the shared fill into every texture set (48 panels, one UV space)."""
    sets = textureset.all_texture_sets()
    step(f"texture sets: {len(sets)} ({[s.name() for s in sets][:3]}...)")
    if not sets:
        raise RuntimeError("no texture sets after project create (mesh import failed?)")
    for ts in sets:
        stack = ts.get_stack()
        pos = layerstack.InsertPosition.from_textureset_stack(stack)
        fill = layerstack.insert_fill(pos)
        fill.set_name(f"START_{ts.name()}")
        wired, skipped = [], []
        for ch_name, rid in rid_by_name.items():
            ct = getattr(textureset.ChannelType, ch_name, None)
            if ct is None or rid is None:
                skipped.append(ch_name)
                continue
            try:
                fill.set_source(ct, rid)
                wired.append(ch_name)
            except Exception as exc:
                skipped.append(f"{ch_name}({type(exc).__name__})")
        log.append({"stack": ts.name(), "wired": wired, "skipped": skipped})


def _next_variant():
    from PySide6.QtCore import QTimer
    v = STATE["current"]
    if v is not None:
        if project.is_open():
            try:
                project.close()
            except Exception:
                pass
        if STATE["queue"] and STATE["queue"][0] == v:
            STATE["queue"].pop(0)
        STATE["current"] = None
    if STATE["queue"]:
        QTimer.singleShot(800, _start_variant)
    else:
        finish()


def _start_variant():
    v = STATE["queue"][0]
    STATE["current"] = v
    step(f"{v}: creating project")
    try:
        if project.is_busy():
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, _start_variant)
            return
        if project.is_open():
            project.close()
        settings = project.Settings(
            normal_map_format=project.NormalMapFormat.DirectX,   # bake-of-record is DirectX Y+
            default_texture_resolution=4096,
            export_path=str(STAGE / "export" / v),
            default_save_path=str(SPP / f"{v}.spp"),
        )
        project.create(str(MESH), settings=settings)
        project.execute_when_not_busy(_wire_and_save)
    except Exception:
        STATE["results"].append({"variant": v, "saved": False,
                                  "error": traceback.format_exc()[:500]})
        step(f"{v}: CREATE ERROR " + traceback.format_exc()[:300])
        _next_variant()


def _wire_and_save():
    v = STATE["current"]
    try:
        step(f"{v}: importing resources")
        rid_by_name = {}
        for ch_name, f in CHANNEL_MAP.items():
            if not f.exists():
                step(f"missing map: {f}")
                rid_by_name[ch_name] = None
                continue
            try:
                rid_by_name[ch_name] = resource.import_project_resource(
                    str(f), resource.Usage.TEXTURE).identifier()
            except Exception as exc:
                step(f"import failed {f.name}: {type(exc).__name__}")
                rid_by_name[ch_name] = None
        for f in EXTRA_RESOURCES:
            if f.exists():
                try:
                    resource.import_project_resource(str(f), resource.Usage.TEXTURE)
                except Exception:
                    pass
        step(f"{v}: wiring {len(textureset.all_texture_sets())} texture sets")
        wire_all_sets(rid_by_name, STATE["stacks"])
        project.execute_when_not_busy(_save)
    except Exception:
        STATE["results"].append({"variant": v, "saved": False,
                                  "error": traceback.format_exc()[:500]})
        step(f"{v}: WIRE ERROR " + traceback.format_exc()[:300])
        _next_variant()


def _save():
    v = STATE["current"]
    try:
        project.save_as(str(SPP / f"{v}.spp"))
        STATE["results"].append({"variant": v, "saved": True, "stacks": STATE["stacks"]})
        step(f"{v}: saved")
        project.execute_when_not_busy(_next_variant)
    except Exception:
        STATE["results"].append({"variant": v, "saved": False,
                                  "error": traceback.format_exc()[:500]})
        step(f"{v}: SAVE ERROR " + traceback.format_exc()[:300])
        _next_variant()


STATE = {"queue": list(VARIANTS), "current": None, "results": [], "stacks": []}


def finish():
    try:
        all_ok = all(r.get("saved") for r in STATE["results"])
        DONE.write_text(json.dumps({
            "schema": "melodia.shorewake48_painter_build.v1",
            "mesh": str(MESH),
            "projects": [str(SPP / f"{v}.spp") for v in VARIANTS],
            "results": STATE["results"],
            "all_saved": all_ok,
            "open_projects": [project.name()] if project.is_open() else [],
        }, indent=1), encoding="utf-8")
        step(f"done marker written (all_saved={all_ok})")
        if all_ok:
            os.remove(os.path.abspath(__file__))
    except Exception:
        step("finish crashed: " + traceback.format_exc()[:400])


def run_builder():
    try:
        step("builder fired")
        SPP.mkdir(parents=True, exist_ok=True)
        if project.is_open():
            step(f"closing pre-opened project: {project.name()}")
            try:
                project.close()
            except Exception as exc:
                step(f"pre-open close failed: {type(exc).__name__}: {exc}")
        _start_variant()
    except Exception:
        step("run_builder crashed: " + traceback.format_exc()[:600])


def _schedule_once():
    global _FS_SCHEDULED
    if _FS_SCHEDULED:
        return
    _FS_SCHEDULED = True
    from PySide6.QtCore import QTimer
    QTimer.singleShot(12000, run_builder)


def start_plugin():
    step("plugin loaded; deferring builder 12s")
    _schedule_once()


def close_plugin():
    pass


# Startup-module mode: imported automatically at Painter launch.
try:
    step("startup module imported; deferring builder 12s")
    _schedule_once()
except Exception:
    import traceback as _tb
    step("defer at import failed: " + _tb.format_exc()[:300])
