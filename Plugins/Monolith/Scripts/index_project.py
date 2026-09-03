#!/usr/bin/env python3
"""Index a UE project's C++ source into an existing Monolith EngineSource.db.

Discovers all Source/ directories under the project root (top-level modules
and plugin modules) and indexes them into the same database used for engine
source, enabling cross-references between project and engine symbols.

Usage:
    python index_project.py                          # auto-detect project root
    python index_project.py --project /path/to/MyGame
    python index_project.py --db /path/to/EngineSource.db
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

# Allow importing from sibling package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_indexer.db.schema import init_db
from source_indexer.indexer.pipeline import IndexingPipeline

GAME_FEATURES_DIR = "Plugins/GameFeatures"


def discover_modules(project: Path) -> list[tuple[Path, str, str]]:
    """Find all Source/ dirs under the project."""
    modules: list[tuple[Path, str, str]] = []

    # Top-level Source/ (e.g. LyraGame, LyraEditor, MyGame)
    top_source = project / "Source"
    if top_source.is_dir():
        for child in sorted(top_source.iterdir()):
            if child.is_dir():
                modules.append((child, child.name, "Project"))

    # All plugin Source/ dirs (recursive glob catches nested plugins too)
    plugins_dir = project / "Plugins"
    if plugins_dir.is_dir():
        for source_dir in sorted(plugins_dir.rglob("Source")):
            if source_dir.is_dir():
                plugin_name = source_dir.parent.name
                is_gfp = GAME_FEATURES_DIR in str(source_dir.relative_to(project))
                mod_type = "GameFeature" if is_gfp else "Plugin"
                modules.append((source_dir, plugin_name, mod_type))

    return modules


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    default_project = script_dir.parents[2]  # Two levels up from Scripts/
    default_db = script_dir.parent / "Saved" / "EngineSource.db"

    parser = argparse.ArgumentParser(description="Index project C++ source into EngineSource.db")
    parser.add_argument("--db", type=Path, default=default_db, help="Path to existing EngineSource.db")
    parser.add_argument("--project", type=Path, default=default_project, help="Path to project root")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Error: database not found: {args.db}", file=sys.stderr)
        print("Run engine source indexing first to create the DB.", file=sys.stderr)
        sys.exit(1)

    modules = discover_modules(args.project)
    if not modules:
        print(f"No source directories found under {args.project}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(modules)} module(s) to index under {args.project}")

    conn = sqlite3.connect(str(args.db))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    pipeline = IndexingPipeline(conn)

    # Load existing engine symbols so project->engine cross-references resolve
    print("Loading existing symbol map from DB...")
    pipeline.load_existing_symbols()

    total_files = total_symbols = total_errors = 0
    t0 = time.monotonic()

    for i, (path, name, mod_type) in enumerate(modules, 1):
        print(f"[{i}/{len(modules)}] {name} ({mod_type}) -- {path}")
        stats = pipeline.index_directory(path, module_name=name, module_type=mod_type, finalize=False)
        total_files += stats["files_processed"]
        total_symbols += stats["symbols_extracted"]
        total_errors += stats["errors"]
        print(f"         {stats['files_processed']} files, {stats['symbols_extracted']} symbols, {stats['errors']} errors")

    print(f"\nIndexing done ({time.monotonic() - t0:.1f}s). Finalizing...")
    pipeline._finalize()

    diag = pipeline.diagnostics
    elapsed = time.monotonic() - t0
    print(f"\nDone in {elapsed:.1f}s: {total_files} files, {total_symbols} symbols, {total_errors} errors")
    print(f"  Definitions:          {diag['definitions']}")
    print(f"  Forward declarations: {diag['forward_decls']}")
    print(f"  Inheritance resolved: {diag['inheritance_resolved']}")
    print(f"  Inheritance failed:   {diag['inheritance_failed']}")

    conn.close()


if __name__ == "__main__":
    main()
