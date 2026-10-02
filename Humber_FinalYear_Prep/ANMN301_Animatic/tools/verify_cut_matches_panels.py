
from PIL import Image, ImageChops
import os, subprocess

PF  = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\panels_final"
MP4 = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4"
TMP = r"C:\Users\brenn\AppData\Local\Temp\animcheck\vframe2"
os.makedirs(TMP, exist_ok=True)

# VSE: PANEL_06 f457-576, PANEL_11 f769-864, PANEL_16 f1273-1392
# 0-based video frame index = blender_frame - 1
checks = [("06", 500), ("11", 810), ("16", 1330)]

def grab(idx, out):
    # -vf select on the decoded stream = exact frame, no keyframe guesswork
    subprocess.run(["ffmpeg","-v","error","-y","-i",MP4,
                    "-vf","select=eq(n\\,%d)"%idx,"-frames:v","1",out],
                   check=True)

print("MP4 vs panels_final, EXACT frame selection")
for num, bframe in checks:
    idx = bframe - 1
    out = os.path.join(TMP, "f%s.png" % num)
    grab(idx, out)
    a = Image.open(out).convert("RGB")
    b = Image.open(os.path.join(PF,"panel_%s.png"%num)).convert("RGB")
    if a.size != b.size:
        print("  panel %s SIZE %s vs %s" % (num, a.size, b.size)); continue
    d = ImageChops.difference(a,b); px = d.load(); W,H = d.size
    nz = sum(1 for y in range(0,H,2) for x in range(0,W,2) if sum(px[x,y]) > 30)
    tot = (H//2)*(W//2)
    mx = max(max(px[x,y]) for y in range(0,H,8) for x in range(0,W,8))
    print("  panel %s blender_frame %d (idx %d): diff=%.3f%%  maxdelta=%d  %s" % (
        num, bframe, idx, 100.0*nz/tot, mx, "MATCH" if nz/tot < 0.005 else "DIFFERS"))
