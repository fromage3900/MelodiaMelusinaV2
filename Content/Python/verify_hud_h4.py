"""H4 verification: is the live overworld HUD showing real data or sitting empty?

Run inside the editor via Monolith run_python.

NOTE THE TRAPS THIS WORKS AROUND (both hit on 2026-09-25):
  * `UserWidget.WidgetTree` is a PROTECTED property -- reading it raises. So we
    never touch it; we walk ObjectIterator and filter by path instead.
  * `MetaSoundSource.graph` is protected the same way.
  * A "0 widgets found" result from ObjectIterator is NOT proof of absence: the
    iterator also returns CDO/template objects whose paths contain the widget
    name. Filter to the live PIE instance by requiring "WidgetTree_0".

Read-only. Touches no asset.
"""
import json

OUT = "C:/Users/froma/AppData/Local/hermes/cache/scratch/hud_data.json"
res = {}

live = None
for o in unreal.ObjectIterator():
    try:
        cn = o.get_class().get_name()
    except Exception:
        continue
    if cn == "WBP_Melodia_OverworldHUD_C" and "WidgetTree_0" in o.get_path_name():
        live = o
        break

res["found_live"] = live.get_path_name() if live else None

if live:
    for prop in ("visibility", "render_opacity"):
        try:
            res[prop] = str(live.get_editor_property(prop))
        except Exception as e:
            res[prop + "_err"] = str(e)[:60]
    for meth in ("is_in_viewport",):
        try:
            res[meth] = str(getattr(live, meth)())
        except Exception as e:
            res[meth + "_err"] = str(e)[:60]

# Every control under the LIVE widget's tree, with its current value.
texts, controls = [], []
for o in unreal.ObjectIterator():
    # get_path_name() is a STATIC taking the object in this build; the no-arg
    # form raises TypeError. Pass it explicitly.
    try:
        pn = unreal.get_path_name(o)
    except Exception:
        continue
    if "OverworldHUD" not in pn or "WidgetTree_0" not in pn:
        continue
    try:
        cn = o.get_class().get_name()
    except Exception:
        continue
    leaf = pn.split(":")[-1]
    if cn in ("TextBlock", "CommonTextBlock"):
        try:
            val = str(o.get_editor_property("Text"))
        except Exception:
            val = "?"
        texts.append({"name": leaf, "text": val[:70]})
    elif cn in ("ProgressBar", "ProgressBarBase"):
        try:
            val = str(o.get_editor_property("Percent"))
        except Exception:
            val = "?"
        controls.append({"class": cn, "name": leaf, "percent": val})
    else:
        controls.append({"class": cn, "name": leaf})

res["text_blocks"] = texts
res["controls"] = controls
res["text_count"] = len(texts)
res["control_count"] = len(controls)
res["classes_seen"] = sorted({c["class"] for c in controls} | {t.get("class", "TextBlock") for t in texts})

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2)
