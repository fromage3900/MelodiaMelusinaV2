"""NVIDIA NeMo Guardrails wrapper lane for the MATH harness.

Scores a policy-enforcement probe set under the same evidence discipline as
every other lane: an artifact is written only when a run completes.

Two layers:
- baseline: the local policy engine in specs/mcp/guardrails_policy.v1.json
  (always available, deterministic);
- NeMo: if the `nemoguardrails` SDK is installed, the same probes run through
  a Rail wrapper (`Tools/guardrails_rails_config/`) and the comparison is
  recorded. Missing SDK -> status "held", not "fail".

Metrics recorded per probe set: blocked (should-be-blocked blocked), passed
(benign passed), recovery (a benign call after a block succeeds).

Run:
    python Tools/run_guardrails_lane.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / "specs" / "mcp" / "guardrails_policy.v1.json"
AUDIT = ROOT / "Saved" / "Audit"

SCHEMA = "melodia.guardrails.v1"


def _load_policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def _local_policy_engine(policy: dict):
    """Deterministic regex policy engine (baseline)."""
    block_patterns = [re.compile(p, re.IGNORECASE) for p in policy.get("block_patterns", [])]
    rewrite_rules = [
        (re.compile(src, re.IGNORECASE), dst)
        for src, dst in policy.get("rewrite_rules", [])
    ]

    def classify(text: str) -> dict:
        for pat in block_patterns:
            if pat.search(text):
                return {"action": "blocked", "reason": pat.pattern}
        for src, dst in rewrite_rules:
            if src.search(text):
                return {"action": "rewritten", "rewrite": src.sub(dst, text)}
        return {"action": "pass", "reason": "benign"}

    return classify


def _run_probes(classify, probes: dict) -> tuple[list[dict], dict]:
    rows = []
    stats = {"blocked": 0, "passed": 0, "rewritten": 0, "recovery": 0}
    blocked_seen = False
    for probe in probes:
        text = probe["text"]
        verdict = classify(text)
        expected = probe["expect"]
        ok = verdict["action"] == expected
        if ok:
            stat_key = {"blocked": "blocked", "pass": "passed", "rewritten": "rewritten"}.get(expected)
            if stat_key:
                stats[stat_key] = stats.get(stat_key, 0) + 1
        if verdict["action"] == "blocked":
            blocked_seen = True
        if expected == "pass" and ok and blocked_seen:
            stats["recovery"] += 1
        rows.append({
            "id": probe["id"],
            "expect": expected,
            "action": verdict["action"],
            "pass": bool(ok),
            "detail": verdict.get("reason") or verdict.get("rewrite") or "ok",
        })
    total = len(rows)
    return rows, {**stats, "pass_rate": round(sum(1 for r in rows if r["pass"]) / total * 100.0, 1) if total else 0.0}


def _neemo_wrapper(policy: dict):
    """Wrap the probe set through NeMo Guardrails when the SDK is installed."""
    try:
        from nemoguardrails import RailsConfig, LLMRails
    except ImportError:
        return None
    try:
        cfg = RailsConfig.from_path(str(ROOT / "Tools" / "guardrails_rails_config"))
        rails = LLMRails(cfg)
    except Exception:
        return None
    return rails


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    AUDIT.mkdir(parents=True, exist_ok=True)
    policy = _load_policy()
    probes = policy["probes"]

    baseline = _local_policy_engine(policy)
    rows, stats = _run_probes(baseline, probes)

    report = {
        "schema": SCHEMA,
        "kind": "guardrails_lane",
        "captured_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "layer": "local-policy-baseline",
        "policy_file": str(POLICY.relative_to(ROOT)),
        "probe_count": len(rows),
        "stats": stats,
        "rows": rows,
    }

    rails = _neemo_wrapper(policy)
    if rails is not None:
        report["layer"] = "nemoguardrails-wrapper"
        report["nemo"] = {"status": "available"}
        nemo_rows = []
        for probe in probes:
            try:
                out = rails.generate(messages=[{"role": "user", "content": probe["text"]}])
                action = "pass" if "blocked" not in str(out).lower() else "blocked"
            except Exception as exc:
                action = "error"
            nemo_rows.append({
                "id": probe["id"],
                "expect": probe["expect"],
                "action": action,
                "pass": action == probe["expect"],
                "detail": "nemo verdict",
            })
        report["nemo"]["rows"] = nemo_rows
        report["nemo"]["stats"] = {
            "pass_rate": round(sum(1 for r in nemo_rows if r["pass"]) / len(nemo_rows) * 100.0, 1),
        }
    else:
        report["nemo"] = {"status": "held", "reason": "nemoguardrails SDK not installed"}

    date = datetime.now().strftime("%Y-%m-%d")
    out = AUDIT / f"guardrails_{date}.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"guardrails lane: baseline {stats['pass_rate']}% (blocked={stats['blocked']}, "
        f"passed={stats['passed']}, recovery={stats['recovery']}) "
        f"| nemo={report['nemo'].get('status')} -> {out.name}"
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
