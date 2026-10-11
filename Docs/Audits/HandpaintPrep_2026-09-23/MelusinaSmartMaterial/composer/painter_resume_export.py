"""Melodia Composer — resume export pass on the already-built session.

The first run (2026-10-10) built SMS stack + 16_Composer variants inside the
open Mr. Sheep project, then died on an export API mismatch. This module
finishes THAT session: toggles each variant's visibility with the layerstack
API, exports the composed texture set per variant, restores state, saves the
project. NO rebuild — build_sms must not run twice (duplicate stack).

Injected via:
    G = {}
    exec(compile(open(FILE, encoding='utf-8').read(), FILE, 'exec'), G)
    G['resume'](composer_json, exports_dir, project_path, log_path)

Findings baked in (Painter 11.1.1, python API 0.3.5):
  - layerstack.get_root_layer_nodes(stack); Node.get_name()/set_visible();
    GroupLayerNode.sub_layers = children.
  - Export = JSON dict: exportPath (dir) + defaultExportPreset (resource URL)
    + exportList[{"rootPath": <TextureSetName>}] + exportParameters with
    paddingAlgorithm:"infinite" REQUIRED, sizeLog2 11 = 2K.

Melodia / Melusina only. No Grok*.
"""
import json
import os
import time
import traceback

LOG_PATH = None


def _log(path, msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def _node_name(node):
    g = getattr(node, "get_name", None)
    try:
        n = g() if callable(g) else None
    except Exception:
        n = None
    return n or str(node)


def _set_visible(node, on, log):
    sv = getattr(node, "set_visible", None)
    if callable(sv):
        try:
            sv(bool(on))
        except Exception as e:
            log("  set_visible(%s) failed: %r" % (on, e))
    iv = getattr(node, "is_visible", None)
    try:
        return iv() if callable(iv) else None
    except Exception:
        return None


def _children(node):
    sl = getattr(node, "sub_layers", None)
    try:
        return list(sl() if callable(sl) else sl)
    except Exception:
        return []


def resume(composer_json, exports_dir, project_path, log_path=None):
    log_path = log_path or os.path.join(os.path.dirname(composer_json),
                                        "resume.log")
    report = {"ok": False, "exports": {}}
    try:
        import substance_painter.project as spj
        import substance_painter.textureset as ts
        import substance_painter.layerstack as ls
        import substance_painter.export as ex
        import substance_painter.resource as res

        def log(m):
            _log(log_path, m)

        log("=== resume export start ===")

        body = None
        for t in ts.all_texture_sets():
            if _node_name(t) == "IDMAP_Sheep_Body":
                body = t
        if body is None:
            raise RuntimeError("IDMAP_Sheep_Body texture set not found")
        st = body.get_stack()
        comp = None
        for r in ls.get_root_layer_nodes(st):
            if _node_name(r) == "16_Composer":
                comp = r
        if comp is None:
            raise RuntimeError("16_Composer group not found in stack")

        groups = {}
        washes = {}
        for k in _children(comp):
            nm = _node_name(k)
            log("  child: %s" % nm)
            if nm.startswith("16_") and nm.endswith("_Wash"):
                washes[nm[3:-5]] = k
            elif nm.startswith("16_") and nm != "16_Composer":
                groups[nm[3:]] = k

        cfg = json.load(open(composer_json, encoding="utf-8"))
        names = [v["name"] for v in cfg["variants"]]
        log("variants: %s" % names)
        log("groups: %s | washes: %s" % (sorted(groups), sorted(washes)))

        preset_url = None
        for p in ex.list_resource_export_presets():
            rid = getattr(p, "resource_id", None)
            rid = rid() if callable(rid) else rid
            a = getattr(rid, "name", None)
            nm = a() if callable(a) else str(a)
            if nm == "PBR Metallic Roughness":
                u = getattr(rid, "url", None)
                preset_url = u() if callable(u) else u
                break
        if not preset_url:
            preset_url = res.ResourceID(context="starter_assets",
                                        name="PBR Metallic Roughness").url()
        log("preset: %s" % preset_url)

        os.makedirs(exports_dir, exist_ok=True)
        for name in names:
            for other in names:
                on = (other == name)
                for d in (groups, washes):
                    node = d.get(other)
                    if node is not None:
                        vis = _set_visible(node, on, log)
                        if other == name:
                            log("  toggle %s visible=%s" % (other, vis))
            outd = os.path.join(exports_dir, name)
            os.makedirs(outd, exist_ok=True)
            econfig = {
                "exportShaderParams": False,
                "exportPath": outd.replace("\\", "/"),
                "defaultExportPreset": preset_url,
                "exportList": [{"rootPath": "IDMAP_Sheep_Body"}],
                "exportParameters": [{"parameters": {
                    "fileFormat": "png", "bitDepth": "8", "sizeLog2": 11,
                    "paddingAlgorithm": "infinite"}}],
            }
            t0 = time.time()
            r = ex.export_project_textures(econfig)
            status = str(getattr(r, "status", "?"))
            files = sorted(os.listdir(outd))
            report["exports"][name] = {"status": status, "files": len(files),
                                       "secs": round(time.time() - t0, 1),
                                       "sample": files[:3]}
            log("export %s: %s, %d files (%.1fs)"
                % (name, status, len(files), time.time() - t0))

        # restore: all off, then Verse on so the project browses composed
        for name in names:
            for d in (groups, washes):
                node = d.get(name)
                if node is not None:
                    _set_visible(node, False, log)
        for d in (groups, washes):
            node = d.get("Verse")
            if node is not None:
                _set_visible(node, True, log)
        log("state restored: Verse visible, others off")

        try:
            spj.save_as(project_path)
            report["saved"] = project_path
            log("saved: %s" % project_path)
        except Exception as e:
            report["save_err"] = repr(e)[:200]
            log("save failed: %r" % e)

        report["ok"] = True
    except Exception as e:
        report["error"] = repr(e)
        _log(log_path, "FATAL: " + traceback.format_exc())

    rep_path = os.path.join(os.path.dirname(log_path), "resume_report.json")
    try:
        with open(rep_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, default=str)
    except Exception:
        pass
    return report
