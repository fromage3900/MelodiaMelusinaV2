"""Run full Ornament Kitbash monetization pipeline inside the open UE editor.

Output Log (one line):
  py Content/Python/run_ornament_kitbash_in_editor.py

Or:
  import run_ornament_kitbash_in_editor as r; r.main()
"""
from __future__ import annotations

import traceback

import unreal


def _step(label: str, fn) -> bool:
    unreal.log(f"[OrnamentKitbash] === {label} ===")
    try:
        result = fn()
        ok = result is None or result is True or (isinstance(result, int) and result == 0)
        unreal.log(f"[OrnamentKitbash] {label}: {'OK' if ok else f'WARN result={result}'}")
        return bool(ok)
    except Exception:
        unreal.log_error(f"[OrnamentKitbash] {label} FAILED:\n{traceback.format_exc()}")
        return False


def main() -> int:
    unreal.log("[OrnamentKitbash] Starting in-editor monetization pipeline...")

    # Meshes already exist on disk (15 SM_Orn_*) — generate is idempotent / skip-safe
    import generate_ornamental_meshes as gen
    import kitbash_prep_meshes as prep
    import build_pcg_ornamental as pcg
    import setup_ornament_demo_level as demo

    steps = [
        ("1/4 Generate ornamental meshes", gen.main if hasattr(gen, "main") else lambda: gen.run()),
        ("2/4 LOD + collision + FBX export", prep.main),
        ("3/4 PCG ornamental graphs", pcg.main),
        ("4/4 Demo showcase level", demo.main),
    ]

    # Prefer generate_all / --all style if present
    if hasattr(gen, "generate_all"):
        steps[0] = ("1/4 Generate ornamental meshes", gen.generate_all)
    elif hasattr(gen, "main"):
        steps[0] = ("1/4 Generate ornamental meshes", gen.main)

    failed = []
    for label, fn in steps:
        if not _step(label, fn):
            failed.append(label)

    if failed:
        unreal.log_error(f"[OrnamentKitbash] DONE WITH FAILURES: {failed}")
        unreal.log_error("[OrnamentKitbash] Check Saved/Audit/kitbash_export_manifest.json")
        return 1

    unreal.log("[OrnamentKitbash] ALL STEPS OK")
    unreal.log("[OrnamentKitbash] Next: python Content/Python/package_ornament_kitbash.py --zip")
    unreal.log("[OrnamentKitbash] Then capture 6 screenshots in L_OrnamentKitbashShowcase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
