"""Calibration probe #2: is the white BaseColor the paint or the bitmap?

Melodia / Melusina only. No Grok*.

Inserts a magenta fill at the top of SMS2_Core, exports IDMAP_Sheep_Body
to the scratch dir, then removes the probe fill. Also introspects the
ramp resource (retrieve/usages) to see what pixels the import stored.
Magenta in the export -> painting works, bitmap content is the suspect.
Still white -> something above the fills overrides the export.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from painter_remote import RemotePainter  # noqa: E402

SMS = os.path.dirname(HERE)
EXPORTS = os.path.join(SMS, "exports", "MrSheep", "_test_cal2").replace("\\", "/")
PLUGIN_DIR = os.path.join(SMS, "painter_plugins").replace("\\", "/")

code = '''
import json, os, time, sys
import substance_painter.project as spj
import substance_painter.export as ex
import substance_painter.layerstack as ls
import substance_painter.textureset as ts
import substance_painter.resource as spres
import importlib
if PLUGIN_DIR_LIT not in sys.path:
    sys.path.insert(0, PLUGIN_DIR_LIT)
import melodia_build_sms_handpaint as m
m = importlib.reload(m)
out = {}
def nm(n):
    for a in ("get_name", "name"):
        v = getattr(n, a, None)
        try:
            v = v() if callable(v) else v
            if v:
                return str(v)
        except Exception:
            pass
    return "?"
body = None
for t in ts.all_texture_sets():
    if str(t.name()) == "IDMAP_Sheep_Body":
        body = t
stack = body.get_stack()

# --- introspect the ramp resource (what did the import store?) ---
ramp = None
core = None
for r in ls.get_root_layer_nodes(stack):
    if nm(r) == "SMS2_Core":
        core = r
        for k in r.sub_layers():
            if nm(k) == "S2_Base_Ramp":
                ramp = k
if ramp is not None:
    src = ramp.get_source(ls.ChannelType.BaseColor)
    rid = getattr(src, "resource_id", None)
    rid = rid() if callable(rid) else rid
    res = spres.Resource(rid)
    for prop in ("type", "category", "location", "internal_properties",
                 "usages", "tags"):
        try:
            v = getattr(res, prop)
            v = v() if callable(v) else v
            out["res_" + prop] = str(v)[:200]
        except Exception as e:
            out["res_" + prop + "_err"] = repr(e)[:80]
    try:
        data = res.retrieve()
        out["retrieve_type"] = str(type(data).__name__)
        try:
            out["retrieve_len"] = len(data)
        except Exception:
            pass
        try:
            import numpy as np
            arr = np.asarray(data)
            out["retrieve_shape"] = list(arr.shape)
            if arr.ndim >= 2:
                flat = arr.reshape(-1, arr.shape[-1]) if arr.ndim == 3 else arr.reshape(-1)
                out["retrieve_mean"] = [round(float(x), 1) for x in flat.mean(0)]
        except Exception as e:
            out["retrieve_np_err"] = repr(e)[:100]
    except Exception as e:
        out["retrieve_err"] = repr(e)[:160]

# --- magenta probe fill inside SMS2_Core (plugin helpers, as the runner) ---
bc = m._chan("BaseColor")
cal = ls.insert_fill(m._inside_group(core))
m._set_name(cal, "ZZ_Cal2")
ok = m._set_fill_color(cal, bc, (1.0, 0.0, 1.0))
out["cal_set"] = bool(ok)
try:
    out["cal_active"] = [str(c) for c in cal.active_channels]
except Exception as e:
    out["cal_active_err"] = repr(e)[:80]

os.makedirs(EXPORTS_DIR_LIT, exist_ok=True)
cfg_base = {
    "exportShaderParams": False,
    "exportPath": EXPORTS_DIR_LIT,
    "exportList": [{"rootPath": "IDMAP_Sheep_Body"}],
    "exportParameters": [{"parameters": {
        "fileFormat": "png", "bitDepth": "8", "sizeLog2": 11,
        "paddingAlgorithm": "infinite"}}],
}
cfg_plain = dict(cfg_base, defaultExportPreset=
                 "resource://starter_assets/PBR Metallic Roughness"
                 "?version=12212909757578709068.spexp")
try:
    t0 = time.time()
    r = ex.export_project_textures(cfg_plain)
    out["export"] = {"status": str(getattr(r, "status", "?")),
                     "secs": round(time.time() - t0, 1)}
except Exception as e:
    out["export"] = "FAILED: " + repr(e)[:250]

# remove the probe fill
try:
    ls.delete_node(cal)
    out["cal_removed"] = True
except Exception as e:
    out["cal_removed"] = repr(e)[:120]

files = []
for f in sorted(os.listdir(EXPORTS_DIR_LIT)):
    fp = os.path.join(EXPORTS_DIR_LIT, f)
    if os.path.isfile(fp):
        files.append(f + ":" + str(os.path.getsize(fp)))
out["files"] = files
raise Exception("PROBE:" + json.dumps(out, default=str))
'''
code = code.replace("EXPORTS_DIR_LIT", json.dumps(EXPORTS))
code = code.replace("PLUGIN_DIR_LIT", json.dumps(PLUGIN_DIR))


def main():
    rp = RemotePainter()
    if not rp.wait_ready(timeout=20):
        print("FAIL: wire not ready")
        return 1
    try:
        rp.exec_python(code)
        print("clean return (no payload)")
        return 0
    except Exception as e:
        msg = str(e)
        if "PROBE:" in msg:
            rest = msg.split("PROBE:", 1)[1].strip()
            for attempt in (rest, rest.replace("\\'", "'")):
                try:
                    val, _ = json.JSONDecoder().raw_decode(attempt)
                    print(json.dumps(val, indent=1))
                    return 0
                except Exception:
                    continue
            print("RAW:", rest[:2200])
            return 0
        print("ERR:", msg[:900])
        return 1


if __name__ == "__main__":
    sys.exit(main())
