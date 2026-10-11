"""SMS v2 recon probe B — channels enum, fill material source, export maps.

Melodia / Melusina only. No Grok*.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from painter_remote import PainterError, RemotePainter  # noqa: E402

rp = RemotePainter()
if not rp.wait_ready(timeout=15):
    print("NOT READY")
    raise SystemExit(1)

out = {}
LS = "__import__('substance_painter.layerstack', fromlist=['x'])"
TS = "__import__('substance_painter.textureset', fromlist=['x'])"
EX = "__import__('substance_painter.export', fromlist=['x'])"

A = f"[m.name for m in {LS}.ChannelType]"
BODY = (f"[t for t in {TS}.all_texture_sets() "
        f"if t.name() == 'IDMAP_Sheep_Body'][0]")
B = f"[x for x in dir({BODY}) if not x.startswith('_')]"
C = (f"[(k.get_name(), str(k.get_type()), str(k.get_material_source()), "
     f"[x for x in dir(k.get_material_source()) if not x.startswith('_')]) "
     f"for k in [c for n in {LS}.get_root_layer_nodes({BODY}.get_stack()) "
     f"if n.get_name() == '16_Composer' for c in n.sub_layers() "
     f"if type(c).__name__ == 'FillLayerNode'][:1]]")
D = (f"[(p.name(), [str(m) for m in p.list_output_maps()]) "
     f"for p in {EX}.list_predefined_export_presets()]")

for key, expr in (("channels", A), ("textureset_api", B),
                  ("fill_repr", C), ("presets_all", D)):
    try:
        out[key] = rp.sheet(expr)
    except Exception as e:
        out[key + "_err"] = str(e)[:400]

print(json.dumps(out, indent=1, default=str))
rep = os.path.join(HERE, "out", "v2_recon_b.json")
with open(rep, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, default=str)
print("wrote", rep)
