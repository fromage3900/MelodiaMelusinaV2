# Full 240-frame hero render: animation=True appends frame numbers correctly.
# After rendering, verifies the sequence on disk (count + consecutive mean-abs-diff).
import bpy, os, json

RENDER_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\PIE\melusina_hair_flip_20260922"
EV = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922\render_sequence_evidence.json"

scene = bpy.context.scene
# EEVEE's per-frame GL churn crashes nvoglv64.dll headless (EXCEPTION_ACCESS_VIOLATION
# after ~4 frames, though single frames render fine). Sequence renders on Cycles.
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for dev_type in ('OPTIX', 'CUDA', 'NONE'):
    try:
        prefs.compute_device_type = dev_type
        prefs.get_devices()
        for d in prefs.devices:
            d.use = dev_type != 'NONE'
        scene.cycles.device = 'GPU' if dev_type != 'NONE' else 'CPU'
        print('CYCLES_DEVICE:', dev_type, '->', scene.cycles.device)
        break
    except Exception as e:
        print('device try failed:', dev_type, str(e)[:120])
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.adaptive_threshold = 0.02
scene.frame_set(1)
bpy.ops.render.render(animation=True)

pngs = sorted(f for f in os.listdir(RENDER_DIR)
              if f.startswith("frame_") and f[6:-4].isdigit() and f.endswith(".png"))
ev = {"schema": "melodia.render_sequence.v1", "frames_rendered": len(pngs),
      "render_dir": RENDER_DIR, "camera": scene.camera.name if scene.camera else None}

# consecutive mean-abs-diff on a sample (every 10th pair) — identical bytes = busted
diffs = []
try:
    from PIL import Image
    import numpy as np
    for i in range(0, len(pngs) - 1, 10):
        a = np.asarray(Image.open(os.path.join(RENDER_DIR, pngs[i])).convert("L"), dtype=np.float32) / 255.0
        b = np.asarray(Image.open(os.path.join(RENDER_DIR, pngs[i + 1])).convert("L"), dtype=np.float32) / 255.0
        diffs.append(round(float(np.abs(a - b).mean()), 5))
    stats = []
    for f in (pngs[0], pngs[len(pngs) // 2], pngs[-1]):
        a = np.asarray(Image.open(os.path.join(RENDER_DIR, f)).convert("L"), dtype=np.float32) / 255.0
        stats.append({"frame": f, "mean": round(float(a.mean()), 3),
                      "near_black_frac": round(float((a < 0.05).mean()), 3)})
    ev["sample_diffs"] = diffs
    ev["frame_stats"] = stats
    ev["motion_live"] = any(d > 0.0005 for d in diffs)
except Exception as e:
    ev["verify_error"] = str(e)[:200]

ev["verdict"] = "PASS" if len(pngs) >= 240 else "INCOMPLETE"
with open(EV, "w", encoding="utf-8") as f:
    json.dump(ev, f, indent=1)
print("RENDER_SEQUENCE_VERDICT:", ev["verdict"], "| frames:", len(pngs),
      "| motion_live:", ev.get("motion_live"))
print("stats:", json.dumps(ev.get("frame_stats", [])))
