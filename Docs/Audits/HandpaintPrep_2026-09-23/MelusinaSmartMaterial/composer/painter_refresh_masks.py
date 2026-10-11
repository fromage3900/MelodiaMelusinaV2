"""Refresh Mr. Sheep composer score masks (v2, shared pitch axis) + re-export.

Deletes the 16_* variant nodes, re-imports the new mask set, re-inserts
(engrave now tries the score as a BITMAP SOURCE on the Height channel),
toggles per variant, exports, restores, saves.

Deleted nodes are gone for good — deletion is verified before inserting.

Injected via:
    G = {}
    exec(compile(open(FILE, encoding='utf-8').read(), FILE, 'exec'), G)
    G['refresh'](composer_json, exports_dir, project_path, log_path)

Melodia / Melusina only. No Grok*.
"""
import json
import os
import sys
import time
import traceback

SMS_ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\Docs\Audits\HandpaintPrep_2026-09-23\MelusinaSmartMaterial"
SMS_PLUGINS = os.path.join(SMS_ROOT, "painter_plugins")


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


def _children(node):
    sl = getattr(node, "sub_layers", None)
    try:
        return list(sl() if callable(sl) else sl)
    except Exception:
        return []


def get_sms():
    if SMS_PLUGINS not in sys.path:
        sys.path.insert(0, SMS_PLUGINS)
    import melodia_build_sms_handpaint as m
    return m


def refresh(composer_json, exports_dir, project_path, log_path=None):
    log_path = log_path or os.path.join(os.path.dirname(composer_json),
                                        "painter_run.log")
    report = {"ok": False, "deleted": [], "exports": {}}
    try:
        import substance_painter.project as spj
        import substance_painter.textureset as ts
        import substance_painter.layerstack as ls
        import substance_painter.export as ex
        import substance_painter.resource as spresource

        def log(m):
            _log(log_path, m)

        m = get_sms()
        log("=== mask refresh start ===")

        cfg = json.load(open(composer_json, encoding="utf-8"))
        names = [v["name"] for v in cfg["variants"]]
        params = {v["name"]: v["params"] for v in cfg["variants"]}
        masks = {v["name"]: v["score_mask_png"] for v in cfg["variants"]}

        body = None
        for t in ts.all_texture_sets():
            if _node_name(t) == "IDMAP_Sheep_Body":
                body = t
        if body is None:
            raise RuntimeError("IDMAP_Sheep_Body not found")
        st = body.get_stack()
        comp = None
        for r in ls.get_root_layer_nodes(st):
            if _node_name(r) == "16_Composer":
                comp = r
        if comp is None:
            raise RuntimeError("16_Composer not found")
        comp.set_visible(True)

        # --- delete old variant nodes ------------------------------------
        olds = [k for k in _children(comp) if _node_name(k).startswith("16_")]
        for k in olds:
            nm = _node_name(k)
            try:
                ls.delete_node(k)
                report["deleted"].append(nm)
                log("deleted %s" % nm)
            except Exception as e:
                log("DELETE FAILED %s: %r" % (nm, e))
        left = [_node_name(k) for k in _children(comp)]
        report["left_after_delete"] = left
        if left:
            raise RuntimeError("nodes remain after delete: %s" % left)

        # --- import new masks ---------------------------------------------
        usage = m.resolve_usage()
        rids = {}
        for name in names:
            p = masks[name]
            r = spresource.import_project_resource(
                p, usage, name="Melodia_Score2_%s" % name,
                group="Melodia Composer Scores")
            rids[name] = r.identifier()
            log("imported mask %s" % name)

        # --- insert new set -------------------------------------------------
        bc = m._chan("BaseColor")
        emiss = m._chan("Emissive") or m._chan("Emission")
        height = m._chan("Height")
        log("channels bc=%s emiss=%s height=%s" % (
            bc is not None, emiss is not None, height is not None))

        for name in names:
            prm = params[name]
            vg = splayers_insert = None
            import substance_painter.layerstack as splayers
            vg = splayers.insert_group(m._inside_group(comp))
            m._set_name(vg, "16_%s" % name)
            vg.add_mask(splayers.MaskBackground.Black)
            mask_fill = splayers.insert_fill(m._inside_mask(vg))
            m._set_name(mask_fill, "16_%s_scoreMask" % name)
            m._try_mask_bitmap(mask_fill, rids[name], "16_%s" % name)

            glow = splayers.insert_fill(m._inside_group(vg))
            m._set_name(glow, "16_%s_ScoreGlow" % name)
            if emiss:
                m._set_fill_color(glow, emiss, tuple(prm["accent"]))
                m._set_blend(glow, "Add", emiss)
            m._set_opacity(glow, prm["score_glow_op"])

            tint = splayers.insert_fill(m._inside_group(vg))
            m._set_name(tint, "16_%s_ScoreTint" % name)
            if bc:
                m._set_fill_color(tint, bc, (0.62, 0.42, 0.27))
                m._set_blend(tint, "Multiply", bc)
            m._set_opacity(tint, float(prm.get("tint_op", 0.22)))

            eng = splayers.insert_fill(m._inside_group(vg))
            m._set_name(eng, "16_%s_ScoreEngrave" % name)
            okb = False
            if height:
                okb = m._set_fill_bitmap(eng, height, rids[name])
            if not okb and height:
                m._set_fill_color(eng, height, (0.62, 0.62, 0.62))
            m._set_opacity(eng, 0.8 if okb else prm["score_engrave_op"])
            report.setdefault("engrave_bitmap", {})[name] = bool(okb)

            wash = splayers.insert_fill(m._inside_group(comp))
            m._set_name(wash, "16_%s_Wash" % name)
            if bc:
                m._set_fill_color(wash, bc, tuple(prm["score_tint"]))
                m._set_blend(wash, "SoftLight", bc)
            wash_op = float(prm.get(
                "wash_op",
                0.10 + 0.18 * min(1.0, float(prm["decoration_intensity"]))))
            m._set_opacity(wash, round(wash_op, 3))
            log("wired %s (engrave_bitmap=%s)" % (name, okb))

        # --- toggle + export -------------------------------------------------
        groups = {}
        washes = {}
        for k in _children(comp):
            nm = _node_name(k)
            if nm.startswith("16_") and nm.endswith("_Wash"):
                washes[nm[3:-5]] = k
            elif nm.startswith("16_"):
                groups[nm[3:]] = k

        preset = None
        for p in ex.list_resource_export_presets():
            rid = getattr(p, "resource_id", None)
            rid = rid() if callable(rid) else rid
            a = getattr(rid, "name", None)
            nm = a() if callable(a) else str(a)
            if nm == "PBR Metallic Roughness":
                u = getattr(rid, "url", None)
                preset = u() if callable(u) else u
                break

        os.makedirs(exports_dir, exist_ok=True)
        for name in names:
            for other in names:
                on = (other == name)
                for d in (groups, washes):
                    node = d.get(other)
                    if node is not None:
                        node.set_visible(on)
            outd = os.path.join(exports_dir, name)
            os.makedirs(outd, exist_ok=True)
            econfig = {
                "exportShaderParams": False,
                "exportPath": outd.replace("\\", "/"),
                "defaultExportPreset": preset,
                "exportList": [{"rootPath": "IDMAP_Sheep_Body"}],
                "exportParameters": [{"parameters": {
                    "fileFormat": "png", "bitDepth": "8", "sizeLog2": 11,
                    "paddingAlgorithm": "infinite"}}],
            }
            t0 = time.time()
            r = ex.export_project_textures(econfig)
            outd_files = sorted(os.listdir(outd))
            report["exports"][name] = {
                "status": str(getattr(r, "status", "?")),
                "n": len(outd_files),
                "secs": round(time.time() - t0, 1)}
            log("export %s: %s (%d files, %.1fs)" % (
                name, report["exports"][name]["status"], len(outd_files),
                report["exports"][name]["secs"]))

        for name in names:
            for d in (groups, washes):
                node = d.get(name)
                if node is not None:
                    node.set_visible(False)
        for d in (groups, washes):
            node = d.get("Verse")
            if node is not None:
                node.set_visible(True)
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

    rep_path = os.path.join(os.path.dirname(log_path), "mask_refresh_report.json")
    try:
        with open(rep_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, default=str)
    except Exception:
        pass
    return report
