"""Sakura PCG â€” thin style wrapper on universal portfolio graphs.

  py Content/Python/setup_pcg_sakura.py
  py Content/Python/setup_pcg_sakura.py --rebuild
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std
import pcg_sakura_standards as sakura_std

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sakura_pcg_build.json"


def build_all(*, rebuild: bool = False, spawn: bool = True, **_kwargs) -> dict:
    if unreal is None:
        raise RuntimeError("setup_pcg_sakura.py must run inside Unreal Editor")

    import setup_pcg_universal as uni
    import setup_pcg_greybox as grey

    if rebuild:
        uni.build_all(force=True)

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "style": "Sakura",
        "wrapper": "setup_pcg_greybox.showcase",
        "graphs": {
            "foliage": std.GRAPH_FOLIAGE,
            "rock": std.GRAPH_ROCK,
        },
        "kit": sakura_std.COLLECTION_PATH,
        "level_spawn": {},
        "gates": {},
    }

    if spawn:
        report["level_spawn"] = grey.apply_greybox_pcg(
            sakura_std.LEVEL,
            preset="showcase",
            generate=True,
            grass_mi=std.MI_SAKURA_GRASS,
        )
        # Relabel volume for Sakura convention
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in eas.get_all_level_actors():
            if actor.get_actor_label() == std.ACTOR_GROUND_COVER:
                actor.set_actor_label(std.ACTOR_SAKURA_VOLUME)

    lo, hi = std.ISM_BAND_SAKURA
    ism = report.get("level_spawn", {}).get("ism_foliage", 0)
    report["gates"] = {
        "graph_exists": unreal.EditorAssetLibrary.does_asset_exist(std.GRAPH_FOLIAGE),
        "ism_valid": report.get("level_spawn", {}).get("passed", False),
    }
    report["passed"] = report["gates"]["graph_exists"] and (
        report["gates"]["ism_valid"] or not spawn
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SakuraPCG] wrapper passed={report['passed']} -> {REPORT_PATH}")
    return report


def main() -> int:
    rebuild = "--rebuild" in sys.argv
    spawn = "--no-spawn" not in sys.argv
    if unreal is None:
        import subprocess
        ue = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
        if not ue.exists():
            return 1
        script = (PROJECT_ROOT / "Content/Python/setup_pcg_sakura.py").as_posix()
        forwarded = []
        if rebuild:
            forwarded.append("--rebuild")
        if not spawn:
            forwarded.append("--no-spawn")
        if forwarded:
            script = script + " " + " ".join(forwarded)
        cmd = [
            str(ue), str(PROJECT_ROOT / "BS_GodFile.uproject"),
            f"-ExecutePythonScript={script}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode
    report = build_all(rebuild=rebuild, spawn=spawn)
    print(f"SAKURA_PCG passed={report['passed']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

