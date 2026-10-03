#!/usr/bin/env python3
"""Verify gate - the only thing that may close an agent card.

Mechanism 4 of `.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`:
"a card moves to Done only after the verifier writes `verified.json` (who, what
artifact was opened, pass/fail). Hermes self-reports never close a card."

It was the last unimplemented mechanism of H1. Everything else in H1 (task packet,
router, editor lease) is in place, which means the loop could already be RUNNING
with nothing stopping a worker from declaring its own work done. That is the
dangerous state, and it is not hypothetical here:

  * `CURRENT_STATE.md` records a session where four rhythm-scalar source edits
    "did land, build, and pass their tests - and were then silently reverted by
    the read-only freeze before the commit". The green evidence described a tree
    state that no longer existed.
  * A subagent once reported a "smooth" SDF bake that was scattered dots.
  * AGENTS.md: "delegated output is not evidence. Open the artifact yourself."

So this gate is deliberately hard to satisfy by accident:

  * the receipt must name the ARTIFACT that was opened, not the report about it
  * the verifier must not be the producer (`no_self_certification`, a tier-registry
    rule, not a preference)
  * a receipt with no artifact and no measurement is rejected, because that is
    just a self-report with better JSON
  * `close` refuses on a missing, malformed, failing, stale, or self-certified
    receipt - and on a `pass` receipt whose named artifact is not on disk
  * `uncertain` is a first-class outcome. "I could not confirm this" must be
    recordable, or agents will write `pass` to make the loop move.

Usage:
  python Tools/verify_gate.py record  <card> --verifier <id> --producer <id> \\
      --artifact <path> [--artifact <path> ...] [--measured <text>] \\
      [--result pass|fail|uncertain] [--uncertainty <text>]
  python Tools/verify_gate.py check    <card>
  python Tools/verify_gate.py close    <card> [--json]
  python Tools/verify_gate.py list     [--json]
  python Tools/verify_gate.py sweep    <dir-of-cards>     # unattended loop guard

Exit codes: 0 pass, 1 fail, 2 refused (usage/policy), 3 no receipt.
Read-only apart from `record`, which writes Saved/Audit/<card>/verified.json
(Saved/ is gitignored by design; the receipt is evidence for this machine, and the
artifact it names is what travels).
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIT = os.path.join(ROOT, "Saved", "Audit")

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_REFUSED = 2
EXIT_NO_RECEIPT = 3

VALID_RESULTS = ("pass", "fail", "uncertain")
SCHEMA = "melodia.verification_receipt/v1"


def receipt_path(card):
    return os.path.join(AUDIT, card, "verified.json")


def now_iso():
    return (datetime.datetime.now().astimezone()
            .replace(microsecond=0).isoformat())


def record(card, verifier, producer, artifacts, measured, result,
           uncertainty="", kind="artifact_open", note=""):
    """Write a receipt. Refuses the receipts that cannot mean anything."""
    if result not in VALID_RESULTS:
        return EXIT_REFUSED, "result must be one of %s" % "/".join(VALID_RESULTS)
    if verifier == producer:
        return EXIT_REFUSED, (
            "no_self_certification: verifier %r is the producer %r. The tier registry "
            "requires the producer's own lane to be excluded from grading. Use "
            "--result uncertain and hand the card to the owner instead."
            % (verifier, producer))
    if not artifacts:
        return EXIT_REFUSED, (
            "a receipt must name at least one artifact that was OPENED. "
            "A receipt with no artifact is a self-report.")
    if result == "uncertain" and not uncertainty:
        return EXIT_REFUSED, "--result uncertain requires --uncertainty saying what is unresolved"

    missing = [a for a in artifacts if not os.path.exists(os.path.join(ROOT, a))]
    if missing:
        return EXIT_REFUSED, ("artifact(s) not on disk, so 'opened' would be a lie: %s"
                              % ", ".join(missing))

    receipt = {
        "schema": SCHEMA,
        "card": card,
        "verifier": verifier,
        "producer": producer,
        "result": result,
        "verify_kind": kind,
        "artifacts_opened": list(artifacts),
        "measured": measured,
        "residual_uncertainty": uncertainty,
        "note": note,
        "recorded_at": now_iso(),
        "machine": os.environ.get("COMPUTERNAME", "unknown"),
    }
    path = receipt_path(card)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")
    return EXIT_PASS, path


def load(card):
    path = receipt_path(card)
    if not os.path.exists(path):
        return None, path
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), path
    except (OSError, ValueError) as exc:
        return {"_malformed": str(exc)}, path


def check(card, producer=None):
    """Is this card closable? Returns (exit_code, [reasons])."""
    reasons = []
    receipt, path = load(card)
    if receipt is None:
        return EXIT_NO_RECEIPT, ["no receipt at %s - Hermes self-report never closes a card"
                                 % os.path.relpath(path, ROOT)]
    if "_malformed" in receipt:
        return EXIT_REFUSED, ["receipt is unreadable: %s" % receipt["_malformed"]]
    for field in ("verifier", "producer", "result", "artifacts_opened", "recorded_at"):
        if not receipt.get(field):
            reasons.append("receipt is missing required field %r" % field)
    result = receipt.get("result")
    if result not in VALID_RESULTS:
        reasons.append("result %r is not one of %s" % (result, "/".join(VALID_RESULTS)))
    if receipt.get("verifier") == receipt.get("producer"):
        reasons.append("no_self_certification: verifier == producer (%r)" % receipt.get("producer"))
    artifacts = receipt.get("artifacts_opened") or []
    if not artifacts:
        reasons.append("receipt names no artifact that was opened")
    vanished = [a for a in artifacts if not os.path.exists(os.path.join(ROOT, a))]
    if vanished:
        reasons.append("artifact(s) named as opened are no longer on disk: %s"
                       % ", ".join(vanished))
    if result == "pass" and not receipt.get("measured"):
        reasons.append("a 'pass' receipt must record what was MEASURED")
    if producer and receipt.get("producer") != producer:
        reasons.append("receipt producer %r does not match the dispatched producer %r"
                       % (receipt.get("producer"), producer))
    if reasons:
        code = EXIT_REFUSED if result != "fail" else EXIT_FAIL
        return code, reasons
    if result == "fail":
        return EXIT_FAIL, ["verifier recorded FAIL: %s" % (receipt.get("measured") or "")]
    if result == "uncertain":
        # Making "I could not confirm this" recordable is the point. It is NOT
        # the same as passing, and a loop that treats it as done has learned
        # nothing. Only an owner or a gate script may resolve it.
        return EXIT_REFUSED, ["verifier recorded UNCERTAIN: %s -- hand to the owner, "
                              "do not close"
                              % (receipt.get("residual_uncertainty")
                                 or receipt.get("measured") or "no detail given")]
    return EXIT_PASS, ["verifier %s opened %d artifact(s): %s"
                       % (receipt.get("verifier"), len(artifacts), ", ".join(artifacts))]


def close_card(card, producer=None, json_out=False):
    code, reasons = check(card, producer=producer)
    ok = (code == EXIT_PASS)
    if json_out:
        print(json.dumps({"card": card, "closable": ok, "exit_code": code,
                          "reasons": reasons}, indent=2))
    else:
        print("%s  %s" % ("CLOSE " if ok else "REFUSE", card))
        for reason in reasons:
            print("  %s" % reason)
    return code


def sweep(root_dir):
    """Loop guard. Run this before an unattended loop takes another turn: every
    card under root_dir must either be genuinely open, or closeable on a real
    receipt. A card that claims done without a receipt is the failure this
    whole tool exists to catch."""
    cards = sorted(d for d in os.listdir(root_dir)
                   if os.path.isdir(os.path.join(root_dir, d)))
    rows = []
    for card in cards:
        receipt, _ = load(card)
        if receipt is None:
            state = "open"
            detail = "no receipt"
        elif receipt.get("_malformed"):
            state = "refuse"
            detail = "unreadable receipt"
        else:
            state = {"pass": "closable", "fail": "failed", "uncertain": "uncertain"}.get(
                receipt.get("result"), "refuse")
            detail = "%s by %s" % (receipt.get("result"), receipt.get("verifier"))
            if receipt.get("verifier") == receipt.get("producer"):
                state = "refuse"
                detail = "self-certified"
        rows.append((card, state, detail))
    width = max([len(c) for c, _, _ in rows] or [4])
    for card, state, detail in rows:
        print("%-*s  %-9s %s" % (width, card, state, detail))
    blocked = [r for r in rows if r[1] in ("failed", "refuse")]
    print("\n%d card(s): %d closable, %d open, %d needing attention"
          % (len(rows),
             len([r for r in rows if r[1] == "closable"]),
             len([r for r in rows if r[1] == "open"]),
             len(blocked)))
    return EXIT_REFUSED if blocked else EXIT_PASS


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Verify gate - the only thing that closes a card.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("record")
    p_rec.add_argument("card")
    p_rec.add_argument("--verifier", required=True)
    p_rec.add_argument("--producer", required=True)
    p_rec.add_argument("--artifact", action="append", default=[])
    p_rec.add_argument("--measured", default="")
    p_rec.add_argument("--result", choices=list(VALID_RESULTS), default="pass")
    p_rec.add_argument("--uncertainty", default="")
    p_rec.add_argument("--kind", default="artifact_open")
    p_rec.add_argument("--note", default="")

    p_check = sub.add_parser("check")
    p_check.add_argument("card")
    p_check.add_argument("--producer")

    p_close = sub.add_parser("close")
    p_close.add_argument("card")
    p_close.add_argument("--producer")
    p_close.add_argument("--json", dest="json_out", action="store_true")

    p_list = sub.add_parser("list")
    p_list.add_argument("--json", dest="json_out", action="store_true")

    p_sweep = sub.add_parser("sweep")
    p_sweep.add_argument("dir", nargs="?", default=AUDIT)

    args = ap.parse_args()

    if args.cmd == "record":
        code, detail = record(args.card, args.verifier, args.producer, args.artifact,
                              args.measured, args.result, args.uncertainty,
                              kind=args.kind, note=args.note)
        if code != EXIT_PASS:
            sys.stderr.write("refused: %s\n" % detail)
            return code
        print("recorded %s -> %s" % (args.card, os.path.relpath(detail, ROOT)))
        return code

    if args.cmd == "check":
        code, reasons = check(args.card, producer=args.producer)
        print("%s  %s" % ("CLOSABLE" if code == EXIT_PASS else "NOT CLOSABLE", args.card))
        for reason in reasons:
            print("  %s" % reason)
        return code

    if args.cmd == "close":
        return close_card(args.card, producer=args.producer, json_out=args.json_out)

    if args.cmd == "list":
        rows = []
        if os.path.isdir(AUDIT):
            for card in sorted(os.listdir(AUDIT)):
                receipt, _ = load(card)
                if receipt and not receipt.get("_malformed"):
                    rows.append({"card": card, "result": receipt.get("result"),
                                 "verifier": receipt.get("verifier"),
                                 "producer": receipt.get("producer"),
                                 "recorded_at": receipt.get("recorded_at")})
        if args.json_out:
            print(json.dumps(rows, indent=2))
        else:
            for row in rows:
                print("%-34s %-10s %s" % (row["card"], row["result"], row["verifier"]))
        return 0

    if args.cmd == "sweep":
        target = args.dir
        if not os.path.isdir(target):
            sys.stderr.write("no such card directory: %s\n" % target)
            return EXIT_REFUSED
        return sweep(target)

    return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())