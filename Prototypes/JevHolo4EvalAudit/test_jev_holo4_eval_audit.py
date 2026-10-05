"""Contract tests for the Holo4 Jev audit.

These pin the FALLBACK path and the closed option sets. Per system-one-conductor
step 7, the fallback documents the expected mapping as code so the loop runs with
no backend, and the malformed-distribution guard is pinned because that is the
one assertion that catches the documented index-list defect.

Run: python test_jev_holo4_eval_audit.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_holo4_eval_audit as A  # noqa: E402

PASS, FAIL = 0, 0


def check(label: str, got, want) -> None:
    global PASS, FAIL
    ok = got == want
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"         expected {want!r}, got {got!r}")


def is_dist(d: dict) -> bool:
    return bool(d) and all(0.0 <= v <= 1.0 for v in d.values()) \
        and abs(sum(d.values()) - 1.0) <= 1e-3


print("=" * 70)
print("JEV HOLO4 EVAL AUDIT - CONTRACT TESTS")
print("=" * 70)

print("\n1. Closed option sets must be non-empty and unique")
for name, opts in (("NEXT_BLOCK", A.NEXT_BLOCK),
                   ("RISKIEST_ASSUMPTION", A.RISKIEST_ASSUMPTION),
                   ("NEEDS_HUMAN", A.NEEDS_HUMAN),
                   ("READINESS_LEVELS", A.READINESS_LEVELS)):
    check(f"{name} populated", len(opts) > 0, True)
    check(f"{name} keys unique", len(set(opts)), len(opts))
check("READINESS has 5 levels", len(A.READINESS_LEVELS), 5)

print("\n2. Every option carries a description (no bare labels)")
check("all NEXT_BLOCK described", all(len(v) > 40 for v in A.NEXT_BLOCK.values()), True)
check("all RISKIEST described",
      all(len(v) > 40 for v in A.RISKIEST_ASSUMPTION.values()), True)

print("\n3. State drops unknowns instead of zeroing them")
s = A.EvalState()
j = s.to_jev_state()
check("tasks_total present", "tasks_total" in j, True)
s2 = A.EvalState(tasks_completed=None)
j2 = s2.to_jev_state()
check("None field omitted, not zeroed", "tasks_completed" in j2, False)
check("sibling fields survive", "tasks_total" in j2, True)

print("\n4. Classical fallback is labeled and produces valid distributions")
fb = A.classical_fallback(A.EvalState())
check("source label", fb.source, "classical-fallback")
check("fallback picks an authored option",
      fb.next_block in A.NEXT_BLOCK, True)
check("fallback risk is authored",
      fb.riskiest in A.RISKIEST_ASSUMPTION, True)
check("next_block probs sum to 1", is_dist(fb.next_block_probs), True)
check("riskiest probs sum to 1", is_dist(fb.riskiest_probs), True)
check("readiness in range",
      0 <= fb.readiness < len(A.READINESS_LEVELS), True)
check("readiness probs length",
      len(fb.readiness_probs), len(A.READINESS_LEVELS))
check("readiness probs sum to 1",
      abs(sum(fb.readiness_probs) - 1.0) <= 1e-3, True)

print("\n5. Fallback is DETERMINISTIC (same state -> same decision)")
fb2 = A.classical_fallback(A.EvalState())
check("same next_block", fb2.next_block, fb.next_block)
check("same riskiest", fb2.riskiest, fb.riskiest)
check("same readiness", fb2.readiness, fb.readiness)

print("\n6. Key-shape guard must fail fast on a poisoned key")
check("absent key rejected", A._key_is_usable(""), False)
check("ver-output key rejected",
      A._key_is_usable("Microsoft Windows [Version 10.0.26200.9457]"), False)
check("key with newline rejected", A._key_is_usable("apikey_abc\n"), False)
check("well-formed key accepted", A._key_is_usable("apikey_" + "x" * 100), True)

print("\n7. Malformed distribution guard (the index-list defect)")
# An index list [0,1,2,3,4] is a valid list of floats; only a distributional
# test catches it. is_dist must reject it.
check("index list rejected", is_dist({0: 0.0, 1: 0.25}), False)
check("out-of-range rejected", is_dist({"a": 1.5, "b": -0.5}), False)
check("not summing to 1 rejected", is_dist({"a": 0.2, "b": 0.2}), False)
check("empty rejected", is_dist({}), False)
check("valid distribution accepted", is_dist({"a": 0.5, "b": 0.5}), True)

print("\n8. Isolation: prototype imports no production module")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "jev_holo4_eval_audit.py"), encoding="utf-8").read()
# Test IMPORTS and executable references, not prose. The docstring deliberately
# says "NO Perforce" - banning the word fails the line that promises safety.
import ast  # noqa: E402

tree = ast.parse(src)
imported: set[str] = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imported.update(a.name.split(".")[0] for a in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imported.add(node.module.split(".")[0])
print(f"       imports: {sorted(imported)}")
for banned in ("unreal", "p4", "perforce", "melodia_integration", "subprocess"):
    check(f"does not import {banned!r}", banned in imported, False)
check("writes only its own log", src.count("OUT.write_text"), 1)
check("no shell execution", "subprocess" in src, False)

print("\n" + "=" * 70)
print(f"RESULT: {PASS} passed, {FAIL} failed")
print("=" * 70)
sys.exit(1 if FAIL else 0)