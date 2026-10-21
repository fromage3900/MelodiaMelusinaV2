"""Melodia Studio - STUDIO_PT_* N-panels.

Split out of studio_panel.py on 2026-10-04 (monolith split, no logic change).
bl_idnames STUDIO_PT_panel / STUDIO_PT_management and the "Melodia Studio"
category are unchanged. Registration happens in the studio_panel facade.
"""

import os
import sys

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge
from . import midi_picker

# Optional QOL helpers - offline-safe
try:
    from . import addon_utils  # type: ignore
except Exception:
    addon_utils = None  # type: ignore

try:
    from . import melodia_chrome as _chrome  # type: ignore
except Exception:
    _chrome = None  # type: ignore

try:
    import melodia_utils as _mu  # type: ignore
except Exception:
    # Fallback: parent of addons root is on sys.path when loaded as Script Directory
    try:
        _ADDONS_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        if _ADDONS_ROOT not in sys.path:
            sys.path.insert(0, _ADDONS_ROOT)
        import melodia_utils as _mu  # type: ignore
    except Exception:
        _mu = None  # type: ignore


# ------------------------------------------------------------- panels

if bpy is not None:

    def _icon(key, fallback):
        if addon_utils is not None:
            try:
                return addon_utils.icon_kwargs(key, fallback)
            except Exception:
                pass
        return {"icon": fallback}

    class STUDIO_PT_panel(bpy.types.Panel):
        bl_label = "Melodia Studio"
        bl_idname = "STUDIO_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"  # separate tab per owner
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            props = context.scene.melodia_studio

            # Gold-ivory luxury header with pink/rose-gold pillar (cathedral)
            if _chrome is not None:
                try:
                    _chrome.chrome_header(layout, "Studio", "MIDI  ->  Walkable Ground  |  Field-Wins", pillar="cathedral", icon_key="starlight")
                except Exception:
                    pass
                # Canon version line - the panel always reports the live product
                # version (source: surreal_architecture_gen bl_info), so "which
                # build am I running" is never archaeology again.
                # (desktop main delta, ported into the split 2026-10-04)
                try:
                    from surreal_architecture_gen import bl_info as _sag_bl_info
                    _v = ".".join(str(x) for x in _sag_bl_info.get("version", (0, 0, 0)))
                    layout.label(text=f"Melodia Studio  v{_v}", icon="CHECKMARK")
                except Exception:
                    pass
            else:
                # fallback: health hint (one line, not noisy)
                if _mu is not None:
                    h = _mu.health_check()
                    if not h["ok"] and h["issues"]:
                        box = layout.box()
                        box.alert = True
                        box.label(text="Setup needed", icon='ERROR')
                        box.label(text=h["issues"][0])

            # Health status as single kicker line (luxury, not red box) when chrome present
            if _chrome is not None and _mu is not None:
                try:
                    h = _mu.health_check()
                    if not h["ok"] and h["issues"]:
                        _chrome.chrome_status(layout, False, "Setup needed", h["issues"][0])
                except Exception:
                    pass

            # Resonant World
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(layout, "Resonant World", icon='FILE_SOUND')
                except Exception:
                    pass
            box = layout.box()
            row = box.row()
            if _chrome is None:
                row.label(text="Resonant World", icon='FILE_SOUND')
            row.operator("melodia_studio.refresh_midi", text="", icon='FILE_REFRESH')
            # Search + MIDI picker
            box.prop(props, "midi_filter", text="", icon='VIEWZOOM')
            box.prop(props, "midi_file", text="")
            # Truncate hint (audit P0)
            try:
                _found_all = midi_picker._discover_cached()
                if len(_found_all) > 64:
                    box.label(text=f"Showing 64 of {len(_found_all)} - use search", icon='INFO')
            except Exception:
                pass
            # Preview line for selected MIDI
            midi = midi_picker._selected_midi(props)
            if midi and os.path.exists(midi):
                box.label(text=midi_picker._midi_preview_lines(midi), icon='INFO')
            box.prop(props, "preset", text="Preset")
            box.prop(props, "custom_midi", text="Custom")

            # Dressing + options
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(box, "Dressing  |  Pink  &  Rose Gold", icon='BRUSH_DATA')
                except Exception:
                    pass
            box.prop(props, "dressing_style", text="Dressing")
            row = box.row()
            row.prop(props, "auto_cleanup")
            row.prop(props, "show_advanced", text="Advanced")
            # Instance controls (-visible always; advanced shows seed/budget)
            row2 = box.row(align=True)
            row2.prop(props, "dress_instance", text="Instance Props")
            if props.show_advanced:
                row3 = box.row(align=True)
                row3.prop(props, "dress_seed", text="Seed")
                row3.prop(props, "dress_budget", text="Budget")

            col = box.column(align=True)
            col.scale_y = 1.4
            col.operator("melodia_studio.generate_from_midi", **_icon("generate", 'MOD_BUILD'))  # type: ignore[arg-type]

            # Presentation
            if _chrome is not None:
                try:
                    _chrome.chrome_kicker(layout, "Presentation", icon='LIGHT')
                except Exception:
                    pass
            box2 = layout.box()
            if _chrome is None:
                box2.label(text="Presentation", icon='LIGHT')
            col = box2.column(align=True)
            col.operator("melodia_studio.frame_terrain", icon='CAMERA_DATA')
            row = col.row(align=True)
            row.operator("melodia_studio.render_proof", icon='RENDER_STILL')
            row.operator("melodia_studio.batch_render", icon='RENDER_ANIMATION')
            row = col.row(align=True)
            row.operator("melodia_studio.save_scene", icon='FILE_TICK')
            row.operator("melodia_studio.cleanup_scene", icon='TRASH')

            # Config
            if props.show_advanced:
                box3 = layout.box()
                box3.label(text="Config", icon='PREFERENCES')
                box3.operator("melodia_studio.write_presets", icon='EXPORT')
                row = box3.row(align=True)
                row.operator("melodia_studio.open_folder", text="MIDI").folder = "midi"  # type: ignore[attr-defined]
                row.operator("melodia_studio.open_folder", text="Scenes").folder = "scenes"  # type: ignore[attr-defined]
                row = box3.row(align=True)
                row.operator("melodia_studio.validate_health", icon='CHECKMARK')

            if props.last_report:
                layout.separator()
                box = layout.box()
                box.label(text="Last run", icon='CHECKMARK')
                # Wrap long report
                for line in str(props.last_report).split(" | "):
                    box.label(text=line)
                if props.last_midi:
                    box.label(text=os.path.basename(props.last_midi), icon='FILE_SOUND')

    class STUDIO_PT_management(bpy.types.Panel):
        bl_label = "Management"
        bl_idname = "STUDIO_PT_management"
        bl_parent_id = "STUDIO_PT_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Melodia Studio"
        bl_options = {'DEFAULT_CLOSED'}

        def draw(self, context):
            layout = self.layout
            if _chrome is not None:
                try:
                    _chrome.chrome_header(layout, "Management", "C Authority  |  Autosync", pillar="grotto", icon_key="starlight")
                except Exception:
                    pass

            # 4-row health dashboard
            if _mu is not None:
                root = _mu.repo_root()
                h = _mu.health_check()

                box = layout.box()
                box.label(text="Health", icon='HEART')
                row = box.row()
                row.label(text="Repo: %s" % os.path.basename(root), icon='FILE_FOLDER')
                row.alignment = 'RIGHT'
                row.label(text="OK" if h["ok"] else "ISSUES",
                          icon='CHECKMARK' if h["ok"] else 'ERROR')

                row = box.row()
                row.label(text="MIDI: %d files" % h.get("midi_count", 0),
                          icon='FILE_SOUND')

                if h.get("issues"):
                    for iss in h["issues"][:3]:
                        row = box.row()
                        row.label(text=iss, icon='ERROR')
                    if len(h["issues"]) > 3:
                        row = box.row()
                        row.label(text=f"... +{len(h['issues'])-3} more", icon='INFO')
                else:
                    row = box.row()
                    row.label(text="All systems nominal", icon='CHECKMARK')

                vers = _mu.addon_versions()
                if vers:
                    row = box.row()
                    row.label(text="Addons: %d" % len(vers), icon='PACKAGE')
                # GN preset badge — live audit if surreal_arch on path
                try:
                    import importlib.util as _ilu
                    import pathlib as _pl
                    _gn_presets = _pl.Path(midi_bridge.repo_root()) / "deploy" / "surreal_arch" / "melodia_gn" / "presets.py"
                    if _gn_presets.exists():
                        spec = _ilu.spec_from_file_location("_gn_presets_tmp", str(_gn_presets))
                        if spec and spec.loader:
                            mod = _ilu.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            rep = mod.audit_presets() if hasattr(mod, "audit_presets") else {}
                            cov = rep.get("coverage_ratio", 0)
                            pb = rep.get("preset_builders", 0)
                            rb = rep.get("registered_builders") or rep.get("preset_builders", 0)
                            row = box.row()
                            row.label(text=f"GN: {pb}/{rb} presets {cov*100:.0f}%", icon='NODETREE')
                except Exception:
                    pass
                # AppData drift hint
                try:
                    if _mu is not None and hasattr(_mu, "addon_versions"):
                        av = _mu.addon_versions()
                        tools_ver = None
                        appdata_ver = None
                        for k, v in (av or {}).items():
                            if "melodia_studio" in k.lower():
                                tools_ver = v
                                break
                        if tools_ver:
                            row = box.row()
                            row.label(text=f"Melodia Studio {tools_ver}", icon='INFO')
                except Exception:
                    pass
            else:
                layout.label(text=midi_bridge.repo_root(), icon='FILE_FOLDER')
                layout.label(text="melodia_utils not available", icon='ERROR')

            col = layout.column(align=True)
            col.operator("melodia_studio.validate_health", icon='HEART')
            row = col.row(align=True)
            row.operator("melodia_studio.setup_script_directory",
                         icon='SCRIPTPLUGINS')
            row.operator("melodia_studio.open_folder",
                         text="Addons").folder = "addons"  # type: ignore[attr-defined]
            row = col.row(align=True)
            row.operator("melodia_studio.open_folder",
                         text="Showroom").folder = "showroom"  # type: ignore[attr-defined]

    PANEL_CLASSES = [
        STUDIO_PT_panel,
        STUDIO_PT_management,
    ]

else:
    PANEL_CLASSES = []  # type: ignore
