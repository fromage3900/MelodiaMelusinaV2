# melodia_chrome - luxury editorial chrome for Melodia Studio panels
# Gold-ivory with pink & rose-gold details (tokens.json + wix/melodia-tokens.css)
# Blender 4.0+ : uses icon_value previews, not theme tint. Offline-safe.

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------- tokens (parsed once, no bpy)
_REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
_CSS = Path(r"C:\EnvironmentPortfolio\wix\melodia-tokens.css")
_JSON = _REPO / "melodia-design-system" / "tokens.json"

def _parse_tokens():
    try:
        text = _CSS.read_text(encoding="utf-8", errors="ignore")
        def _hex(k): 
            import re as _re
            m = _re.search(rf"{_re.escape(k)}:\s*#([0-9A-Fa-f]+)", text)
            return f"#{m.group(1)}" if m else None
        return {
            "gold_500": _hex("--primitive-gold-500") or "#C9A86A",
            "gold_700": _hex("--primitive-gold-700") or "#A7884E",
            "ivory_50": _hex("--primitive-ivory-50") or "#FFF8EE",
            "ivory_100": _hex("--primitive-ivory-100") or "#F8ECD6",
            "plum_800": _hex("--primitive-plum-800") or "#241B2E",
            "sakura_300": _hex("--primitive-sakura-300") or "#E7C9CE",
            "sakura_500": _hex("--primitive-sakura-500") or "#D6A9B0",
            "iris_500": _hex("--primitive-iris-500") or "#6E5AA6",
        }
    except Exception:
        return {"gold_500": "#C9A86A", "gold_700": "#A7884E", "ivory_50": "#FFF8EE",
                "ivory_100": "#F8ECD6", "plum_800": "#241B2E", "sakura_300": "#E7C9CE",
                "sakura_500": "#D6A9B0", "iris_500": "#6E5AA6"}

TOKENS = _parse_tokens()

# Pillar -> chrome accent (maps data-pillar tokens.css:264)
PILLAR_ACCENT = {
    "cathedral": "pillar_cathedral",  # cosmic #66D9FF
    "cosmic": "pillar_cathedral",
    "kaleidonave": "pillar_cathedral",
    "grotto": "pillar_grotto",        # gold #C9A86A
    "melusina": "pillar_grotto",
    "zen": "pillar_zen",              # sakura #D6A9B0 / pink
    "zen_shrine": "pillar_zen",
    "plaza": "pillar_plaza",          # lavender
    "default": "pillar_grotto",
}

# Preset -> chrome card key
PRESET_CARD = {
    "walkable_valley": "preset_walkable_valley",
    "walkable_highlands": "preset_walkable_highlands",
    "walkable_plaza": "preset_walkable_plaza",
    "walkable_canyon": "preset_walkable_canyon",
    "walkable_spiral_arena": "preset_walkable_spiral_arena",
    "cathedral_wide": "preset_cathedral_wide",
}

# ---------------------------------------------------------------- helpers (need bpy at draw time)
def _addon_utils():
    try:
        from . import addon_utils as _au  # type: ignore
        return _au
    except Exception:
        return None

def _icon_id(key: str) -> int:
    au = _addon_utils()
    if au is not None:
        try:
            return au.get_icon_id(key)
        except Exception:
            pass
    return 0

def _icon_kwargs(key: str, fallback: str = 'NONE') -> dict:
    au = _addon_utils()
    if au is not None:
        try:
            return au.icon_kwargs(key, fallback)
        except Exception:
            pass
    return {"icon": fallback}

# ---------------------------------------------------------------- chrome draw calls

def chrome_header(layout, title: str, subtitle: str = "", pillar: str = "cathedral", icon_key: str = "starlight"):
    """Luxury header: [star gold glow] MELODIA -- TITLE + subtitle + gold rule image if available."""
    try:
        import bpy  # type: ignore
    except Exception:
        layout.label(text=f"MELODIA -- {title}")
        if subtitle:
            layout.label(text=subtitle)
        return
    au = _addon_utils()
    # Box as plate
    box = layout.box()
    # Row 1: star + wordmark + pillar dot
    row = box.row()
    # Icon - prefer starlight_gold if chrome generated, else starlight
    icon_id = _icon_id("starlight_gold")
    if not icon_id:
        icon_id = _icon_id(icon_key)
    if icon_id:
        row.label(text="", icon_value=icon_id)
    else:
        row.label(text="*")
    # Cinzel wordmark simulation uppercase
    row.label(text=f"MELODIA  --  {title.upper()}")
    # Pillar dot on right
    pillar_key = PILLAR_ACCENT.get(pillar.lower(), PILLAR_ACCENT.get("default"))
    dot_id = _icon_id(pillar_key) if pillar_key else 0
    if dot_id:
        row.label(text="", icon_value=dot_id)
    if subtitle:
        sub = box.row()
        sub.alignment = 'CENTER'
        sub.label(text=subtitle, icon='DOT')
    # Gold rule: prefer image, else ASCII
    rule_id = _icon_id("gold_rule")
    if rule_id:
        r = box.row()
        r.alignment = 'CENTER'
        r.label(text="", icon_value=rule_id)
    elif au is not None:
        try:
            au.draw_gold_rule(box)
        except Exception:
            box.separator()
    else:
        box.separator()

def chrome_kicker(layout, text: str, icon: str = 'NONE'):
    """Azeret Mono 11px uppercase tracking -- spaced kicker."""
    au = _addon_utils()
    if au is not None:
        try:
            au.draw_kicker(layout, text, icon=icon)
            return
        except Exception:
            pass
    row = layout.row()
    row.alignment = 'CENTER'
    spaced = "  ".join(text.upper())
    if icon != 'NONE':
        row.label(text=spaced, icon=icon)
    else:
        row.label(text=spaced)

def chrome_status(layout, ok: bool, text: str, detail: str = ""):
    """Single-line status: dot + line, replaces 4-row dashboard."""
    row = layout.row()
    row.label(text=text, icon='CHECKMARK' if ok else 'ERROR')
    if detail:
        row.label(text=detail)

def chrome_preset_grid(layout, context, prop_path: str = "tandem_preset"):
    """Large thumbnail preset picker -- replaces raw EnumProperty dropdown.
    Uses melodia_chrome preset_*.png cards. Falls back to normal prop if missing.
    prop_path: scene.melodia_studio.<prop>
    """
    try:
        import bpy  # type: ignore
        props = getattr(context.scene, "melodia_studio", None)
        if props is None:
            return False
        # Try icon grid
        has_cards = any(_icon_id(k) for k in PRESET_CARD.values())
        if has_cards:
            # Use template_icon_view if available (needs EnumProperty with preview)
            # Instead we draw a row of icon buttons that set the enum (Blender-safe)
            current = getattr(props, prop_path, "")
            grid = layout.grid_flow(columns=3, even_columns=True, align=True)
            for preset_id, card_key in PRESET_CARD.items():
                icon_id = _icon_id(card_key)
                if not icon_id:
                    continue
                is_active = (preset_id == current)
                # operator to set preset
                op = grid.operator("melodia_studio.chrome_set_preset", text="", icon_value=icon_id, depress=is_active)
                op.preset_id = preset_id
                op.target = prop_path
            # Show current label underneath
            if current:
                layout.label(text=f"Selected: {current}", icon='DOT')
            return True
        # fallback: normal prop
        layout.prop(props, prop_path, text="Preset")
        return False
    except Exception:
        try:
            layout.prop(context.scene.melodia_studio, prop_path, text="Preset")
        except Exception:
            pass
        return False

# ---------------------------------------------------------------- operator for preset grid (registered only when bpy present)
def _register_preset_op():
    try:
        import bpy  # type: ignore
        class CHROME_OT_set_preset(bpy.types.Operator):  # type: ignore
            bl_idname = "melodia_studio.chrome_set_preset"
            bl_label = "Set Preset"
            preset_id: bpy.props.StringProperty()  # type: ignore
            target: bpy.props.StringProperty(default="tandem_preset")  # type: ignore
            def execute(self, context):
                try:
                    props = context.scene.melodia_studio
                    if hasattr(props, self.target):
                        setattr(props, self.target, self.preset_id)
                    # redraw
                    for area in context.screen.areas:
                        area.tag_redraw()
                    self.report({'INFO'}, f"Preset: {self.preset_id}")
                except Exception as exc:
                    self.report({'WARNING'}, str(exc))
                return {'FINISHED'}
        bpy.utils.register_class(CHROME_OT_set_preset)
        return CHROME_OT_set_preset
    except Exception:
        return None

_CHROME_OP = None

def register():
    global _CHROME_OP
    # ensure chrome icons are loaded via addon_utils (which picks up melodia_chrome/)
    au = _addon_utils()
    if au is not None:
        try:
            au._load_icons()  # warm cache
        except Exception:
            pass
    _CHROME_OP = _register_preset_op()

def unregister():
    global _CHROME_OP
    if _CHROME_OP is not None:
        try:
            import bpy  # type: ignore
            bpy.utils.unregister_class(_CHROME_OP)
        except Exception:
            pass
        _CHROME_OP = None
