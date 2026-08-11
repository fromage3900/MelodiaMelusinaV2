"""Standalone indexer for Monolith plugin. Usage: python -m source_indexer --source PATH --db PATH [--shaders PATH] [--clean]"""
import argparse
import sqlite3
import sys
from pathlib import Path

from .db.schema import init_db
from .indexer.pipeline import IndexingPipeline


def main():
    parser = argparse.ArgumentParser(description="Index Unreal Engine C++ source into SQLite")
    parser.add_argument("--source", required=True, help="UE Engine/Source path")
    parser.add_argument("--db", required=True, help="Output SQLite DB path")
    parser.add_argument("--shaders", default="", help="UE Shaders path")
    parser.add_argument("--clean", action="store_true", help="Delete existing DB before indexing")
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.clean and db_path.exists():
        db_path.unlink()
        print(f"Deleted existing database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    pipeline = IndexingPipeline(conn)
    shader_path = Path(args.shaders) if args.shaders else None

    def on_progress(name, idx, total, files, syms):
        print(f"[{idx}/{total}] {name} ({files} files, {syms} symbols)", flush=True)

    stats = pipeline.index_engine(Path(args.source), shader_path=shader_path, on_progress=on_progress)
    print(f"Done: {stats['files_processed']} files, {stats['symbols_extracted']} symbols, {stats['errors']} errors")

    diag = pipeline.diagnostics
    print(f"\nDiagnostics:")
    print(f"  Class/struct definitions: {diag['definitions']}")
    print(f"  Forward declarations:     {diag['forward_decls']}")
    print(f"  With base classes:        {diag['with_base_classes']}")
    print(f"  Inheritance resolved:     {diag['inheritance_resolved']}")
    print(f"  Inheritance failed:       {diag['inheritance_failed']}")

    conn.close()


if __name__ == "__main__":
    main()
