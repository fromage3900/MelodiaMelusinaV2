"""Create hda/SpaceTraversal_OrbitalRings_1.0.hda via hython — BS_GodFile

Space traversal: orbital rings around orrery core, deterministic per WP chunk.
Integrates with pcg_scale_world_pipeline.py (WP 25600, stable_chunk_seed, shared_border_signature).

Usage:
    & "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Content/Python/create_hda_space_orbital_rings.py
    & "...\hython.exe" Content/Python/create_hda_space_orbital_rings.py --out hda/SpaceTraversal_OrbitalRings_1.0.hda
    & "...\hython.exe" Content/Python/create_hda_space_orbital_rings.py --test-cook  # quick cook test without saving HDA

Requires Houdini Engine license (not Apprentice). Education ($95/yr via Proxi.ID with Humber email) works.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "hda" / "SpaceTraversal_OrbitalRings_1.0.hda"

def build_hda(out: Path, test_cook: bool = False) -> int:
    try:
        import hou
    except ImportError as e:
        print(f"[Orbital] hou not available — run inside hython: {e}", file=sys.stderr)
        print(r'[Orbital] & "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Content/Python/create_hda_space_orbital_rings.py', file=sys.stderr)
        return 2

    print(f"[Orbital] Houdini {hou.applicationVersionString()}")

    obj = hou.node("/obj")
    if obj is None:
        print("[Orbital] /obj not found", file=sys.stderr)
        return 1

    # Clean previous template geo
    prev = hou.node("/obj/SpaceOrbital_Template")
    if prev:
        try:
            prev.destroy()
        except Exception:
            pass

    geo = obj.createNode("geo", "SpaceOrbital_Template")
    # Remove default children
    for c in list(geo.children()):
        try:
            c.destroy()
        except Exception:
            pass

    # Controls null with orbital parameters — these become HDA parms
    controls = geo.createNode("null", "controls")
    ptg = controls.parmTemplateGroup()
    # Use hou parm templates
    ptg.append(hou.IntParmTemplate("seed", "Seed (stable_chunk_seed)", 1, default_value=(3900,), min=1, max=2147483647))
    ptg.append(hou.IntParmTemplate("ringCount", "Ring Count", 1, default_value=(2,), min=1, max=5))
    ptg.append(hou.FloatParmTemplate("ringRadiusBase", "Ring Radius Base (cm)", 1, default_value=(1200,), min=400, max=5000))
    ptg.append(hou.FloatParmTemplate("ringRadiusStep", "Radius Step per Ring (cm)", 1, default_value=(700,), min=200, max=2000))
    ptg.append(hou.FloatParmTemplate("ringTiltDeg", "Ring Tilt Degrees", 1, default_value=(12,), min=0, max=90))
    ptg.append(hou.IntParmTemplate("platformsPerRing", "Platforms Per Ring", 1, default_value=(12,), min=4, max=32))
    ptg.append(hou.FloatParmTemplate("platformWidth", "Platform Width (cm)", 1, default_value=(110,), min=50, max=400))
    ptg.append(hou.FloatParmTemplate("platformDepth", "Platform Depth (cm)", 1, default_value=(110,), min=50, max=400))
    ptg.append(hou.FloatParmTemplate("platformHeight", "Platform Height (cm)", 1, default_value=(16,), min=8, max=40))
    ptg.append(hou.FloatParmTemplate("bridgeArchHeight", "Bridge Arch Height (cm)", 1, default_value=(80,), min=0, max=300))
    ptg.append(hou.IntParmTemplate("baseMidiNote", "Base MIDI Note", 1, default_value=(60,), min=21, max=108))
    ptg.append(hou.MenuParmTemplate("scale", "Scale", ("major","minor","pentatonic","chromatic"), default_value=0))
    ptg.append(hou.ToggleParmTemplate("addCenterCore", "Add Center Orrery Core", default_value=True))
    ptg.append(hou.FloatParmTemplate("coreRadius", "Core Radius (cm)", 1, default_value=(180,), min=60, max=600))
    controls.setParmTemplateGroup(ptg)
    # Position controls out of the way
    try:
        controls.setPosition(hou.Vector2(0, 2))
    except Exception:
        pass

    # One circle per ring -> will be generated via copy or loop
    # Approach: scatter points on rings using wrangle + copy, not multiple circles manually

    # Create a single template platform box that will be copied
    box = geo.createNode("box", "platform_box")
    box.parm("sizex").setExpression('ch("../controls/platformWidth")/100')
    box.parm("sizey").setExpression('ch("../controls/platformHeight")/100')
    box.parm("sizez").setExpression('ch("../controls/platformDepth")/100')
    # Houdini units are meters internally for some contexts but we treat cm/100 for box size (box is in Houdini units ~ meters). Keep as 1.1m = 110cm.
    # So divide by 100.

    # Core sphere (optional)
    sphere = geo.createNode("sphere", "core_sphere")
    sphere.parm("radx").setExpression('ch("../controls/coreRadius")/100')
    sphere.parm("rady").setExpression('ch("../controls/coreRadius")/100')
    sphere.parm("radz").setExpression('ch("../controls/coreRadius")/100')
    sphere.parm("type").set(1)  # polygon

    # Wrangle to generate ring points
    # We will use a single Add -> Wrangle that creates points in a loop, then Copy.
    # Simpler: use two nodes: Add (1 point) -> Wrangle that generates all ring points via addpoint, then delete template.
    add = geo.createNode("add", "single_point")
    add.parm("useTemplate").set(False)

    wrangle = geo.createNode("attribwrangle", "gen_orbital_points")
    wrangle.parm("class").set(0)  # Detail -> run once
    wrangle.parm("snippet").set(r'''
int seed = chi("../controls/seed");
int ringCount = chi("../controls/ringCount");
int ppr = chi("../controls/platformsPerRing");
float rBase = chf("../controls/ringRadiusBase");
float rStep = chf("../controls/ringRadiusStep");
float tiltDeg = chf("../controls/ringTiltDeg");
int baseMidi = chi("../controls/baseMidiNote");
int scale = chi("../controls/scale");
float tilt = radians(tiltDeg);

// Seed RNG
int total = ringCount * ppr;
// Use PCG-like deterministic: key = seed + ring*100 + platform
for (int r = 0; r < ringCount; r++) {
    float radius = rBase + r * rStep;
    float ringTilt = tilt * (r+1) * 0.5; // incremental tilt per ring
    for (int p = 0; p < ppr; p++) {
        float theta = float(p) / float(ppr) * 2 * 3.14159265;
        // base circle in XZ
        float x = cos(theta) * radius;
        float z = sin(theta) * radius;
        float y = 0;
        // tilt around X axis
        float y2 = y * cos(ringTilt) - z * sin(ringTilt);
        float z2 = y * sin(ringTilt) + z * cos(ringTilt);
        int pt = addpoint(0, set(x/100, y2/100, z2/100));
        // musical mapping
        int degree = p % 7;
        if (scale == 2) degree = p % 5; // pentatonic
        else if (scale == 3) degree = p;
        int lane = p % 8;
        int stepIdx = r * ppr + p;
        setpointattrib(0, "ring", pt, r);
        setpointattrib(0, "platform", pt, p);
        setpointattrib(0, "lane", pt, lane);
        setpointattrib(0, "stepIndex", pt, stepIdx);
        setpointattrib(0, "midiNote", pt, baseMidi + degree);
        setpointattrib(0, "seed", pt, seed + stepIdx);
        setpointattrib(0, "radius", pt, radius);
        // bridge flag: every 3rd gap gets a bridge (or connect all)
        setpointattrib(0, "hasBridge", pt, (p % 2 == 0) ? 1 : 0);
    }
}
// also optionally add center core point for reference
if (chi("../controls/addCenterCore")) {
    int cpt = addpoint(0, set(0,0,0));
    setpointattrib(0, "ring", cpt, -1);
    setpointattrib(0, "platform", cpt, -1);
    setpointattrib(0, "lane", cpt, -1);
    setpointattrib(0, "stepIndex", cpt, -1);
    setpointattrib(0, "midiNote", cpt, baseMidi);
    setpointattrib(0, "seed", cpt, seed);
    setpointattrib(0, "radius", cpt, 0);
    setpointattrib(0, "hasBridge", cpt, 0);
}
// remove template point 0
removeprim(0, 0, 1);
''')
    wrangle.setInput(0, add)

    # Delete template point wrangle created via addpoint loop keeps all, need to handle remove properly
    # Use blast to delete the first template if still there, but our wrangle already deletes prim 0
    # So net: wrangle outputs all ring points

    # Copy platforms to points (exclude core if ring==-1)
    # Use attribute filter to separate core vs platforms
    blast_core = geo.createNode("blast", "blast_core_filter")
    blast_core.parm("group").set("@ring==-1")
    blast_core.parm("negate").set(True)  # keep only platforms (ring != -1)
    blast_core.setInput(0, wrangle)

    copy = geo.createNode("copytopoints::2.0", "copy_platforms")
    copy.setInput(0, box)
    copy.setInput(1, blast_core)
    # Enable transform by N/up etc not needed
    copy.parm("useptorient").set(False)

    # Bridges: create polylines between successive platforms on same ring, then sweep
    # Use add to connect points: we can use polywire or sweep with a curve
    # Simpler: use convert to polyline via add with pattern, then resample + sweep
    # For now, create a simple tube bridge using polywire if hasBridge

    # To make bridges, we need edge connectivity. Use a second wrangle to add prims
    add_bridges = geo.createNode("attribwrangle", "add_bridge_prims")
    add_bridges.parm("class").set(0)  # detail
    add_bridges.parm("snippet").set(r'''
int ppr = chi("../controls/platformsPerRing");
int ringCount = chi("../controls/ringCount");
float arch = chf("../controls/bridgeArchHeight")/100;
int npt = npoints(0);
for (int r = 0; r < ringCount; r++) {
    for (int p = 0; p < ppr; p++) {
        if (p % 2 != 0) continue; // only even gaps get bridge (sparse)
        int a = r * ppr + p;
        int b = r * ppr + ((p+1) % ppr);
        vector pa = point(0, "P", a);
        vector pb = point(0, "P", b);
        vector mid = (pa + pb) * 0.5 + set(0, arch, 0);
        int prim = addprim(0, "polyline");
        addvertex(0, prim, a);
        // add midpoint arch
        int midpt = addpoint(0, mid);
        addvertex(0, prim, midpt);
        addvertex(0, prim, b);
        // copy musical attrs to prim for debugging
        setprimattrib(0, "ring", prim, r);
        setprimattrib(0, "bridge", prim, 1);
    }
}
''')
    add_bridges.setInput(0, blast_core)

    # Sweep bridges: need a cross-section circle
    circle = geo.createNode("circle", "bridge_profile")
    circle.parm("radx").set(0.15)
    circle.parm("rady").set(0.15)
    circle.parm("type").set(1)  # polygon
    circle.parm("divs").set(6)

    sweep = geo.createNode("sweep::2.0", "sweep_bridges")
    sweep.setInput(0, circle)
    sweep.setInput(1, add_bridges)

    # Core: keep center if enabled
    blast_platforms = geo.createNode("blast", "keep_core")
    blast_platforms.parm("group").set("@ring==-1")
    blast_platforms.parm("negate").set(False)  # keep core only
    blast_platforms.setInput(0, wrangle)
    # Transform core sphere to origin (already there) and copy? Just use sphere at origin
    # Instead, use xform to place sphere at core point (which is 0,0,0 anyway)
    # So we can just merge sphere directly
    # But filter sphere visibility via switch
    switch_core = geo.createNode("switch", "switch_core")
    switch_core.parm("input").setExpression('chi("../controls/addCenterCore")')
    # input 0 = sphere, input 1 = null (empty)
    null_empty = geo.createNode("null", "null_empty")
    switch_core.setInput(0, sphere)
    switch_core.setInput(1, null_empty)

    # Final merge: platforms + bridges + core
    merge = geo.createNode("merge", "merge_all")
    merge.setInput(0, copy)
    merge.setInput(1, sweep)
    merge.setInput(2, switch_core)

    # Output
    output = geo.createNode("output", "output0")
    output.setInput(0, merge)

    # Layout
    try:
        geo.layoutChildren()
    except Exception:
        pass

    if test_cook:
        # Quick cook test: force cook and count points/prims
        print("[Orbital] Test cook — cooking geo...")
        try:
            geo.cook(force=True)
            # Count via detail
            # need to evaluate after cook
            out_geo = output.geometry()
            if out_geo:
                print(f"[Orbital] Test cook OK: points={len(list(out_geo.points()))} prims={len(list(out_geo.prims()))}")
            else:
                print("[Orbital] Test cook: no geometry after cook (check wrangle snippet)")
        except Exception as e:
            print(f"[Orbital] Test cook failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        return 0

    # Create HDA
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"[Orbital] Removing existing {out}")
        try:
            import os
            os.remove(out)
        except Exception:
            pass

    print(f"[Orbital] Creating HDA {out}")
    try:
        # createDigitalAsset signature varies: name, hda_file_name, description
        geo.createDigitalAsset(name="SpaceTraversal_OrbitalRings", hda_file_name=str(out), description="Space Traversal Orbital Rings (BS_GodFile)")
        print(f"[Orbital] HDA created: {out} ({out.stat().st_size} bytes)")
    except TypeError as te:
        print(f"[Orbital] createDigitalAsset TypeError: {te}, trying fallback")
        geo.createDigitalAsset("SpaceTraversal_OrbitalRings", str(out), "Space Traversal Orbital Rings")
        print(f"[Orbital] HDA created (fallback): {out}")
    except Exception as e:
        print(f"[Orbital] HDA creation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Build SpaceTraversal Orbital Rings HDA")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output .hda path")
    parser.add_argument("--test-cook", action="store_true", help="Only test cook, don't save HDA")
    args = parser.parse_args()

    if args.test_cook:
        return build_hda(args.out, test_cook=True)
    return build_hda(args.out, test_cook=False)

if __name__ == "__main__":
    sys.exit(main())
