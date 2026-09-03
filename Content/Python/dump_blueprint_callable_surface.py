#!/usr/bin/env python3
"""Scan Melodia C++ headers for the Blueprint-exposed API surface and write a JSON manifest.

Regeneration source for Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md.

Usage:
    python Content/Python/dump_blueprint_callable_surface.py [--out PATH]

Output (default): Saved/Audit/blueprint_callable_surface.json

Heuristic regex parser (NOT UHT). Tuned to this codebase's formatting.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = PROJECT_ROOT / "Saved" / "Audit" / "blueprint_callable_surface.json"

HEADER_ROOTS = [
    PROJECT_ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration",
    PROJECT_ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore",
]

UFUNCTION_RE = re.compile(
    r"UFUNCTION\s*\(\s*(?P<specs>[^)]*?)\)\s*\n"
    r"(?P<ret>[\w:<>,*&\s]+?)\s+"
    r"(?P<name>\w+)\s*\((?P<params>[^;]*?)\)\s*(?:const\s*)?;",
    re.MULTILINE,
)
UPROPERTY_RE = re.compile(
    r"UPROPERTY\s*\(\s*(?P<specs>[^)]*?)\)\s*\n"
    r"(?P<type>[\w:<>,*&\s]+?)\s+"
    r"(?P<name>\w+)\s*(?:=\s*[^;]*?)?;",
    re.MULTILINE,
)
UENUM_RE = re.compile(
    r"UENUM\s*\(\s*BlueprintType\s*\)\s*\n"
    r"enum\s+class\s+(?P<name>\w+)\s*:\s*\w+\s*\{(?P<body>[^}]*)\}",
    re.MULTILINE,
)
USTRUCT_RE = re.compile(
    r"USTRUCT\s*\(\s*BlueprintType\s*\)\s*\n"
    r"struct\s+(?P<name>\w+)\s*\{(?P<body>.*?)\n\};",
    re.MULTILINE | re.DOTALL,
)
DELEGATE_RE = re.compile(
    r"DECLARE_DYNAMIC_MULTICAST_DELEGATE_(?P<arity>\w+)Params?\(\s*"
    r"(?P<name>\w+)\s*,(?P<params>[^)]*)\)",
    re.MULTILINE,
)


def _clean(s):
    return " ".join(s.split())


def parse_ufunction(m):
    return {
        "name": m.group("name"),
        "return_type": _clean(m.group("ret")),
        "params": _clean(m.group("params")),
        "specifiers": [s.strip() for s in m.group("specs").split(",") if s.strip()],
        "is_static": "static" in m.group("ret"),
    }


def parse_uproperty(m):
    return {
        "name": m.group("name"),
        "type": _clean(m.group("type")),
        "specifiers": [s.strip() for s in m.group("specs").split(",") if s.strip()],
    }


def parse_uenum(m):
    values = []
    for line in m.group("body").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        line = re.sub(r"UMETA\([^)]*\)", "", line).rstrip(",").strip()
        if line:
            values.append(line)
    return {"name": m.group("name"), "values": values}


def parse_ustruct(m):
    return {
        "name": m.group("name"),
        "fields": [parse_uproperty(fm) for fm in UPROPERTY_RE.finditer(m.group("body"))],
    }


def parse_delegate(m):
    return {
        "name": m.group("name"),
        "arity": m.group("arity"),
        "params": _clean(m.group("params")),
    }


def scan_header(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "ufunctions": [parse_ufunction(m) for m in UFUNCTION_RE.finditer(text)],
        "uproperties": [parse_uproperty(m) for m in UPROPERTY_RE.finditer(text)],
        "uenums": [parse_uenum(m) for m in UENUM_RE.finditer(text)],
        "ustructs": [parse_ustruct(m) for m in USTRUCT_RE.finditer(text)],
        "delegates": [parse_delegate(m) for m in DELEGATE_RE.finditer(text)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    headers = []
    for root in HEADER_ROOTS:
        if not root.exists():
            print(f"WARNING: header root not found: {root}", file=sys.stderr)
            continue
        for h in sorted(root.glob("*.h")):
            headers.append(scan_header(h))

    manifest = {
        "generated_by": "dump_blueprint_callable_surface.py",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "header_roots": [str(r.relative_to(PROJECT_ROOT)) for r in HEADER_ROOTS],
        "headers": headers,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(headers)} headers -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())