"""Melodia Composer — Mr. Sheep run: SMS stack + score variants + exports.

This file is injected into Substance 3D Painter 11.x over remote scripting.
It is NOT imported by normal Python (it needs the substance_painter modules).

Usage from the orchestrator (painter survives, no UI clicks):
    exec(compile(open(RUNNER).read(), RUNNER, 'exec'))
    ensure_project(mesh, 2048, log)
    ... bake via alg.baking JS (orchestrator) ...
    rep = run_job(composer_json, exports_dir, project_path, log_path)

Everything is fail-soft per phase; the report + log land under
SMS/composer/out/ so the orchestrator can read them from disk.

Melodia / Melusina naming only. No Grok*.
"""
import json
import os
import sys
import time
import traceback

SMS_ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\Docs\Audits\HandpaintPrep_2026-09-23\MelusinaSmartMaterial"


class Log:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.fh = open(path, "a", encoding="utf-8", buffering=1)

    def __call__(self, msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        try:
            print(line, flush=True)
        except Exception:
            pass
        self.fh.write(line + "\n")
        self.fh.flush()


def get_sms():
    plug = os.path.join(SMS_ROOT, "painter_plugins")
    if plug not in sys.path:
        sys.path.insert(0, plug)
    import melodia_build_sms_handpaint as m
    return m


def ensure_project(mesh_path, res=2048, log_path=None):
    """Create the project from the sheep mesh if none is open. Returns state."""
    log = Log(log_path or os.path.join(SMS_ROOT, "composer", "out",
                                       "painter_run.log"))
    import substance_painter.project as spproject
    if spproject.is_open():
        log("project already open - waiting for edition state")
    else:
        log("creating project from %s" % mesh_path)
        try:
            settings = spproject.Settings(
                import_cameras=False,
                normal_map_format=spproject.NormalMapFormat.OpenGL,
                default_texture_resolution=res)
        except Exception:
            settings = spproject.Settings()
            try:
                settings.normal_map_format = spproject.NormalMapFormat.OpenGL
                settings.default_texture_resolution = res
            except Exception:
                pass
        spproject.create(mesh_file_path=mesh_path, settings=settings)
    for i in range(72):
        try:
            if spproject.is_in_edition_state():
                log("edition state ready (%ss)" % (i * 5))
                return "edition"
        except Exception:
            pass
        time.sleep(5)
    log("TIMEOUT waiting for edition state")
    return "timeout"


def _set_node_vis(m, node, on, log):
    """Best-effort enable/disable one composer variant folder."""
    if node is None:
        return False
    done = False
    fn = getattr(node, "set_visible", None)
    if callable(fn):
        try:
            fn(bool(on))
            done = True
        except Exception as e:
            log("set_visible failed: %s" % e)
    try:
        if m._set_opacity(node, 1.0 if on else 0.0):
            done = True
    except Exception as e:
        log("opacity toggle failed: %s" % e)
    return done


def run_job(composer_json, exports_dir, project_path, log_path=None,
            phase_note=""):
    log = Log(log_path or os.path.join(SMS_ROOT, "composer", "out",
                                       "painter_run.log"))
    report = {"ok": False, "exports": {}, "phases": [], "notes": []}
    try:
        import substance_painter as sp
        import substance_painter.project as spproject
        import substance_painter.textureset as sptextureset
        import substance_painter.layerstack as splayers
        import substance_painter.resource as spresource
        import substance_painter.export as spexport

        m = get_sms()
        log("=== composer job start %s ===" % phase_note)
        try:
            log("substance_painter %s" % sp.__version__)
        except Exception:
            pass

        cfg = json.load(open(composer_json, encoding="utf-8"))
        variants = cfg["variants"]
        log("theme=%s notes=%s variants=%s" %
            (cfg.get("theme"), cfg.get("note_count"), len(variants)))

        if not spproject.is_open():
            raise RuntimeError("no project open")
        try:
            if not spproject.is_in_edition_state():
                raise RuntimeError("project not in edition state")
        except RuntimeError:
            raise
        except Exception:
            pass

        stack = sptextureset.get_active_stack()
        log("active stack: %s" % (stack,))

        # ---- 1. base SMS stack -------------------------------------------
        t0 = time.time()
        okbuild = m.build_sms(create_project_if_needed=False)
        log("build_sms -> %s (%.1fs)" % (okbuild, time.time() - t0))
        if not okbuild:
            raise RuntimeError("build_sms returned False")
        report["phases"].append("stack")

        # ---- 2. import score masks ---------------------------------------
        usage = m.resolve_usage()
        score_rids = {}
        for v in variants:
            p = v["score_mask_png"]
            if not os.path.isfile(p):
                log("score mask missing: %s" % p)
                continue
            try:
                r = spresource.import_project_resource(
                    p, usage, name="Melodia_Score_%s" % v["name"],
                    group="Melodia Composer Scores")
                score_rids[v["name"]] = r.identifier()
            except Exception as e:
                log("score import failed for %s: %s" % (v["name"], e))
        log("score masks imported: %s" % sorted(score_rids))
        report["phases"].append("resources")

        # ---- 3. composer group on top of the stack -----------------------
        bc = m._chan("BaseColor")
        emiss = m._chan("Emissive") or m._chan("Emission")
        height = m._chan("Height")

        top = splayers.InsertPosition.from_textureset_stack(stack)
        croot = splayers.insert_group(top)
        m._set_name(croot, "16_Composer")
        log("composer group inserted on top")

        variant_nodes = {}
        for v in variants:
            name = v["name"]
            prm = v["params"]
            vg = splayers.insert_group(m._inside_group(croot))
            m._set_name(vg, "16_%s" % name)
            # folder mask = the variant's score map -> children live on the notes
            try:
                vg.add_mask(splayers.MaskBackground.Black)
                mask_fill = splayers.insert_fill(m._inside_mask(vg))
                m._set_name(mask_fill, "16_%s_scoreMask" % name)
                rid = score_rids.get(name)
                if rid:
                    m._try_mask_bitmap(mask_fill, rid, "16_%s" % name)
            except Exception as e:
                log("folder mask failed for %s: %s" % (name, e))

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
            m._set_opacity(tint, 0.22)

            eng = splayers.insert_fill(m._inside_group(vg))
            m._set_name(eng, "16_%s_ScoreEngrave" % name)
            if height:
                m._set_fill_color(eng, height, (0.62, 0.62, 0.62))
            m._set_opacity(eng, prm["score_engrave_op"])

            # full-surface wash, sibling of the masked group
            wash = splayers.insert_fill(m._inside_group(croot))
            m._set_name(wash, "16_%s_Wash" % name)
            if bc:
                m._set_fill_color(wash, bc, tuple(prm["score_tint"]))
                m._set_blend(wash, "SoftLight", bc)
            wash_op = 0.10 + 0.18 * min(1.0, float(prm["decoration_intensity"]))
            m._set_opacity(wash, round(wash_op, 3))

            variant_nodes[name] = (vg, wash)
            log("variant wired: %s (glow=%.2f eng=%.2f wash=%.2f)" % (
                name, prm["score_glow_op"], prm["score_engrave_op"], wash_op))
        report["phases"].append("composer")

        # ---- 4. export passes ---------------------------------------------
        os.makedirs(exports_dir, exist_ok=True)
        templates = spexport.list_output_templates()
        target = None
        tname = ""
        for t in templates:
            try:
                n = t.name()
            except Exception:
                continue
            if "PBR Metallic Roughness" in n:
                target, tname = t, n
                break
        if target is None:
            for t in templates:
                try:
                    n = t.name()
                except Exception:
                    continue
                if "PBR" in n:
                    target, tname = t, n
                    break
        log("export template: %r" % tname)
        if target is None:
            raise RuntimeError("no PBR export template found")

        config_cls = getattr(spexport, "TextureExportConfig", None) or \
            getattr(spexport, "ExportConfig")

        for v in variants:
            name = v["name"]
            for other, (dg, dw) in variant_nodes.items():
                on = (other == name)
                _set_node_vis(m, dg, on, log)
                _set_node_vis(m, dw, on, log)
            outd = os.path.join(exports_dir, name)
            os.makedirs(outd, exist_ok=True)
            try:
                config = config_cls()
                config.set_output_dir(outd)
                config.set_file_format(spexport.FileFormat.PNG)
                for ts in sptextureset.all_texture_sets():
                    try:
                        config.add_textureset(ts, target)
                    except TypeError:
                        config.add_textureset(ts, tname)
                t0 = time.time()
                result = spexport.export_project_textures(config)
                status = getattr(result, "status", None)
                success = (str(status).lower().endswith("success"))
                files = sorted(os.listdir(outd))
                report["exports"][name] = {
                    "ok": bool(success), "files": files,
                    "secs": round(time.time() - t0, 1)}
                log("export %s: ok=%s files=%d (%.1fs)" % (
                    name, success, len(files), time.time() - t0))
            except Exception as e:
                report["exports"][name] = {"ok": False, "error": str(e)}
                log("export %s FAILED: %s" % (name, e))
        report["phases"].append("export")

        # ---- 5. save project ----------------------------------------------
        try:
            spproject.save_as(project_path)
            report["phases"].append("save")
            log("project saved: %s" % project_path)
        except Exception as e:
            log("save_as failed: %s" % e)

        report["ok"] = True
    except Exception as e:
        report["error"] = str(e)
        log("FATAL: %s" % traceback.format_exc())

    out_dir = os.path.join(SMS_ROOT, "composer", "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "painter_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    log("=== composer job end ok=%s ===" % report["ok"])
    return report
