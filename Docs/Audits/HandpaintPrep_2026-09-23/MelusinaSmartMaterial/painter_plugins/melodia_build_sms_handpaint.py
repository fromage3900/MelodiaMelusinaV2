# Melodia - build SMS_Melusina_Handpaint layer stack on the active ZenLantern
# (or any open) Texture Set. Melodia / Melusina naming only - never Grok*.
#
# Stack: layers 01-10 + 11 VeryNormal_Workflow + 15 ResonanceBloom.
#
# Console:
#   import melodia_build_sms_handpaint as m; m.build_sms()
# Menu (once plugin loaded):
#   Melodia: Build SMS_Melusina_Handpaint
#
# Installed 2026-09-24 into Painter python/plugins (+ OneDrive copy + SMS tree).
# Resonance Bloom / VNP workflow extension: 2026-09-24.

import os
import traceback

import substance_painter as sp
import substance_painter.project as spproject
import substance_painter.resource as spresource
import substance_painter.textureset as sptextureset
import substance_painter.layerstack as splayers

try:
    import substance_painter.colormanagement as spcm
except Exception:
    spcm = None

SMS_ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial"
CYMATIC_DIR = os.path.join(SMS_ROOT, "resources", "cymatic")
SHOWCASE_FBX = (
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23"
    r"\02_ZenLantern\substance\meshes\ZenLantern_V2_Showcase.fbx"
)
EXPORT_SPSM = os.path.join(SMS_ROOT, "exports", "SMS_Melusina_Handpaint.spsm")

FOLDER_NAME = "SMS_Melusina_Handpaint"

# ZenLantern palette (sRGB 0-1)
PRIMARY = (0xF5 / 255.0, 0xEC / 255.0, 0xD7 / 255.0)   # paper
SECONDARY = (0x8B / 255.0, 0x5E / 255.0, 0x3C / 255.0)  # cedar
ACCENT = (0xFF / 255.0, 0xC9 / 255.0, 0x78 / 255.0)     # glow
CAVITY_DARK = (0.12, 0.10, 0.18)  # deep navy multiply
# Resonance Bloom Inner Ember - warm cedar-leaning tint
INNER_EMBER = (0.55, 0.28, 0.12)

CYMATIC_MAPS = {
    "Height": "T_Cymatic_FrozenFracture_Height.png",
    "Emissive": "T_Cymatic_FrozenFracture_Emissive.png",
    "Metallic": "T_Cymatic_FrozenFracture_Metallic.png",
    "Opacity": "T_Cymatic_FrozenFracture_Opacity.png",
    "Normal": "T_Cymatic_FrozenFracture_Normal.png",
    "BaseColor": "T_Cymatic_FrozenFracture_BaseColor.png",
}

# Defaults from SPEC
CAVITY_INTENSITY = 0.55
DECORATION_INTENSITY = 0.40
CYMATIC_INTENSITY = 0.35
BEAT_EMISSIVE = 0.45
ROUGHNESS_BASE = 0.55
ROUGHNESS_MIN = 0.35
ROUGHNESS_MAX = 0.72
METALLIC_ACCENT = 0.15
# Resonance Bloom (folder 15) - SPEC Exposed parameters
RESONANCE_CORE = 0.55
MOONGLOW_HALO = 0.40
CHARM_FLASH = 0.35
INNER_EMBER_OPACITY = 0.25


def log(msg):
    print("[Melodia SMS] " + msg, flush=True)


def _color(rgb):
    r, g, b = rgb
    if spcm is not None and hasattr(spcm, "Color"):
        try:
            return spcm.Color(r, g, b)
        except TypeError:
            try:
                return spcm.Color(r, g, b, 1.0)
            except Exception:
                pass
    # Fallback: some builds accept plain tuples via set_source
    return (r, g, b)


def _set_name(node, name):
    try:
        node.set_name(name)
        return
    except Exception:
        pass
    try:
        node.name = name
    except Exception as e:
        log("Could not name node %r: %s" % (name, e))


def _chan(name):
    """Resolve textureset.ChannelType member by loose name."""
    ct = sptextureset.ChannelType
    upper = {m.upper(): getattr(ct, m) for m in dir(ct) if not m.startswith("_")}
    for cand in (name.upper(), name.upper().replace("EMISSIVE", "EMISSION"),
                 "EMISSIVE" if name.upper() == "EMISSION" else None,
                 "DIFFUSE" if name.upper() == "BASECOLOR" else None):
        if cand and cand in upper:
            return upper[cand]
    return None


def _blend(name):
    bm = splayers.BlendingMode
    upper = {m.upper(): getattr(bm, m) for m in dir(bm) if not m.startswith("_")}
    key = name.upper().replace(" ", "")
    return upper.get(key) or upper.get(name.upper())


def _set_blend(node, mode_name, channel):
    mode = _blend(mode_name)
    if mode is None or channel is None:
        return False
    try:
        if hasattr(node, "has_blending") and not node.has_blending():
            return False
        node.set_blending_mode(mode, channel)
        return True
    except Exception as e:
        log("Blend %s/%s skipped: %s" % (mode_name, channel, e))
        return False


def _set_opacity(node, value):
    for attr in ("set_opacity", "set_layer_opacity"):
        fn = getattr(node, attr, None)
        if callable(fn):
            try:
                fn(float(value))
                return True
            except Exception:
                try:
                    fn(float(value), _chan("BaseColor"))
                    return True
                except Exception as e:
                    log("Opacity via %s failed: %s" % (attr, e))
    for prop in ("opacity", "layer_opacity"):
        if hasattr(node, prop):
            try:
                setattr(node, prop, float(value))
                return True
            except Exception:
                pass
    return False


def _set_fill_color(node, channel, rgb):
    if channel is None:
        return False
    try:
        node.active_channels = {channel}
    except Exception:
        pass
    try:
        node.set_source(channel, _color(rgb))
        return True
    except TypeError:
        # Older plugin style: set_source(resource) after active_channels
        try:
            node.set_source(_color(rgb))
            return True
        except Exception as e:
            log("set_source color failed (%s): %s" % (channel, e))
            return False
    except Exception as e:
        log("set_source color failed (%s): %s" % (channel, e))
        return False


def _set_fill_bitmap(node, channel, res_id):
    if channel is None or res_id is None:
        return False
    try:
        # Keep previously activated channels + this one
        try:
            cur = set(node.active_channels) if node.active_channels else set()
            cur.add(channel)
            node.active_channels = cur
        except Exception:
            node.active_channels = {channel}
        node.set_source(channel, res_id)
        return True
    except TypeError:
        try:
            node.active_channels = {channel}
            node.set_source(res_id)
            return True
        except Exception as e:
            log("set_source bitmap failed (%s): %s" % (channel, e))
            return False
    except Exception as e:
        log("set_source bitmap failed (%s): %s" % (channel, e))
        return False


def _inside_group(group):
    return splayers.InsertPosition.inside_node(group, splayers.NodeStack.Substack)


def _inside_mask(layer):
    return splayers.InsertPosition.inside_node(layer, splayers.NodeStack.Mask)


def resolve_usage():
    for name in ("TEXTURE", "IMAGE", "BASE_MATERIAL", "MATERIAL"):
        if hasattr(spresource.Usage, name):
            return getattr(spresource.Usage, name)
    raise RuntimeError("No usable resource Usage enum")


def import_cymatic():
    usage = resolve_usage()
    ids = {}
    missing = []
    for key, fn in CYMATIC_MAPS.items():
        path = os.path.join(CYMATIC_DIR, fn)
        if not os.path.isfile(path):
            missing.append(fn)
            continue
        r = spresource.import_project_resource(
            path, usage,
            name="Melodia_Cymatic_%s" % key,
            group="Melodia Cymatic FrozenFracture")
        ids[key] = r.identifier()
    if missing:
        log("MISSING cymatic PNGs: %s" % ", ".join(missing))
    else:
        log("Imported %d cymatic maps from %s" % (len(ids), CYMATIC_DIR))
    return ids


def _add_mask_todo(layer, todo_msg):
    """Black mask + empty fill so the artist has a slot; print TODO for generators."""
    try:
        layer.add_mask(splayers.MaskBackground.Black)
    except Exception as e:
        log("add_mask failed: %s" % e)
        log("TODO MASK: %s" % todo_msg)
        return None
    fill = None
    try:
        fill = splayers.insert_fill(_inside_mask(layer))
        _set_name(fill, "TODO_mask_wire")
    except Exception as e:
        log("mask fill insert failed: %s" % e)
    log("TODO MASK (manual click): %s" % todo_msg)
    return fill


def _try_mask_bitmap(mask_fill, res_id, label):
    """Best-effort assign a project bitmap into a mask fill. Fail soft."""
    if mask_fill is None or res_id is None:
        return False
    for attempt in (
        lambda: mask_fill.set_source(None, res_id),
        lambda: mask_fill.set_source(res_id),
    ):
        try:
            attempt()
            log("%s mask fill <- bitmap OK" % label)
            return True
        except Exception:
            continue
    log("%s mask bitmap assign failed - leave TODO fill" % label)
    return False


def build_sms(create_project_if_needed=False):
    """Build folder SMS_Melusina_Handpaint + layers 01-10 + 11 VNP + 15 ResonanceBloom."""
    log("=== build_sms start (01-10 + 11 VNP + 15 ResonanceBloom) ===")
    if not spproject.is_open():
        if create_project_if_needed and os.path.isfile(SHOWCASE_FBX):
            log("No project open - creating from Showcase FBX")
            settings = spproject.Settings()
            if hasattr(spproject, "NormalMapFormat"):
                settings.normal_map_format = spproject.NormalMapFormat.OpenGL
            try:
                if hasattr(spproject.Settings, "__dataclass_fields__") and \
                   "default_texture_resolution" in spproject.Settings.__dataclass_fields__:
                    settings.default_texture_resolution = 4096
            except Exception:
                pass
            spproject.create(SHOWCASE_FBX, settings=settings)
            import time
            ready = False
            for _ in range(60):
                try:
                    if spproject.is_in_edition_state():
                        ready = True
                        break
                except Exception:
                    pass
                time.sleep(5)
            if not ready:
                log("Project never became ready - aborting.")
                return False
        else:
            log("No project open. Open ZenLantern Showcase (or any mesh), then rerun.")
            log("FBX: " + SHOWCASE_FBX)
            return False

    try:
        if not spproject.is_in_edition_state():
            log("Project not in edition state yet - wait for load, then rerun.")
            return False
    except Exception:
        pass

    stack = sptextureset.get_active_stack()
    log("Active stack: %s" % getattr(stack, "name", lambda: str(stack))())

    cym = import_cymatic()

    # Root folder
    root_pos = splayers.InsertPosition.from_textureset_stack(stack)
    root = splayers.insert_group(root_pos)
    _set_name(root, FOLDER_NAME)
    log("Created folder %s" % FOLDER_NAME)

    bc = _chan("BaseColor")
    rough = _chan("Roughness")
    metal = _chan("Metallic")
    height = _chan("Height")
    normal = _chan("Normal")
    emissive = _chan("Emissive") or _chan("Emission")
    opacity = _chan("Opacity")

    # --- 01 BaseFill
    n01 = splayers.insert_fill(_inside_group(root))
    _set_name(n01, "01_Melodia_BaseFill")
    if bc:
        _set_fill_color(n01, bc, PRIMARY)
    if rough:
        _set_fill_color(n01, rough, (ROUGHNESS_BASE, ROUGHNESS_BASE, ROUGHNESS_BASE))
    if metal:
        _set_fill_color(n01, metal, (0.0, 0.0, 0.0))
    if height:
        try:
            n01.active_channels = ({bc, rough, metal, height} - {None})
        except Exception:
            pass
        _set_fill_color(n01, height, (0.5, 0.5, 0.5))
    log("01_Melodia_BaseFill OK")

    # --- 02 PaintSlot under subfolder 02_Paint
    paint_folder = splayers.insert_group(_inside_group(root))
    _set_name(paint_folder, "02_Paint")
    n02 = splayers.insert_paint(_inside_group(paint_folder))
    _set_name(n02, "02_Melodia_PaintSlot")
    log("02_Melodia_PaintSlot OK (paint here)")

    # --- 03 Cavity Multiply
    n03 = splayers.insert_fill(_inside_group(root))
    _set_name(n03, "03_Cavity_Multiply")
    if bc:
        _set_fill_color(n03, bc, CAVITY_DARK)
        _set_blend(n03, "Multiply", bc)
    _set_opacity(n03, CAVITY_INTENSITY)
    _add_mask_todo(
        n03,
        "03_Cavity_Multiply: add Generator Ambient Occlusion (Levels) "
        "MULTIPLY Color-to-mask on vcol_melodia.R (wear/cavity)")
    log("03_Cavity_Multiply scaffolded")

    # --- 04 DecorationWear
    n04 = splayers.insert_fill(_inside_group(root))
    _set_name(n04, "04_DecorationWear")
    if bc:
        _set_fill_color(n04, bc, ACCENT)
    if rough:
        _set_fill_color(n04, rough, (ROUGHNESS_MIN, ROUGHNESS_MIN, ROUGHNESS_MIN))
    _set_opacity(n04, DECORATION_INTENSITY)
    _add_mask_todo(
        n04,
        "04_DecorationWear: Generator Curvature (convex) x Levels x "
        "vcol_melodia.G (decoration density)")
    log("04_DecorationWear scaffolded")

    # --- 05 RoughnessClamp (roughness only)
    n05 = splayers.insert_fill(_inside_group(root))
    _set_name(n05, "05_RoughnessClamp")
    mid = 0.5 * (ROUGHNESS_MIN + ROUGHNESS_MAX)
    if rough:
        try:
            n05.active_channels = {rough}
        except Exception:
            pass
        _set_fill_color(n05, rough, (mid, mid, mid))
    log("05_RoughnessClamp OK (roughness-only fill @ %.2f)" % mid)

    # --- 06 BeatEmissive (kept for compatibility; 15a is refined Resonance Core above)
    n06 = splayers.insert_fill(_inside_group(root))
    _set_name(n06, "06_BeatEmissive")
    if emissive:
        try:
            n06.active_channels = {emissive}
        except Exception:
            pass
        _set_fill_color(n06, emissive, ACCENT)
        _set_blend(n06, "Add", emissive)
    _set_opacity(n06, BEAT_EMISSIVE)
    _add_mask_todo(
        n06,
        "06_BeatEmissive: mask = vcol_melodia.A (emissive zones); "
        "optionally multiply by vcol_melodia.B for beat pulse. "
        "Note: 15a_ResonanceCore is the refined bloom-stack core above this.")
    log("06_BeatEmissive scaffolded (compat; see 15a ResonanceCore)")

    # --- 07 NPR_StrokeGrunge (optional, low opacity)
    n07 = splayers.insert_fill(_inside_group(root))
    _set_name(n07, "07_NPR_StrokeGrunge")
    if rough:
        try:
            n07.active_channels = {rough}
        except Exception:
            pass
        _set_fill_color(n07, rough, (0.6, 0.6, 0.6))
    _set_opacity(n07, 0.12)
    _add_mask_todo(
        n07,
        "07_NPR_StrokeGrunge (optional): drop a Grunge / brush-stroke alpha "
        "into the mask; keep opacity very low")
    log("07_NPR_StrokeGrunge scaffolded (optional)")

    # --- 08 VerticalGrade (pair as two fills in a folder)
    grade_folder = splayers.insert_group(_inside_group(root))
    _set_name(grade_folder, "08_VerticalGrade")
    n08a = splayers.insert_fill(_inside_group(grade_folder))
    _set_name(n08a, "08a_BottomMultiply")
    if bc:
        _set_fill_color(n08a, bc, (0.25, 0.18, 0.12))
        _set_blend(n08a, "Multiply", bc)
    _set_opacity(n08a, 0.25)
    _add_mask_todo(n08a, "08a: mask = Position Y bottom (or UV gradient)")
    n08b = splayers.insert_fill(_inside_group(grade_folder))
    _set_name(n08b, "08b_TopSoftLight")
    if bc:
        _set_fill_color(n08b, bc, PRIMARY)
        _set_blend(n08b, "SoftLight", bc)
    _set_opacity(n08b, 0.20)
    _add_mask_todo(n08b, "08b: mask = Position Y top (or UV gradient)")
    log("08_VerticalGrade scaffolded")

    # --- 09 MelodiaGrade
    n09 = splayers.insert_fill(_inside_group(root))
    _set_name(n09, "09_MelodiaGrade")
    if bc:
        _set_fill_color(n09, bc, ACCENT)
        _set_blend(n09, "Overlay", bc)
    _set_opacity(n09, 0.18)
    log("09_MelodiaGrade OK")

    # --- 10 Cymatic_FrozenFracture folder
    cym_folder = splayers.insert_group(_inside_group(root))
    _set_name(cym_folder, "10_Cymatic_FrozenFracture")
    _set_opacity(cym_folder, CYMATIC_INTENSITY)

    def _cym_fill(title, chan_key, channel, strength_note=""):
        node = splayers.insert_fill(_inside_group(cym_folder))
        _set_name(node, title)
        rid = cym.get(chan_key)
        if rid and channel:
            ok = _set_fill_bitmap(node, channel, rid)
            log("%s bitmap=%s %s" % (title, ok, strength_note))
        else:
            log("%s SKIPPED (missing map or channel)" % title)
        return node

    _cym_fill("10a_Cymatic_Height", "Height", height, "(low scale - dial in UI)")
    n_em = _cym_fill("10b_Cymatic_Emissive", "Emissive", emissive,
                     "x CymaticIntensity (~0.55 on paper)")
    if emissive:
        _set_blend(n_em, "Add", emissive)
    _cym_fill("10c_Cymatic_Metallic", "Metallic", metal,
              "x MetallicAccent=%.2f" % METALLIC_ACCENT)
    # Opacity as dedicated fill if channel exists; also used as folder mask TODO
    if opacity:
        _cym_fill("10d_Cymatic_Opacity", "Opacity", opacity, "@ ~0.5 on paper")
    else:
        log("Opacity channel absent - use 10d map as folder/layer mask manually")
    _cym_fill("10e_Cymatic_Normal", "Normal", normal, "@ ~0.2 on cedar frame")
    # Optional desaturated wash - keep Melodia palette hero, so low opacity
    n_bc = _cym_fill("10f_Cymatic_BaseWash", "BaseColor", bc, "optional desat wash")
    _set_opacity(n_bc, 0.15)

    # Folder mask from Opacity map when possible
    try:
        cym_folder.add_mask(splayers.MaskBackground.Black)
        mask_fill = splayers.insert_fill(_inside_mask(cym_folder))
        _set_name(mask_fill, "10_mask_Opacity")
        if cym.get("Opacity"):
            try:
                mask_fill.set_source(None, cym["Opacity"])
                log("10 folder mask <- Opacity bitmap")
            except Exception as e:
                log("10 folder mask bitmap assign failed (%s) - TODO: assign "
                    "T_Cymatic_FrozenFracture_Opacity.png to folder mask" % e)
        else:
            log("TODO: assign Opacity PNG to 10_Cymatic_FrozenFracture folder mask")
    except Exception as e:
        log("10 folder mask: %s - TODO: mask folder with Opacity PNG" % e)

    log("10_Cymatic_FrozenFracture folder complete")

    # =========================================================================
    # --- 11_VeryNormal_Workflow (VNP pattern, Melusina-owned - NO Nhance binary)
    # =========================================================================
    try:
        vnp_folder = splayers.insert_group(_inside_group(root))
        _set_name(vnp_folder, "11_VeryNormal_Workflow")
        log("11_VeryNormal_Workflow folder created")

        # 11a_WSN_Inject - Fill Normal; TODO assign baked World Space Normal
        n11a = splayers.insert_fill(_inside_group(vnp_folder))
        _set_name(n11a, "11a_WSN_Inject")
        if normal:
            try:
                n11a.active_channels = {normal}
            except Exception:
                pass
            # Neutral flat normal placeholder until artist wires mesh WSN
            _set_fill_color(n11a, normal, (0.5, 0.5, 1.0))
        log("TODO: 11a_WSN_Inject - assign baked mesh World Space Normal "
            "(Add WS Normal HERE analogue). Bake WSN before wiring.")

        # 11b_PaintNormals under subfolder 11b_Paint - stroke normals here
        paint_n_folder = splayers.insert_group(_inside_group(vnp_folder))
        _set_name(paint_n_folder, "11b_Paint")
        n11b = splayers.insert_paint(_inside_group(paint_n_folder))
        _set_name(n11b, "11b_PaintNormals")
        log("11b_PaintNormals OK (VNP Paint Here - stroke normals)")

        # 11c_WSN_Anchor - named fill/anchor placeholder (DataActionAnchor analogue)
        n11c = splayers.insert_fill(_inside_group(vnp_folder))
        _set_name(n11c, "11c_WSN_Anchor")
        if normal:
            try:
                n11c.active_channels = {normal}
            except Exception:
                pass
            _set_fill_color(n11c, normal, (0.5, 0.5, 1.0))
        _set_opacity(n11c, 0.0)  # anchor placeholder - no visual until wired
        log("TODO: 11c_WSN_Anchor - Anchor WSN contribution "
            "(DataActionAnchor analogue; Painter: named fill + note)")

        # 11d_TangentCombine - Fill Normal; TODO mesh Tangent Normal / converter
        n11d = splayers.insert_fill(_inside_group(vnp_folder))
        _set_name(n11d, "11d_TangentCombine")
        if normal:
            try:
                n11d.active_channels = {normal}
            except Exception:
                pass
            # Prefer soft-light Cymatic Normal if bitmap available (low strength)
            rid_n = cym.get("Normal")
            if rid_n:
                ok = _set_fill_bitmap(n11d, normal, rid_n)
                _set_blend(n11d, "SoftLight", normal)
                _set_opacity(n11d, 0.15)
                log("11d_TangentCombine: optional Cymatic Normal soft-light "
                    "(bitmap=%s @0.15)" % ok)
            else:
                _set_fill_color(n11d, normal, (0.5, 0.5, 1.0))
        log("TODO: 11d_TangentCombine - mesh Tangent Normal and/or Very Normal "
            "Converter if artist drops shelf filter; Melusina does NOT ship "
            "VNP converter SBSAR.")
        log("11_VeryNormal_Workflow complete")
    except Exception as e:
        log("11_VeryNormal_Workflow FAILED (soft): %s" % e)
        log(traceback.format_exc())

    # =========================================================================
    # --- 15_ResonanceBloom (creative emissive - remap unused maps as masks)
    # =========================================================================
    try:
        bloom = splayers.insert_group(_inside_group(root))
        _set_name(bloom, "15_ResonanceBloom")
        log("15_ResonanceBloom folder created")

        # 15a_ResonanceCore - refined core (06 stays for compat)
        n15a = splayers.insert_fill(_inside_group(bloom))
        _set_name(n15a, "15a_ResonanceCore")
        if emissive:
            try:
                n15a.active_channels = {emissive}
            except Exception:
                pass
            _set_fill_color(n15a, emissive, ACCENT)
            _set_blend(n15a, "Add", emissive)
        _set_opacity(n15a, RESONANCE_CORE)
        _add_mask_todo(
            n15a,
            "15a_ResonanceCore: mask = vcol_melodia.A "
            "(optionally x vcol_melodia.B). Stage-makeup core above 06.")
        log("15a_ResonanceCore OK (opacity=%.2f)" % RESONANCE_CORE)

        # 15b_MoonglowHalo - Accent emissive; mask TODO (1-Opacity) x Height x vcol.B
        n15b = splayers.insert_fill(_inside_group(bloom))
        _set_name(n15b, "15b_MoonglowHalo")
        if emissive:
            try:
                n15b.active_channels = {emissive}
            except Exception:
                pass
            # Slightly cooler Accent whisper (nudge toward cool paper)
            cool_accent = (
                ACCENT[0] * 0.92,
                ACCENT[1] * 0.95,
                min(1.0, ACCENT[2] * 1.08),
            )
            _set_fill_color(n15b, emissive, cool_accent)
            _set_blend(n15b, "Add", emissive)
        _set_opacity(n15b, MOONGLOW_HALO)
        mf15b = _add_mask_todo(
            n15b,
            "15b_MoonglowHalo: mask = (1 - Cymatic Opacity) x soft Height x "
            "vcol_melodia.B. Height = who catches beat light; inverted Opacity "
            "= ghost-ring shutter. TODO INVERT Opacity in UI after assign.")
        # Try assign Opacity into mask fill (artist inverts in UI)
        if mf15b is not None and cym.get("Opacity"):
            _try_mask_bitmap(mf15b, cym["Opacity"], "15b Opacity")
            log("TODO INVERT: 15b mask Opacity bitmap - invert in UI, then "
                "multiply soft Height x vcol.B")
        log("15b_MoonglowHalo OK (opacity=%.2f)" % MOONGLOW_HALO)

        # 15c_CharmFlash - Metallic remapped as sparkle MASK (not Metallic channel)
        n15c = splayers.insert_fill(_inside_group(bloom))
        _set_name(n15c, "15c_CharmFlash")
        if emissive:
            try:
                n15c.active_channels = {emissive}
            except Exception:
                pass
            # Slightly hotter Accent
            hot_accent = (
                min(1.0, ACCENT[0] * 1.05),
                ACCENT[1] * 0.92,
                ACCENT[2] * 0.85,
            )
            _set_fill_color(n15c, emissive, hot_accent)
            _set_blend(n15c, "Add", emissive)
        _set_opacity(n15c, CHARM_FLASH)
        mf15c = _add_mask_todo(
            n15c,
            "15c_CharmFlash: mask = vcol_melodia.G x Cymatic Metallic bitmap "
            "(Metallic remapped as sparkle mask - NOT written to Metallic channel). "
            "TODO multiply by vcol.G after bitmap assign.")
        if mf15c is not None and cym.get("Metallic"):
            _try_mask_bitmap(mf15c, cym["Metallic"], "15c Metallic-as-mask")
            log("TODO: 15c multiply mask by vcol_melodia.G "
                "(Metallic map = sparkle, remapped)")
        log("15c_CharmFlash OK (opacity=%.2f)" % CHARM_FLASH)

        # 15d_InnerEmber - warm cedar cavities via inverted AO
        n15d = splayers.insert_fill(_inside_group(bloom))
        _set_name(n15d, "15d_InnerEmber")
        if emissive:
            try:
                n15d.active_channels = {emissive}
            except Exception:
                pass
            _set_fill_color(n15d, emissive, INNER_EMBER)
            _set_blend(n15d, "Add", emissive)
        _set_opacity(n15d, INNER_EMBER_OPACITY)
        _add_mask_todo(
            n15d,
            "15d_InnerEmber: mask = inverted mesh Ambient Occlusion "
            "(lantern cavities glow warm). Add AO generator + Invert.")
        log("15d_InnerEmber OK (opacity=%.2f, tint=%.2f,%.2f,%.2f)" % (
            INNER_EMBER_OPACITY, INNER_EMBER[0], INNER_EMBER[1], INNER_EMBER[2]))

        log("15_ResonanceBloom complete")
    except Exception as e:
        log("15_ResonanceBloom FAILED (soft): %s" % e)
        log(traceback.format_exc())

    # Try create_smart_material if API present (does not invent binary offline)
    sms_created = False
    if hasattr(splayers, "create_smart_material"):
        try:
            splayers.create_smart_material(root, FOLDER_NAME)
            sms_created = True
            log("create_smart_material('%s') called - check Shelf Smart materials" %
                FOLDER_NAME)
        except TypeError:
            try:
                splayers.create_smart_material(root)
                sms_created = True
                log("create_smart_material(root) called - rename shelf item to %s" %
                    FOLDER_NAME)
            except Exception as e:
                log("create_smart_material failed: %s" % e)
        except Exception as e:
            log("create_smart_material failed: %s" % e)
    if not sms_created:
        log("TODO FINAL: Right-click folder '%s' -> Create smart material, "
            "then copy .spsm to:\n  %s" % (FOLDER_NAME, EXPORT_SPSM))

    log("=== build_sms DONE (01-10 + 11 VNP + 15 ResonanceBloom) ===")
    log("Manual mask wires still needed: 03 (AO x vcol.R), 04 (Curv x vcol.G), "
        "06 (vcol.A), 11a/c/d (WSN/Tangent), 15a (vcol.A), 15b INVERT Opacity, "
        "15c x vcol.G, 15d inverted AO. Bake mesh maps + WSN + vcol first.")
    return True


def build_sms_safe():
    try:
        return build_sms(create_project_if_needed=False)
    except Exception:
        log("build_sms FAILED:\n" + traceback.format_exc())
        return False


# Alias for the exact console one-liner in the brief
def build():
    return build_sms_safe()


_ACTIONS = []


def start_plugin():
    global _ACTIONS
    import PySide6.QtGui as qtg
    import substance_painter.ui as spui
    action = qtg.QAction("Melodia: Build SMS_Melusina_Handpaint", None)
    action.triggered.connect(build_sms_safe)
    if os.environ.get("MELUSINA_AUTO_BUILD_SMS") == "1":
        from PySide6.QtCore import QTimer
        QTimer.singleShot(20000, build_sms_safe)
        log("Auto-build armed (MELUSINA_AUTO_BUILD_SMS=1) - building in ~20s.")
    added = False
    menu = getattr(spui, "ApplicationMenu", None)
    if menu is not None:
        for member in ("Window", "Tools", "Scripts", "View"):
            if hasattr(menu, member):
                try:
                    spui.add_action(getattr(menu, member), action)
                    added = True
                    log("Menu action added under %s." % member)
                    break
                except Exception:
                    continue
    if not added:
        log("No menu slot - use console: "
            "import melodia_build_sms_handpaint as m; m.build_sms()")
    _ACTIONS = [action]
    return _ACTIONS


def close_plugin():
    return None
