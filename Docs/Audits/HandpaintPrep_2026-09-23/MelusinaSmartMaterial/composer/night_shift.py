#!/usr/bin/env python
"""Composer Night Shift — cut one new page of Mr. Sheep variants, unattended.

Nightly flow (02:00 ET via Hermes cron):
  1. date-seeded music: alternating theme + seeded transform parameters and
     amplitudes (so each night is a NEW page, not a repeat)
  2. live Painter: join the wire if up, else launch with
     --enable-remote-scripting and wait (never touches a foreign project)
  3. refresh the 16_Composer set on the master .spp (delete -> re-import
     masks -> re-insert -> toggle -> export) and save the master
  4. export maps to exports/MrSheep/nightly/<date>/variants/<Name>/
  5. contact sheets + per-variant beauty & albedo renders -> _ContactSheets/
  6. summary.txt + out/night_shift_report.json (always on disk, ok or not)

Usage:  python -u night_shift.py [--date YYYY-MM-DD] [--no-render]

Melodia / Melusina only. No Grok*.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SMS = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(SMS, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from painter_remote import PainterError, RemotePainter  # noqa: E402

THEMES = [
    os.path.join(REPO, "Content", "MelodiaIntegration", "MIDI",
                 "128BPMarpeggiomelody.mid"),
    os.path.join(REPO, "Exports", "melodia_history.mid"),
]
MASTER_SPP = os.path.join(SMS, "exports", "MrSheep", "MrSheep_SMS.spp")
MESH_FBX = os.path.join(SMS, "exports", "MrSheep", "mesh",
                        "choralsheep_painter_mesh.fbx")
BLENDER = "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
RUNNER_REFRESH = os.path.join(HERE, "painter_refresh_masks.py")
PAINTER_EXE = ("C:\\Program Files\\Adobe\\Adobe Substance 3D Painter\\"
               "Adobe Substance 3D Painter.exe")


def log(msg, path):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def run(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def ensure_painter(logp):
    rp = RemotePainter()
    if rp.wait_ready(timeout=20):
        log("painter wire already up (joined)", logp)
        return rp
    log("launching Painter with --enable-remote-scripting ...", logp)
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "Start-Process -FilePath '%s' -ArgumentList "
             "'--enable-remote-scripting'" % PAINTER_EXE],
            capture_output=True, timeout=60)
    except Exception as e:
        log("launch failed: %r" % e, logp)
    if rp.wait_ready(timeout=420):
        log("painter up", logp)
        return rp
    log("painter never came up", logp)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()

    date = args.date or datetime.date.today().isoformat()
    day_seed = int(date.replace("-", ""))
    outroot = os.path.join(SMS, "exports", "MrSheep", "nightly", date)
    variants_dir = os.path.join(outroot, "variants")
    sheets_dir = os.path.join(outroot, "_ContactSheets")
    os.makedirs(variants_dir, exist_ok=True)
    os.makedirs(sheets_dir, exist_ok=True)
    logp = os.path.join(HERE, "out", "night_shift_%s.log" % date)
    rep_path = os.path.join(HERE, "out", "night_shift_report.json")

    report = {"date": date, "ok": False, "seed": day_seed}
    theme = THEMES[day_seed % len(THEMES)]
    report["theme"] = os.path.basename(theme)
    log("=== Night Shift %s | theme=%s seed=%d ===" %
        (date, report["theme"], day_seed), logp)

    def finish():
        try:
            with open(rep_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=1, default=str)
        except Exception:
            pass
        log("=== Night Shift end ok=%s ===" % report["ok"], logp)
        return 0 if report["ok"] else 1

    # 1. composer (seeded)
    c = run([sys.executable, os.path.join(HERE, "melodia_composer.py"),
             "--midi", theme, "--out", os.path.join(HERE, "out"),
             "--variants", "6", "--jitter-seed", str(day_seed)],
            cwd=HERE, timeout=300)
    if c.returncode != 0:
        report["error"] = "composer failed: " + (c.stderr or "")[-600:]
        return finish()
    log("composer ok", logp)

    # 2. painter (join or launch; never kill)
    rp = ensure_painter(logp)
    if rp is None:
        report["error"] = "painter unavailable (wire never came up)"
        return finish()

    # 3. ensure a project is open (open the master only when none is)
    try:
        is_open = rp.exec_js("alg.project.isOpen()").strip().lower() == "true"
    except PainterError:
        is_open = False
    if not is_open:
        log("opening master .spp", logp)
        try:
            rp.exec_python(
                "import substance_painter.project as p\np.open(r'%s')"
                % MASTER_SPP.replace("\\", "/"))
        except PainterError as e:
            log("open call: %s" % str(e)[:200], logp)
        t0 = time.time()
        while time.time() - t0 < 300:
            try:
                ok = bool(rp.sheet(
                    "__import__('substance_painter.project', "
                    "fromlist=['x']).is_in_edition_state()"))
            except PainterError:
                ok = False
            if ok:
                break
            time.sleep(6)
        log("edition wait done after %ds" % int(time.time() - t0), logp)

    # 4. SMS2 build loop: one compact rebuild per variant (delete -> build
    # -> export), replacing the retired 16_Composer refresh. Master saved
    # only on the final variant.
    with open(os.path.join(HERE, "out", "composer_params.json"),
              encoding="utf-8") as fh:
        cfg_names = [v["name"] for v in json.load(fh)["variants"]]
    runner_sms2 = os.path.join(HERE, "painter_build_sms2_run.py")
    payload = (
        "import json\n"
        "G = {}\n"
        "exec(compile(open(r'%s', encoding='utf-8').read(), r'%s', 'exec'), G)\n"
        "names = json.loads(r'''%s''')\n"
        "reps = {}\n"
        "for i, nm in enumerate(names):\n"
        "    reps[nm] = G['build'](composer_json=r'%s', exports_dir=r'%s', "
        "project_path=r'%s', log_path=r'%s', variant_name=nm, "
        "save=(i == len(names) - 1))\n"
        "raise Exception('NS:' + json.dumps(reps, default=str))"
        % (runner_sms2, runner_sms2, json.dumps(cfg_names),
           os.path.join(HERE, "out", "composer_params.json"),
           variants_dir, MASTER_SPP,
           os.path.join(HERE, "out", "painter_run.log")))
    try:
        rp.exec_python(payload)
    except PainterError as e:
        msg = str(e)
        if "NS:" not in msg:
            report["error"] = "sms2 transport: " + msg[:500]
            return finish()
    ok_all = True
    for nm in cfg_names:
        vd = os.path.join(variants_dir, nm)
        n = len(os.listdir(vd)) if os.path.isdir(vd) else 0
        report.setdefault("variants", {})[nm] = n
        if n < 6:
            ok_all = False
    if not ok_all:
        report["error"] = "some variants exported < 6 maps"
        return finish()
    log("sms2 builds ok; exports -> %s" % variants_dir, logp)

    # strip UDIM tile suffixes (.1001 / _1001) so sheet/render finders match
    renamed = 0
    for dv in os.listdir(variants_dir):
        dpath = os.path.join(variants_dir, dv)
        if not os.path.isdir(dpath):
            continue
        for f in sorted(os.listdir(dpath)):
            for marker in (".1001", "_1001"):
                if marker in f:
                    tgt = os.path.join(dpath, f.replace(marker, ""))
                    if os.path.exists(tgt):
                        os.remove(tgt)
                    os.rename(os.path.join(dpath, f), tgt)
                    renamed += 1
                    break
    log("stripped UDIM suffixes on %d files" % renamed, logp)

    # 5. sheets
    ms = run([sys.executable, os.path.join(HERE, "make_map_sheets.py"),
              "--exports", variants_dir,
              "--out", os.path.join(sheets_dir,
                                    "ContactSheet_MrSheep_TextureMaps_%s.png"
                                    % date)], cwd=HERE, timeout=300)
    report["map_sheet"] = ms.returncode == 0
    src = os.path.join(HERE, "out", "ContactSheet_MrSheep_Scores_%s.png" % date)
    if os.path.isfile(src):
        try:
            shutil.copy(src, sheets_dir)
            report["scores_sheet"] = True
        except Exception:
            pass

    # 6. renders
    if not args.no_render:
        names = sorted(d for d in os.listdir(variants_dir)
                       if os.path.isdir(os.path.join(variants_dir, d)))
        beauty = os.path.join(outroot, "_renders")
        albedo = os.path.join(outroot, "_renders_albedo")
        for v in names:
            rb = run([BLENDER, "-b", "-P",
                      os.path.join(HERE, "render_variant_blender.py"), "--",
                      "--exports", variants_dir, "--fbx", MESH_FBX,
                      "--outdir", beauty, "--variant", v, "--res", "512",
                      "--samples", "64"], cwd=HERE, timeout=900)
            ra = run([BLENDER, "-b", "-P",
                      os.path.join(HERE, "render_variant_blender.py"), "--",
                      "--exports", variants_dir, "--fbx", MESH_FBX,
                      "--outdir", albedo, "--variant", v, "--res", "512",
                      "--samples", "24", "--albedo"], cwd=HERE, timeout=900)
            log("render %s beauty=%s albedo=%s" %
                (v, rb.returncode == 0, ra.returncode == 0), logp)
        for tag, d, out in (("renders", beauty,
                             "ContactSheet_MrSheep_Renders_%s.png" % date),
                            ("albedo", albedo,
                             "ContactSheet_MrSheep_Albedo_%s.png" % date)):
            run([sys.executable, os.path.join(HERE, "montage_renders.py"),
                 "--renders", d, "--params",
                 os.path.join(HERE, "out", "composer_params.json"),
                 "--out", os.path.join(sheets_dir, out)], cwd=HERE,
                timeout=300)
            report["sheet_" + tag] = True

    # 7. summary
    try:
        cfg = json.load(open(os.path.join(HERE, "out", "composer_params.json"),
                             encoding="utf-8"))
        lines = ["Mr. Sheep — Night Shift page %s" % date,
                 "theme: %s | seed: %d" % (report["theme"], day_seed), ""]
        for v in cfg["variants"]:
            p = v["params"]
            lines.append("%-10s notes=%3d wash=%.2f glow=%.2f | %s" %
                         (v["name"], v["notes"], p["wash_op"],
                          p["score_glow_op"], v["desc"]))
        lines.append("")
        lines.append("sheets: _ContactSheets/  | maps: variants/<Name>/  | "
                     "master: exports/MrSheep/MrSheep_SMS.spp")
        with open(os.path.join(outroot, "summary.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        report["summary"] = True
    except Exception as e:
        report["summary_err"] = repr(e)[:200]

    report["ok"] = True
    return finish()


if __name__ == "__main__":
    sys.exit(main())
