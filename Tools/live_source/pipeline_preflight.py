"""Read-only readiness report for the Melusina live tracking bridge.

This command joins the existing VRM, capture inbox, AIRI, and UE checks. It
does not enable plugins, import assets, start capture, or write the session
ledger. Use ``--json-out`` when a reviewable report is needed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import preflight


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASK_ROOT = Path.home() / "Documents" / "Codex" / "2026-09-29" / "files-pasted-by-the-user-goal"
DEFAULT_VRM = DEFAULT_TASK_ROOT / "outputs" / "Melusina_AIRI" / "Melusina_AIRI.vrm"
DEFAULT_ROUNDTRIP = DEFAULT_TASK_ROOT / "outputs" / "Melusina_AIRI" / "roundtrip_report.json"
DEFAULT_AIRI_SDK = DEFAULT_TASK_ROOT / "work" / "airi-sdk"


def _file_status(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else 0,
    }


def _first_existing(paths: list[Path]) -> str | None:
    for path in paths:
        if path.is_file():
            return str(path)
    return None


def _inbox_status(path: Path, pattern) -> dict[str, Any]:
    files = sorted(path.glob("*.fbx")) if path.is_dir() else []
    accepted = [p.name for p in files if pattern.match(p.name)]
    rejected = [p.name for p in files if not pattern.match(p.name)]
    return {
        "path": str(path),
        "exists": path.is_dir(),
        "fbx_count": len(files),
        "accepted_count": len(accepted),
        "accepted_samples": accepted[:5],
        "rejected_samples": rejected[:5],
    }


def _tracked_in_git(repo: Path, relative_path: str) -> bool:
    if not (repo / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{relative_path}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _uproject_plugins(path: Path) -> dict[str, bool]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(item.get("Name")): bool(item.get("Enabled"))
        for item in data.get("Plugins", [])
        if item.get("Name")
    }


def _gate(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def build_report(
    *,
    project_root: Path = PROJECT_ROOT,
    task_root: Path = DEFAULT_TASK_ROOT,
    vrm_path: Path = DEFAULT_VRM,
    airi_sdk: Path = DEFAULT_AIRI_SDK,
) -> dict[str, Any]:
    roundtrip_path = vrm_path.parent / "roundtrip_report.json"
    if not roundtrip_path.exists():
        roundtrip_path = DEFAULT_ROUNDTRIP

    roundtrip: dict[str, Any] = {}
    if roundtrip_path.is_file():
        try:
            roundtrip = json.loads(roundtrip_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            roundtrip = {}

    uproject = project_root / "BS_GodFile.uproject"
    plugins = _uproject_plugins(uproject)
    smartsuit = project_root / "Plugins" / "Smartsuit" / "Smartsuit.uplugin"
    rokoko_inbox = project_root / "Imports" / "Mocap" / "Rokoko" / "Inbox"
    cascadeur_inbox = project_root / "Imports" / "Animations" / "Cascadeur" / "Inbox"

    cascadeur_exe = Path(r"C:\Program Files\Cascadeur\cascadeur.exe")
    airi_exe = Path.home() / "AppData" / "Local" / "Programs" / "airi" / "airi.exe"
    obsbot_exe = _first_existing([
        Path(r"C:\Program Files\OBSBOT Center\OBSBOT Center.exe"),
        Path(r"C:\Program Files\OBSBOT Center\bin\OBSBOT_Center.exe"),
        Path(r"C:\Program Files\OBSBOT Center\bin\OBSBOT_Main.exe"),
        Path(r"C:\Program Files (x86)\OBSBOT Center\OBSBOT Center.exe"),
    ])
    rokoko_exe = _first_existing([
        Path(r"C:\Program Files (x86)\Rokoko Electronics ApS\Rokoko Studio\Rokoko Studio.exe"),
        Path(r"C:\Program Files\Rokoko Electronics ApS\Rokoko Studio\Rokoko Studio.exe"),
    ])

    media_pipe_relative = "packages/model-driver-mediapipe"
    media_pipe_dir = airi_sdk / media_pipe_relative
    airi_source = {
        "sdk_root": str(airi_sdk),
        "sdk_on_disk": airi_sdk.is_dir(),
        "mediapipe_package_on_disk": media_pipe_dir.is_dir(),
        "mediapipe_package_tracked": _tracked_in_git(airi_sdk, media_pipe_relative),
        "desktop_app": _file_status(airi_exe),
    }

    rokoko_status = _inbox_status(rokoko_inbox, preflight.VERB_NAME)
    cascadeur_status = _inbox_status(cascadeur_inbox, preflight.CAS_NAME)
    avatar_status = _file_status(vrm_path)
    avatar_status["roundtrip_report"] = _file_status(roundtrip_path)
    avatar_status["humanoid_bone_count"] = roundtrip.get("humanoid_bone_count")
    avatar_status["mesh_count"] = len(roundtrip.get("meshes", []))
    avatar_status["expression_preset_count"] = len(roundtrip.get("expression_preset_bind_counts", {}))

    live_link_names = ("LiveLink", "LiveLinkHub", "LiveLinkControlRig")
    live_link_enabled = {name: plugins.get(name, False) for name in live_link_names}
    ue_status = {
        "uproject": _file_status(uproject),
        "smartsuit_plugin": _file_status(smartsuit),
        "smartsuit_engine_version": "5.8.0",
        "project_plugins": {
            "VRM4U": plugins.get("VRM4U", False),
            "Smartsuit": plugins.get("Smartsuit", False),
            **live_link_enabled,
        },
        "live_link_project_enabled": all(live_link_enabled.values()),
    }

    gates = [
        _gate("Melusina AIRI VRM", "READY" if avatar_status["exists"] else "BLOCKED", "VRM file is present" if avatar_status["exists"] else "VRM file is missing"),
        _gate("VRM roundtrip", "READY" if avatar_status["roundtrip_report"]["exists"] else "UNVERIFIED", "roundtrip report is present" if avatar_status["roundtrip_report"]["exists"] else "roundtrip report is missing"),
        _gate("Rokoko inbox", "READY" if rokoko_status["accepted_count"] else "BLOCKED", f"{rokoko_status['accepted_count']} accepted FBX source(s)"),
        _gate("Cascadeur inbox", "READY" if cascadeur_status["accepted_count"] else "BLOCKED", f"{cascadeur_status['accepted_count']} accepted FBX source(s)"),
        _gate("Cascadeur executable", "READY" if cascadeur_exe.is_file() else "UNVERIFIED", str(cascadeur_exe)),
        _gate("OBSBOT Center", "READY" if obsbot_exe else "UNVERIFIED", obsbot_exe or "OBSBOT Center executable not found"),
        _gate("Rokoko Studio", "READY" if rokoko_exe else "UNVERIFIED", rokoko_exe or "Rokoko Studio executable not found"),
        _gate("AIRI desktop", "READY" if airi_source["desktop_app"]["exists"] else "UNVERIFIED", "installed executable is present" if airi_source["desktop_app"]["exists"] else "AIRI executable not found"),
        _gate("AIRI MediaPipe source", "READY" if airi_source["mediapipe_package_on_disk"] else "UNVERIFIED", "package source is on disk" if airi_source["mediapipe_package_on_disk"] else "package is tracked in git but absent from this sparse checkout"),
        _gate("UE Rokoko plugin", "READY" if smartsuit.is_file() else "BLOCKED", "Smartsuit plugin is on disk" if smartsuit.is_file() else "Smartsuit plugin is missing"),
        _gate("UE Live Link project wiring", "READY" if ue_status["live_link_project_enabled"] else "BLOCKED", "all required Live Link plugins are enabled" if ue_status["live_link_project_enabled"] else "project config does not enable the required Live Link plugins"),
    ]

    return {
        "schema": "melodia.live_tracking/v1",
        "project_root": str(project_root),
        "task_root": str(task_root),
        "avatar": avatar_status,
        "sources": {
            "rokoko": rokoko_status,
            "cascadeur": cascadeur_status,
        },
        "capture_tools": {
            "cascadeur": str(cascadeur_exe),
            "obsbot_center": obsbot_exe,
            "rokoko_studio": rokoko_exe,
        },
        "airi": airi_source,
        "ue": ue_status,
        "gates": gates,
        "mutations_performed": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--task-root", type=Path, default=DEFAULT_TASK_ROOT)
    parser.add_argument("--vrm", type=Path, default=DEFAULT_VRM)
    parser.add_argument("--airi-sdk", type=Path, default=DEFAULT_AIRI_SDK)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="return 1 when a gate is BLOCKED")
    args = parser.parse_args()

    report = build_report(
        project_root=args.project_root,
        task_root=args.task_root,
        vrm_path=args.vrm,
        airi_sdk=args.airi_sdk,
    )
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload + "\n", encoding="utf-8")

    return 1 if args.strict and any(g["status"] == "BLOCKED" for g in report["gates"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
