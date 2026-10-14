# Melodia Studio - headless Blender smoke test (the harness that runs is the harness that ships).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Verifies the 2026-10-04 monolith split end-to-end against a real bpy:
# register() -> 15 registered classes + Scene.melodia_studio -> unregister() -> gone.
# Also reports which melodia_studio copy the live Blender 5.2 profile would load
# (repo Tools/BlenderAddons vs the AppData mirror), so "is the updated build
# installed?" is a fact, not prose.
#
# Run (no other Blender instance running):
#   blender --background --python Tools/BlenderAddons/melodia_studio/tests/blender_smoke.py
#
# Exits non-zero on any failure. Note: Blender background teardown can crash at
# exit after all checks pass (environment addon-prefs shutdown bug) - judge by
# the [SMOKE] lines, not the process exit code alone.

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADDONS_ROOT = HERE.parent.parent          # Tests -> melodia_studio -> Tools/BlenderAddons
REPO = ADDONS_ROOT.parent.parent          # Tools/BlenderAddons -> Tools -> repo root

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[SMOKE] PASS {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"[SMOKE] FAIL {name} -- {detail}")


def _profile_init_py() -> Path:
    return (Path.home() / "AppData" / "Roaming" / "Blender Foundation"
            / "Blender" / "5.2" / "scripts" / "addons" / "melodia_studio" / "__init__.py")


def _version_from(path: Path) -> tuple | None:
    try:
        m = re.search(r'"version"\s*:\s*\(([^)]*)\)', path.read_text(encoding="utf-8", errors="ignore"))
        if not m:
            return None
        return tuple(int(x) for x in re.findall(r"\d+", m.group(1)))
    except Exception:
        return None


def main() -> None:
    import bpy
    import addon_utils  # Blender builtin

    # ---- 1. Profile report: what copy would this Blender load?
    repo_ver = None
    prof_init = _profile_init_py()
    if prof_init.exists():
        prof_ver = _version_from(prof_init)
        print(f"[SMOKE] INFO profile copy present: {prof_init} (version {prof_ver})")
    else:
        print("[SMOKE] INFO no profile copy at AppData - Script Directory step already in effect")

    # ---- 2. Drop any profile-loaded copy; force the repo copy
    try:
        res = addon_utils.check("melodia_studio")
        enabled = res.get("enabled", []) if isinstance(res, dict) else []
        if "melodia_studio" in enabled:
            print("[SMOKE] INFO profile auto-enabled the melodia_studio copy - disabling before repo load")
            addon_utils.disable("melodia_studio")
    except Exception as exc:
        print(f"[SMOKE] WARN profile disable skipped: {exc!r}")
    for name in list(sys.modules):
        if name == "melodia_studio" or name.startswith("melodia_studio."):
            del sys.modules[name]
    if str(ADDONS_ROOT) not in sys.path:
        sys.path.insert(0, str(ADDONS_ROOT))

    import melodia_studio  # noqa: E402  (repo copy - asserted below)

    check("repo_module_loaded",
          ADDONS_ROOT.name in melodia_studio.__file__ and "melodia_studio" in melodia_studio.__file__,
          f"loaded {melodia_studio.__file__} instead of {ADDONS_ROOT}")
    repo_ver = tuple(melodia_studio.bl_info["version"])
    check("version_1_6_0", repo_ver == (1, 6, 0), f"bl_info version {repo_ver}")
    if prof_init.exists() and _version_from(prof_init) != repo_ver:
        print("[SMOKE] NOTE profile copy version differs from repo - Blender loads the profile copy until "
              "the Script Directories step points at Tools/BlenderAddons (or the AppData copy is updated)")

    # ---- 3. Register
    melodia_studio.register()

    # Scene property proves StudioProps is a registered type (PointerProperty
    # binding requires it) - the authoritative props check.
    check("scene_prop", hasattr(bpy.types.Scene, "melodia_studio"), "bpy.types.Scene.melodia_studio missing")

    # Module-level census: every split module must hold a REAL class with the
    # expected bl_idname (the offline 'object' placeholder would fail this).
    props = melodia_studio.properties
    check("prefs_idname", getattr(props.MelodiaStudioPreferences, "bl_idname", None) == "melodia_studio",
          f"got {getattr(props.MelodiaStudioPreferences, 'bl_idname', None)}")
    # StudioProps property definitions are consumed into the RNA type at class
    # creation (_RNAMetaPropGroup) - they are NOT Python class attributes.
    # The authoritative source is the registered type's RNA, via the scene
    # pointer that register() just bound.
    # Live-instance check: the registered property group on the real scene must
    # expose every one of the original monolith's 15 properties, with the
    # original defaults intact (property definitions live on the RNA instance,
    # not on the Python class).
    expected_props = ("midi_file", "midi_filter", "preset", "custom_midi", "dressing_style",
                      "auto_cleanup", "last_report", "last_midi", "show_advanced",
                      "tandem_preset", "tandem_style", "tandem_plan",
                      "dress_instance", "dress_seed", "dress_budget")
    inst = bpy.context.scene.melodia_studio
    missing = [n for n in expected_props if not hasattr(inst, n)]
    check("studio_props_live", not missing, f"missing on live instance: {missing}")
    check("studio_props_defaults",
          inst.dressing_style == "verdant" and inst.dress_seed == 11 and inst.dress_budget == 400,
          f"dressing_style={inst.dressing_style!r} dress_seed={inst.dress_seed!r} dress_budget={inst.dress_budget!r}")
    expected_ops = [
        ("STUDIO_OT_generate_from_midi", "melodia_studio.generate_from_midi"),
        ("STUDIO_OT_frame_terrain", "melodia_studio.frame_terrain"),
        ("STUDIO_OT_write_presets", "melodia_studio.write_presets"),
        ("STUDIO_OT_save_scene", "melodia_studio.save_scene"),
        ("STUDIO_OT_cleanup_scene", "melodia_studio.cleanup_scene"),
        ("STUDIO_OT_setup_script_directory", "melodia_studio.setup_script_directory"),
        ("STUDIO_OT_render_proof", "melodia_studio.render_proof"),
        ("STUDIO_OT_batch_render", "melodia_studio.batch_render"),
        ("STUDIO_OT_open_folder", "melodia_studio.open_folder"),
        ("STUDIO_OT_refresh_midi", "melodia_studio.refresh_midi"),
        ("STUDIO_OT_validate_health", "melodia_studio.validate_health"),
    ]
    for cls_name, bl_id in expected_ops:
        cls = getattr(melodia_studio.operators, cls_name, None)
        # Registered Blender classes carry an _RNAMeta metaclass; the offline
        # fallback is bare 'object'. isinstance(cls, type) accepts both real
        # Python classes and _RNAMeta instances (it is a type subclass).
        check(f"op_class_{cls_name}",
              cls is not None and isinstance(cls, type) and cls.bl_idname == bl_id,
              f"module class missing or wrong bl_idname: {getattr(cls, 'bl_idname', cls)!r}")

    # Panels: bpy.types exposure verified on this build - keep the live check.
    for cls_name, bl_id in (("STUDIO_PT_panel", "STUDIO_PT_panel"),
                            ("STUDIO_PT_management", "STUDIO_PT_management")):
        cls = getattr(bpy.types, cls_name, None)
        check(f"panel_{cls_name}", cls is not None and cls.bl_idname == bl_id,
              f"bpy.types.{cls_name} missing or wrong bl_idname")
    check("panel_category", getattr(bpy.types.STUDIO_PT_panel, "bl_category", "") == "Melodia Studio")
    check("panel_parent", getattr(bpy.types.STUDIO_PT_management, "bl_parent_id", "") == "STUDIO_PT_panel")

    # Operator registration proof: call a side-effect-free registered operator.
    # (An unregistered operator raises on call; a registered one returns a set.)
    try:
        result = bpy.ops.melodia_studio.validate_health()
        # Blender returns its own runtime set type, not a Python frozenset.
        check("op_validate_health_runs", "FINISHED" in result, f"result={result}")
    except Exception as exc:
        check("op_validate_health_runs", False, f"operator call raised: {exc!r}")

    # ---- 4. Unregister -> gone
    melodia_studio.unregister()
    check("scene_prop_removed", not hasattr(bpy.types.Scene, "melodia_studio"))
    check("panel_removed", not hasattr(bpy.types, "STUDIO_PT_panel"))

    # ---- 5. Verdict
    if FAILURES:
        print(f"[SMOKE] FAIL {len(FAILURES)} check(s): " + "; ".join(FAILURES))
        sys.exit(1)
    print("[SMOKE] OK - melodia_studio split registers and unregisters cleanly "
          f"(repo version {repo_ver}, {len(expected_ops) + 4} classes)")


if __name__ == "__main__":
    main()
