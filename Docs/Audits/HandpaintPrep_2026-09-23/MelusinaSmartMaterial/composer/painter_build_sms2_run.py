"""SMS2 build — injected side (executed inside Substance Painter).

Rebuilds the Melodia musical material as a compact parameterized pair:
  SMS2_Core      — ombre ramp, edge iridescence (SpecularEdgeColor),
                   aurora coat (Coat*), sheen veil, curvature glow,
                   curvature roughness
  SMS2_Notation  — fine ink, engrave (Height bitmap), glow, BOLD readable
                   notes subgroup (ink + glow + notes-edge experiment),
                   bent-normal swell experiment
Plus it can EXTEND the export preset with the new channels (coat / sheen /
specular-edge) so the renderer sees the iridescence.

Replaces the old 12-node 16_Composer group (deleted, verified).

Melodia / Melusina only. No Grok*.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback


def _log(path, msg):
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def _children(node):
    try:
        return list(node.sub_layers())
    except Exception:
        return []


def _name(node):
    for attr in ("get_name", "name"):
        a = getattr(node, attr, None)
        if a is None:
            continue
        try:
            v = a() if callable(a) else a
            if v:
                return str(v)
        except Exception:
            continue
    return "?"


def build(composer_json, exports_dir, project_path, log_path=None,
          variant_name="Verse", save=True):
    log_path = log_path or os.path.join(os.path.dirname(composer_json),
                                        "painter_run.log")
    report = {"ok": False, "channels": {}, "deleted": [], "nodes": [],
              "exports": {}}
    try:
        # Painter's exec has no __file__ — derive roots from log_path
        # (…/composer/out/painter_run.log -> composer -> SMS root)
        composer_dir = os.path.dirname(os.path.dirname(
            os.path.abspath(log_path)))
        plugin_dir = os.path.join(os.path.dirname(composer_dir),
                                  "painter_plugins")

        import substance_painter.project as spj
        import substance_painter.layerstack as ls
        import substance_painter.export as ex
        import substance_painter.resource as spresource
        import substance_painter.textureset as spts

        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        import importlib
        import melodia_build_sms_handpaint as m
        # Painter caches modules for the session — a patched plugin on disk
        # is invisible until reloaded.
        m = importlib.reload(m)

        def log(msg):
            _log(log_path, msg)

        log("=== SMS2 build start (variant %s) ===" % variant_name)
        cfg = json.load(open(composer_json, encoding="utf-8"))
        by_name = {v["name"]: v for v in cfg["variants"]}
        if variant_name not in by_name:
            raise RuntimeError("variant %r not in composer json" % variant_name)
        V = by_name[variant_name]
        prm = V["params"]
        accent = tuple(prm["accent"])

        body = None
        for t in spts.all_texture_sets():
            if _name(t) == "IDMAP_Sheep_Body":
                body = t
        if body is None:
            raise RuntimeError("IDMAP_Sheep_Body not found")
        st = body.get_stack()
        CTs = spts.ChannelType

        # ---------------------------------------------------------- channels
        CF = spts.ChannelFormat
        want = [
            ("SpecularEdgeColor", getattr(CTs, "SpecularEdgeColor", None),
             getattr(CF, "RGB8", None)),
            ("CoatColor", getattr(CTs, "CoatColor", None),
             getattr(CF, "RGB8", None)),
            ("CoatOpacity", getattr(CTs, "CoatOpacity", None),
             getattr(CF, "L8", None)),
            ("CoatRoughness", getattr(CTs, "CoatRoughness", None),
             getattr(CF, "L8", None)),
            ("SheenColor", getattr(CTs, "SheenColor", None),
             getattr(CF, "RGB8", None)),
            ("SheenOpacity", getattr(CTs, "SheenOpacity", None),
             getattr(CF, "L8", None)),
        ]
        for nm, ct, cf in want:
            if ct is None or cf is None:
                report["channels"][nm] = "enum-missing"
                continue
            try:
                if st.has_channel(ct):
                    report["channels"][nm] = "present"
                else:
                    st.add_channel(channel_type=ct, channel_format=cf)
                    report["channels"][nm] = "added"
            except Exception as e:
                report["channels"][nm] = "FAILED: %r" % e
            log("channel %s -> %s" % (nm, report["channels"][nm]))

        def chok(nm):
            return report["channels"].get(nm, "").startswith(("added",
                                                              "present"))

        # ---------------------------------------------- delete old sprawl
        for r in list(ls.get_root_layer_nodes(st)):
            nm = _name(r)
            if nm in ("16_Composer", "SMS2_Core", "SMS2_Notation",
                      "SMS2_Hero"):
                try:
                    ls.delete_node(r)
                    report["deleted"].append(nm)
                    log("deleted %s" % nm)
                except Exception as e:
                    log("delete failed %s: %r" % (nm, e))
        roots_now = [_name(r) for r in ls.get_root_layer_nodes(st)]
        report["roots_after_delete"] = roots_now
        if "16_Composer" in roots_now:
            raise RuntimeError("16_Composer still present after delete")

        # ------------------------------------------------------ resources
        usage = m.resolve_usage()
        rid = {}
        import hashlib
        for key, label in (("mask", "ScoreMask"), ("bold", "ScoreBold"),
                           ("ramp", "Ramp"), ("iri", "Aurora"),
                           ("hero", "Hero"), ("ink", "Ink"),
                           ("glowf", "GlowFine"), ("hfine", "HFine"),
                           ("boldink", "BoldInk"), ("boldglow", "BoldGlow"),
                           ("boldglint", "BoldGlint"),
                           ("herogold", "HeroGold"),
                           ("herowglow", "HeroGlow"),
                           ("heroh", "HeroH"), ("heromet", "HeroMet"),
                           ("heroglint", "HeroGlint")):
            p = V.get({"mask": "score_mask_png", "bold": "score_bold_png",
                       "ramp": "ramp_png", "iri": "iri_png",
                       "hero": "hero_png", "ink": "ink_png",
                       "glowf": "glow_fine_png", "hfine": "h_fine_png",
                       "boldink": "bold_ink_png",
                       "boldglow": "bold_glow_png",
                       "boldglint": "bold_glint_png",
                       "herogold": "hero_gold_png",
                       "herowglow": "hero_glow_png",
                       "heroh": "hero_h_png", "heromet": "hero_met_png",
                       "heroglint": "hero_glint_png"}[key])
            if not p or not os.path.isfile(p):
                raise RuntimeError("missing canvas %s: %r" % (key, p))
            # Painter does NOT update an existing resource on re-import with
            # the same name (masks kept pointing at day-one bitmaps). Name
            # resources by CONTENT hash: changed canvas -> new resource;
            # unchanged canvas -> no duplicate.
            with open(p, "rb") as fh:
                h = hashlib.md5(fh.read()).hexdigest()[:8]
            r = spresource.import_project_resource(
                p, usage,
                name="Melodia_SMS2_%s_%s_%s_r2" % (label, V["name"], h),
                group="Melodia SMS2")
            rid[key] = (r.identifier()
                        if callable(getattr(r, "identifier", None)) else r)
            log("imported %s" % key)
        curv = body.get_mesh_map_resource(spts.MeshMapUsage.Curvature)
        bent = body.get_mesh_map_resource(spts.MeshMapUsage.BentNormals)
        # mesh maps come back as ResourceID already — no identifier() call
        rid["curv"] = curv if curv else None
        rid["bent"] = bent if bent else None

        bc = m._chan("BaseColor")
        emiss = m._chan("Emissive") or m._chan("Emission")
        height = m._chan("Height")
        rough = m._chan("Roughness")

        def top_group(name):
            g = ls.insert_group(ls.InsertPosition.from_textureset_stack(st))
            m._set_name(g, name)
            report["nodes"].append(name)
            return g

        def fill_in(parent, name, group=True):
            pos = (m._inside_group(parent) if group
                   else m._inside_mask(parent))
            f = ls.insert_fill(pos)
            m._set_name(f, name)
            report["nodes"].append(name)
            return f

        def masked(parent, name, res_id):
            """Subgroup whose mask bitmap is res_id (notes-only region)."""
            g = top_group(name) if parent is None else None
            if g is None:
                g = ls.insert_group(m._inside_group(parent))
                m._set_name(g, name)
                report["nodes"].append(name)
            g.add_mask(ls.MaskBackground.Black)
            mf = ls.insert_fill(m._inside_mask(g))
            m._set_name(mf, name + "_maskFill")
            m._try_mask_bitmap(mf, res_id, name)
            return g

        def crush_mask(parent_fill, input_min, input_max):
            """Levels inside a mask stack: keep only the bright zone, so
            curvature / bent-normal maps stop glowing the whole body."""
            try:
                lev = ls.insert_levels_effect(
                    ls.InsertPosition.inside_node(parent_fill,
                                                  ls.NodeStack.Mask))
                p = lev.get_parameters()
                p.input_min = input_min
                p.input_max = input_max
                p.output_min = 0.0
                p.output_max = 1.0
                p.gamma = 1.0
                p.clamp = True
                try:
                    lev.set_parameters(p)
                except Exception:
                    pass
                report.setdefault("crushes", []).append(
                    [getattr(parent_fill, "get_name", lambda: "?")(),
                     input_min])
                return True
            except Exception as e:
                log("levels crush failed: %r" % e)
                return False

        # ================================================== SMS2_Core
        core = top_group("SMS2_Core")

        f1 = fill_in(core, "S2_Base_Ramp")
        if not m._set_fill_bitmap(f1, bc, rid["ramp"]):
            log("ramp bitmap failed on BaseColor")
        m._set_blend(f1, "Normal", bc) if bc else None

        if chok("SpecularEdgeColor"):
            f2 = fill_in(core, "S2_Iri_Edge")
            cte = getattr(ls.ChannelType, "SpecularEdgeColor")
            if not m._set_fill_bitmap(f2, cte, rid["iri"]):
                m._set_fill_color(f2, cte, accent)
            m._set_opacity(f2, 0.65)
        else:
            log("skip S2_Iri_Edge (no channel)")

        if chok("CoatColor"):
            c3a = fill_in(core, "S2_Coat_Color")
            m._set_fill_bitmap(c3a, getattr(ls.ChannelType, "CoatColor"),
                               rid["iri"])
            m._set_opacity(c3a, 0.75)
            if chok("CoatOpacity"):
                c3b = fill_in(core, "S2_Coat_Opacity")
                m._set_fill_color(c3b, getattr(ls.ChannelType, "CoatOpacity"),
                                  (0.40, 0.40, 0.40))
                m._set_opacity(c3b, 0.75)
            if chok("CoatRoughness"):
                c3c = fill_in(core, "S2_Coat_Rough")
                m._set_fill_color(c3c,
                                  getattr(ls.ChannelType, "CoatRoughness"),
                                  (0.14, 0.14, 0.14))
                m._set_opacity(c3c, 0.75)
        else:
            log("skip S2_Coat_Aurora (no channel)")

        if chok("SheenColor"):
            f4a = fill_in(core, "S2_Sheen_Color")
            m._set_fill_color(f4a, getattr(ls.ChannelType, "SheenColor"),
                              (0.93, 0.90, 0.97))
            if chok("SheenOpacity"):
                f4b = fill_in(core, "S2_Sheen_Opacity")
                m._set_fill_color(f4b, getattr(ls.ChannelType, "SheenOpacity"),
                                  (0.28, 0.28, 0.28))

        if emiss and rid["curv"]:
            f5 = fill_in(core, "S2_Curv_Glow")
            m._set_fill_color(f5, emiss, accent)
            m._set_blend(f5, "Add", emiss)
            f5.add_mask(ls.MaskBackground.Black)
            mf = fill_in(f5, "S2_Curv_Glow_maskFill", group=False)
            report.setdefault("masks", {})["curv"] = bool(
                m._try_mask_bitmap(mf, rid["curv"], "S2_Curv_Glow"))
            crush_mask(f5, 0.60, 1.0)
            m._set_opacity(f5, 0.45)

        if rough and rid["curv"]:
            f6 = fill_in(core, "S2_Curv_Rough")
            m._set_fill_bitmap(f6, rough, rid["curv"])
            m._set_blend(f6, "SoftLight", rough)
            m._set_opacity(f6, 0.35)

        # ================================================ SMS2_Notation
        nota = top_group("SMS2_Notation")
        # NOTE: no group masks — this Painter build's mask fills do not bind
        # imported bitmaps (mesh-map masks DO work; curvature/bent keep
        # theirs). Content is self-contained: recolored bitmaps + blend
        # modes (white bg = no-op under Multiply, black = no-op under Add,
        # 0.5 gray = neutral for Height).
        g1 = fill_in(nota, "S2_Nota_Ink")
        if bc:
            m._set_fill_bitmap(g1, bc, rid["ink"])
            m._set_blend(g1, "Multiply", bc)
        m._set_opacity(g1, 0.85)

        g2 = fill_in(nota, "S2_Nota_Engrave")
        okb = False
        if height:
            okb = m._set_fill_bitmap(g2, height, rid["hfine"])
        if not okb and height:
            m._set_fill_color(g2, height, (0.62, 0.62, 0.62))
        m._set_opacity(g2, 0.9)
        report["engrave_bitmap"] = bool(okb)

        g3 = fill_in(nota, "S2_Nota_Glow")
        if emiss:
            m._set_fill_bitmap(g3, emiss, rid["glowf"])
            m._set_blend(g3, "Add", emiss)
        m._set_opacity(g3, float(prm.get("score_glow_op", 0.4)))

        # BOLD readable notes (own mask subgroup)
        bold = ls.insert_group(m._inside_group(nota))
        m._set_name(bold, "S2_Nota_Bold")
        report["nodes"].append("S2_Nota_Bold")

        b1 = fill_in(bold, "S2_Bold_Ink")
        if bc:
            m._set_fill_bitmap(b1, bc, rid["boldink"])
            m._set_blend(b1, "Multiply", bc)
        m._set_opacity(b1, 0.9)

        b2 = fill_in(bold, "S2_Bold_Glow")
        if emiss:
            m._set_fill_bitmap(b2, emiss, rid["boldglow"])
            m._set_blend(b2, "Add", emiss)
        m._set_opacity(b2, 0.75)

        if chok("SpecularEdgeColor"):
            b3 = fill_in(bold, "S2_Exp_NotesEdge")
            cte = getattr(ls.ChannelType, "SpecularEdgeColor")
            m._set_fill_bitmap(b3, cte, rid["boldglint"])
            m._set_blend(b3, "Add", cte)
            m._set_opacity(b3, 0.85)

        # EXP: soft bent-normal swell on the whole body (outside the mask)
        if emiss and rid["bent"]:
            e1 = fill_in(core, "S2_Exp_BentSwell")
            m._set_fill_color(e1, emiss, tuple(min(1.0, c * 0.35 + 0.25)
                                               for c in accent))
            m._set_blend(e1, "Add", emiss)
            e1.add_mask(ls.MaskBackground.Black)
            mf = fill_in(e1, "S2_Exp_BentSwell_maskFill", group=False)
            report.setdefault("masks", {})["bent"] = bool(
                m._try_mask_bitmap(mf, rid["bent"], "S2_Exp_BentSwell"))
            crush_mask(e1, 0.78, 1.0)
            m._set_opacity(e1, 0.22)

        # ==================================================== SMS2_Hero
        # Tier-1: staff band + clef + giant motif notes as GOLD embroidery
        # (raised, metallic, glinting) — the layer that must read at distance.
        hero = top_group("SMS2_Hero")
        report["hero_vis"] = bool(hero.is_visible())

        hg = fill_in(hero, "S2_Hero_Gold")
        if bc:
            m._set_fill_bitmap(hg, bc, rid["herogold"])
            m._set_blend(hg, "Multiply", bc)

        met = m._chan("Metallic")
        if met:
            hgm = fill_in(hero, "S2_Hero_GoldMet")
            m._set_fill_bitmap(hgm, met, rid["heromet"])

        hr = fill_in(hero, "S2_Hero_Raise")
        okh = False
        if height:
            okh = m._set_fill_bitmap(hr, height, rid["heroh"])
        if not okh and height:
            m._set_fill_color(hr, height, (0.85, 0.85, 0.85))
        m._set_opacity(hr, 0.9)

        hgl = fill_in(hero, "S2_Hero_Glow")
        if emiss:
            m._set_fill_bitmap(hgl, emiss, rid["herowglow"])
            m._set_blend(hgl, "Add", emiss)
        m._set_opacity(hgl, 0.85)

        if chok("SpecularEdgeColor"):
            hgt = fill_in(hero, "S2_Hero_Glint")
            cte = getattr(ls.ChannelType, "SpecularEdgeColor")
            m._set_fill_bitmap(hgt, cte, rid["heroglint"])
            m._set_blend(hgt, "Add", cte)
            m._set_opacity(hgt, 0.9)

        # (calibration probes removed — diagnosis complete: masks on group
        # fills never bound imported bitmaps; content now maskless)

        # ------------------------------------------------------------ export
        # Let the texture cache finish computing before exporting. Early
        # exports after big stack changes race the async texture updates and
        # come back stale/partial (white BaseColor, zeroed channels — seen
        # both in single builds and in the 2026-10-11 Night Shift run where
        # 4 of 6 variants lost their core maps).
        try:
            import substance_painter.project as _spj
            t0 = time.time()
            while _spj.is_busy() and time.time() - t0 < 180:
                time.sleep(2)
            time.sleep(4)
            report["settle_secs"] = round(time.time() - t0, 1)
        except Exception as e:
            report["settle_err"] = repr(e)[:120]
        os.makedirs(exports_dir, exist_ok=True)
        preset = None
        pbr_url = None
        for p in ex.list_resource_export_presets():
            r = getattr(p, "resource_id", None)
            r = r() if callable(r) else r
            a = getattr(r, "name", None)
            nm = a() if callable(a) else str(a)
            if nm == "PBR Metallic Roughness":
                u = getattr(r, "url", None)
                pbr_url = u() if callable(u) else u
                preset = p
                break

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
        if chok("CoatColor"):
            extra += [docmap("CoatColor"),
                      docmap("CoatOpacity", True),
                      docmap("CoatRoughness", True)]
        if chok("SheenColor"):
            extra += [docmap("SheenColor"), docmap("SheenOpacity", True)]
        if chok("SpecularEdgeColor"):
            extra += [docmap("SpecularEdgeColor")]
        new_name = "SMS2 Pilot (PBR MR + iridescence)"

        outd = os.path.join(exports_dir, variant_name)
        os.makedirs(outd, exist_ok=True)
        cfg_base = {
            "exportShaderParams": False,
            "exportPath": outd.replace("\\", "/"),
            "exportList": [{"rootPath": "IDMAP_Sheep_Body"}],
            "exportParameters": [{"parameters": {
                "fileFormat": "png", "bitDepth": "8", "sizeLog2": 11,
                "paddingAlgorithm": "infinite"}}],
        }
        attempts = []
        if extra:
            cfg_rich = dict(cfg_base, defaultExportPreset=new_name,
                            exportPresets=[{"name": new_name,
                                            "maps": maps + extra}])
            attempts.append(("rich", cfg_rich))
        cfg_plain = dict(cfg_base, defaultExportPreset=pbr_url)
        attempts.append(("plain", cfg_plain))
        for tag, conf in attempts:
            try:
                t0 = time.time()
                r = ex.export_project_textures(conf)
                n_files = len(os.listdir(outd))
                report["exports"][tag] = {
                    "status": str(getattr(r, "status", "?")),
                    "n": n_files, "secs": round(time.time() - t0, 1)}
                log("export %s: %s (%d files)" %
                    (tag, report["exports"][tag]["status"], n_files))
                break
            except Exception as e:
                report["exports"][tag] = "FAILED: %r" % e
                log("export %s failed: %r" % (tag, e))

        # -------------------------------------------------------------- save
        if save:
            try:
                # settle before saving: the .spp must capture flushed
                # resources + textures, or a future reopen loads broken
                # bitmaps (the 2026-10-11 white-export incident: cron saved
                # mid-flush, reopen -> every imported canvas dead).
                try:
                    t0 = time.time()
                    while spj.is_busy() and time.time() - t0 < 120:
                        time.sleep(2)
                    time.sleep(8)
                    report["save_settle_secs"] = round(time.time() - t0, 1)
                except Exception as e:
                    report["save_settle_err"] = repr(e)[:120]
                spj.save_as(project_path)
                report["saved"] = project_path
            except Exception as e:
                report["save_err"] = repr(e)[:200]
        report["ok"] = True
    except Exception as e:
        report["error"] = repr(e)
        _log(log_path, "FATAL: " + traceback.format_exc())

    rep_path = os.path.join(os.path.dirname(log_path), "sms2_report.json")
    try:
        with open(rep_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, default=str)
    except Exception:
        pass
    return report
