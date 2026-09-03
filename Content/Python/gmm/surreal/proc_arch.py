"""Procedural architecture generators — cathedral grammar, style bundles, PCG orchestration.

Wraps build_cathedral_grammar.py (recursive nave/buttress grammar) and
apply_style_bundle.py (style-packaged PCG + material + Niagara bundles).
"""
from __future__ import annotations

from typing import Optional

from gmm.core import GmmAudit

STYLE_BUNDLE_NAMES = ("Sakura", "Baroque", "Escher", "Zen", "Cosmic")


def build_cathedral_nave(bay_count: int = 4, buttress_depth: int = 3, force: bool = False) -> dict:
    """Build cathedral grammar PCG graph (recursive nave + buttress system).

    Args:
        bay_count: Number of bays along the nave spine (1-8).
        buttress_depth: Recursion depth for flying buttress system (1-4).
        force: Rebuild even if graph exists.

    Returns audit dict.
    """
    try:
        import build_cathedral_grammar as bcg
    except ImportError:
        return {"ok": False, "error": "build_cathedral_grammar not available"}
    try:
        bcg.build_nave(bay_count=bay_count, buttress_depth=buttress_depth)
        audit = GmmAudit(action="surreal.proc_arch.cathedral",
                         bay_count=bay_count, buttress_depth=buttress_depth, ok=True)
        audit.save("gmm_cathedral.json")
        return audit.to_dict()
    except Exception as e:
        audit = GmmAudit(action="surreal.proc_arch.cathedral", ok=False, error=str(e))
        audit.save("gmm_cathedral.json")
        return audit.to_dict()


def apply_style_bundle(style: str, target_actor_label: str = "") -> dict:
    """Apply a named style bundle (PCG graph + material + Niagara) to a target.

    Style must be one of STYLE_BUNDLE_NAMES.
    If target_actor_label is empty, logs validation-only.
    """
    try:
        import apply_style_bundle as asb
    except ImportError:
        return {"ok": False, "error": "apply_style_bundle not available"}

    if style not in STYLE_BUNDLE_NAMES:
        return {"ok": False, "error": f"unknown style '{style}'. Known: {STYLE_BUNDLE_NAMES}"}

    try:
        import unreal
        target_actor = None
        if target_actor_label:
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            for actor in eas.get_all_level_actors() or []:
                if actor.get_actor_label() == target_actor_label:
                    target_actor = actor
                    break
        result = asb.apply_style_bundle(style, target_actor=target_actor)
        audit = GmmAudit(action="surreal.proc_arch.style_bundle",
                         style=style, ok=result.get("ok", False), applied_to=target_actor_label)
        audit.save("gmm_style_bundle.json")
        return audit.to_dict()
    except Exception as e:
        audit = GmmAudit(action="surreal.proc_arch.style_bundle",
                         style=style, ok=False, error=str(e))
        audit.save("gmm_style_bundle.json")
        return audit.to_dict()


def CATHEDRAL_STATUS() -> dict:
    """Check if cathedral grammar graphs exist on disk."""
    try:
        import unreal
    except ImportError:
        return {"ok": False, "error": "unreal not available"}
    dest = "/Game/EnvSandbox/PCG/Styles/Baroque"
    paths = {
        "nave": f"{dest}/PCG_CathedralGrammar_Nave",
        "buttress": f"{dest}/PCG_CathedralGrammar_Buttress",
    }
    return {k: unreal.EditorAssetLibrary.does_asset_exist(v) for k, v in paths.items()}
