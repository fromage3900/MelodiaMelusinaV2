# variant_encode.py — encode sil_* frame sequences to mp4 + webm + poster (ffmpeg).
# Mirrors encode_loops.py but globs any tag starting with the given prefix instead
# of a hardcoded list.
import glob
import os
import shutil
import subprocess

ROOT = r"P:/MelodiaMelusinaV2-Laptop/Saved/Website/Brooch"
FR = os.path.join(ROOT, "frames")
PREFIX = "sil_"
FF = shutil.which("ffmpeg") or (
    r"C:/Users/brenn/AppData/Local/Microsoft/WinGet/Packages/"
    r"Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe")

fail = 0
firsts = sorted(glob.glob(os.path.join(FR, PREFIX + "*_0000.png")))
if not firsts:
    print("no %s* frame sequences found" % PREFIX)
    raise SystemExit(1)
for first in firsts:
    tag = os.path.basename(first)[:-9]  # strip _0000.png
    pat = os.path.join(FR, tag + "_%04d.png")
    jobs = [
        (os.path.join(ROOT, tag + ".mp4"),
         ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"]),
        (os.path.join(ROOT, tag + ".webm"),
         ["-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0"]),
    ]
    for out, codec in jobs:
        r = subprocess.run([FF, "-y", "-framerate", "24", "-i", pat] + codec + [out],
                           capture_output=True, text=True)
        print(("OK  " if r.returncode == 0 else "FAIL"), os.path.basename(out))
        fail += r.returncode != 0
    # poster = first frame at 720x900
    r = subprocess.run([FF, "-y", "-i", first, "-vf", "scale=720:900",
                        os.path.join(ROOT, tag + "_poster.jpg")],
                       capture_output=True, text=True)
    print(("OK  " if r.returncode == 0 else "FAIL"), os.path.basename(tag + "_poster.jpg"))
    fail += r.returncode != 0
raise SystemExit(1 if fail else 0)
