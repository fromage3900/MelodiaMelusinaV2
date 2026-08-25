# Gaea panel - surfaced because Gaea is installed and highly important (owner 2026-08-24)
# Provides terrain inspector + erosion processor + UE handoff, C: authority

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

# Shared helpers
try:
    from . import addon_utils  # type: ignore
    import melodia_utils as _mu  # type: ignore
except Exception:
    addon_utils = None  # type: ignore
    try:
        _ADDONS_ROOT = Path(__file__).resolve().parent.parent
        if str(_ADDONS_ROOT) not in sys.path:
            sys.path.insert(0, str(_ADDONS_ROOT))
        import melodia_utils as _mu  # type: ignore
    except Exception:
        _mu = None  # type: ignore

# Gaea install detection (C: authority, QuadSpinner)
_GAEA_CANDIDATES = [
    Path(r"C:\Program Files\QuadSpinner\Gaea 2\Gaea.exe"),
    Path(r"C:\Program Files\QuadSpinner\Gaea\Gaea.exe"),
]
_GAEA_EXAMPLES = Path(r"C:\Program Files\QuadSpinner\Gaea 2\Examples")
_GAEA_EXAMPLES_LEGACY = Path(r"C:\Program Files\QuadSpinner\Gaea\Examples")

def _gaea_status():
    for p in _GAEA_CANDIDATES:
        if p.exists():
            examples = _GAEA_EXAMPLES if _GAEA_EXAMPLES.is_dir() else _GAEA_EXAMPLES_LEGACY
            count = len(list(examples.glob("*.terrain"))) if examples.is_dir() else 0
            return {"installed": True, "exe": str(p), "examples": str(examples), "example_count": count}
    return {"installed": False, "exe": "", "examples": "", "example_count": 0}

def _project_terrains():
    # Project has no .terrain yet (per audit) - look in repo
    if _mu is None:
        root = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
    else:
        root = _mu.repo_root()
    found = list(root.rglob("*.terrain"))
    # Exclude Program Files examples if root search leaked (should not)
    found = [p for p in found if "QuadSpinner" not in str(p)]
    return found[:16]

def _audit_heightfields():
    if _mu is None:
        base = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\world_build_20260824")
    else:
        base = _mu.repo_root() / "Saved" / "Audit" / "world_build_20260824"
    if not base.is_dir():
        return [], 0
    hfs = list(base.rglob("heightfield*.png"))
    # also ue_handoff/heightfield.png
    hfs += list(base.rglob("ue_handoff/heightfield.png"))
    # dedup
    uniq = {}
    for p in hfs:
        uniq[str(p.resolve()).lower()] = p
    return sorted(uniq.values()), len(uniq)


if bpy is not None:

    class GAEA_OT_validate_terrain(bpy.types.Operator):
        bl_idname = "melodia_studio.gaea_validate"
        bl_label = "Validate .terrain"
        bl_options = {'REGISTER'}
        filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'HIDDEN','SKIP_SAVE'})  # type: ignore
        filter_glob: bpy.props.StringProperty(default="*.terrain", options={'HIDDEN'})  # type: ignore

        def execute(self, context):
            from . import gaea_terrain_io as gti  # type: ignore
            props = context.scene.melodia_studio
            path = self.filepath or getattr(props, "gaea_terrain_path", "")
            if not path or not os.path.exists(path):
                # Default to first example if no selection
                st = _gaea_status()
                if st["installed"]:
                    cand = list(Path(st["examples"]).glob("*.terrain"))
                    if cand:
                        path = str(cand[0])
            if not path or not os.path.exists(path):
                self.report({'WARNING'}, "No .terrain found - pick a file")
                return {'CANCELLED'}
            try:
                res = gti.validate_terrain(path)
                ok = res.get("ok", False)
                summ = res.get("summary", {})
                msg = f"{'OK' if ok else 'ISSUE'} {summ.get('resolution','?')}px {summ.get('width_m','?')}x{summ.get('height_m','?')}m {summ.get('node_count','?')} nodes"
                if res.get("issues"):
                    msg += " | " + "; ".join(res["issues"])
                props.last_report = msg
                self.report({'INFO'} if ok else {'WARNING'}, msg)
                return {'FINISHED'}
            except Exception as exc:
                self.report({'ERROR'}, f"Validate failed: {exc}")
                return {'CANCELLED'}

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

    class GAEA_OT_process_erosion(bpy.types.Operator):
        bl_idname = "melodia_studio.gaea_process_erosion"
        bl_label = "Erode Heightfield"
        bl_options = {'REGISTER'}

        def execute(self, context):
            props = context.scene.melodia_studio
            # Process all 14 presets or single? For now single + audit folder
            if _mu is None:
                self.report({'ERROR'}, "melodia_utils not available")
                return {'CANCELLED'}
            base = _mu.repo_root() / "Saved" / "Audit" / "world_build_20260824"
            if not base.is_dir():
                self.report({'WARNING'}, f"Audit folder not found: {base}")
                return {'CANCELLED'}
            # Pick first heightfield as demo
            hfs, _ = _audit_heightfields()
            if not hfs:
                self.report({'WARNING'}, "No heightfield PNGs found")
                return {'CANCELLED'}
            src = hfs[0]
            dst = base / "gaea_eroded" / src.name
            try:
                from . import gaea_erosion_processor as gep  # type: ignore
                res = gep.process_heightfield(src, dst)
                msg = f"Eroded {res['width']}x{res['height']} mean {res['mean']:.3f} -> {dst}"
                props.last_report = msg
                self.report({'INFO'}, msg)
                return {'FINISHED'}
            except Exception as exc:
                # PIL may be missing headless
                self.report({'ERROR'}, f"Erosion failed (need PIL?): {exc}")
                return {'CANCELLED'}

    class GAEA_OT_build_handoff(bpy.types.Operator):
        bl_idname = "melodia_studio.gaea_build_handoff"
        bl_label = "Build UE Handoff"
        bl_options = {'REGISTER'}

        def execute(self, context):
            if _mu is None:
                self.report({'ERROR'}, "melodia_utils missing")
                return {'CANCELLED'}
            base = _mu.repo_root() / "Saved" / "Audit" / "world_build_20260824"
            # pick first preset's heightfield and dressing_plan
            cand = list(base.glob("*/ue_handoff/heightfield.png"))
            if not cand:
                cand = list(base.glob("*/heightfield*.png"))
            if not cand:
                self.report({'WARNING'}, "No heightfield found")
                return {'CANCELLED'}
            hf = cand[0]
            # sibling dressing_plan
            dp = hf.parent / "dressing_plan.json"
            if not dp.exists():
                # search nearby
                dps = list(hf.parent.parent.glob("dressing_plan*.json"))
                dp = dps[0] if dps else hf
            if not dp.exists():
                self.report({'WARNING'}, f"Dressing plan not found near {hf}")
                return {'CANCELLED'}
            try:
                from . import gaea_erosion_processor as gep  # type: ignore
                out_dir = base / "gaea_handoff_demo"
                manifest = gep.build_mesh_terrain_handoff(hf, dp, preset_id=hf.parent.name if hf.parent.name != "ue_handoff" else hf.parent.parent.name, output_dir=out_dir)
                msg = f"Handoff {manifest['ue']['recommended_content_path']} -> {out_dir/'handoff_manifest.json'}"
                context.scene.melodia_studio.last_report = msg
                self.report({'INFO'}, msg)
                return {'FINISHED'}
            except Exception as exc:
                self.report({'ERROR'}, f"Handoff failed: {exc}")
                return {'CANCELLED'}

    class GAEA_OT_open_gaea(bpy.types.Operator):
        bl_idname = "melodia_studio.open_gaea"
        bl_label = "Open Gaea"
        def execute(self, context):
            st = _gaea_status()
            if not st["installed"]:
                self.report({'WARNING'}, "Gaea not found in Program Files\\QuadSpinner")
                return {'CANCELLED'}
            try:
                import subprocess
                # Don't actually launch Gaea exe headless - open its folder
                if addon_utils is not None:
                    addon_utils.open_folder(Path(st["exe"]).parent)
                else:
                    import os as _os
                    _os.startfile(str(Path(st["exe"]).parent))  # type: ignore
                self.report({'INFO'}, f"Opened {st['exe']}")
            except Exception as exc:
                self.report({'ERROR'}, str(exc))
                return {'CANCELLED'}
            return {'FINISHED'}

    class GAEA_PT_panel(bpy.types.Panel):
        bl_label = "Melodia Gaea"
        bl_idname = "GAEA_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            # Bespoke header
            if addon_utils is not None:
                try:
                    addon_utils.draw_melodia_header(layout, "Gaea", "Heightfields * Erosion * UE Mesh Terrain", icon_key="generate")
                except Exception:
                    layout.label(text="*  MELODIA  -  GAEA")
            else:
                layout.label(text="*  MELODIA  -  GAEA")

            st = _gaea_status()
            box = layout.box()
            if st["installed"]:
                box.label(text="G a e a   I n s t a l l e d", icon='CHECKMARK')
                box.label(text=st["exe"])
                box.label(text=f"Examples: {st['example_count']} .terrain")
            else:
                box.alert = True
                box.label(text="Gaea not found", icon='ERROR')
                box.label(text=r"C:\Program Files\QuadSpinner\Gaea 2\Gaea.exe")

            # Project terrains
            proj = _project_terrains()
            box2 = layout.box()
            box2.label(text="P r o j e c t   . t e r r a i n", icon='FILE')
            if proj:
                for p in proj[:4]:
                    box2.label(text=p.name)
                if len(proj) > 4:
                    box2.label(text=f"... +{len(proj)-4} more")
            else:
                box2.label(text="No project .terrain yet")
                box2.label(text="Using Gaea Examples as source")

            # Heightfields
            hfs, count = _audit_heightfields()
            box3 = layout.box()
            box3.label(text=f"H e i g h t f i e l d s  ({count})", icon='IMAGE_DATA')
            if hfs:
                for p in hfs[:3]:
                    box3.label(text=p.name + f"  {p.stat().st_size//1024}KB" if p.exists() else p.name)
                if count > 3:
                    box3.label(text=f"... +{count-3} more")
            else:
                box3.label(text="No heightfields in Saved/Audit/world_build_20260824")

            # Actions
            col = layout.column(align=True)
            col.scale_y = 1.1
            col.operator("melodia_studio.gaea_validate", text="Validate .terrain", icon='FILE_TICK')
            col.operator("melodia_studio.gaea_process_erosion", text="Erode Heightfield (PIL)", icon='MOD_SMOOTH')
            col.operator("melodia_studio.gaea_build_handoff", text="Build UE Handoff", icon='EXPORT')
            row = col.row(align=True)
            row.operator("melodia_studio.open_gaea", text="Open Gaea Folder", icon='FILE_FOLDER')
            # Quick audit count
            if hfs:
                col.label(text=f"{count} heightfields ready for Mesh Terrain", icon='INFO')

    classes = [
        GAEA_OT_validate_terrain,
        GAEA_OT_process_erosion,
        GAEA_OT_build_handoff,
        GAEA_OT_open_gaea,
        GAEA_PT_panel,
    ]

else:
    classes = []  # type: ignore

def register():
    if bpy is None:
        return
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass

def unregister():
    if bpy is None:
        return
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
