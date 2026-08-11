"""Probe UV edit proxy bake-commit path on live GN zen greybox (v2.73.5)."""

from __future__ import annotations


def probe_zen_uv_proxy_bake(context, monolith):
    """Return list of failure strings for proxy → bake commit workflow."""
    import bpy

    from surreal_arch import uv_workflow

    fails = []
    mesh = bpy.data.meshes.new("ProxyProbeHost")
    obj = bpy.data.objects.new("ProxyProbe_Zen", mesh)
    context.collection.objects.link(obj)
    props = obj.surreal_arch_props
    props.arch_type = "GB_ZEN_ROJI_STEP"
    props.gb_length = 4.0
    props.gb_width = 1.8
    props.gb_trim_mode = "RECESS"
    props.uv_unwrap_mode = "TRIM_SHEET"
    context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.surreal_arch.generate()

    proxy, msg = uv_workflow.create_uv_edit_proxy(context, obj, apply_modifiers=False)
    if proxy is None:
        fails.append(f"create_proxy_failed: {msg}")
        return fails

    ok, commit_msg = uv_workflow.commit_uv_from_proxy(context, obj, proxy)
    if not ok:
        fails.append(f"commit_failed: {commit_msg}")
        return fails
    if not obj.get(uv_workflow.BAKED_TAG):
        fails.append("commit_ok_but_missing_baked_tag")
    if any(m.name.startswith("SurrealArch") for m in obj.modifiers):
        fails.append("gn_modifier_still_present_after_bake_commit")
    if not props.uv_lock_external:
        fails.append("uv_lock_external_not_set")
    if len(obj.data.loops) < 8:
        fails.append(f"baked_mesh_too_small loops={len(obj.data.loops)}")
    return fails
