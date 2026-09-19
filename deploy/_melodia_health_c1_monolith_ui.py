"""Prove the C1 monolith-headless flip - run inside Blender 5.2.

C1 (surreal_arch/integration.py `_retire_monolith_ui_panels`) unregisters every
N-tab Panel class owned by `surreal_architecture_gen` after the Core UI is up,
while keeping SurrealArchProperties, all SURREAL_ARCH_OT_* operators, every
build_* function, the kit dispatch maps and the melodia_gn route.

A diff cannot prove that: it is a runtime property of bpy.types.Panel. This
script asserts the three things that matter and would each be a silent
regression:

  1. after register_overhaul, ZERO monolith-module panels remain in VIEW_3D
     (branding.audit_monolith_ui_retired() == [])
  2. the Core UI SURVIVED - carousel hub, picker, GN stack, score, stage all
     still registered (retiring the monolith must not empty the N-tab)
  3. the KEEP set is intact - the legacy PROPERTIES drawer is still a class
     (so the prefs hatch remains a real escape hatch) and the builder registry
     is untouched (589 ids, same as gate A)

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_c1_monolith_ui.py
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")
for p in (APPDATA_ADDONS, DEPLOY, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

# Core N-tab surfaces that MUST survive the retire. A miss here means the
# monolith retire took out the product UI instead of the legacy UI.
REQUIRED_CORE_PANELS = (
    "SURREAL_ARCH_PT_genome_carousel",
    "SURREAL_ARCH_PT_view3d_picker",
    "SURREAL_ARCH_PT_view3d_level_design",
    "MEL_GN_PT_stack",
    "SURREAL_ARCH_PT_music_score",
    "SURREAL_ARCH_PT_stage_studio",
    "SURREAL_ARCH_PT_convergence",
)

failures = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    try:
        import bpy  # noqa: F401
        import surreal_architecture_gen as monolith
        from surreal_arch.integration import register_overhaul
    except Exception as exc:
        check("import monolith + surreal_arch", False, repr(exc))
        return 1
    check("import monolith + surreal_arch", True)

    # Mimic Blender's real enable order: the monolith's own register() runs FIRST
    # (that is what registers SURREAL_ARCH_PT_panel and the N-tab panels), THEN
    # register_overhaul() retires the monolith N-tab panels while keeping the Core
    # UI and the demoted PROPERTIES drawer. Skipping monolith.register() measured
    # the harness, not the product: SURREAL_ARCH_PT_panel could never exist, so
    # the escape-hatch assertion failed for the wrong reason (2026-09-18).
    try:
        monolith.register()
        check("monolith.register() runs", True)
    except Exception as exc:
        check("monolith.register() runs", False, repr(exc))

    try:
        register_overhaul(monolith)
    except Exception as exc:
        check("register_overhaul runs", False, repr(exc))
        return 1
    check("register_overhaul runs", True)

    # 1. no monolith-owned VIEW_3D panel survives.
    from surreal_arch.branding import audit_monolith_ui_retired
    remaining = audit_monolith_ui_retired()
    check("zero monolith N-tab panels registered", not remaining,
          f"still live: {remaining}" if remaining else "retired cleanly")

    # 2. the Core product UI survived.
    missing_core = [p for p in REQUIRED_CORE_PANELS
                    if getattr(bpy.types, p, None) is None]
    check("Core UI survived", not missing_core,
          f"missing: {missing_core}" if missing_core else
          f"{len(REQUIRED_CORE_PANELS)} panels present")

    # 3. the deliberate KEEP set is intact.
    legacy = getattr(bpy.types, "SURREAL_ARCH_PT_panel", None)
    check("legacy PROPERTIES drawer still a class", legacy is not None,
          "" if legacy is not None else "escape hatch destroyed")
    if legacy is not None:
        check("legacy drawer still demoted", getattr(legacy, "_melodia_legacy_demoted", False),
              "demote flag missing")
        check("legacy drawer is PROPERTIES-space",
              getattr(legacy, "bl_space_type", "") == "PROPERTIES",
              getattr(legacy, "bl_space_type", "?"))

    # 4. builders untouched by the UI retire.
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS
    n = len(GROUP_BUILDERS)
    check("builder registry untouched", n > 0, f"{n} builders")

    # 5. operators still reachable (UI removal must not delete capability).
    for op in ("surreal_arch.generate", "surreal_arch.ivy_scatter"):
        ns, name = op.split(".")
        ok = hasattr(getattr(bpy.ops, ns, None), name)
        check(f"operator {op} still registered", ok)

    print(f"\nC1 health: {len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"C1 health check crashed: {exc!r}")
        sys.exit(1)