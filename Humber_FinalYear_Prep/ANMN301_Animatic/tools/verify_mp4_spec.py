
import subprocess, os, json
F = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic\ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4"
out = subprocess.run(["ffprobe","-v","error","-print_format","json","-show_streams","-show_format",F],
                     capture_output=True, text=True).stdout
d = json.loads(out)
v = [s for s in d["streams"] if s["codec_type"]=="video"]
a = [s for s in d["streams"] if s["codec_type"]=="audio"]
s = v[0]
print("MP4 video streams :", len(v))
print("MP4 audio streams :", len(a), "(brief: silent -> must be 0)")
print("MP4 codec         :", s["codec_name"])
print("MP4 resolution    : %dx%d" % (s["width"], s["height"]))
print("MP4 frame rate    : %s" % s["r_frame_rate"])
print("MP4 frames        : %s" % s.get("nb_frames"))
print("MP4 duration      : %s s" % d["format"]["duration"])
print("MP4 size          : %.1f MB" % (int(d["format"]["size"])/1048576))
print()
checks = [
 ("1920x1080", s["width"]==1920 and s["height"]==1080),
 ("24 fps", s["r_frame_rate"]=="24/1"),
 ("1560 frames", s.get("nb_frames")=="1560"),
 ("65.000s", abs(float(d["format"]["duration"])-65.0)<0.01),
 ("silent (0 audio)", len(a)==0),
 ("h264", s["codec_name"]=="h264"),
]
for name, ok in checks:
    print("  %-20s %s" % (name, "PASS" if ok else "FAIL"))
print()
print("ALL PASS" if all(ok for _,ok in checks) else "SOME FAILED")
