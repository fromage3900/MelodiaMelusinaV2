"""Post-generate pipeline stages for Surreal Architecture."""
from __future__ import annotations

from . import bevel_bridge, higgsas_bridge


def run_post_generate(obj, props, monolith, *, skip_bevel: bool = False, bevel_backend: str = "auto") -> None:
    """Ordered post-pass: higgsas detail → bevel (modifier by default)."""
    if obj is None or props is None:
        return
    try:
        higgsas_bridge.apply_surface_pass(obj, props, monolith)
    except Exception as exc:
        print(f"[Surreal Architecture] higgsas pass skipped: {exc}")

    if skip_bevel:
        return
    if getattr(props, "bevel_mode", "NONE") == "NONE":
        return
    if not getattr(props, "auto_bevel_on_generate", True) and bevel_backend == "auto":
        return
    try:
        bevel_bridge.apply_bevel(obj, props, backend=bevel_backend, monolith=monolith)
    except Exception as exc:
        print(f"[Surreal Architecture] bevel pass skipped: {exc}")


def uv_pack_hint(props) -> str | None:
    """Return workflow hint when trim-sheet UV expects external pack (MioUV / UVPackmaster)."""
    mode = getattr(props, "uv_unwrap_mode", "")
    if mode not in ("TRIM_SHEET", "MODULAR", "ARCHITECTURAL"):
        return None
    if getattr(props, "gb_trim_mode", "NONE") == "NONE":
        return None
    return "trim_sheet_ready: use Level Design → UV Proxy → MioUV Pack → Commit UV"


def apply_pipeline_batch(objects, monolith, *, bevel_backend: str = "BEAVEL") -> int:
    """Run export-time Beavel bake on a selection of objects."""
    count = 0
    for obj in objects:
        props = getattr(obj, "surreal_arch_props", None)
        if not props:
            continue
        run_post_generate(obj, props, monolith, bevel_backend=bevel_backend)
        count += 1
    return count
