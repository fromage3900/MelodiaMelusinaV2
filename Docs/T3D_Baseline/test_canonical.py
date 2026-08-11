#!/usr/bin/env python3
"""Proof that verify_baseline.py's reorder tolerance did not make the gate blind.

verify_baseline.py treats a payload that differs from its baseline ONLY in
exporter object order as clean. That is the right call -- UE reorders sibling
objects on every export, and four materials were reporting false DRIFT with
provably identical content on 2026-08-08 -- but it is also exactly the kind of
loosening that can quietly destroy a gate.

So this asserts both directions: reordering compares equal, and every real
mutation still compares different. Run it after touching canonical().

    python Docs/T3D_Baseline/test_canonical.py

Exit 0 = all assertions hold. Needs no editor; it reads a committed .t3d.
"""
import importlib.util
import os
import re
import sys

_spec = importlib.util.spec_from_file_location(
    "vb", os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_baseline.py"))
vb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vb)

FIXTURE = os.path.join(vb.BASE, "materials", "MF_Gemstone.t3d")


def main():
    base = open(FIXTURE, encoding="utf-8").read()
    lines = base.split("\n")
    results = []

    def check(label, mutated, expect):
        got = vb.reordered_only(base, mutated)
        results.append((got == expect, label, got, expect))

    check("identical input", base, True)

    blocks = re.findall(r"(?ms)^(   Begin Object.*?^   End Object$)", base)
    if len(blocks) >= 2:
        s = base.replace(blocks[0], "@@A@@").replace(blocks[1], "@@B@@")
        s = s.replace("@@A@@", blocks[1]).replace("@@B@@", blocks[0])
        check(f"two of {len(blocks)} sibling blocks swapped", s, True)

    altered, done = [], False
    for l in lines:
        if not done and re.search(r"=-?\d+\.\d+", l):
            altered.append(re.sub(r"=(-?\d+\.\d+)", "=99.125", l, count=1)); done = True
        else:
            altered.append(l)
    check("one float value altered", "\n".join(altered), False)

    dropped, done = [], False
    for l in lines:
        if not done and "=" in l and not l.strip().startswith(("Begin", "End")):
            done = True
            continue
        dropped.append(l)
    check("one property line deleted", "\n".join(dropped), False)

    check("one property line added", base + "\n   NewBogusProperty=1", False)
    check("truncated/unbalanced payload", base.replace("End Object", "", 1), False)

    failed = 0
    for ok, label, got, expect in results:
        print(f"  {'PASS' if ok else '*** FAIL ***'}  {label}: "
              f"reordered_only={got} (expected {expect})")
        failed += 0 if ok else 1

    print(f"\n=== {len(results) - failed}/{len(results)} passed ===")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
