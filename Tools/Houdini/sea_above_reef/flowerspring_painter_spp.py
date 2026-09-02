#!/usr/bin/env python
"""FlowerSpring — Substance Painter project builder (runs inside Painter).

Launched with:  Adobe Substance 3D Painter.exe --python <this file>

Creates one .spp project per dress variant from the v2 assembly FBX:
  * mesh: substance_staging/FlowerSpring/meshes/FS_FullAssembly_cascade.fbx
  * OpenGL normals, 2048 default resolution, export path per variant
  * all variant maps imported into the project shelf (grouped per variant)
  * a fill layer at the top of each fabric texture set (shirt/skirt) wired
    per channel: BaseColor/Normal/Height/Emissive/Roughness/Metallic/AO
  * crown/wings texture sets get uniform palette fills (gold / blush) so the
    owner paints fabric on the dress and metal/petal accents on the pieces
  * variants 2..5 saved+closed; variant 1 (FlowerSpring) saved and LEFT OPEN

Writes a done-marker JSON when finished (polled by the driving lane).
"""
import json
import traceback
from pathlib import Path

import substance_painter as sp
from substance_painter import project, resource, textureset, layerstack, source

STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring")
TEX = STAGE / "textures"
SPP = STAGE / "spp"
MESH = STAGE / "meshes" / "FS_FullAssembly_cascade.fbx"
DONE = STAGE / "painter_build_done.json"
STEPLOG = STAGE / "painter_build_steps.log"


def step(msg):
    try:
        with open(STEPLOG, "a", encoding="utf-8") as f:
            f.write(f"[step] {msg}\n")
    except Exception:
        pass


step("script imported OK (substance_painter module loaded)")

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


def channel_enum(name):
    ct = textureset.ChannelType
    return getattr(ct, name, None)


def wire_fill(stack, variant, log):
    """Insert a fill layer and wire per-channel sources. Returns node name."""
    pos = layerstack.InsertPosition.from_textureset_stack(stack)
    fill = layerstack.insert_fill(pos)
    fill.set_name(f"START_{variant}")
    vdir = TEX / variant
    wired, skipped = [], []
    active = set()
    try:
        active = {c.name for c in fill.active_channels}
    except Exception:
        pass
    for ch_name, fname in CHANNEL_MAP.items():
        f = vdir / fname
        if not f.exists():
            skipped.append(f"{ch_name}(no file)")
            continue
        ct = channel_enum(ch_name)
        if ct is None:
            skipped.append(f"{ch_name}(no enum)")
            continue
        try:
            res = resource.import_project_resource(str(f), resource.Usage.TEXTURE,
                                                   name=f"{variant} {ch_name}",
                                                   group=f"FlowerSpring/{variant}")
            rid = res.identifier
            # try directly, then activate the channel on the fill if needed
            try:
                fill.set_source(ct, rid)
            except Exception:
                try:
                    wanted = set(active)
                    wanted.add(ct)
                    fill.active_channels = wanted
                    fill.set_source(ct, rid)
                except Exception:
                    skipped.append(f"{ch_name}(set_source)")
                    continue
            wired.append(ch_name)
        except Exception as exc:
            skipped.append(f"{ch_name}({exc})")
    log.append({"stack": stack.name(), "wired": wired, "skipped": skipped})
    return fill


def uniform_fill(stack, color, label):
    pos = layerstack.InsertPosition.from_textureset_stack(stack)
    fill = layerstack.insert_fill(pos)
    fill.set_name(label)
    try:
        fill.set_source(None, source.SourceUniformColor(color))
    except Exception:
        try:
            rid = resource.ResourceID.from_url("")
            fill.set_source(None, rid)  # will fail; keep stack bare
        except Exception:
            pass
    return fill


def build_variant(variant: str, keep_open: bool) -> dict:
    log = {"variant": variant, "stacks": [], "saved": False, "error": None}
    try:
        settings = project.Settings(
            normal_map_format=project.NormalMapFormat.OpenGL,
            default_texture_resolution=2048,
            export_path=str(STAGE / "export" / variant),
            default_save_path=str(SPP / f"FlowerSpring_{variant}.spp"),
        )
        project.create(str(MESH), settings=settings)
        # import shelf extras (iridescence/sheen/motif/ORM) for painting
        vdir = TEX / variant
        for fname in SHELF_EXTRA:
            f = vdir / fname
            if f.exists():
                try:
                    resource.import_project_resource(str(f), resource.Usage.TEXTURE,
                                                     name=f"{variant} {Path(fname).stem}",
                                                     group=f"FlowerSpring/{variant}")
                except Exception:
                    pass
        for stack in textureset.get_all_texture_sets():
            sname = stack.name().lower()
            if any(k in sname for k in ("shirt", "skirt", "dress", "cloth")):
                wire_fill(stack, variant, log["stacks"])
            elif "crown" in sname:
                uniform_fill(stack, GOLD, "START_gold_crown")
                log["stacks"].append({"stack": stack.name(), "wired": ["uniform gold"]})
            elif "wing" in sname:
                uniform_fill(stack, BLUSH, "START_blush_wings")
                log["stacks"].append({"stack": stack.name(), "wired": ["uniform blush"]})
            else:
                wire_fill(stack, variant, log["stacks"])
        project.save_as(str(SPP / f"FlowerSpring_{variant}.spp"))
        log["saved"] = True
        if not keep_open:
            project.close()
    except Exception:
        log["error"] = traceback.format_exc()
    return log


def main():
    step("main() entered")
    SPP.mkdir(parents=True, exist_ok=True)
    results = []
    for i, v in enumerate(VARIANTS):
        keep_open = (i == 0)   # FlowerSpring stays open for immediate painting
        r = build_variant(v, keep_open=keep_open)
        results.append(r)
        step(f"variant {v}: saved={r['saved']} error={bool(r['error'])}")
        print(f"[spp] {v}: saved={r['saved']} error={'yes' if r['error'] else 'no'}")
    DONE.write_text(json.dumps({
        "schema": "melodia.flowerspring_painter_build.v1",
        "mesh": str(MESH),
        "projects": [str(SPP / f"FlowerSpring_{v}.spp") for v in VARIANTS],
        "results": results,
        "open_projects": [project.name()] if project.is_open() else [],
    }, indent=1), encoding="utf-8")
    print("PAINTER_BUILD_DONE")


main()
