import os, json
from playwright.sync_api import sync_playwright

OUT = "/home/ubuntu/melodia-design-system/psd_layers"
os.makedirs(OUT, exist_ok=True)
URL = "file:///home/ubuntu/melodia-design-system/psd.html"

STAGES = {
    "constellation": (1440, 900, ["bg", "atmosphere", "brandmark", "headline", "passport"]),
    "nebula":        (1440, 900, ["bg", "atmosphere", "brandmark", "headline", "passport"]),
    "ornate":        (1440, 900, ["bg", "atmosphere", "brandmark", "headline"]),
    "ivory":         (1440, 900, ["bg", "atmosphere", "brandmark", "headline", "passport"]),
    "passport-dark": (420, 600, ["passport"]),
    "passport-light":(420, 600, ["passport"]),
}

manifest = {}
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:29229")
    ctx = b.contexts[0] if b.contexts else b.new_context()
    pg = ctx.new_page()
    pg.set_viewport_size({"width": 1500, "height": 1000})
    for stage, (w, h, layers) in STAGES.items():
        manifest[stage] = {"w": w, "h": h, "layers": [], "composite": None}
        # composite (all layers)
        pg.goto(URL + "?stage=%s&layer=all" % stage)
        pg.wait_for_function("window.__ready===true")
        pg.evaluate("async()=>{await document.fonts.ready;}")
        pg.wait_for_timeout(700)
        comp = os.path.join(OUT, "%s__all.png" % stage)
        pg.locator("#stage-%s" % stage).screenshot(path=comp, omit_background=True)
        manifest[stage]["composite"] = comp
        # individual layers
        for ly in layers:
            pg.goto(URL + "?stage=%s&layer=%s" % (stage, ly))
            pg.wait_for_function("window.__ready===true")
            pg.evaluate("async()=>{await document.fonts.ready;}")
            pg.wait_for_timeout(500)
            fp = os.path.join(OUT, "%s__%s.png" % (stage, ly))
            pg.locator("#stage-%s" % stage).screenshot(path=fp, omit_background=True)
            manifest[stage]["layers"].append({"name": ly, "file": fp})
        print("rendered", stage)
    pg.close()

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
print("manifest written")
