"""Configuration for source_indexer."""

import os
import re
from pathlib import Path

DB_DIR = Path(os.environ.get("UNREAL_SOURCE_MCP_DB_DIR", os.path.expanduser("~/.unreal-source-mcp")))
UE_SOURCE_PATH = os.environ.get("UE_SOURCE_PATH", "")
UE_SHADER_PATH = os.environ.get("UE_SHADER_PATH", "")
UE_VERSION = os.environ.get("UE_VERSION", "")


def _detect_version() -> str:
    """Detect UE version from UE_VERSION env var or UE_SOURCE_PATH."""
    if UE_VERSION:
        return UE_VERSION
    m = re.search(r"(\d+\.\d+)", UE_SOURCE_PATH)
    if m:
        return m.group(1)
    return "unknown"


def _engine_root() -> str:
    """Return the Engine/ root prefix for path shortening."""
    if not UE_SOURCE_PATH:
        return ""
    p = Path(UE_SOURCE_PATH)
    if p.name == "Source" and p.parent.name == "Engine":
        return str(p.parent.parent) + os.sep
    return ""


def get_db_path() -> Path:
    """Return the path to the SQLite database, creating the directory if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    version = _detect_version()
    return DB_DIR / f"ue_{version}.db"
