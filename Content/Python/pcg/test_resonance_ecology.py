"""Offline contract test for resonance_ecology_processor.derive (no Unreal needed).

Runs two ways:
  python Content/Python/pcg/test_resonance_ecology.py     (script, exit code 0/1)
  python -m pytest Content/Python/pcg/test_resonance_ecology.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resonance_ecology_processor as rep  # noqa: E402

CHECK_COUNT = 10


def run_checks(verbose=True):
    """Run every contract check and return the list of failed check names."""
    failures = []

    def check(name, cond):
        if verbose:
            print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failures.append(name)

    r_low = rep.derive(100.0, 100.0, 0.0, 7)
    r_high = rep.derive(100.0, 100.0, 2000.0, 7)

    check("resonance stays in 0..1", all(0.0 <= rep.derive(x * 137.0, x * 71.0, x * 33.0, 7)[0] <= 1.0 for x in range(500)))
    check("height raises resonance", r_high[0] > r_low[0])
    check("deterministic for same input", rep.derive(512.0, 256.0, 900.0, 3) == rep.derive(512.0, 256.0, 900.0, 3))
    check("seed changes the result", rep.derive(512.0, 256.0, 900.0, 3) != rep.derive(512.0, 256.0, 900.0, 4))
    check("ecology class in 0..2", all(rep.derive(x * 11.0, x * 29.0, x * 4.0, 1)[1] in (0, 1, 2) for x in range(500)))
    check("low band is class 0", r_low[1] == 0)
    check("top band is class 2", r_high[1] == 2)
    classes = {rep.derive(x * 97.0, x * 53.0, (x % 40) * 50.0, 5)[1] for x in range(500)}
    check("at least two classes separate on a grid  [%s]" % sorted(classes), len(classes) >= 2)
    check("material variant in 0..2", all(rep.derive(x * 7.0, x * 13.0, x * 3.0, 2)[2] in (0, 1, 2) for x in range(500)))
    check("scale bias bounded", all(rep.SCALE_BIAS_MIN <= rep.derive(x * 17.0, x * 23.0, x * 9.0, 6)[3] <= rep.SCALE_BIAS_MAX for x in range(500)))
    return failures


def test_resonance_ecology_contract():
    failures = run_checks(verbose=False)
    assert not failures, "failed contract checks: %s" % failures


if __name__ == "__main__":
    _failures = run_checks()
    print("\n=== %d/%d passed ===" % (CHECK_COUNT - len(_failures), CHECK_COUNT))
    sys.exit(1 if _failures else 0)
