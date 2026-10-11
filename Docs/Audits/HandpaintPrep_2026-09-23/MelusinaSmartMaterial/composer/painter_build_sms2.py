"""SMS2 pilot driver — build the compact Melodia material on the OPEN Painter.

Deletes the old 16_Composer sprawl, builds SMS2_Core + SMS2_Notation from
composer canvases (ramp / aurora / score / bold score), extends the export
preset with the iridescence channels, exports, saves the master.

Usage:
  python painter_build_sms2.py [--variant Verse] [--no-export] [--no-save]

Melodia / Melusina only. No Grok*.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SMS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from painter_remote import PainterError, RemotePainter  # noqa: E402

RUNNER = os.path.join(HERE, "painter_build_sms2_run.py")
MASTER_SPP = os.path.join(SMS, "exports", "MrSheep", "MrSheep_SMS.spp")


def parse_marker(msg, marker="SMS2REP:"):
    if marker not in msg:
        return None
    rest = msg.split(marker, 1)[1].strip()
    for attempt in (rest, rest.replace("\\'", "'")):
        try:
            value, _ = json.JSONDecoder().raw_decode(attempt)
            return value
        except json.JSONDecodeError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="Verse")
    ap.add_argument("--exports",
                    default=os.path.join(SMS, "exports", "MrSheep", "pilot"))
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    rp = RemotePainter()
    if not rp.wait_ready(timeout=20):
        print("PAINTER NOT READY (wire down)")
        return 1
    try:
        is_open = rp.exec_js("alg.project.isOpen()").strip().lower() == "true"
    except PainterError:
        is_open = False
    if not is_open:
        print("No project open — open MrSheep_SMS.spp first.")
        return 1

    log_path = os.path.join(HERE, "out", "painter_run.log")
    payload = (
        "import json\n"
        "G = {}\n"
        "exec(compile(open(r'%s', encoding='utf-8').read(), r'%s', 'exec'), G)\n"
        "rep = G['build'](composer_json=r'%s', exports_dir=r'%s', "
        "project_path=r'%s', log_path=r'%s', variant_name='%s')\n"
        "raise Exception('SMS2REP:' + json.dumps(rep, default=str))"
        % (RUNNER, RUNNER,
           os.path.join(HERE, "out", "composer_params.json"),
           args.exports, MASTER_SPP, log_path, args.variant))
    rep = None
    try:
        rp.exec_python(payload)
    except PainterError as e:
        rep = parse_marker(str(e))
        if rep is None:
            print("TRANSPORT ERROR:", str(e)[:800])
            return 1

    disk = os.path.join(HERE, "out", "sms2_report.json")
    if os.path.isfile(disk):
        try:
            rep = json.load(open(disk, encoding="utf-8"))
        except Exception:
            pass
    if rep is None:
        print("no report produced")
        return 1

    print("=== SMS2 report ===")
    print("ok:", rep.get("ok"), "| error:", rep.get("error"))
    print("channels:", json.dumps(rep.get("channels", {}), indent=1))
    print("deleted:", rep.get("deleted"))
    print("roots after delete:", rep.get("roots_after_delete"))
    print("nodes built: %d" % len(rep.get("nodes", [])))
    for n in rep.get("nodes", []):
        print("  -", n)
    print("engrave bitmap:", rep.get("engrave_bitmap"))
    print("exports:", json.dumps(rep.get("exports", {}), indent=1))
    print("saved:", rep.get("saved"), "| save_err:", rep.get("save_err"))
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
