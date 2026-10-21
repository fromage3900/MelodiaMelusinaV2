#!/usr/bin/env python
"""Run the resume export pass inside the live Painter session.

Usage: python run_resume.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from painter_remote import PainterError, RemotePainter  # noqa: E402

SMS = os.path.abspath(os.path.join(HERE, ".."))
RUNNER = os.path.join(HERE, "painter_resume_export.py")


def main():
    rp = RemotePainter()
    print("waiting for Painter remote server ...")
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
        "rep = G['resume'](composer_json=r'%s', exports_dir=r'%s', "
        "project_path=r'%s', log_path=r'%s')\n"
        "raise Exception('COMPOSER_REPORT:' + json.dumps(rep, default=str))"
        % (RUNNER, RUNNER, composer, exports, project, log))
    try:
        rp.exec_python(script)
        print("(clean return - unexpected)")
    except PainterError as e:
        print("remote result:", str(e)[:2000])

    rep_path = os.path.join(HERE, "out", "resume_report.json")
    if os.path.isfile(rep_path):
        print("---- resume_report.json ----")
        print(open(rep_path, encoding="utf-8").read()[:4000])
    else:
        print("no resume report - check", log)


if __name__ == "__main__":
    main()
