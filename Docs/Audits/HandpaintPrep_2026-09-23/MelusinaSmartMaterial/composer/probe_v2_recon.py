"""SMS v2 recon probe — channels, fill capabilities, export maps, stack size.

Read-only. Answers: (1) which channels this Painter build exposes (is there
iridescence/anisotropy?), (2) what a FillLayerNode API offers (gradients?),
(3) what maps the export preset can emit, (4) how big the current stack
sprawl is per group.

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

# 1. texture-set channels
expr1 = ("[str(getattr(c, 'type', lambda: c)()) for c in "
         "__import__('substance_painter.textureset', fromlist=['x'])"
         ".active_texture_set().all_channels()]")
try:
    out["channels"] = rp.sheet(expr1)
except PainterError as e:
    out["channels_err"] = str(e)[:300]

# 2a. layerstack module surface
expr2 = ("[x for x in dir(__import__('substance_painter.layerstack', "
         "fromlist=['x'])) if not x.startswith('_')]")
try:
    out["layerstack_api"] = rp.sheet(expr2)
except PainterError as e:
    out["layerstack_err"] = str(e)[:300]

# 2b. fill node class surface (gradients? iridescence?)
expr3 = ("[x for x in dir(__import__('substance_painter.layerstack', "
         "fromlist=['x']).FillLayerNode) if not x.startswith('_')]")
try:
    out["fill_api"] = rp.sheet(expr3)
except PainterError as e:
    out["fill_err"] = str(e)[:300]

# 3. export presets: names + their exposure
expr4 = ("[(getattr(p, 'name', lambda: str(p))(), "
         "[str(m) for m in getattr(p, 'exports', lambda: [])()] "
         "if callable(getattr(p, 'exports', None)) else str(p)) for p in "
         "__import__('substance_painter.export', fromlist=['x'])"
         ".list_predefined_export_presets()]")
try:
    out["export_presets"] = rp.sheet(expr4)
except PainterError as e:
    out["preamble"] = str(e)[:200]
    expr4b = ("[getattr(p, 'name', lambda: str(p))() for p in "
              "__import__('substance_painter.export', fromlist=['x'])"
              ".list_predefined_export_presets()]")
    try:
        out["export_preset_names"] = rp.sheet(expr4b)
    except PainterError as e2:
        out["export_err"] = str(e2)[:300]

# 4. stack sprawl per texture set (roots + direct child counts)
expr5 = ("{tx.name(): [[n.get_name(), type(n).__name__, bool(n.is_visible()), "
         "len(list(n.sub_layers())) if hasattr(n, 'sub_layers') else 0] "
         "for n in __import__('substance_painter.layerstack', "
         "fromlist=['x']).get_root_layer_nodes(tx.get_stack())] for tx in "
         "__import__('substance_painter.textureset', fromlist=['x'])"
         ".all_texture_sets()}")
try:
    out["stack"] = rp.sheet(expr5)
except PainterError as e:
    out["stack_err"] = str(e)[:300]

print(json.dumps(out, indent=1, default=str))
rep = os.path.join(HERE, "out", "v2_recon.json")
with open(rep, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, default=str)
print("wrote", rep)
