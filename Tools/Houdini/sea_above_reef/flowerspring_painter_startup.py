"""FlowerSpring Substance Painter project builder — self-removing startup module.

Runs ONCE at Painter launch (from Documents .../python/startup/):
  1. closes any auto-restored session project,
  2. creates one .spp per FlowerSpring dress variant from the v2 assembly FBX,
     wiring per-channel fill sources from the baked staging maps,
  3. saves .spp files into substance_staging/FlowerSpring/spp/,
  4. writes painter_build_done.json; deletes ITSELF only on full success.

Master copy lives in the repo (Tools/Houdini/sea_above_reef/); the startup
folder gets a deployment copy.
"""
import json
import os
import traceback
from pathlib import Path

from substance_painter import project, resource, textureset, layerstack, source
from substance_painter import colormanagement as _cm

STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring")
TEX = STAGE / "textures"
SPP = STAGE / "spp"
MESH = STAGE / "meshes" / "FS_FullAssembly_cascade.fbx"
DONE = STAGE / "painter_build_done.json"
STEPLOG = STAGE / "painter_build_steps.log"

VARIANTS = ["FlowerSpring", "GildedLoom", "SilkWaterfall", "CherryBlossomWood", "StarlitAbyss"]

CHANNEL_MAP = {
    "BaseColor": "T_{v}_BaseColor.png",
    "Normal": "T_{v}_Normal.png",
    "Height": "T_{v}_Height.png",
    "Emissive": "T_{v}_Emissive.png",
    "Roughness": "T_{v}_Roughness.png",
    "Metallic": "T_{v}_Metallic.png",
    "AO": "T_{v}_AO.png",
}
SHELF_EXTRA = ["T_{v}_Iridescence.png", "T_{v}_Sheen.png", "T_{v}_Motif_N.png", "T_{v}_ORM.png"]

GOLD = (0.91, 0.72, 0.29, 1.0)
BLUSH = (0.95, 0.63, 0.66, 1.0)


def step(msg):
    try:
        with open(STEPLOG, "a", encoding="utf-8") as f:
            f.write(f"[step] {msg}\n")
    except Exception:
        pass


def wire_fill(stack, variant, log, ts_name=""):
    pos = layerstack.InsertPosition.from_textureset_stack(stack)
    fill = layerstack.insert_fill(pos)
    fill.set_name(f"START_{variant}")
    vdir = TEX / variant
    wired, skipped = [], []
    for ch_name, fname in CHANNEL_MAP.items():
        f = vdir / fname.format(v=variant)
        if not f.exists():
            skipped.append(f"{ch_name}(no file)")
            continue
        ct = getattr(textureset.ChannelType, ch_name, None)
        if ct is None:
            skipped.append(f"{ch_name}(no enum)")
            continue
        try:
            res = resource.import_project_resource(str(f), resource.Usage.TEXTURE)
            rid = res.identifier()
        except Exception as exc:
            skipped.append(f"{ch_name}(import:{type(exc).__name__}:{str(exc)[:70]})")
            continue
        try:
            fill.set_source(ct, rid)
        except Exception:
            try:
                wanted = set(fill.active_channels)
                wanted.add(ct)
                fill.active_channels = wanted
                fill.set_source(ct, rid)
            except Exception as exc:
                skipped.append(f"{ch_name}(set:{type(exc).__name__}:{str(exc)[:70]})")
                continue
        wired.append(ch_name)
    log.append({"stack": ts_name, "wired": wired, "skipped": skipped})


def uniform_fill(stack, color, label):
    pos = layerstack.InsertPosition.from_textureset_stack(stack)
    fill = layerstack.insert_fill(pos)
    fill.set_name(label)
    try:
        col = _cm.Color(color[0], color[1], color[2])
        fill.set_source(textureset.ChannelType.BaseColor, col)
    except Exception as exc:
        step(f"uniform fill {label} failed: {exc}")


def _next_variant():
    """Pop finished variant, start the next one (or finish)."""
    from PySide6.QtCore import QTimer
    v = STATE["current"]
    if v is not None:
        keep_open = (len(STATE["results"]) == 1)  # leave first variant open
        if not keep_open and project.is_open():
            try:
                project.close()
            except Exception:
                pass
        STATE["queue"].pop(0) if STATE["queue"] and STATE["queue"][0] == v else None
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
            # previous close may still be settling — retry shortly
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, _start_variant)
            return
        if project.is_open():
            project.close()
        settings = project.Settings(
            normal_map_format=project.NormalMapFormat.OpenGL,
            default_texture_resolution=2048,
            export_path=str(STAGE / "export" / v),
            default_save_path=str(SPP / f"FlowerSpring_{v}.spp"),
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
        step(f"{v}: wiring")
        wire_variant(v)
        project.execute_when_not_busy(_save)
    except Exception:
        STATE["results"].append({"variant": v, "saved": False,
                                  "error": traceback.format_exc()[:500]})
        step(f"{v}: WIRE ERROR " + traceback.format_exc()[:300])
        _next_variant()


def _save():
    v = STATE["current"]
    try:
        project.save_as(str(SPP / f"FlowerSpring_{v}.spp"))
        STATE["results"].append({"variant": v, "saved": True, "stacks": STATE["stacks"]})
        step(f"{v}: saved")
        project.execute_when_not_busy(_next_variant)
    except Exception:
        STATE["results"].append({"variant": v, "saved": False,
                                  "error": traceback.format_exc()[:500]})
        step(f"{v}: SAVE ERROR " + traceback.format_exc()[:300])
        _next_variant()


def wire_variant(v):
    STATE["stacks"] = []
    vdir = TEX / v
    for fname in SHELF_EXTRA:
        f = vdir / fname.format(v=v)
        if f.exists():
            try:
                resource.import_project_resource(str(f), resource.Usage.TEXTURE)
            except Exception:
                pass
    sets = textureset.all_texture_sets()
    step(f"{v}: texture sets: {[s.name() for s in sets]}")
    if not sets:
        raise RuntimeError("no texture sets after project create (mesh import failed?)")
    for ts in sets:
        sname = ts.name().lower()
        stack = ts.get_stack()
        try:
            if any(k in sname for k in ("shirt", "skirt", "dress", "cloth")):
                wire_fill(stack, v, STATE["stacks"], ts_name=ts.name())
            elif "crown" in sname:
                uniform_fill(stack, GOLD, "START_gold_crown")
                STATE["stacks"].append({"stack": ts.name(), "wired": ["uniform gold"]})
            elif "wing" in sname:
                uniform_fill(stack, BLUSH, "START_blush_wings")
                STATE["stacks"].append({"stack": ts.name(), "wired": ["uniform blush"]})
            else:
                wire_fill(stack, v, STATE["stacks"], ts_name=ts.name())
        except Exception as exc:
            step(f"stack {ts.name()} wiring failed (continuing): {exc}")


STATE = {"queue": list(VARIANTS), "current": None, "phase": "create",
         "results": [], "stacks": [], "waited": 0}


def finish():
    try:
        all_ok = all(r.get("saved") for r in STATE["results"])
        DONE.write_text(json.dumps({
            "schema": "melodia.flowerspring_painter_build.v4",
            "mesh": str(MESH),
            "projects": [str(SPP / f"FlowerSpring_{v}.spp") for v in VARIANTS],
            "results": STATE["results"],
            "all_saved": all_ok,
            "open_projects": [project.name()] if project.is_open() else [],
        }, indent=1), encoding="utf-8")
        step(f"done marker written (all_saved={all_ok})")
        if all_ok:
            os.remove(os.path.abspath(__file__))  # self-remove only on success
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
                step("pre-opened project closed")
            except Exception as exc:
                step(f"pre-open close failed: {type(exc).__name__}: {exc}")
        _start_variant()
    except Exception:
        step("run_builder crashed: " + traceback.format_exc()[:600])


_FS_SCHEDULED = False


def _schedule_once():
    """Guard: startup-import and start_plugin() can both fire — schedule once."""
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
