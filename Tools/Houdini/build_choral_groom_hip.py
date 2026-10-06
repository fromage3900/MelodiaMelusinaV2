#!/usr/bin/env python
"""
Build Houdini HIPNC for Choral Sheep groom 12 variants.

Creates a Guide Groom + Hair Generate network with 12 per-PC wedges.

  /obj/choral_sheep_groom                subnet
    guide_groom1  (SOP net — Guide Groom)
    hair_generate1 (SOP — Hair Generate per variant via wedge)
    groom_merge    (merge 12 grooms for preview)

  /out/groom_abc_rop   ROP Alembic per PC -> Saved/Audit/choral_sheep/grooms/Groom_ChoralSheep_PC{label}.abc
  /out/groom_cards_rop ROP FBX/Cards per PC mid LOD

Apprentice: saves as .hipnc only. If hou missing, writes JSON stub.
Run:
    hython Tools/Houdini/build_choral_groom_hip.py --out Tools/Houdini/choral_sheep_groom.hipnc
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SPEC_PATH = Path(__file__).parent / "choral_groom_variants_spec.json"

def load_spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))

def build_with_hou(out: Path):
    import hou
    spec = load_spec()
    hou.hipFile.clear(suppress_save_prompt=True)

    obj = hou.node("/obj")
    groom_subnet = obj.createNode("subnet", "choral_sheep_groom")
    groom_subnet.setPosition([0, 0])

    # Import placeholder: file SOP pulling SK_ChoralSheep FBX if present, else sphere
    # Inside subnet, create a geo for base mesh
    base_geo = groom_subnet.createNode("geo", "base_mesh")
    base_geo.setPosition([0, 0])
    file_sop = base_geo.createNode("file", "import_sheep")
    # Try the tracked ARP export as groom base; fallback will be sphere
    candidate = Path("Content/Melodia/Companions/ChoralSheep/ChoralSheepARPExport.fbx")
    if candidate.is_file():
        file_sop.parm("file").set(str(candidate.resolve()).replace("\\", "/"))
    else:
        # keep file empty; add sphere for offline bootstrap
        sphere = base_geo.createNode("sphere", "fallback_sphere")
        sphere.parm("rad").set((0.6, 0.6, 0.8))
        sphere.parm("rows").set(12)
        sphere.parm("cols").set(14)
        # wire fallback
        file_sop.destroy()

    # Guide groom setup (per Houdini 20.5 Groom SOPs)
    guide_groom = groom_subnet.createNode("geo", "guide_groom1")
    guide_groom.setPosition([2, 0])
    # Object merge from base_mesh
    objmerge = guide_groom.createNode("object_merge", "from_base")
    objmerge.parm("objpath1").set("/obj/choral_sheep_groom/base_mesh")
    objmerge.parm("xformtype").set(1)  # into this object

    # Guide Groom node (new in 19.5+) — create if type exists
    groom_node = None
    for typename in ("guidegroom::2.0", "guidegroom", "guide_groom", "hair::guide_groom"):
        try:
            groom_node = guide_groom.createNode(typename, "groom")
            break
        except Exception:
            continue
    if groom_node is None:
        # fallback: scatter + attribute wrangle to simulate guides
        scatter = guide_groom.createNode("scatter", "guide_scatter")
        scatter.setInput(0, objmerge)
        scatter.parm("npts").set(120)
        groom_node = scatter
    else:
        groom_node.setInput(0, objmerge)
        # seed params that survive version drift
        for parm, val in [("density", 0.65), ("length", 0.062), ("guide_count", 120)]:
            try:
                groom_node.parm(parm).set(val)
            except Exception:
                pass

    # Attribute wrangle to drive per-PC params via wedge
    wrangle = guide_groom.createNode("attribwrangle", "pc_drive")
    wrangle.setInput(0, groom_node)
    wrangle.parm("class").set(1)  # detail
    wrangle.parm("snippet").set(
        '// PC wedge driven — integer pc 0..11 provided by wedge ROP\n'
        'int pc = chi("pc");\n'
        'float scales[] = {0.62,0.63,0.64,0.65,0.66,0.67,0.68,0.66,0.65,0.64,0.63,0.62};\n'
        'f@wool_clump_scale = scales[pc];\n'
        'f@clump_size = 0.45 + pc*0.01;\n'
        'f@curl = 0.30 + (pc%6)*0.02;\n'
    )
    try:
        wrangle.parm("pc").set(0)
    except Exception:
        try:
            hou.ParmTemplateGroup  # noqa
        except Exception:
            pass

    # Hair Generate (actual strands)
    hairgen_geo = groom_subnet.createNode("geo", "hair_generate1")
    hairgen_geo.setPosition([4, 0])
    hg_merge = hairgen_geo.createNode("object_merge", "from_guides")
    hg_merge.parm("objpath1").set("/obj/choral_sheep_groom/guide_groom1/pc_drive")
    hair_gen = None
    for typename in ("hairgen::2.0", "hairgen", "hairgenerate::2.0", "hairgenerate",
                     "hair_gen", "hair::generate"):
        try:
            hair_gen = hairgen_geo.createNode(typename, "hairgen")
            break
        except Exception:
            continue
    if hair_gen is None:
        hair_gen = hairgen_geo.createNode("copytopoints", "hair_proxy")
        hair_gen.setInput(0, hg_merge)
        # copytopoints needs a template on input 1 — clump-puff proxy sphere.
        puff = hairgen_geo.createNode("sphere", "clump_puff")
        puff.parm("rad").set((0.008, 0.008, 0.008))
        puff.parm("rows").set(4)
        puff.parm("cols").set(6)
        hair_gen.setInput(1, puff)

    else:
        hair_gen.setInput(0, hg_merge)
        for parm, val in [("density", 9000), ("length", 0.06), ("thickness", 0.0012)]:
            try: hair_gen.parm(parm).set(val)
            except Exception: pass

    # Null output
    out_null = hairgen_geo.createNode("null", "OUT_GROOM")
    out_null.setInput(0, hair_gen)
    out_null.setDisplayFlag(True)
    out_null.setRenderFlag(True)

    # ROPs at /out
    out_net = hou.node("/out")
    if out_net is None:
        out_net = hou.node("/").createNode("ropnet", "out")
    # Wedge + Alembic
    wedge = out_net.createNode("wedge", "groom_wedge")
    try:
        wedge.parm("wedge_count").set(12)
        wedge.parm("wedge_var").set("pc")
        wedge.parm("wedge_start").set(0)
        wedge.parm("wedge_end").set(11)
    except Exception:
        pass

    abc_rop = out_net.createNode("alembic", "groom_abc_rop")
    try:
        abc_rop.parm("soppath").set("/obj/choral_sheep_groom/hair_generate1/OUT_GROOM")
        abc_rop.parm("filename").set("$HIP/../Saved/Audit/choral_sheep/grooms/Groom_ChoralSheep_PC`padzero(2, ch(\"../groom_wedge/pc\"))`_`chs(\"../groom_wedge/label\")`.abc")
    except Exception:
        abc_rop.parm("filename").set("$HIP/../Saved/Audit/choral_sheep/grooms/Groom_ChoralSheep_PC00_C.abc")

    # Cards ROP fallback (FBX export mid LOD)
    fbx_rop = out_net.createNode("rop_fbx", "groom_cards_rop") if hou.nodeType(hou.ropNodeTypeCategory(), "rop_fbx") else out_net.createNode("alembic", "groom_cards_proxy")
    try:
        fbx_rop.parm("soppath").set("/obj/choral_sheep_groom/hair_generate1/OUT_GROOM")
        fbx_rop.parm("filename").set("$HIP/../Saved/Audit/choral_sheep/grooms/FurShell_ChoralSheep_PC`padzero(2,ch(\"../groom_wedge/pc\"))`_`chs(\"../groom_wedge/label\")`.fbx")
    except Exception:
        pass

    hou.hipFile.save(str(out))
    print(f"[groom] saved {out} — guide_groom + hair_generate + wedge(12) + abc/cards ROPs")
    print(f"[groom] spec wool_clump_scale base {spec['base']['wool_clump_scale']} -> per-PC {list(spec['per_pc_overrides'].values())[:2]} ...")

def build_stub(out: Path):
    spec = load_spec()
    out.parent.mkdir(parents=True, exist_ok=True)
    stub = out.with_suffix(".json")
    data = {
        "schema": "melodia.houdini_groom_hip.v1",
        "note": "hou unavailable - JSON stub for groom HIP; run with hython to materialize",
        "hip": str(out),
        "obj": "/obj/choral_sheep_groom",
        "guide_groom": "/obj/choral_sheep_groom/guide_groom1",
        "hair_generate": "/obj/choral_sheep_groom/hair_generate1",
        "spec": spec,
        "intended_chain": "file(SK_ChoralSheep.fbx) -> GuideGroom(scatter 120) -> AttribWrangle(pc->wool_clump_scale) -> HairGenerate(9000 strands, 6cm) -> OUT_GROOM -> Alembic wedge(12)",
        "exports": spec["exports"],
        "ue_binding": spec["ue"]["groom_binding"],
        "next_hython": "hython Tools/Houdini/build_choral_groom_hip.py --out Tools/Houdini/choral_sheep_groom.hipnc",
    }
    stub.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out.write_bytes(b"# Houdini GROOM HIPNC stub - run build_choral_groom_hip.py under hython\n")
    print(f"[groom] hou not available - wrote stub {stub}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Tools/Houdini/choral_sheep_groom.hipnc")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import hou
        build_with_hou(out)
    except ImportError:
        build_stub(out)
    except Exception as e:
        print(f"[groom] build failed: {e}")
        import traceback; traceback.print_exc()
        try: build_stub(out)
        except Exception: raise
