# -*- coding: utf-8 -*-
"""Choral Sheep 12-PC albedo re-key: even chromatic wheel.
hue(PC) = (350 + PC*30) mod 360 (C=rose), value/clump/fiber luminance preserved,
saturation normalized to family mean (~0.38 pastel) so PC01 beige stops lagging.
Outputs houdini_variants_v2/ + contact sheet; originals untouched."""
import numpy as np, os, json
from PIL import Image

SRC = r"Saved/Audit/choral_sheep/houdini_variants"
DST = r"Saved/Audit/choral_sheep/houdini_variants_v2"
os.makedirs(DST, exist_ok=True)
LABELS = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]

def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); df = mx - mn
    v = mx
    s = np.where(mx > 1e-9, df / np.maximum(mx, 1e-9), 0.0)
    h = np.zeros_like(mx)
    m = df > 1e-9
    ir = (g - b) / np.maximum(df, 1e-9); ig = (b - r) / np.maximum(df, 1e-9); ib = (r - g) / np.maximum(df, 1e-9)
    h = np.where(m & (mx == r), (ir % 6.0), h)
    h = np.where(m & (mx == g) & (mx != r), ig + 2.0, h)
    h = np.where(m & (mx == b) & (mx != r) & (mx != g), ib + 4.0, h)
    h = h / 6.0 % 1.0
    return h, s, v

def hsv_to_rgb(h, s, v):
    h6 = (h * 6.0) % 6.0
    i = np.floor(h6).astype(int); f = h6 - i
    p = v * (1 - s); q = v * (1 - s * f); t = v * (1 - s * (1 - f))
    r = np.choose(i % 6, [v, q, p, p, t, v])
    g = np.choose(i % 6, [t, v, v, q, p, p])
    b = np.choose(i % 6, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)

report = {"phase": "1.3", "ok": True, "sat_target": 0.38, "before": {}, "after": {}}
for pc, lab in enumerate(LABELS):
    p = os.path.join(SRC, f"ChoralWool_PC_{lab}.png")
    a = np.array(Image.open(p).convert("RGB")).astype(float) / 255.0
    h, s, v = rgb_to_hsv(a)
    report["before"][lab] = {"hue_mean": round(float(h[(s>0.02)].mean()*360), 1) if (s>0.02).any() else None,
                             "sat_mean": round(float(s.mean()), 3)}
    hnew = ((350.0 + pc * 30.0) % 360.0) / 360.0
    h2 = np.full_like(h, hnew)
    # blend original micro-variance in (tiny jitter) to avoid posterized flat hue
    jitter = (h - h[(s > 0.02)].mean() if (s > 0.02).any() else 0) * 0.15
    h2 = (h2 + jitter) % 1.0
    # normalize saturation: keep per-px ratios, lift toward 0.38 mean
    smean = float(s.mean())
    s2 = np.clip(s * (0.38 / max(smean, 1e-6)) ** 0.6, 0.0, 0.62)
    out = hsv_to_rgb(h2, s2, v)
    out = np.clip(out * 255, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(os.path.join(DST, f"ChoralWool_PC_{lab}.png"))
    hh, ss, vv = rgb_to_hsv(out.astype(float)/255)
    report["after"][lab] = {"hue_mean": round(float(hh[(ss>0.02)].mean()*360), 1), "sat_mean": round(float(ss.mean()), 3)}

# contact sheet 4x3
thumbs = [Image.open(os.path.join(DST, f"ChoralWool_PC_{l}.png")).resize((341, 264)) for l in LABELS]
sheet = Image.new("RGB", (341*4, 264*3))
for i, t in enumerate(thumbs):
    sheet.paste(t, ((i % 4)*341, (i//4)*264))
sheet.save(os.path.join(DST, "_v2_chromatic_contact.png"))
json.dump(report, open(os.path.join(DST, "rekey_report.json"), "w"), indent=1)
print("REKEY DONE")
for l in LABELS:
    print(f"  {l:2s} hue {report['before'][l]['hue_mean']} -> {report['after'][l]['hue_mean']}  sat {report['after'][l]['sat_mean']}")
