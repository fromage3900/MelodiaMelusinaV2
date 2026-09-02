"""Create hda/ArpeggioStair_1.0.hda headlessly via hython — BS_GodFile Houdini 22.0.368

Usage (from project root):
    & "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Content/Python/create_hda_arpeggio_stair.py
    # optional: explicit output
    & "...\hython.exe" Content/Python/create_hda_arpeggio_stair.py --out hda/ArpeggioStair_1.0.hda

Requires Houdini Engine license (hserver -l shows Houdini Engine, not None). No UE needed.
Falls back to informative exit if hou not available.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "hda" / "ArpeggioStair_1.0.hda"

def main() -> int:
    parser = argparse.ArgumentParser(description="Create ArpeggioStair HDA via hython")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output .hda path")
    args = parser.parse_args()

    try:
        import hou
    except ImportError as e:
        print(f"[HDA] hou not available (are you running inside hython?): {e}", file=sys.stderr)
        print("[HDA] Run: & \"C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe\" Content/Python/create_hda_arpeggio_stair.py", file=sys.stderr)
        return 2

    print(f"[HDA] Houdini {hou.applicationVersionString()}  hou {hou.__version__}")
    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    # Create a new HIP in memory
    try:
        # Ensure we have an OBJ context
        obj = hou.node("/obj")
        if obj is None:
            print("[HDA] /obj not found", file=sys.stderr)
            return 1

        # Clean previous if exists
        existing = hou.node("/obj/ArpeggioStair_Template")
        if existing:
            existing.destroy()

        geo = obj.createNode("geo", "ArpeggioStair_Template")
        geo.moveToGoodPosition()

        # Remove default file node
        for child in geo.children():
            try:
                child.destroy()
            except Exception:
                pass

        # Grid: stepCount x laneCount points
        grid = geo.createNode("grid", "grid_steps_lanes")
        grid.parm("sizex").set(10)
        grid.parm("sizey").set(10)
        grid.parm("rows").setExpression('ch("../controls/stepCount")')
        grid.parm("cols").setExpression('ch("../controls/laneCount")')
        # Use oriented grid on XZ plane
        grid.parm("orient").set(2)  # ZX plane

        # Controls null with parameters
        controls = geo.createNode("null", "controls")
        # Create spare parameters on controls (HDA-style). Use simple parm template group.
        import hou as _hou
        group = controls.parmTemplateGroup()
        group.append(_hou.IntParmTemplate("seed", "Seed", 1, default_value=(1337,), min=1, max=9999999))
        group.append(_hou.IntParmTemplate("stepCount", "Step Count", 1, default_value=(16,), min=4, max=32))
        group.append(_hou.IntParmTemplate("laneCount", "Lane Count", 1, default_value=(4,), min=1, max=8))
        group.append(_hou.FloatParmTemplate("stepSpacing", "Step Spacing (cm)", 1, default_value=(200,), min=10, max=1000))
        group.append(_hou.FloatParmTemplate("laneSpacing", "Lane Spacing (cm)", 1, default_value=(150,), min=10, max=1000))
        group.append(_hou.IntParmTemplate("baseMidiNote", "Base MIDI Note", 1, default_value=(60,), min=21, max=108))
        group.append(_hou.MenuParmTemplate("scale", "Scale", ("major","minor","pentatonic","chromatic"), default_value=0))
        group.append(_hou.FloatParmTemplate("heightPerDegree", "Height Per Degree (cm)", 1, default_value=(15,), min=0, max=100))
        controls.setParmTemplateGroup(group)

        # Point wrangle: assign seed/midi/lane/stepIndex, offset by spacing, height by scale degree
        wrangle = geo.createNode("attribwrangle", "assign_musical")
        wrangle.parm("class").set(0)  # points
        wrangle.parm("snippet").set(
            'int stepCount = chi("../controls/stepCount");\n'
            'int laneCount = chi("../controls/laneCount");\n'
            'float stepSpacing = chf("../controls/stepSpacing");\n'
            'float laneSpacing = chf("../controls/laneSpacing");\n'
            'int baseMidi = chi("../controls/baseMidiNote");\n'
            'float hPerDeg = chf("../controls/heightPerDegree");\n'
            'int stepIdx = @ptnum / laneCount;\n'
            'int lane = @ptnum % laneCount;\n'
            'int scale = chi("../controls/scale");\n'
            '// pentatonic/major mapping simplified\n'
            'int degree = lane % 7;\n'
            'if (scale == 2) degree = lane % 5;\n'
            'if (scale == 3) degree = lane;\n'
            'i@lane = lane;\n'
            'i@stepIndex = stepIdx;\n'
            'i@midiNote = baseMidi + degree;\n'
            'i@seed = chi("../controls/seed") + @ptnum;\n'
            '@P.x = (stepIdx - stepCount/2) * stepSpacing;\n'
            '@P.z = (lane - laneCount/2) * laneSpacing;\n'
            '@P.y = degree * hPerDeg;\n'
        )

        # Simple box copy for visual
        box = geo.createNode("box", "pad_box")
        box.parm("sizex").set(1.0)
        box.parm("sizey").set(0.16)
        box.parm("sizez").set(1.0)

        copy = geo.createNode("copytopoints::2.0", "copy_pads")
        copy.setInput(0, box)
        copy.setInput(1, wrangle)

        # Output
        out_node = geo.createNode("output", "output0")
        out_node.setInput(0, copy)

        wrangle.setInput(0, grid)

        # Layout
        geo.layoutChildren()

        # Create HDA from this subnet
        # Define new digital asset
        hda_name = "ArpeggioStair::1.0"
        if out.exists():
            print(f"[HDA] Removing existing {out}")
            try:
                out.unlink()
            except Exception:
                out.unlink(missing_ok=True) if hasattr(out, "unlink") else None
            try:
                out.unlink(missing_ok=True)
            except Exception:
                pass
            # actual delete
            import os
            try:
                os.remove(out)
            except Exception:
                pass

        print(f"[HDA] Creating digital asset {hda_name} -> {out}")
        # createDigitalAsset(section) API: use hou.hda
        try:
            geo.createDigitalAsset(name="ArpeggioStair", hda_file_name=str(out), description="ArpeggioStair musical stair (BS_GodFile)")
            print(f"[HDA] Created {out} ({out.stat().st_size} bytes)")
        except TypeError:
            # older signature
            geo.createDigitalAsset("ArpeggioStair", str(out), "ArpeggioStair musical stair")
            print(f"[HDA] Created (fallback) {out}")

        return 0

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[HDA] Failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
