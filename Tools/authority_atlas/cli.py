"""Command-line entry point for the offline authority atlas."""

from __future__ import annotations

import argparse
from pathlib import Path

from .atlas import ROOT, build_atlas, write_outputs


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=ROOT)
    result.add_argument("--json", type=Path)
    result.add_argument("--report", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    atlas = build_atlas(args.root)
    validation = atlas["validation"]
    if not validation["classifications_valid"] or validation["core_domains_without_owner"] or not validation["all_nodes_have_required_fields"]:
        raise SystemExit(f"atlas validation failed: {validation}")
    json_path, report_path = write_outputs(atlas, args.root, args.json, args.report)
    print(f"nodes={validation['node_count']}")
    print(json_path.as_posix())
    print(report_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
