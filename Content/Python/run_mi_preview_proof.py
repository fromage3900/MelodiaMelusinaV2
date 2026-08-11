"""FlowersLots proof capture — single MI loop validation entry point.

Run in-editor after shaders are ready:
  py Content/Python/run_mi_preview_proof.py

Equivalent to:
  py Content/Python/run_mi_preview_mrq.py --proof
"""
from __future__ import annotations

import json
import sys

import run_mi_preview_mrq as mrq


def main() -> int:
    result = mrq.run_batch(only="MI_ZenTrim_FlowersLots", prepare=True)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
