"""Dispatch the post-build Unreal Python authoring scripts to the live editor."""
from pathlib import Path
import json

from monolith_mcp_client import call_tool

ROOT = Path(__file__).resolve().parent
SCRIPTS = (
    "author_melodia_persona_foundation.py",
    "compile_melodia_quill_priestess.py",
    "assign_melodia_quill_presentation.py",
)

reports = []
for script_name in SCRIPTS:
    script_path = (ROOT / script_name).as_posix()
    result = call_tool(
        "editor_query",
        {"action": "run_console_command", "command": f'py "{script_path}"'},
    )
    if result.get("isError"):
        raise RuntimeError(f"Failed to dispatch {script_name}: {json.dumps(result)}")
    reports.append({"script": script_name, "dispatch": result})

print(json.dumps({"status": "dispatched", "scripts": reports}, indent=2))
