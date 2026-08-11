"""Direct Cascadeur animation import for the real Melusina skeleton.

Lane A only: Cascadeur exports must use the Melusina deform skeleton. This
script imports animation data without mesh/material duplication and writes
clips to the Cascadeur folder. It deliberately does not retarget.

Run in the Unreal Editor Python console:
    import import_cascadeur_anim as c
    print(c.import_inbox())

Drop FBX files into Imports/Animations/Cascadeur/Inbox first.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import unreal


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INBOX = PROJECT_ROOT / "Imports" / "Animations" / "Cascadeur" / "Inbox"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Melodia" / "cascadeur_import_report.json"
TARGET_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
DESTINATION = "/Game/Melodia/Characters/Melusina/Animations/Cascadeur"
PREFIX = "A_Cascadeur_"


def _stem(path: Path) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_")
    return value or "Take"


def _asset_path(path: str) -> str:
    return path.split(".", 1)[0]


def list_inbox() -> list[Path]:
    INBOX.mkdir(parents=True, exist_ok=True)
    return sorted(INBOX.glob("*.fbx"))


def import_animation(fbx_path: Path, destination_name: str) -> list[str]:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx_path))
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("skeleton", unreal.load_asset(TARGET_SKELETON))
    options.set_editor_property("skeletal_mesh", unreal.load_asset(TARGET_MESH))
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths") or [])


def _sequence_report(path: str) -> dict:
    sequence = unreal.EditorAssetLibrary.load_asset(_asset_path(path))
    if not sequence:
        return {"asset": path, "loaded": False}
    return {
        "asset": _asset_path(path),
        "loaded": True,
        "skeleton": str(sequence.get_editor_property("skeleton")) if sequence.get_editor_property("skeleton") else "",
        "duration": float(sequence.get_editor_property("sequence_length")),
        "rate_scale": float(sequence.get_editor_property("rate_scale")),
        "loop": bool(sequence.get_editor_property("loop")),
    }


def import_inbox() -> dict:
    report = {
        "lane": "A",
        "inbox": str(INBOX),
        "destination": DESTINATION,
        "target_skeleton": TARGET_SKELETON,
        "files": [],
        "warnings": [],
    }
    for fbx_path in list_inbox():
        destination_name = PREFIX + _stem(fbx_path)
        try:
            imported = import_animation(fbx_path, destination_name)
            report["files"].append({
                "source": str(fbx_path),
                "destination_name": destination_name,
                "imported": imported,
                "assets": [_sequence_report(path) for path in imported],
            })
        except Exception as exc:
            report["warnings"].append({"source": str(fbx_path), "error": str(exc)})

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
