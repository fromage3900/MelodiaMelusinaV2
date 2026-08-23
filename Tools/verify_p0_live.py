#!/usr/bin/env python3
"""
Live P0 verification helper — records intent, does not fake a ledger pass.
Requires one editor on http://localhost:9316/mcp (monolith). See research/live_verification_kit.md.
"""
import argparse, json, sys
from pathlib import Path

GATES = ["rhythm_owner","hud_single_writer","wardrobe_equip_roundtrip","rhythm_grade_to_result","music_world_key","wardrobe_gameplay_hook"]

def main():
    p = argparse.ArgumentParser(description="Live P0 verification kit (no probe-only pass)")
    p.add_argument("--gate", choices=GATES, help="single gate")
    p.add_argument("--all", action="store_true", help="list all gates")
    args = p.parse_args()
    if args.all or not args.gate:
        print("P0 gates:", ", ".join(GATES))
        print("Run: python Tools/verify_p0_live.py --gate <id>  (requires editor + 9316 health)")
        print("Then, ONLY with real-input evidence: python Tools/echo_run.py record <gate> pass")
        return 0
    out = Path("Saved/Echo") / f"live_verify_{args.gate}_intent.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"gate": args.gate, "requires": "real keyboard PIE Q/W/O/P + ledger row", "probe_only": "HOLD per AGENTS.md Evidence standard"}, indent=2))
    print(f"Wrote intent marker {out} — now run the PIE session per research/live_verification_kit.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
