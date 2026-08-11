"""Integrate /Game/Textures compositing library + fix dead refs on portfolio masters.

Editor (Output Log):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/integrate_compositing_textures.py"

Shell (headless):
  python Content/Python/integrate_compositing_textures.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "compositing_integration.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
SDF_TEX_ROOT = "/Game/EnvSandbox/Materials/SDF/Textures"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _build_texture_rewire_map() -> dict[str, str]:
    """Map _PROJECT texture paths to portfolio SDF/Textures when stem matches."""
    import unreal

    mapping: dict[str, str] = {}
    project_root = f"{SDF_TEX_ROOT}"
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/_PROJECT/04_Materials/Textures"):
        return mapping
    for path in unreal.EditorAssetLibrary.list_assets(
        "/Game/_PROJECT/04_Materials/Textures", recursive=True, include_folder=False
    ):
        old_base = path.split(".", 1)[0]
        stem = old_base.rsplit("/", 1)[-1]
        for sub in ("Marble", "Perlin", "Voronoi", "Noise"):
            candidate = f"{project_root}/{sub}/{stem}.{stem}"
            if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                mapping[old_base] = candidate.split(".", 1)[0]
                break
    return mapping


def _rewire_textures(report: dict) -> int:
    import unreal
    import rewire_portfolio_texture_refs as rptr

    extra = _build_texture_rewire_map()
    merged = {**rptr.TEXTURE_REPLACEMENTS}
    for k, v in extra.items():
        merged[k] = v
    rptr.TEXTURE_REPLACEMENTS = merged

    before = report.get("textures_rewired", 0)
    rptr.main()
    rewire_report = json.loads((PROJECT_ROOT / "Saved" / "Audit" / "portfolio_texture_rewire.json").read_text())
    report["texture_rewire"] = rewire_report
    return rewire_report.get("textures_rewired", 0) - before


def _wire_masters_and_instances(report: dict) -> None:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as catalog

    master_paths = [
        f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal",
        f"{MATERIALS_ROOT}/Masters/M_Master_SDF_Toon.M_Master_SDF_Toon",
        f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Unified.M_Master_Toon_Unified",
    ]
    master_wired: dict[str, dict] = {}
    for mp in master_paths:
        if not unreal.EditorAssetLibrary.does_asset_exist(mp.split(".", 1)[0]):
            continue
        mat = unreal.load_asset(mp)
        if not mat:
            continue
        wired = catalog.apply_master_defaults(mat, mp.split(".", 1)[0], force=True)
        lib.save_package(mat)
        master_wired[mp] = wired

    import setup_universal_instances as inst

    results = inst.build_instances()
    report["instances_refreshed"] = len(results)
    report["master_texture_defaults"] = master_wired


def _fix_dead_links(report: dict) -> None:
    import audit_dead_material_nodes as dead

    dead.main()
    dead_before = REPORT.parent / "dead_material_nodes.json"
    if dead_before.exists():
        report["dead_nodes"] = json.loads(dead_before.read_text())


def _run_in_ue() -> int:
    import unreal

    unreal.log("=== COMPOSITING INTEGRATION ===")
    report: dict = {"timestamp": datetime.now(timezone.utc).isoformat(), "steps": []}

    def step(name: str, fn) -> None:
        unreal.log(f"[Compositing] >>> {name}")
        try:
            fn()
            report["steps"].append({"step": name, "ok": True})
        except Exception as exc:
            report["steps"].append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[Compositing] FAILED {name}: {exc}")

    step("texture rewire", lambda: _rewire_textures(report))
    step("master + instance texture defaults", lambda: _wire_masters_and_instances(report))
    step("dead node audit (safe, no recompile)", lambda: __import__("audit_dead_material_nodes").main())

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Compositing] report -> {REPORT}")
    ok = all(s["ok"] for s in report["steps"])
    return 0 if ok else 1


def main() -> int:
    if not _in_ue():
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        # Port SDFs + restore textures on disk first (no editor)
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/port_sdf_expansion.py")], check=False)
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/restore_portfolio_textures.py")], check=False)
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/portfolio_texture_catalog.py")], check=False)
        # Never binary-patch texture uassets (length changes corrupt packages Ã¢â€ â€™ editor crash).
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/restore_portfolio_textures.py")], check=False)
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/restore_portfolio_masters.py")], check=False)
        log = PROJECT_ROOT / "Saved" / "Logs" / "compositing_integration.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/integrate_compositing_textures.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            f"-log={log}",
        ]
        print(f"Compositing integration -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    return _run_in_ue()


if __name__ == "__main__":
    raise SystemExit(main())
