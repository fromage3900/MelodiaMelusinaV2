"""Assemble Sir KineFX contact sheets (pure Python + PIL, no DCC).

Reads contact/render_report.json + wingtip_probe.json + Wingbeat curves,
writes one labeled sheet per clip and a Fly v5-vs-v6 fan pair sheet.
Labels carry the KineFX instrumentation (tip travel, Hz, symmetry, seam,
wingbeat value at frame) — that is what makes these KineFX contact sheets,
not just renders.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
DOCTOR = REPO / "Saved/Audit/sirmelodious_kinefx_doctor"
CONTACT = DOCTOR / "contact"
AUDIT = REPO / "Saved/Audit/SirMelodious_FlightUnit_20261003"

rep = json.loads((CONTACT / "render_report.json").read_text())["clips"]
wt = json.loads((DOCTOR / "wingtip_probe.json").read_text())["clips"]
wing = json.loads((AUDIT / "exports/ue_arp/Wingbeat_curves_v5.json").read_text())

try:
    f_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
    f_label = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
except Exception:
    f_title = ImageFont.load_default()
    f_label = ImageFont.load_default()

BG, HD, TX, SUB = (16, 14, 20), (30, 26, 36), (242, 235, 228), (175, 168, 160)


def wingbeat_at(clip: str, frame: int) -> str:
    base = clip.replace("_ARP", "")
    for k, v in wing.items():
        if k.split("_v")[0] in base:
            # ARP FBX actions run +1 vs the authored 0-based curve keys
            for f, val in v["keys"]:
                if f in (frame, frame - 1):
                    return f"{val:.2f}"
            return "0.00"
    return "—"


def sheet(shots: list[dict], title: str, subtitle: str, out: Path,
          thumbs: tuple[int, int] = (480, 270)) -> None:
    cols = 3
    rows = (len(shots) + cols - 1) // cols
    W = cols * thumbs[0] + (cols + 1) * 12
    H = 96 + rows * (thumbs[1] + 30) + 16
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 96], fill=HD)
    d.text((16, 12), title, fill=TX, font=f_title)
    d.text((16, 52), subtitle, fill=SUB, font=f_label)
    for i, s in enumerate(shots):
        im = Image.open(s["path"]).convert("RGB").resize(thumbs)
        x = 12 + (i % cols) * (thumbs[0] + 12)
        y = 96 + 12 + (i // cols) * (thumbs[1] + 30)
        img.paste(im, (x, y))
        d.text((x + 4, y + thumbs[1] + 5), s["label"], fill=SUB, font=f_label)
    img.save(out)
    print("wrote", out.name)


for clip, info in rep.items():
    if info.get("status") != "DONE":
        print("skip", clip, info.get("error", "?")[:80])
        continue
    w = wt.get(clip + ".fbx", wt.get(clip, {}))
    l = w.get("left", {})
    sub = (f"tip {l.get('tip_travel_cm')}cm @{l.get('stroke_hz')}Hz "
           f"| L/R {w.get('lr_symmetry')} | seam {w.get('seam_max_mm')}mm "
           f"| frames {info['frames'][0]}-{info['frames'][1]} "
           f"| mesh_vs_bone {info.get('span_check', {}).get('mesh_vs_bone')}")
    shots = [{"path": s["path"],
              "label": f"f{s['frame']:03d}  wingbeat {wingbeat_at(clip, s['frame'])}"}
             for s in info["shots"]]
    sheet(shots, clip, sub, CONTACT / f"sheet_{clip}.png")

# Fly v5 vs v6 fan pair (rows alternate v5/v6 at matched frames)
f5, f6 = rep.get("A_Sir_Fly_Loop_v5_ARP"), rep.get("A_Sir_Fly_Loop_v6_ARP")
if f5 and f6 and f5.get("status") == "DONE" and f6.get("status") == "DONE":
    shots = []
    for a, b in zip(f5["shots"], f6["shots"]):
        shots.append({"path": a["path"], "label": f"v5 f{a['frame']:03d}"})
        shots.append({"path": b["path"], "label": f"v6 f{b['frame']:03d}"})
    sheet(shots, "Fly v5 vs v6 — feather-fan read",
          "odd rows v5, even rows v6 (matched frames; fan = twist/spread, head-travel identical per probe)",
          CONTACT / "sheet_Fly_v5_vs_v6.png")
print("done")
