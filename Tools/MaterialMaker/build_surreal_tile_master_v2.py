#!/usr/bin/env python3
"""
MM_Master_SurrealAnimatedPBR v2 — Full redesign with 3-layer architecture.

Usage:
  py Tools/MaterialMaker/build_surreal_tile_master_v2.py
  py Tools/MaterialMaker/build_surreal_tile_master_v2.py --source-image path/to/photo.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT_STATIC = ROOT / "MM_Master_SurrealAnimatedPBR_v2_Static.ptex"
OUT_DYNAMIC = ROOT / "MM_Master_SurrealAnimatedPBR_v2_Dynamic.ptex"

LANE_WIDTH = 960
LANE_GAP = 200
HEADER_Y = -520
ROW_SPACING = 110

P_ALBEDO, P_MET, P_ROUGH, P_EMISS, P_NORM, P_AO, P_DEPTH, P_OPACITY, P_SSS = range(9)

BT_LERP, BT_ADD, BT_MUL, BT_SCREEN, BT_OVERLAY, BT_MAX = 0, 1, 5, 9, 10, 12

COLOR_BLACK = {"a": 1, "b": 0, "g": 0, "r": 0, "type": "Color"}


def _gradient(points):
    return {"interpolation": 1, "points": points, "type": "Gradient"}


GRADIENT_BW = _gradient([
    {"a": 1, "b": 0, "g": 0, "pos": 0, "r": 0},
    {"a": 1, "b": 1, "g": 1, "pos": 1, "r": 1},
])

GRADIENT_DREAM = _gradient([
    {"a": 1, "b": 0.92, "g": 0.78, "pos": 0, "r": 0.95},
    {"a": 1, "b": 0.88, "g": 0.82, "pos": 0.35, "r": 0.98},
    {"a": 1, "b": 0.95, "g": 0.90, "pos": 0.70, "r": 0.85},
    {"a": 1, "b": 0.75, "g": 0.65, "pos": 1.0, "r": 0.78},
])

GRADIENT_MADOKA_CUTE = _gradient([
    {"a": 1, "b": 0.88, "g": 0.78, "pos": 0, "r": 0.92},
    {"a": 1, "b": 0.55, "g": 0.72, "pos": 1, "r": 0.88},
])

GRADIENT_MADOKA_CORRUPT = _gradient([
    {"a": 1, "b": 0.12, "g": 0.15, "pos": 0, "r": 0.98},
    {"a": 1, "b": 0.72, "g": 0.20, "pos": 1, "r": 0.95},
])

GRADIENT_MADOKA_EMISSIVE = _gradient([
    {"a": 1, "b": 0.10, "g": 0.40, "pos": 0, "r": 0.00},
    {"a": 1, "b": 0.90, "g": 0.50, "pos": 0.50, "r": 0.10},
    {"a": 1, "b": 0.30, "g": 0.00, "pos": 1, "r": 0.80},
])

GRADIENT_ITTO = _gradient([
    {"a": 1, "b": 0.08, "g": 0.08, "pos": 0, "r": 0.12},
    {"a": 1, "b": 0.85, "g": 0.82, "pos": 0.45, "r": 0.92},
    {"a": 1, "b": 0.05, "g": 0.04, "pos": 1, "r": 0.55},
])

GRADIENT_ROUGH = _gradient([
    {"a": 1, "b": 0.85, "g": 0.85, "pos": 0, "r": 0.85},
    {"a": 1, "b": 0.20, "g": 0.20, "pos": 1, "r": 0.20},
])

def _tones_range(*, value=0.5, contrast=0.0, width=0.25, invert=False):
    """MM `tones` uses color ramps; value/contrast belong on `tones_range`."""
    return {"value": value, "contrast": contrast, "width": width, "invert": invert}


def _image(image: str, *, fix_ar: bool = True, clamp: bool = False):
    return {"image": image, "fix_ar": fix_ar, "clamp": clamp}


def _buffer(size: int = 0, lod: int = 0):
    return {"size": size, "lod": lod}


GRADIENT_NEBULA_EMISSIVE = _gradient([
    {"a": 1, "b": 0.20, "g": 0.05, "pos": 0, "r": 0.00},
    {"a": 1, "b": 0.60, "g": 0.15, "pos": 0.35, "r": 0.10},
    {"a": 1, "b": 0.80, "g": 0.20, "pos": 0.70, "r": 0.50},
    {"a": 1, "b": 1.00, "g": 0.40, "pos": 1, "r": 0.90},
])


class GraphBuilderV2:
    def __init__(self, *, dynamic, source_image):
        self.dynamic = dynamic
        self.source_image = source_image.replace("\\", "/")
        self.anim_var = "$time" if dynamic else "$BakeTime"
        self.nodes = []
        self.connections = []
        self._lane_x = -6400

    def lane(self, lane_id, title, subtitle="", witch=False):
        x = self._lane_x
        self._lane_x += LANE_WIDTH + LANE_GAP
        color = (
            {"a": 1, "b": 0.38, "g": 0.12, "r": 0.28, "type": "Color"}
            if witch else
            {"a": 1, "b": 0.55, "g": 0.35, "r": 0.45, "type": "Color"}
        )
        text = f"[lane:{lane_id}]"
        if subtitle:
            text += f"\n{subtitle}"
        self.nodes.append({
            "name": f"Comment_{lane_id}",
            "node_position": {"x": x, "y": HEADER_Y},
            "parameters": {"size": 4},
            "title": title,
            "text": text,
            "size": {"x": LANE_WIDTH - 40, "y": 100},
            "color": color,
            "type": "comment",
        })
        return x

    def add(self, name, ntype, x, y, **params):
        if ntype == "image":
            image = params.pop("image")
            fix_ar = params.pop("fix_ar", params.pop("fix_ratio", True))
            clamp = params.pop("clamp", False)
            params = {**_image(image, fix_ar=fix_ar, clamp=clamp), **params}
        if ntype == "buffer":
            size = params.pop("size", 0)
            lod = params.pop("lod", 0)
            params = {**_buffer(size=size, lod=lod), **params}
        if ntype == "tones_range":
            p = params.copy()
            params = _tones_range(
                value=p.pop("value", 0.5),
                contrast=p.pop("contrast", 0.0),
                width=p.pop("width", 0.25),
                invert=p.pop("invert", False),
            )
            params.update(p)
        # MM does NOT support 'seed' in JSON for perlin/voronoi/warp
        if ntype in ("perlin", "voronoi", "warp"):
            params.pop("seed", None)
        self.nodes.append({
            "name": name,
            "node_position": {"x": x, "y": y},
            "parameters": params,
            "type": ntype,
        })
        return name

    def wire(self, src, src_port, dst, dst_port):
        self.connections.append({"from": src, "from_port": src_port, "to": dst, "to_port": dst_port})

    def anim_phase(self, speed=1.0):
        s = f" * {speed}" if speed != 1.0 else ""
        return f"fract({self.anim_var} * $AnimSpeed + $AnimOffset){s}"

    def anim_wave(self, speed=1.0):
        return f"sin(({self.anim_var} * $AnimSpeed + $AnimOffset) * 6.2832 * {speed})"

    def build(self):
        ax = self.lane("00", "00 | INPUT", "Source + Remote params")
        bx = self.lane("01", "01 | PREPROCESS", "Scale . levels . buffer")
        cx = self.lane("02", "02 | SEAMLESS TILE", "Kaleido . mirror . repeat")
        nx = self.lane("08", "08 | NIKKI", "Fabric . sparkle . dream grade")
        mx = self.lane("22", "22 | MADOKA", "Witch barrier . SSS . radial", witch=True)
        ix = self.lane("23", "23 | ITTO", "Oni . wear . cracks . erosion")
        celx = self.lane("14", "14 | CELESTIAL", "Sphere . nebula . stars . CMB")
        hx = self.lane("05", "05 | HEIGHT", "Composite displacement")
        px = self.lane("06", "06 | PBR MAPS", "All channel split + micro detail")
        ox = self.lane("07", "07 | OUTPUT", "Material + exports")

        y = 40
        R = ROW_SPACING
        nasa = "NASA_Refs"
        phase = self.anim_phase()
        phase_slow = self.anim_phase(0.1)
        wave_fast = self.anim_wave(4.0)

        remote_widgets = [
            {"name": "BakeTime", "label": "Bake Time", "type": "named_parameter", "min": 0, "max": 1, "step": 0.001, "default": 0},
            {"name": "AnimSpeed", "label": "Anim Speed", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.15},
            {"name": "AnimOffset", "label": "Anim Offset", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "GlobalSeed", "label": "Global Seed", "type": "named_parameter", "min": 0, "max": 1, "step": 0.001, "default": 0.5},
            {"name": "TileRepeat", "label": "Tile Repeat", "type": "named_parameter", "min": 0.5, "max": 8, "step": 0.1, "default": 2},
            {"name": "SeamBlend", "label": "Seam Blend", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.35},
            {"name": "StyleNikki", "label": "Style Nikki", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "StyleMadoka", "label": "Style Madoka", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "StyleItto", "label": "Style Itto", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "StyleCelestial", "label": "Style Celestial", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "NikkiPastelLift", "label": "Pastel Lift", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.22},
            {"name": "NikkiSparkleAmount", "label": "Sparkle Amount", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.35},
            {"name": "NikkiFabricDetail", "label": "Fabric Detail", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.15},
            {"name": "NikkiFlowStrength", "label": "Flow Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.25},
            {"name": "NikkiSaturation", "label": "Saturation", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.8},
            {"name": "SparkleDriftSpeed", "label": "Sparkle Drift", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.3},
            {"name": "MadokaGlowAmount", "label": "SSS Glow", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.3},
            {"name": "MadokaEmissiveBrightness", "label": "Emissive Brightness", "type": "named_parameter", "min": 0, "max": 5, "step": 0.1, "default": 2.0},
            {"name": "MadokaCuteBias", "label": "Cute vs Corrupt", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "MadokaVeinEmissive", "label": "Vein Emissive", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.35},
            {"name": "WitchBarrierWallpaperScale", "label": "Wallpaper Scale", "type": "named_parameter", "min": 1, "max": 12, "step": 0.1, "default": 4},
            {"name": "WitchBarrierMazeTightness", "label": "Maze Tightness", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "WitchBarrierPhaseSpeed", "label": "Barrier Phase", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.45},
            {"name": "IttoPatternScale", "label": "Pattern Scale", "type": "named_parameter", "min": 1, "max": 12, "step": 0.1, "default": 3},
            {"name": "IttoCrackDepth", "label": "Crack Depth", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.4},
            {"name": "IttoWearAmount", "label": "Wear Amount", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.4},
            {"name": "IttoBreakupAmount", "label": "Surface Breakup", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.25},
            {"name": "IttoErosionStrength", "label": "Erosion Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.2},
            {"name": "IttoInkStrength", "label": "Ink Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.6},
            {"name": "CelestialScale", "label": "Sphere Scale", "type": "named_parameter", "min": 0.5, "max": 4, "step": 0.1, "default": 1.0},
            {"name": "CelestialNebulaScale", "label": "Nebula Scale", "type": "named_parameter", "min": 0.1, "max": 2, "step": 0.01, "default": 0.42},
            {"name": "CelestialTwinkle", "label": "Star Twinkle", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "CelestialDrift", "label": "Star Drift", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.1},
            {"name": "CelestialOrbitSpeed", "label": "Orbit Speed", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.05},
            {"name": "CelestialOrbitPeriod", "label": "Orbit Period", "type": "named_parameter", "min": 1, "max": 360, "step": 1, "default": 60},
            {"name": "CelestialCMBAmount", "label": "CMB Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.15},
            {"name": "CelestialEmissiveBoost", "label": "Emissive Boost", "type": "named_parameter", "min": 0, "max": 5, "step": 0.1, "default": 1.5},
            {"name": "HeightScale", "label": "Height Scale", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.25},
            {"name": "NormalStrength", "label": "Normal Strength", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.8},
            {"name": "NormalDetail", "label": "Normal Detail", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.3},
            {"name": "RoughnessBias", "label": "Roughness Bias", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.55},
            {"name": "RoughnessContrast", "label": "Roughness Micro", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.3},
            {"name": "MetallicAmount", "label": "Metallic Amount", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.05},
            {"name": "AOStrength", "label": "AO Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.7},
            {"name": "SSSAmount", "label": "SSS Amount", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.12},
            {"name": "EmissiveIntensity", "label": "Emissive Intensity", "type": "named_parameter", "min": 0, "max": 5, "step": 0.1, "default": 1.0},
            {"name": "ExportResolution", "label": "Export Resolution", "type": "named_parameter", "min": 8, "max": 12, "step": 1, "default": 11},
        ]
        remote_params = {w["name"]: w["default"] for w in remote_widgets}
        self.nodes.append({
            "name": "Remote_MasterParams",
            "node_position": {"x": ax, "y": -200},
            "parameters": remote_params,
            "type": "remote",
            "widgets": remote_widgets,
        })

        self.add("SourceImage", "image", ax, y, image=self.source_image, fix_ar=True, clamp=False)

        self.add("Transform_Scale", "transform", bx, y, scale_x="$TileRepeat", scale_y="$TileRepeat", repeat=False)
        self.wire("SourceImage", 0, "Transform_Scale", 0)
        self.add("Tones_Prep", "tones_range", bx, y + R, value=0.5, contrast=0.15, width=0.25)
        self.wire("Transform_Scale", 0, "Tones_Prep", 0)
        self.add("Buffer_Prep", "buffer", bx, y + R * 2)
        self.wire("Tones_Prep", 0, "Buffer_Prep", 0)

        self.add("Kaleidoscope_Tile", "kaleidoscope", cx, y, count=6, offset=0)
        self.wire("Buffer_Prep", 0, "Kaleidoscope_Tile", 0)
        self.add("Mirror_Tile", "mirror", cx, y + R, direction=0, offset=0.5)
        self.wire("Kaleidoscope_Tile", 0, "Mirror_Tile", 0)
        self.add("Transform_Repeat", "transform", cx, y + R * 2, scale_x=1, scale_y=1, repeat=True)
        self.wire("Mirror_Tile", 0, "Transform_Repeat", 0)
        self.add("Shape_Seam", "shape", cx, y + R * 3, shape=1, sides=64, radius=0.95, edge=0.15)
        self.add("Blend_Seam", "blend", cx, y + R * 4, amount="$SeamBlend", blend_type=BT_SCREEN)
        self.wire("Transform_Repeat", 0, "Blend_Seam", 0)
        self.wire("Transform_Repeat", 0, "Blend_Seam", 1)
        self.wire("Shape_Seam", 0, "Blend_Seam", 2)
        tiled = "Blend_Seam"

        # == NIKKI ==
        ny = y
        self.add("DreamGrade", "colorize", nx, ny, gradient=GRADIENT_DREAM)
        self.wire(tiled, 0, "DreamGrade", 0)
        self.add("Perlin_Sparkle", "perlin", nx, ny + R, scale_x=32, scale_y=32, iterations=3, persistence=0.6)
        self.add("Translate_Sparkle", "translate", nx, ny + R * 2, translate_x=f"{phase} * $SparkleDriftSpeed", translate_y=0)
        self.wire("Perlin_Sparkle", 0, "Translate_Sparkle", 0)
        self.add("Blend_Sparkle", "blend", nx, ny + R * 3, amount="$NikkiSparkleAmount", blend_type=BT_MAX)
        self.wire("DreamGrade", 0, "Blend_Sparkle", 0)
        self.wire("Translate_Sparkle", 0, "Blend_Sparkle", 1)
        self.add("Noise_Fabric", "perlin", nx, ny + R * 4, scale_x=64, scale_y=64, iterations=2, persistence=0.4)
        self.add("Blend_FabricMicro", "blend", nx, ny + R * 5, amount="$NikkiFabricDetail", blend_type=BT_OVERLAY)
        self.wire("Blend_Sparkle", 0, "Blend_FabricMicro", 0)
        self.wire("Noise_Fabric", 0, "Blend_FabricMicro", 1)
        self.add("SCurve_Nikki", "tones_range", nx, ny + R * 6, value="$NikkiPastelLift", contrast=0.2, width=0.3)
        self.wire("Blend_FabricMicro", 0, "SCurve_Nikki", 0)
        self.add("Blend_Nikki", "blend", nx, ny + R * 7, amount="$StyleNikki", blend_type=BT_LERP)
        self.wire(tiled, 0, "Blend_Nikki", 0)
        self.wire("SCurve_Nikki", 0, "Blend_Nikki", 1)
        self.add("Emissive_Nikki", "blend", nx, ny + R * 8, amount="$NikkiSparkleAmount", blend_type=BT_MAX)
        self.wire("Translate_Sparkle", 0, "Emissive_Nikki", 0)
        self.wire("DreamGrade", 0, "Emissive_Nikki", 1)
        nikki_out, nikki_em = "Blend_Nikki", "Emissive_Nikki"

        # == MADOKA ==
        my = y
        self.add("Voronoi_Maze", "voronoi", mx, my, scale_x="$WitchBarrierWallpaperScale", scale_y="$WitchBarrierWallpaperScale", randomness="$WitchBarrierMazeTightness")
        self.add("Rotate_Madoka", "rotate", mx, my + R, rotate=f"({self.anim_var} * $AnimSpeed + $AnimOffset) * $WitchBarrierPhaseSpeed * 360", cx=0.5, cy=0.5)
        self.wire("Voronoi_Maze", 0, "Rotate_Madoka", 0)
        self.add("Warp_Madoka", "warp", mx, my + R * 2, amount=0.08, eps=0.05)
        self.wire("Rotate_Madoka", 0, "Warp_Madoka", 0)
        warp_out = "Warp_Madoka"
        self.add("Colorize_MadokaCute", "colorize", mx, my + R * 3, gradient=GRADIENT_MADOKA_CUTE)
        self.wire(warp_out, 0, "Colorize_MadokaCute", 0)
        self.add("Colorize_MadokaCorrupt", "colorize", mx, my + R * 4, gradient=GRADIENT_MADOKA_CORRUPT)
        self.wire(warp_out, 0, "Colorize_MadokaCorrupt", 0)
        self.add("Blend_MadokaColors", "blend", mx, my + R * 5, amount="$MadokaCuteBias", blend_type=BT_LERP)
        self.wire("Colorize_MadokaCute", 0, "Blend_MadokaColors", 0)
        self.wire("Colorize_MadokaCorrupt", 0, "Blend_MadokaColors", 1)
        self.add("Blur_SSS_Glow", "blur", mx, my + R * 6, variations=1, filter=1, sigma=8)
        self.wire("Colorize_MadokaCute", 0, "Blur_SSS_Glow", 0)
        self.add("Blend_SSS_Glow", "blend", mx, my + R * 7, amount="$MadokaGlowAmount", blend_type=BT_MAX)
        self.wire("Blur_SSS_Glow", 0, "Blend_SSS_Glow", 0)
        self.wire("Blend_MadokaColors", 0, "Blend_SSS_Glow", 1)
        self.add("Distance_Madoka", "shape", mx, my + R * 8, shape=0, sides=64, radius=0.95, edge=0.15)
        self.add("Translate_Radial", "translate", mx, my + R * 9, translate_x=f"{self.anim_wave(0.2)} * 0.1", translate_y=0)
        self.wire("Distance_Madoka", 0, "Translate_Radial", 0)
        self.add("Colorize_Radial", "colorize", mx, my + R * 10, gradient=GRADIENT_MADOKA_EMISSIVE)
        self.wire("Translate_Radial", 0, "Colorize_Radial", 0)
        self.add("Blend_Radial", "blend", mx, my + R * 11, amount=0.4, blend_type=BT_ADD)
        self.wire("Blend_SSS_Glow", 0, "Blend_Radial", 0)
        self.wire("Colorize_Radial", 0, "Blend_Radial", 1)
        self.add("Edge_MadokaVeins", "edge_detect", mx, my + R * 12, size=2)
        self.wire(warp_out, 0, "Edge_MadokaVeins", 0)
        self.add("Colorize_MadokaEmissive", "colorize", mx, my + R * 13, gradient=GRADIENT_MADOKA_EMISSIVE)
        self.wire(warp_out, 0, "Colorize_MadokaEmissive", 0)
        self.add("Glow_MadokaEmissive", "blur", mx, my + R * 14, variations=1, filter=1, sigma=4)
        self.wire("Colorize_MadokaEmissive", 0, "Glow_MadokaEmissive", 0)
        self.add("Blend_MadokaEmissive", "blend", mx, my + R * 15, amount="$MadokaEmissiveBrightness", blend_type=BT_MAX)
        self.wire("Glow_MadokaEmissive", 0, "Blend_MadokaEmissive", 0)
        self.wire("Edge_MadokaVeins", 0, "Blend_MadokaEmissive", 1)
        self.add("Blend_Madoka", "blend", mx, my + R * 16, amount="$StyleMadoka", blend_type=BT_LERP)
        self.wire(nikki_out, 0, "Blend_Madoka", 0)
        self.wire("Blend_Radial", 0, "Blend_Madoka", 1)
        madoka_out, madoka_em = "Blend_Madoka", "Blend_MadokaEmissive"

        # == ITTO ==
        iy = y
        self.add("Truchet_Itto", "truchet", ix, iy, size="$IttoPatternScale", shape=0)
        self.add("Translate_IttoBase", "translate", ix, iy + R, translate_x=f"{phase_slow} * 0.05", translate_y=0)
        self.wire("Truchet_Itto", 0, "Translate_IttoBase", 0)
        self.add("Colorize_Itto", "colorize", ix, iy + R * 2, gradient=GRADIENT_ITTO)
        self.wire("Translate_IttoBase", 0, "Colorize_Itto", 0)
        self.add("Edge_Curvature", "edge_detect", ix, iy + R * 3, size=4)
        self.wire("Translate_IttoBase", 0, "Edge_Curvature", 0)
        self.add("Levels_Curvature", "tones_range", ix, iy + R * 4, value=0.3, contrast=0.5, width=0.2)
        self.wire("Edge_Curvature", 0, "Levels_Curvature", 0)
        self.add("Noise_Wear", "perlin", ix, iy + R * 5, scale_x=16, scale_y=16, iterations=2, persistence=0.5)
        self.add("Blend_Wear", "blend", ix, iy + R * 6, amount="$IttoWearAmount", blend_type=BT_MUL)
        self.wire("Levels_Curvature", 0, "Blend_Wear", 0)
        self.wire("Noise_Wear", 0, "Blend_Wear", 1)
        self.add("Perlin_Detail", "perlin", ix, iy + R * 7, scale_x=128, scale_y=128, iterations=2, persistence=0.4)
        self.add("Worley_Cracks", "voronoi", ix, iy + R * 8, scale_x=8, scale_y=8, randomness=0.7)
        self.add("Blend_Breakup", "blend", ix, iy + R * 9, amount="$IttoBreakupAmount", blend_type=BT_OVERLAY)
        self.wire("Perlin_Detail", 0, "Blend_Breakup", 0)
        self.wire("Worley_Cracks", 0, "Blend_Breakup", 1)
        self.add("Edge_Cracks", "edge_detect", ix, iy + R * 10, size=1)
        self.wire("Worley_Cracks", 0, "Edge_Cracks", 0)
        self.add("Perlin_Erosion", "perlin", ix, iy + R * 11, scale_x=6, scale_y=6, iterations=2, persistence=0.5)
        self.add("Translate_Erosion", "translate", ix, iy + R * 12, translate_x=f"{phase_slow} * 0.02", translate_y=0)
        self.wire("Perlin_Erosion", 0, "Translate_Erosion", 0)
        self.add("Blend_Erosion", "blend", ix, iy + R * 13, amount="$IttoErosionStrength", blend_type=BT_MUL)
        self.wire("Blend_Wear", 0, "Blend_Erosion", 0)
        self.wire("Translate_Erosion", 0, "Blend_Erosion", 1)
        self.add("Blend_IttoMerge", "blend", ix, iy + R * 14, amount=0.5, blend_type=BT_LERP)
        self.wire("Colorize_Itto", 0, "Blend_IttoMerge", 0)
        self.wire("Blend_Breakup", 0, "Blend_IttoMerge", 1)
        self.add("Blend_IttoFinal", "blend", ix, iy + R * 15, amount="$IttoInkStrength", blend_type=BT_LERP)
        self.wire("Blend_IttoMerge", 0, "Blend_IttoFinal", 0)
        self.wire("Edge_Cracks", 0, "Blend_IttoFinal", 1)
        self.add("Edge_IttoInk", "edge_detect", ix, iy + R * 16, size=2)
        self.wire("Translate_IttoBase", 0, "Edge_IttoInk", 0)
        self.add("Blend_Itto", "blend", ix, iy + R * 17, amount="$StyleItto", blend_type=BT_LERP)
        self.wire(madoka_out, 0, "Blend_Itto", 0)
        self.wire("Blend_IttoFinal", 0, "Blend_Itto", 1)
        itto_out = "Blend_Itto"

        # == CELESTIAL ==
        cely = y
        self.add("Image_SphereMap", "image", celx, cely, image=f"{nasa}/blue_marble_4k.jpg", fix_ar=False, clamp=True)
        self.add("Transform_Sphere", "transform", celx, cely + R, scale_x="$CelestialScale", scale_y="$CelestialScale", repeat=True)
        self.wire("Image_SphereMap", 0, "Transform_Sphere", 0)
        self.add("Image_Hubble", "image", celx, cely + R * 2, image=f"{nasa}/hubble_carina_4k.jpg", fix_ar=False, clamp=True)
        self.add("Transform_Nebula", "transform", celx, cely + R * 3, scale_x="$CelestialNebulaScale", scale_y="$CelestialNebulaScale", repeat=True)
        self.wire("Image_Hubble", 0, "Transform_Nebula", 0)
        self.add("Translate_Nebula", "translate", celx, cely + R * 4, translate_x=f"{phase} * $CelestialNebulaScale", translate_y=0)
        self.wire("Transform_Nebula", 0, "Translate_Nebula", 0)
        self.add("Colorize_NebulaEmissive", "colorize", celx, cely + R * 5, gradient=GRADIENT_NEBULA_EMISSIVE)
        self.wire("Translate_Nebula", 0, "Colorize_NebulaEmissive", 0)
        self.add("Image_StarMask", "image", celx, cely + R * 6, image=f"{nasa}/star_mask.png", fix_ar=False, clamp=True)
        self.add("Transform_Stars", "transform", celx, cely + R * 7, scale_x=1, scale_y=1, repeat=True)
        self.wire("Image_StarMask", 0, "Transform_Stars", 0)
        self.add("Translate_Stars", "translate", celx, cely + R * 8, translate_x=f"{phase} * $CelestialDrift", translate_y=0)
        self.wire("Transform_Stars", 0, "Translate_Stars", 0)
        self.add("Tones_Twinkle", "tones_range", celx, cely + R * 9, value="$CelestialTwinkle", contrast=0, width=0.5)
        self.wire("Translate_Stars", 0, "Tones_Twinkle", 0)
        self.add("Blend_Stars", "blend", celx, cely + R * 10, amount=0.8, blend_type=BT_MAX)
        self.wire("Tones_Twinkle", 0, "Blend_Stars", 0)
        self.wire("Colorize_NebulaEmissive", 0, "Blend_Stars", 1)
        self.add("Perlin_CMB", "perlin", celx, cely + R * 11, scale_x=2, scale_y=2, iterations=4, persistence=0.8)
        self.add("Tones_CMB", "tones_range", celx, cely + R * 12, value=0.5, contrast=0.7, width=0.35)
        self.wire("Perlin_CMB", 0, "Tones_CMB", 0)
        self.add("Blend_CMB", "blend", celx, cely + R * 13, amount="$CelestialCMBAmount", blend_type=BT_MUL)
        self.wire("Blend_Stars", 0, "Blend_CMB", 0)
        self.wire("Tones_CMB", 0, "Blend_CMB", 1)
        orbit_rot = f"({self.anim_var} * $AnimSpeed + $AnimOffset) * 360.0 / $CelestialOrbitPeriod * $CelestialOrbitSpeed"
        self.add("Rotate_Orbit", "rotate", celx, cely + R * 14, rotate=orbit_rot, cx=0.5, cy=0.5)
        self.wire("Blend_CMB", 0, "Rotate_Orbit", 0)
        self.add("Blend_CelestialEmissive", "blend", celx, cely + R * 15, amount="$CelestialEmissiveBoost", blend_type=BT_MAX)
        self.wire("Colorize_NebulaEmissive", 0, "Blend_CelestialEmissive", 0)
        self.wire("Tones_Twinkle", 0, "Blend_CelestialEmissive", 1)
        self.add("Blend_SphereNebula", "blend", celx, cely + R * 17, amount=0.45, blend_type=BT_LERP)
        self.wire("Transform_Sphere", 0, "Blend_SphereNebula", 0)
        self.wire("Rotate_Orbit", 0, "Blend_SphereNebula", 1)
        self.add("Image_MoonElev", "image", celx, cely + R * 18, image=f"{nasa}/moon_lro_elevation_2k.png", fix_ar=False, clamp=True)
        self.add("Image_MarsRough", "image", celx, cely + R * 19, image=f"{nasa}/mars_mola_2k.png", fix_ar=False, clamp=True)
        self.add("Blend_Celestial", "blend", celx, cely + R * 20, amount="$StyleCelestial", blend_type=BT_SCREEN)
        self.wire(itto_out, 0, "Blend_Celestial", 0)
        self.wire("Blend_SphereNebula", 0, "Blend_Celestial", 1)
        final_color, celestial_em = "Blend_Celestial", "Blend_CelestialEmissive"

        # == HEIGHT ==
        hy = y
        self.add("Colorize_HeightBase", "colorize", hx, hy, gradient=GRADIENT_BW)
        self.wire(final_color, 0, "Colorize_HeightBase", 0)
        self.add("Blend_HeightMoon", "blend", hx, hy + R, amount=0.35, blend_type=BT_LERP)
        self.wire("Colorize_HeightBase", 0, "Blend_HeightMoon", 0)
        self.wire("Image_MoonElev", 0, "Blend_HeightMoon", 1)
        self.add("Blend_HeightItto", "blend", hx, hy + R * 2, amount="$IttoCrackDepth", blend_type=BT_LERP)
        self.wire("Blend_HeightMoon", 0, "Blend_HeightItto", 0)
        self.wire("Translate_IttoBase", 0, "Blend_HeightItto", 1)
        self.add("Blend_HeightMadoka", "blend", hx, hy + R * 3, amount=0.25, blend_type=BT_LERP)
        self.wire("Blend_HeightItto", 0, "Blend_HeightMadoka", 0)
        self.wire(warp_out, 0, "Blend_HeightMadoka", 1)
        self.add("Buffer_Height", "buffer", hx, hy + R * 4)
        self.wire("Blend_HeightMadoka", 0, "Buffer_Height", 0)

        # == PBR ==
        pby = y
        self.add("Colorize_AlbExport", "colorize", px, pby, gradient=GRADIENT_BW)
        self.wire(final_color, 0, "Colorize_AlbExport", 0)
        self.add("Blend_Albedo", "blend", px, pby + R, amount=0.85, blend_type=BT_LERP)
        self.wire(final_color, 0, "Blend_Albedo", 0)
        self.wire("Colorize_AlbExport", 0, "Blend_Albedo", 1)

        self.add("Colorize_Rough", "colorize", px, pby + R * 2, gradient=GRADIENT_ROUGH)
        self.wire("Buffer_Height", 0, "Colorize_Rough", 0)
        self.add("Noise_RoughMicro", "perlin", px, pby + R * 3, scale_x=64, scale_y=64, iterations=2, persistence=0.4)
        self.add("Blend_RoughMicro", "blend", px, pby + R * 4, amount="$RoughnessContrast", blend_type=BT_OVERLAY)
        self.wire("Colorize_Rough", 0, "Blend_RoughMicro", 0)
        self.wire("Noise_RoughMicro", 0, "Blend_RoughMicro", 1)
        self.add("Blend_RoughMars", "blend", px, pby + R * 5, amount=0.4, blend_type=BT_LERP)
        self.wire("Blend_RoughMicro", 0, "Blend_RoughMars", 0)
        self.wire("Image_MarsRough", 0, "Blend_RoughMars", 1)
        self.add("Uniform_Black", "uniform", px, pby + R * 5, color=COLOR_BLACK)
        self.add("Tones_RoughBias", "blend", px, pby + R * 6, amount="$RoughnessBias", blend_type=BT_LERP)
        self.wire("Uniform_Black", 0, "Tones_RoughBias", 0)
        self.wire("Blend_RoughMars", 0, "Tones_RoughBias", 1)

        self.add("Blend_MetVeins", "blend", px, pby + R * 7, amount="$MadokaVeinEmissive", blend_type=BT_LERP)
        self.wire("Edge_MadokaVeins", 0, "Blend_MetVeins", 0)
        self.wire("Edge_Cracks", 0, "Blend_MetVeins", 1)
        self.add("Blend_MetStars", "blend", px, pby + R * 8, amount=0.6, blend_type=BT_LERP)
        self.wire("Blend_MetVeins", 0, "Blend_MetStars", 0)
        self.wire("Image_StarMask", 0, "Blend_MetStars", 1)
        self.add("Tones_Metallic", "blend", px, pby + R * 9, amount="$MetallicAmount", blend_type=BT_LERP)
        self.wire("Uniform_Black", 0, "Tones_Metallic", 0)
        self.wire("Blend_MetStars", 0, "Tones_Metallic", 1)

        self.add("Blend_EmissiveStack", "blend", px, pby + R * 10, amount="$EmissiveIntensity", blend_type=BT_MAX)
        self.wire(nikki_em, 0, "Blend_EmissiveStack", 0)
        self.wire(madoka_em, 0, "Blend_EmissiveStack", 1)
        self.add("Blend_EmissiveFinal", "blend", px, pby + R * 11, amount="$StyleCelestial", blend_type=BT_MAX)
        self.wire("Blend_EmissiveStack", 0, "Blend_EmissiveFinal", 0)
        self.wire(celestial_em, 0, "Blend_EmissiveFinal", 1)

        self.add("Blur_AO", "blur", px, pby + R * 12, variations=1, filter=1, sigma=3)
        self.wire("Buffer_Height", 0, "Blur_AO", 0)
        self.add("Colorize_AO", "colorize", px, pby + R * 13, gradient=GRADIENT_BW)
        self.wire("Blur_AO", 0, "Colorize_AO", 0)
        self.add("Tones_AO", "blend", px, pby + R * 14, amount="$AOStrength", blend_type=BT_LERP)
        self.wire("Uniform_Black", 0, "Tones_AO", 0)
        self.wire("Colorize_AO", 0, "Tones_AO", 1)

        self.add("Normal_Map", "normal_map", px, pby + R * 15, param0=11, param1="$NormalStrength", param2=0, param4=1)
        self.wire("Buffer_Height", 0, "Normal_Map", 0)
        self.add("Normal_Detail", "normal_map", px, pby + R * 16, param0=11, param1="$NormalDetail", param2=0, param4=1)
        self.wire("Noise_Fabric", 0, "Normal_Detail", 0)
        self.add("Blend_NormalDetail", "blend", px, pby + R * 17, amount="$NormalDetail", blend_type=BT_LERP)
        self.wire("Normal_Map", 0, "Blend_NormalDetail", 0)
        self.wire("Normal_Detail", 0, "Blend_NormalDetail", 1)
        self.add("Convert_NormalDX", "normal_map_convert", px, pby + R * 18, op=1)
        self.wire("Blend_NormalDetail", 0, "Convert_NormalDX", 0)

        self.add("Tones_Opacity", "tones_range", px, pby + R * 19, value=1, contrast=0.5, width=0.25)
        self.wire(warp_out, 0, "Tones_Opacity", 0)

        self.add("Blend_SSS", "blend", px, pby + R * 20, amount="$SSSAmount", blend_type=BT_LERP)
        self.wire("DreamGrade", 0, "Blend_SSS", 0)
        self.wire("Colorize_AlbExport", 0, "Blend_SSS", 1)

        # == MATERIAL ==
        mat_type = "material_dynamic" if self.dynamic else "material"
        self.nodes.append({
            "export_paths": {},
            "name": "Material",
            "node_position": {"x": ox, "y": y + R * 2},
            "parameters": {
                "albedo_color": {"a": 1, "b": 1, "g": 1, "r": 1, "type": "Color"},
                "ao": 1,
                "depth_scale": "$HeightScale",
                "emission_energy": 1,
                "flags_transparent": True,
                "metallic": 1,
                "normal": 1,
                "roughness": 1,
                "size": "$ExportResolution",
                "sss": 0.15,
            },
            "type": mat_type,
        })
        self.wire("Blend_Albedo", 0, "Material", P_ALBEDO)
        self.wire("Tones_Metallic", 0, "Material", P_MET)
        self.wire("Tones_RoughBias", 0, "Material", P_ROUGH)
        self.wire("Blend_EmissiveFinal", 0, "Material", P_EMISS)
        self.wire("Normal_Map", 0, "Material", P_NORM)
        self.wire("Tones_AO", 0, "Material", P_AO)
        self.wire("Buffer_Height", 0, "Material", P_DEPTH)
        self.wire("Tones_Opacity", 0, "Material", P_OPACITY)
        self.wire("Blend_SSS", 0, "Material", P_SSS)

        if not self.dynamic:
            exports = [
                ("Export_Emission", "Blend_EmissiveFinal", "$project_emission_$resolution", 0),
                ("Export_Opacity", "Tones_Opacity", "$project_opacity_$resolution", 0),
                ("Export_SSS", "Blend_SSS", "$project_sss_$resolution", 3),
                ("Export_HeightEXR", "Buffer_Height", "$project_height_$resolution", 3),
                ("Export_NormalDX", "Convert_NormalDX", "$project_normal_dx_$resolution", 0),
                ("Export_Roughness", "Tones_RoughBias", "$project_roughness_$resolution", 0),
                ("Export_Metallic", "Tones_Metallic", "$project_metallic_$resolution", 0),
                ("Export_AO", "Tones_AO", "$project_ao_$resolution", 0),
            ]
            for i, (ename, src, suffix, fmt) in enumerate(exports):
                self.nodes.append({
                    "name": ename,
                    "node_position": {"x": ox + 280, "y": y + i * 90},
                    "parameters": {"size": "$ExportResolution", "format": fmt, "suffix": suffix},
                    "type": "export",
                })
                self.wire(src, 0, ename, 0)

        return {
            "type": "graph",
            "name": "MM_Master_SurrealAnimatedPBR_v2",
            "label": "MM Master Surreal Animated PBR v2",
            "longdesc": "v2: 3-layer architecture. Base Utility + PBR Engine + Style Trees (Nikki/Madoka/Itto/Celestial)",
            "shortdesc": "",
            "node_position": {"x": 0, "y": 0},
            "parameters": {},
            "nodes": self.nodes,
            "connections": self.connections,
        }


def write_ptex(path, graph):
    path.write_text(json.dumps(graph, indent="\t") + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(graph['nodes'])} nodes, {len(graph['connections'])} connections)")


def main():
    parser = argparse.ArgumentParser(description="Build Surreal Animated PBR v2 master graphs")
    parser.add_argument("--source-image", default="NASA_Refs/blue_marble_4k.jpg",
                        help="Relative path for SourceImage node")
    args = parser.parse_args()
    static = GraphBuilderV2(dynamic=False, source_image=args.source_image).build()
    dynamic = GraphBuilderV2(dynamic=True, source_image=args.source_image).build()
    write_ptex(OUT_STATIC, static)
    write_ptex(OUT_DYNAMIC, dynamic)
    print(f"\nStatic:  {OUT_STATIC.name} ({len(static['nodes'])} nodes)")
    print(f"Dynamic: {OUT_DYNAMIC.name} ({len(dynamic['nodes'])} nodes)")
    print("Done.")


if __name__ == "__main__":
    main()