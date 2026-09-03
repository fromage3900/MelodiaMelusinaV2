#!/usr/bin/env python3
"""
sync_site_status.py - Generate an HONEST, owner-voiced status blob for the
Melodia Melusina portfolio site from the game repo's real gate ledger.

This is the live-sync bridge. It reads BS_GodFile/Saved/gate_ledger.json
(the single source of truth for "is this done") and emits a small JSON the
site can render. It does NOT invent progress: a gate is only PASS when the
ledger has a row for it. Nothing here claims the AI fleet is a product - the
AI is mentioned exactly once, as a drafting tool.

Run from anywhere; paths resolve relative to repo root.
"""
import json
import os
import sys
import argparse
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO_ROOT, "Saved", "gate_ledger.json")
# The site repo checkout sits beside BS_GodFile in the workspace:
SITE_STATUS = os.path.join(
    REPO_ROOT, "..", "my-site-clean", "public", "melodia", "status", "sync_status.json"
)

# Pillars in owner's own categorical language.
PILLARS = ["rhythm", "wardrobe", "ui", "world_puzzle"]

# Honest one-line voice for each gate state (owner tone, no hype verbs).
STATE_LINE = {
    "PASS": "closed - owner-verified, never re-proved",
    "FAIL": "open - real defect, named and tracked",
    "OPEN": "open - not yet converged",
}


def load_ledger():
    if not os.path.exists(LEDGER):
        return {}
    try:
        with open(LEDGER, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[sync] could not read ledger: {e}", file=sys.stderr)
        return {}


def gate_rows(ledger):
    """Normalize whatever shape the ledger uses into {gate_id: status}."""
    rows = {}
    # Common shapes: list of {id,status} or dict of gate->status
    if isinstance(ledger, dict):
        if "gates" in ledger and isinstance(ledger["gates"], list):
            for g in ledger["gates"]:
                rows[g.get("id")] = g.get("status")
        elif "ledger" in ledger and isinstance(ledger["ledger"], dict):
            rows.update(ledger["ledger"])
        else:
            rows.update({k: v for k, v in ledger.items() if isinstance(v, str)})
    elif isinstance(ledger, list):
        for g in ledger:
            if isinstance(g, dict) and "id" in g:
                rows[g["id"]] = g.get("status")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="Write the status JSON here (else the default site path).")
    args = ap.parse_args()

    ledger = load_ledger()
    rows = gate_rows(ledger)

    # Build the honest standing from real rows only.
    pass_count = sum(1 for s in rows.values() if str(s).upper() == "PASS")
    total = len(rows)
    standing = "in progress"  # a one-person convergence project is never "done"
    summary = (
        f"{pass_count}/{total} completion gates closed against the ledger. "
        "Remaining work is convergence, not construction. "
        "The AI is a drafting tool I run locally - it is not the product."
    )

    out = {
        "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "BS_GodFile/Saved/gate_ledger.json",
        "standing": standing,
        "summary": summary,
        "gates_closed": pass_count,
        "gates_total": total,
        "pillars": PILLARS,
        "ai_note": "Local models (Qwen / Muse) used only for catalog rows, "
        "beat maps and QA. Never the product, never sets direction.",
        "ledger_rows": rows,
    }

    out_path = os.path.abspath(args.out) if args.out else SITE_STATUS
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # Copy into the site repo's deploy path as well if the default was used and
    # the alternate clone exists (keeps both _github_deploy and my-site-clean in sync).
    if not args.out:
        alt = os.path.join(REPO_ROOT, "..", "my-site", "public", "melodia", "status", "sync_status.json")
        try:
            os.makedirs(os.path.dirname(alt), exist_ok=True)
            with open(alt, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    print(f"[sync] wrote status: {pass_count}/{total} gates closed -> {out_path}")


if __name__ == "__main__":
    main()
