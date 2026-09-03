"""Searchable asset catalog: Saved/Audit/asset_catalog.json + asset_catalog.html.

Kills file-hunting: one self-contained HTML page with filter-as-you-type search
over every /Game asset (name, class, folder, parent master for MIs). Regenerate
after any reorg:  py Content/Python/run.py catalog   (in-editor).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[2] / "Saved" / "Audit"
SKIP_PREFIXES = ("/Game/__", "/Game/Developers")


def collect() -> list[dict]:
    import unreal

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path("/Game", recursive=True) or []
    rows: list[dict] = []
    for a in assets:
        pkg = str(a.package_name)
        if pkg.startswith(SKIP_PREFIXES):
            continue
        cls = str(a.asset_class_path.asset_name)
        if cls == "ObjectRedirector":
            continue
        row = {
            "name": str(a.asset_name),
            "class": cls,
            "path": pkg,
            "root": pkg.split("/")[2] if pkg.count("/") >= 2 else "",
        }
        if cls == "MaterialInstanceConstant":
            try:
                parent = a.get_tag_value("Parent")
                if parent:
                    row["parent"] = str(parent).rsplit(".", 1)[-1].rstrip("'\"")
            except Exception:  # noqa: BLE001
                pass
        rows.append(row)
    return rows


HTML = """<!doctype html><meta charset="utf-8"><title>BS_GodFile Asset Catalog</title>
<style>
body{{font:13px/1.5 system-ui;margin:20px;background:#0d1224;color:#eceaf4}}
input{{width:100%;padding:10px;font-size:15px;background:#1a1f3a;color:#eceaf4;border:1px solid #444;border-radius:6px}}
table{{border-collapse:collapse;width:100%;margin-top:12px}}
td,th{{padding:3px 10px;text-align:left;border-bottom:1px solid #2a3055;white-space:nowrap}}
th{{color:#66d9ff;position:sticky;top:0;background:#0d1224}}
.c{{color:#cc99ff}} .p{{color:#8a87a0;font-size:11px}} .badge{{color:#ffe666}}
#n{{color:#8a87a0;margin:8px 0}}
</style>
<h2>BS_GodFile Asset Catalog <span class="p">generated {ts} — {count} assets</span></h2>
<input id="q" placeholder="type to filter: name, class, folder… (space-separated terms AND)" autofocus>
<div id="n"></div>
<table><thead><tr><th>Name</th><th>Class</th><th>Root</th><th>Parent</th><th>Path</th></tr></thead><tbody id="t"></tbody></table>
<script>
const D={data};
const t=document.getElementById('t'),q=document.getElementById('q'),n=document.getElementById('n');
function render(rows){{t.innerHTML=rows.slice(0,800).map(r=>`<tr><td>${{r.name}}</td><td class="c">${{r.class}}</td><td class="badge">${{r.root}}</td><td class="p">${{r.parent||''}}</td><td class="p">${{r.path}}</td></tr>`).join('');n.textContent=rows.length+' match'+(rows.length===1?'':'es')+(rows.length>800?' (showing 800)':'');}}
q.addEventListener('input',()=>{{const terms=q.value.toLowerCase().split(/\\s+/).filter(Boolean);render(terms.length?D.filter(r=>{{const s=(r.name+' '+r.class+' '+r.path+' '+(r.parent||'')).toLowerCase();return terms.every(x=>s.includes(x));}}):D);}});
render(D);
</script>"""


def main() -> dict:
    rows = collect()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (OUT_DIR / "asset_catalog.json").write_text(json.dumps(rows), encoding="utf-8")
    html = HTML.format(ts=ts, count=len(rows), data=json.dumps(rows))
    (OUT_DIR / "asset_catalog.html").write_text(html, encoding="utf-8")
    return {"assets": len(rows), "html": str(OUT_DIR / "asset_catalog.html")}
