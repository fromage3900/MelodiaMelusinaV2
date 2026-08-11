"""UMG widget blueprint builder helpers — wraps unreal.WidgetBlueprint API.

Usage in UE Python console:

    from gmm.ui.battle_menu import create_battle_menu_widget
    result = create_battle_menu_widget()
    print(result)

Requires: running Unreal Editor with Python scripting enabled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gmm.ui.colors import GameColors


@dataclass
class WidgetBuildResult:
    ok: bool
    path: str = ""
    asset: Any = None
    error: str = ""


def _rgba(r: float, g: float, b: float, a: float = 1.0):
    try:
        import unreal
        return unreal.LinearColor(r, g, b, a)
    except ImportError:
        return None


def _margin(left=0, top=0, right=0, bottom=0):
    try:
        import unreal
        return unreal.Margin(left, top, right, bottom)
    except ImportError:
        return None


def _vector2d(x=0, y=0):
    try:
        import unreal
        return unreal.Vector2D(x, y)
    except ImportError:
        return None


def new_widget_blueprint(asset_path: str) -> WidgetBuildResult:
    """Create an empty WidgetBlueprint asset at path."""
    try:
        import unreal
        factory = unreal.WidgetBlueprintFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset = asset_tools.create_asset(
            asset_path.split("/")[-1],
            "/".join(asset_path.split("/")[:-1]),
            None,
            unreal.WidgetBlueprint,
            factory,
        )
        if not asset:
            return WidgetBuildResult(ok=False, error="create_asset returned None")
        return WidgetBuildResult(ok=True, path=asset_path, asset=asset)
    except Exception as e:
        return WidgetBuildResult(ok=False, error=str(e))


def set_widget_tree_root(bp, root_widget_class, root_name="Root"):
    """Set root widget of a WidgetBlueprint to an instance of root_widget_class."""
    try:
        import unreal
        tree = bp.get_widget_tree()
        root = unreal.new_object(root_widget_class, tree)
        root.set_name(root_name)
        tree.root_widget = root
        return root
    except Exception:
        return None


def add_child(parent, child_class, child_name="", **slot_kwargs):
    """Add a child widget to a panel parent. Returns the child."""
    try:
        import unreal
        tree = parent.get_editor_property("widget_tree") if hasattr(parent, "get_editor_property") else None
        if tree is None:
            bp = _find_bp(parent)
            if bp:
                tree = bp.get_widget_tree()
        if tree is None:
            obj = unreal.new_object(child_class)
        else:
            obj = unreal.new_object(child_class, tree)
        if child_name:
            obj.set_name(child_name)
        if hasattr(parent, "add_child"):
            parent.add_child(obj)
        elif hasattr(parent, "add_slot"):
            parent.add_slot(obj)
        for k, v in slot_kwargs.items():
            try:
                setattr(obj, k, v)
            except Exception:
                pass
        return obj
    except Exception:
        return None


def _find_bp(widget):
    """Walk up to find the owning WidgetBlueprint."""
    try:
        import unreal
        seen = set()
        obj = widget
        while obj is not None and obj not in seen:
            seen.add(obj)
            if isinstance(obj, unreal.WidgetBlueprint):
                return obj
            try:
                obj = obj.get_outer()
            except Exception:
                break
    except Exception:
        pass
    return None


def make_text_block(content: str, color_rgba: tuple = (1, 1, 1, 1),
                    font_family: str = "Inter", font_size: int = 14,
                    justification: int = 0, name: str = ""):
    """Create a TextBlock widget with styling."""
    try:
        import unreal
        tb = unreal.new_object(unreal.TextBlock)
        if name:
            tb.set_name(name)
        tb.set_text(content)
        lc = _rgba(*color_rgba)
        if lc:
            tb.set_color_and_opacity(lc)
        try:
            fs = unreal.Font()
            fs.set_editor_property("font_object_family", font_family)
            tb.set_font(font_size, fs)
        except Exception:
            tb.set_font(font_size)
        return tb
    except Exception:
        return None


def make_progress_bar(percent: float = 0.5, fill_color: tuple = (1, 1, 1, 1),
                      bg_color: tuple = (1, 1, 1, 0.08), name: str = ""):
    """Create a ProgressBar widget."""
    try:
        import unreal
        pb = unreal.new_object(unreal.ProgressBar)
        if name:
            pb.set_name(name)
        pb.set_percent(percent)
        fill_lc = _rgba(*fill_color)
        bg_lc = _rgba(*bg_color)
        if fill_lc and bg_lc:
            style = unreal.ProgressBarStyle()
            bg_brush = unreal.SlateBrush()
            bg_brush.tint_color = bg_lc
            style.background_image = bg_brush
            fill_brush = unreal.SlateBrush()
            fill_brush.tint_color = fill_lc
            style.fill_image = fill_brush
            pb.set_editor_property("widget_style", style)
        return pb
    except Exception:
        return None


def make_button(label: str, color_rgba: tuple = None, name: str = ""):
    """Create a Button widget."""
    try:
        import unreal
        btn = unreal.new_object(unreal.Button)
        if name:
            btn.set_name(name)
        if label:
            tb = make_text_block(label, color_rgba or GameColors.TEXT_PRIMARY, font_size=12)
            if tb:
                btn.set_content(tb)
        return btn
    except Exception:
        return None


def save_widget_blueprint(bp) -> bool:
    """Save a widget blueprint asset."""
    try:
        import unreal
        unreal.EditorAssetLibrary.save_asset(bp.get_path_name())
        unreal.log(f"[GMM] Saved widget: {bp.get_path_name()}")
        return True
    except Exception as e:
        try:
            import unreal
            unreal.log_error(f"[GMM] Failed to save widget: {e}")
        except Exception:
            pass
        return False
