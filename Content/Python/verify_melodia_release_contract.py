"""No-editor release-contract check for the Melodia vertical slice.

This verifies the checked-in project configuration only. It deliberately does
not load assets or start Unreal, so it is safe to run while an editor session
owns ZenForestTest or rendering work.
"""
from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Melodia" / "release_contract.json"


def _read_ini(path: Path) -> dict[str, dict[str, list[str]]]:
    sections: dict[str, dict[str, list[str]]] = {}
    current: dict[str, list[str]] | None = None
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith((";", "#", "/*", "*", "*/")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = sections.setdefault(line[1:-1], {})
            continue
        if current is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        current.setdefault(key.lstrip("+-"), []).append(value)
    return sections


def _has_value(section: dict[str, list[str]], key: str, expected: str) -> bool:
    return expected in section.get(key, [])


def _check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "passed": passed, "detail": detail}


def verify() -> dict[str, object]:
    engine = _read_ini(PROJECT_ROOT / "Config" / "DefaultEngine.ini")
    game = _read_ini(PROJECT_ROOT / "Config" / "DefaultGame.ini")
    project = json.loads((PROJECT_ROOT / "BS_GodFile.uproject").read_text(encoding="utf-8"))

    renderer = engine.get("/Script/Engine.RendererSettings", {})
    windows = engine.get("/Script/WindowsTargetPlatform.WindowsTargetSettings", {})
    game_maps = game.get("/Script/EngineSettings.GameMapsSettings", {})
    default_map = game_maps.get("GameDefaultMap", [""])[-1]
    default_mode = game.get("/Script/EngineSettings.GameModeSettings", {}).get(
        "GlobalDefaultGameMode", [""]
    )[-1]
    plugin_enabled = any(
        plugin.get("Name") == "MelodiaCore" and plugin.get("Enabled") is True
        for plugin in project.get("Plugins", [])
    )

    required = [
        _check("melodia_plugin", plugin_enabled, "MelodiaCore is enabled in BS_GodFile.uproject."),
        _check(
            "windows_dx12",
            _has_value(windows, "DefaultGraphicsRHI", "DefaultGraphicsRHI_DX12"),
            "Windows uses DX12, required by the desktop Lumen showcase.",
        ),
        _check(
            "windows_sm6",
            _has_value(windows, "D3D12TargetedShaderFormats", "PCD3D_SM6"),
            "Windows targets Shader Model 6.",
        ),
        _check(
            "lumen_gi",
            _has_value(renderer, "r.DynamicGlobalIlluminationMethod", "1"),
            "Project-level dynamic global illumination is Lumen.",
        ),
        _check(
            "lumen_reflections",
            _has_value(renderer, "r.ReflectionMethod", "1"),
            "Project-level reflections use Lumen.",
        ),
        _check(
            "virtual_shadow_maps",
            _has_value(renderer, "r.Shadow.Virtual.Enable", "1"),
            "Virtual Shadow Maps are enabled.",
        ),
        _check(
            "distance_fields",
            _has_value(renderer, "r.GenerateMeshDistanceFields", "True"),
            "Mesh distance fields are enabled for Lumen's software path.",
        ),
        _check(
            "zen_smoke_scripts",
            (PROJECT_ROOT / "Content/Python/setup_melodia_zen_smoke.py").is_file()
            and (PROJECT_ROOT / "Content/Python/verify_melodia_zen_smoke.py").is_file(),
            "ZenForestTest setup and verification scripts are present.",
        ),
    ]

    mobile_widget = PROJECT_ROOT / "Content/Melodia/UI/WBP_Battle_Mobile.uasset"
    warnings = [
        {
            "name": "pc_startup_contract",
            "detail": (
                "Global startup must select the ZenForestTest Melodia GameMode, not the mobile fallback "
                f"({default_map}, {default_mode}). Set the package map explicitly "
                "when the Windows showcase build is frozen."
            ),
            "active": (
                "ZenForestTest" not in default_map
                or not default_mode.endswith("MelodiaGameMode")
                or default_mode.endswith("MelodiaMobileGameMode")
            ),
        },
        {
            "name": "mobile_ui_proof",
            "detail": "WBP_Battle_Mobile is not present; mobile remains unproven for release.",
            "active": not mobile_widget.is_file(),
        },
    ]

    report = {
        "ok": all(item["passed"] for item in required),
        "release_target": "Windows desktop vertical slice",
        "checks": required,
        "warnings": warnings,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)
