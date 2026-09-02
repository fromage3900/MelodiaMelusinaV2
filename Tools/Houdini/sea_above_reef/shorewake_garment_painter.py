"""Shorewake Garment-Layers Substance Painter builder — self-removing startup module.

Builds ONE .spp from the MERGED, silhouette-labeled garment mesh (10 material
slots M_Bodice_*, M_Collar, ... -> 10 texture sets) and wires the refreshed
per-garment-layer fabric maps (shorewake_garment_refresh.py, seed 20260902)
into every set:

  BaseColor   T_Shorewake_Garment_<Layer>_BaseColor.png
  Normal      T_Shorewake_Garment_<Layer>_Normal.png       (OpenGL Y+, flip on export)
  Height      T_Shorewake_Garment_<Layer>_Height.png
  Roughness   T_Shorewake_Garment_<Layer>_Roughness.png

Layers that shipped Metal / Iridescence / Sheen maps also get those wired into
Metal / (none-native; available as resource) / Sheen where the Painter set
supports them; everything else stays as import-resources for hand-paint.

The 48-panel -> 10-garment mapping (merge map) lives in
garment_merge_obj_manifest.json in this staging dir.

Deploy as PAINTER/resources/python/startup/shorewake_garment_builder.py, then
launch Painter. Writes painter_build_done.json + painter_build_steps.log and
DELETES ITSELF on full success (master kept at Tools/Houdini/sea_above_reef/).
"""
import json
import os
import traceback
from pathlib import Path

from substance_painter import project, resource, textureset, layerstack

STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/substance_staging/ShorewakeGarment")
RES = STAGE / "resources"
MESH = STAGE / "meshes" / "SM_ShorewakeDress_48MAT_garment.obj"
SPP = STAGE / "spp"
DONE = STAGE / "painter_build_done.json"
STEPLOG = STAGE / "painter_build_steps.log"

# layer -> required channel source files (within RES/)
LAYER_CHANNELS = {
    "M_Bodice_Torso": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Bodice_Front": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Bodice_Side": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Bodice_Upper": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Collar": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Shoulder_Trim": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Shoulder_Ornament": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Sleeve": ("BaseColor", "Normal", "Height", "Roughness", "Metal"),
    "M_Underskirt": ("BaseColor", "Normal", "Height", "Roughness"),
    "M_Skirt_Full": ("BaseColor", "Normal", "Height", "Roughness"),
}
# resource-only (hand-paint masks), imported but not wired
EXTRA_RESOURCES = [
    "T_DressShorewake_PanelID_4K.png",
    "T_DressShorewake_FoamCrest_Mask_4K.png",
    "T_Shorewake_ChladniWeave_N.png",
    "T_Shorewake_PearlSheen_Iridescence.png",
    "T_Shorewake_PearlSheen_Strength.png",
    "T_Shorewake_PearlWeave_Normal.png",
    "T_Shorewake_PearlWeave_Height.png",
    "T_Shorewake_PearlWeave_AO.png",
    "T_Shorewake_Garment_M_Skirt_Full_Iridescence.png",
    "T_Shorewake_Garment_M_Skirt_Full_Sheen.png",
]

_SCHEDULED = False
STATE = {"queue": ["ShorewakeGarment"], "current": None, "results": [], "stacks": None, "done": False}


def step(msg):
    try:
        with open(STEPLOG, "a", encoding="utf-8") as f:
            f.write(f"[step] {msg}\n")
    except Exception:
        pass


def file_for(layer, ch):
    # map logical channel to the on-disk refreshed map name
    return RES / f"T_Shorewake_Garment_{layer}_{ch}.png"


def wire_sets(rid_by_layer_channel, log):
    sets = textureset.all_texture_sets()
    # keyed by texture-set name = material slot name
    by_name = {s.name(): s for s in sets}
    step(f"texture sets: {len(sets)} ({[s.name() for s in sets][:4]}...)"
         f" expected 10 (M_* garment layers)")
    for layer, channels in LAYER_CHANNELS.items():
        ts = by_name.get(layer)
        if ts is None:
            log.append({"stack": layer, "wired": [], "skipped": ["SET NOT FOUND"]})
            continue
        stack = ts.get_stack()
        pos = layerstack.InsertPosition.from_textureset_stack(stack)
        fill = layerstack.insert_fill(pos)
        fill.set_name(f"START_{layer}")
        wired, skipped = [], []
        for ch in channels:
            ct = getattr(textureset.ChannelType, ch, None)
            rid = rid_by_layer_channel.get((layer, ch))
            if ct is None or rid is None:
                skipped.append(ch)
                continue
            try:
                fill.set_source(ct, rid)
                wired.append(ch)
            except Exception as exc:
                skipped.append(f"{ch}({type(exc).__name__})")
        log.append({"stack": layer, "wired": wired, "skipped": skipped})


def run_builder():
    try:
        step("garment builder fired")
        SPP.mkdir(parents=True, exist_ok=True)
        if project.is_open():
            try:
                project.close()
            except Exception as exc:
                step(f"pre-open close failed: {type(exc).__name__}")
        import resource as _r  # alias safe
        settings = project.Settings(
            normal_map_format=project.NormalMapFormat.OpenGL,  # refreshed kit is OpenGL Y+
            default_texture_resolution=2048,
            export_path=str(STAGE / "export"),
            default_save_path=str(SPP / "ShorewakeGarment.spp"),
        )
        project.create(str(MESH), settings=settings)

        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, _wire_and_save)
    except Exception:
        step("run_builder crashed: " + traceback.format_exc()[:600])


def _wire_and_save():
    try:
        step("importing refreshed garment resources")
        rid_by = {}
        for layer, channels in LAYER_CHANNELS.items():
            for ch in channels:
                f = file_for(layer, ch)
                if not f.exists():
                    step(f"missing map {f.name}")
                    continue
                try:
                    rid_by[(layer, ch)] = resource.import_project_resource(
                        str(f), resource.Usage.TEXTURE).identifier()
                except Exception as exc:
                    step(f"import failed {f.name}: {type(exc).__name__}")
        for fname in EXTRA_RESOURCES:
            p = RES / fname
            if p.exists():
                try:
                    resource.import_project_resource(str(p), resource.Usage.TEXTURE)
                except Exception:
                    pass
        log = []
        wire_sets(rid_by, log)
        STATE["stacks"] = log
        project.execute_when_not_busy(_save)
    except Exception:
        step("_wire_and_save crashed: " + traceback.format_exc()[:500])
        _finish(False)


def _save():
    try:
        project.save_as(str(SPP / "ShorewakeGarment.spp"))
        STATE["results"].append({"variant": "ShorewakeGarment", "saved": True,
                                 "stacks": STATE["stacks"]})
        step("saved")
        _finish(True)
    except Exception:
        step("save crashed: " + traceback.format_exc()[:500])
        _finish(False)


def _finish(all_ok):
    if STATE["done"]:
        return
    STATE["done"] = True
    DONE.write_text(json.dumps({
        "schema": "melodia.shorewake_garment_painter_build.v1",
        "mesh": str(MESH),
        "projects": [str(SPP / "ShorewakeGarment.spp")],
        "texture_set_count": len(LAYER_CHANNELS),
        "results": STATE["results"],
        "all_saved": bool(STATE["results"] and all(r.get("saved") for r in STATE["results"])),
        "open_projects": [project.name()] if project.is_open() else [],
    }, indent=1), encoding="utf-8")
    step(f"done marker written (all_saved={bool(STATE['results'])}")
    if all_ok:
        try:
            os.remove(os.path.abspath(__file__))
        except Exception:
            pass


def start_plugin():
    step("plugin loaded; deferring builder 12s")
    from PySide6.QtCore import QTimer
    QTimer.singleShot(12000, run_builder)


def close_plugin():
    pass


try:
    step("startup module imported; deferring builder 12s")
    from PySide6.QtCore import QTimer
    QTimer.singleShot(12000, run_builder)
except Exception:
    step("defer at import failed: " + traceback.format_exc()[:300])