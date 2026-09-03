"""Command-line validation for Melodia Studio/GMM manifests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .manifest import validate_manifest


def validate_file(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return validate_manifest(manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Melodia project manifest")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        report = validate_file(args.manifest)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)], "warnings": []}, indent=2))
        return 2

    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
