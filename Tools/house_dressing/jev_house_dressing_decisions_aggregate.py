"""Run the house-leg Jev packet N times and aggregate the answers.

Why: a single Jev answer on a close call is one sample. The owner said "I
don't really know; tbh" about these decisions, so the receipt has to carry
run-to-run stability, not one draw. The TypeSafe answer carries a full
probability distribution per run, so N runs give a mean distribution AND an
agreement rate - which is the honest form of "Jev thinks X".

Writes:
  Saved/Audit/house_dressing/JevHouseDressingDecisions_20261022_s{1..N}.json
  Saved/Audit/house_dressing/JevHouseDressingDecisions_20261022_aggregate.json

Usage:
    python Tools/house_dressing/jev_house_dressing_decisions_aggregate.py [--samples 3]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jev_house_dressing_decisions_20261022 as packet  # noqa: E402

OUT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "Saved", "Audit", "house_dressing"))
BASE = "JevHouseDressingDecisions_20261022"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args(argv)

    if not packet.jev_available():
        print("[!] Jev unavailable (TYPESAFE_API_KEY / typesafe_sdk).")
        return 2

    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.questions import Choice

    os.makedirs(OUT_DIR, exist_ok=True)
    questions = {qid: Choice(instructions=spec["question"],
                             criteria=dict(spec["criteria"]))
                 for qid, spec in packet.QUESTIONS.items()}

    samples: list[dict] = []
    for index in range(1, args.samples + 1):
        with TypeSafeClient() as client:
            result = client.system_one(
                state={"verified_state": packet.STATE,
                       "constraints": packet.STATE["constraints"]},
                questions=questions)
        answers = {
            qid: {"choice": a.choice,
                  "confidence": getattr(a, "confidence", None),
                  "probabilities": getattr(a, "probabilities", None)}
            for qid, a in result.answers.items()
        }
        sample = {
            "schema": "melodia.jev.house_dressing_decisions.v1",
            "source": "jev-live",
            "sample": index,
            "model": getattr(result, "model", None),
            "state_verified_at": packet.STATE["verified_at"],
            "answers": answers,
        }
        path = os.path.join(OUT_DIR, f"{BASE}_s{index}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(sample, handle, indent=2, ensure_ascii=False)
        samples.append(sample)
        print(f"   sample {index}: " + ", ".join(
            f"{qid}={a['choice']}({a['confidence']})" for qid, a in answers.items()))

    aggregate = {}
    for qid in packet.QUESTIONS:
        picks = [s["answers"][qid]["choice"] for s in samples]
        options = list(packet.QUESTIONS[qid]["criteria"].keys())
        mean = {opt: round(statistics.fmean(
            (s["answers"][qid]["probabilities"] or {}).get(opt, 0.0) for s in samples), 3)
            for opt in options}
        leader = max(mean, key=lambda o: mean[o])
        agreement = picks.count(leader) / len(picks)
        confidences = [s["answers"][qid]["confidence"] for s in samples
                       if s["answers"][qid]["confidence"] is not None]
        aggregate[qid] = {
            "question": packet.QUESTIONS[qid]["question"],
            "picks": picks,
            "mean_distribution": mean,
            "mean_confidence": round(statistics.fmean(confidences), 3) if confidences else None,
            "leader": leader,
            "leader_share_of_mean": mean[leader],
            "agreement": round(agreement, 3),
            "verdict": ("DECIDED" if (agreement >= 2 / 3 and mean[leader] >= 0.5)
                        else "NEAR_TIE_OWNER_CALL"),
        }

    out = {
        "schema": "melodia.jev.house_dressing_decisions_aggregate.v1",
        "source": "jev-live",
        "state_verified_at": packet.STATE["verified_at"],
        "samples": len(samples),
        "sample_receipts": [f"{BASE}_s{i}.json" for i in range(1, len(samples) + 1)],
        "criteria": {qid: packet.QUESTIONS[qid]["criteria"] for qid in packet.QUESTIONS},
        "aggregate": aggregate,
    }
    dest = os.path.join(OUT_DIR, f"{BASE}_aggregate.json")
    with open(dest, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2, ensure_ascii=False)

    print("\n=== AGGREGATE ===")
    for qid, row in aggregate.items():
        print(f"   {qid}: {row['leader']} ({row['verdict']}, agreement {row['agreement']}, "
              f"mean {row['mean_distribution']}, picks {row['picks']})")
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
