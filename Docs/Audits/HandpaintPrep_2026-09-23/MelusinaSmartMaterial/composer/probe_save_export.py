"""Save-then-export probe: does a full project save flush the texture cache?

Melodia / Melusina only. No Grok*.

Context: exports after scripted stack changes come back white/zeroed
(BaseColor white, Metallic/Emissive 0) even though every fill has its
source bound and Painter reports is_busy() == False. Hypothesis: the
export reads the texture cache before a full project save flushes it.
This probe saves the project, then exports one texture set with the
default PBR preset, to a scratch dir, and reports file sizes.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from painter_remote import RemotePainter  # noqa: E402

SMS = os.path.dirname(HERE)
EXPORTS = os.path.join(SMS, "exports", "MrSheep", "_test_save_export").replace("\\", "/")

code = '''
import json, os, time
import substance_painter.project as spj
import substance_painter.export as spe
import substance_painter.layerstack as ls
out = {}
try:
    t0 = time.time()
    spj.save()
    out["saved"] = round(time.time() - t0, 1)
except Exception as e:
    out["save_err"] = repr(e)[:200]

# runner-style preset lookup: resource presets saved in the project
preset = None
pbr_url = None
for p in spe.list_resource_export_presets():
    r = getattr(p, "resource_id", None)
    r = r() if callable(r) else r
    a = getattr(r, "name", None)
    nm = a() if callable(a) else str(a)
    if nm == "PBR Metallic Roughness":
        u = getattr(r, "url", None)
        pbr_url = u() if callable(u) else u
        preset = p
        break
out["preset_found"] = bool(preset)
out["pbr_url"] = str(pbr_url)[:90]

def docmap(label, scalar=False):
    chans = [("R", "R", label)]
    if not scalar:
        chans += [("G", "G", label), ("B", "B", label)]
    return {
        "channels": [{"destChannel": d, "srcChannel": s,
                      "srcMapName": n, "srcMapType": "documentMap",
                      "srcPath": ""} for d, s, n in chans],
        "fileName": "$textureSet_%s_$udim" % label,
        "parameters": {"bitDepth": "8", "dithering": False,
                       "fileFormat": "png"}}

maps = preset.list_output_maps() if preset else []
extra = []
if hasattr(ls.ChannelType, "CoatColor"):
    extra += [docmap("CoatColor"), docmap("CoatOpacity", True),
              docmap("CoatRoughness", True)]
if hasattr(ls.ChannelType, "SheenColor"):
    extra += [docmap("SheenColor"), docmap("SheenOpacity", True)]
if hasattr(ls.ChannelType, "SpecularEdgeColor"):
    extra += [docmap("SpecularEdgeColor")]
new_name = "SMS2 Pilot (PBR MR + iridescence)"

os.makedirs(EXPORTS_DIR_LIT, exist_ok=True)
cfg_base = {
    "exportShaderParams": False,
    "exportPath": EXPORTS_DIR_LIT,
    "exportList": [{"rootPath": "IDMAP_Sheep_Body"}],
    "exportParameters": [{"parameters": {
        "fileFormat": "png", "bitDepth": "8", "sizeLog2": 11,
        "paddingAlgorithm": "infinite"}}],
}
attempts = []
if extra:
    cfg_rich = dict(cfg_base, defaultExportPreset=new_name,
                    exportPresets=[{"name": new_name, "maps": maps + extra}])
    attempts.append(("rich", cfg_rich))
cfg_plain = dict(cfg_base, defaultExportPreset=pbr_url)
attempts.append(("plain", cfg_plain))
for tag, conf in attempts:
    try:
        t0 = time.time()
        r = spe.export_project_textures(conf)
        n_files = len(os.listdir(EXPORTS_DIR_LIT))
        out[tag] = {"status": str(getattr(r, "status", "?")),
                    "n": n_files, "secs": round(time.time() - t0, 1)}
        break
    except Exception as e:
        out[tag] = "FAILED: " + repr(e)[:200]

files = []
for f in sorted(os.listdir(EXPORTS_DIR_LIT)):
    fp = os.path.join(EXPORTS_DIR_LIT, f)
    if os.path.isfile(fp):
        files.append(f + ":" + str(os.path.getsize(fp)))
out["files"] = files
raise Exception("PROBE:" + json.dumps(out, default=str))
'''
code = code.replace("EXPORTS_DIR_LIT", json.dumps(EXPORTS))


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
            print("RAW:", rest[:1500])
            return 0
        print("ERR:", msg[:900])
        return 1


if __name__ == "__main__":
    sys.exit(main())
