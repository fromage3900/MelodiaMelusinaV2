#!/usr/bin/env python
"""Run the mask refresh pass inside the live Painter session.

Usage: python run_refresh.py   (after re-running melodia_composer.py)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from painter_remote import PainterError, RemotePainter  # noqa: E402

SMS = os.path.abspath(os.path.join(HERE, ".."))
RUNNER = os.path.join(HERE, "painter_refresh_masks.py")


def main():
    rp = RemotePainter()
    print("waiting for Painter ...")
    if not rp.wait_ready(timeout=120):
        raise SystemExit("remote server not up")
    print("connected via", rp.host)

    composer = os.path.join(HERE, "out", "composer_params.json")
    exports = os.path.join(SMS, "exports", "MrSheep", "variants")
    project = os.path.join(SMS, "exports", "MrSheep", "MrSheep_SMS.spp")
    log = os.path.join(HERE, "out", "painter_run.log")

    script = (
        "G = {}\n"
        "exec(compile(open(r'%s', encoding='utf-8').read(), r'%s', 'exec'), G)\n"
        "import json\n"
        "rep = G['refresh'](composer_json=r'%s', exports_dir=r'%s', "
        "project_path=r'%s', log_path=r'%s')\n"
        "raise Exception('COMPOSER_REPORT:' + json.dumps(rep, default=str))"
        % (RUNNER, RUNNER, composer, exports, project, log))
    try:
        rp.exec_python(script)
    except PainterError as e:
        print("remote result:", str(e)[:2500])

    p = os.path.join(HERE, "out", "mask_refresh_report.json")
    if os.path.isfile(p):
        print("---- mask_refresh_report.json ----")
        print(open(p, encoding="utf-8").read()[:3000])


if __name__ == "__main__":
    main()
