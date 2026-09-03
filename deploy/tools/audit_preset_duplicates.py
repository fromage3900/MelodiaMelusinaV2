"""Audit preset operators for duplicate arch_type + identical props (v2.72.2)."""

from __future__ import annotations

import ast
import os
import re
import sys

DEPLOY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONOLITH = os.path.join(DEPLOY, "surreal_architecture_gen.py")

if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)


def _extract_preset_ops(source: str):
    """Parse _make_preset_op blocks with dict(arch_type=...) params."""
    pattern = re.compile(
        r'SURREAL_ARCH_OT_(\w+)\s*=\s*_make_preset_op\(\s*'
        r'"[^"]+",\s*"([^"]+)",\s*"([^"]*)",\s*'
        r'(dict\([^)]*(?:\([^)]*\)[^)]*)*\))',
        re.DOTALL,
    )
    alias_pattern = re.compile(
        r'SURREAL_ARCH_OT_(\w+)\s*=\s*_make_preset_alias_op\(\s*'
        r'"[^"]+",\s*"([^"]+)",\s*"([^"]*)",\s*"([^"]+)"',
    )
    ops = {}
    for m in pattern.finditer(source):
        op_id = m.group(2)
        try:
            params = ast.literal_eval(m.group(4))
        except (SyntaxError, ValueError):
            continue
        if isinstance(params, dict) and "arch_type" in params:
            ops[op_id] = params
    for m in alias_pattern.finditer(source):
        op_id = m.group(2)
        ops[op_id] = {"_alias": m.group(4)}
    return ops


def audit_preset_duplicates(monolith_path: str | None = None):
    path = monolith_path or MONOLITH
    with open(path, encoding="utf-8") as f:
        source = f.read()
    ops = _extract_preset_ops(source)
    try:
        from surreal_arch.preset_catalog import ALLOWED_DUPLICATE_ARCH_TYPES
    except ImportError:
        ALLOWED_DUPLICATE_ARCH_TYPES = {}

    by_arch = {}
    for op_id, params in ops.items():
        if "_alias" in params:
            continue
        at = params.get("arch_type")
        if not at:
            continue
        key = (at, tuple(sorted((k, repr(v)) for k, v in params.items() if k != "arch_type")))
        by_arch.setdefault(key, []).append(op_id)

    failures = []
    for (_at, _sig), op_ids in by_arch.items():
        if len(op_ids) < 2:
            continue
        allowed = ALLOWED_DUPLICATE_ARCH_TYPES.get(_at, frozenset())
        if allowed and all(any(a in op for a in allowed) for op in op_ids):
            continue
        failures.append(f"duplicate preset ops for {_at}: {op_ids}")

    if "surreal_arch.preset_greybox_tower" not in source:
        failures.append("missing surreal_arch.preset_greybox_tower operator")

    return failures


def main():
    failures = audit_preset_duplicates()
    if failures:
        print("PRESET AUDIT FAIL:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("PRESET AUDIT OK")


if __name__ == "__main__":
    main()
