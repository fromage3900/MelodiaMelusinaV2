#!/usr/bin/env python3
"""Generate MM_Master_SurrealAnimatedPBR Static + Dynamic .ptex graphs.

  py Tools/MaterialMaker/build_surreal_tile_master.py
  py Tools/MaterialMaker/build_surreal_tile_master.py --source-image path/to/photo.png
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT_STATIC = ROOT / "MM_Master_SurrealAnimatedPBR_Static.ptex"
OUT_DYNAMIC = ROOT / "MM_Master_SurrealAnimatedPBR_Dynamic.ptex"

LANE_WIDTH = 900
LANE_GAP = 200
ROW = 120
HEADER_Y = -420

# Material input ports
P_ALBEDO, P_MET, P_ROUGH, P_EMISS, P_NORM, P_AO, P_DEPTH, P_OPACITY, P_SSS = range(9)


def gradient_bw() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0, "g": 0, "pos": 0, "r": 0},
            {"a": 1, "b": 1, "g": 1, "pos": 1, "r": 1},
        ],
        "type": "Gradient",
    }


def gradient_dream() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0.92, "g": 0.78, "pos": 0, "r": 0.95},
            {"a": 1, "b": 0.88, "g": 0.82, "pos": 0.35, "r": 0.98},
            {"a": 1, "b": 0.95, "g": 0.9, "pos": 0.7, "r": 0.85},
            {"a": 1, "b": 0.75, "g": 0.65, "pos": 1, "r": 0.78},
        ],
        "type": "Gradient",
    }


def gradient_madoka_cute() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0.88, "g": 0.78, "pos": 0, "r": 0.92},
            {"a": 1, "b": 0.55, "g": 0.72, "pos": 1, "r": 0.88},
        ],
        "type": "Gradient",
    }


def gradient_madoka_corrupt() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0.12, "g": 0.15, "pos": 0, "r": 0.98},
            {"a": 1, "b": 0.72, "g": 0.2, "pos": 1, "r": 0.95},
        ],
        "type": "Gradient",
    }


def gradient_itto() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0.08, "g": 0.08, "pos": 0, "r": 0.12},
            {"a": 1, "b": 0.85, "g": 0.82, "pos": 0.45, "r": 0.92},
            {"a": 1, "b": 0.05, "g": 0.04, "pos": 1, "r": 0.55},
        ],
        "type": "Gradient",
    }


def gradient_rough() -> dict:
    return {
        "interpolation": 1,
        "points": [
            {"a": 1, "b": 0.85, "g": 0.85, "pos": 0, "r": 0.85},
            {"a": 1, "b": 0.2, "g": 0.2, "pos": 1, "r": 0.2},
        ],
        "type": "Gradient",
    }


class GraphBuilder:
    def __init__(self, *, dynamic: bool, source_image: str, anim_var: str) -> None:
        self.dynamic = dynamic
        self.source_image = source_image.replace("\\", "/")
        self.anim_var = anim_var  # "$BakeTime" or "$time"
        self.nodes: list[dict] = []
        self.connections: list[dict] = []
        self._lane_x = -5200

    def lane(self, lane_id: str, title: str, subtitle: str = "", *, witch: bool = False) -> int:
        x = self._lane_x
        self._lane_x += LANE_WIDTH + LANE_GAP
        color = {"a": 1, "b": 0.38, "g": 0.12, "r": 0.28, "type": "Color"} if witch else {
            "a": 1, "b": 0.55, "g": 0.35, "r": 0.45, "type": "Color"
        }
        text = f"[lane:{lane_id}]"
        if subtitle:
            text += f"\n{subtitle}"
        self.nodes.append(
            {
                "name": f"Comment_{lane_id}",
                "node_position": {"x": x, "y": HEADER_Y},
                "parameters": {"size": 4},
                "title": title,
                "text": text,
                "size": {"x": LANE_WIDTH - 40, "y": 100},
                "color": color,
                "type": "comment",
            }
        )
        return x

    def add(self, name: str, ntype: str, x: float, y: float, **parameters: Any) -> str:
        self.nodes.append(
            {
                "name": name,
                "node_position": {"x": x, "y": y},
                "parameters": parameters,
                "type": ntype,
            }
        )
        return name

    def wire(self, src: str, src_port: int, dst: str, dst_port: int) -> None:
        self.connections.append(
            {"from": src, "from_port": src_port, "to": dst, "to_port": dst_port}
        )

    def anim_phase_expr(self) -> str:
        return f"fract({self.anim_var} * $AnimSpeed + $AnimOffset)"

    def build(self) -> dict:
        ax = self.lane("00", "00 | INPUT", "Source + Remote params")
        bx = self.lane("01", "01 | PREPROCESS", "Scale · levels · buffer")
        cx = self.lane("02", "02 | SEAMLESS TILE", "Kaleido · mirror · repeat")
        nx = self.lane("08", "08 | NIKKI", "Rim · sparkle · dream grade")
        mx = self.lane("22", "22 | MADOKA", "Witch barrier analog", witch=True)
        ix = self.lane("23", "23 | ITTO", "Oni geometry · ink cracks")
        celx = self.lane("14", "14 | CELESTIAL", "NASA spatial maps")
        hx = self.lane("05", "05 | HEIGHT", "Composite displacement")
        px = self.lane("06", "06 | PBR MAPS", "All channel split")
        ox = self.lane("07", "07 | OUTPUT", "Material + exports")

        y = 40
        nasa = "NASA_Refs"
        phase = self.anim_phase_expr()

        # --- Remote master parameters ---
        remote_widgets = [
            {"name": "BakeTime", "label": "Bake Time", "type": "named_parameter", "min": 0, "max": 1, "step": 0.001, "default": 0},
            {"name": "AnimSpeed", "label": "Anim Speed", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.15},
            {"name": "AnimOffset", "label": "Anim Offset", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "TileRepeat", "label": "Tile Repeat", "type": "named_parameter", "min": 0.5, "max": 8, "step": 0.1, "default": 2},
            {"name": "SeamBlend", "label": "Seam Blend", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.35},
            {"name": "StyleNikki", "label": "Style Nikki", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "StyleMadoka", "label": "Style Madoka", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "StyleItto", "label": "Style Itto", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "StyleCelestial", "label": "Style Celestial", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0},
            {"name": "DreamSaturation", "label": "Dream Saturation", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.18},
            {"name": "PastelLift", "label": "Pastel Lift", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.22},
            {"name": "SparkleDriftSpeed", "label": "Sparkle Drift", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.3},
            {"name": "WitchBarrierPhaseSpeed", "label": "Barrier Phase", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.45},
            {"name": "WitchBarrierWallpaperScale", "label": "Wallpaper Scale", "type": "named_parameter", "min": 1, "max": 12, "step": 0.1, "default": 4},
            {"name": "WitchBarrierMazeTightness", "label": "Maze Tightness", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "WitchBarrierEmissiveVeins", "label": "Emissive Veins", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.35},
            {"name": "IttoPatternScale", "label": "Itto Pattern Scale", "type": "named_parameter", "min": 1, "max": 12, "step": 0.1, "default": 3},
            {"name": "IttoCrackDepth", "label": "Itto Crack Depth", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.4},
            {"name": "IttoInkStrength", "label": "Itto Ink", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.6},
            {"name": "CelestialNebulaScale", "label": "Nebula Scale", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.42},
            {"name": "CelestialTwinkle", "label": "Celestial Twinkle", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.5},
            {"name": "HeightScale", "label": "Height Scale", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.25},
            {"name": "NormalStrength", "label": "Normal Strength", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.8},
            {"name": "RoughnessBias", "label": "Roughness Bias", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.55},
            {"name": "MetallicAmount", "label": "Metallic Amount", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.05},
            {"name": "AOStrength", "label": "AO Strength", "type": "named_parameter", "min": 0, "max": 1, "step": 0.01, "default": 0.7},
            {"name": "ExportResolution", "label": "Export Resolution", "type": "named_parameter", "min": 8, "max": 12, "step": 1, "default": 11},
        ]
        remote_params = {w["name"]: w["default"] for w in remote_widgets}
        self.nodes.append(
            {
                "name": "Remote_MasterParams",
                "node_position": {"x": ax, "y": -180},
                "parameters": remote_params,
                "type": "remote",
                "widgets": remote_widgets,
            }
        )

        # --- 00 INPUT ---
        self.add("SourceImage", "image", ax, y, image=self.source_image, fix_ratio=True, clamp=False)

        # --- 01 PREPROCESS ---
        self.add("Transform_Scale", "transform", bx, y, scale_x="$TileRepeat", scale_y="$TileRepeat", repeat=False)
        self.wire("SourceImage", 0, "Transform_Scale", 0)
        self.add("Tones_Prep", "tones", bx, y + ROW, value=0.5, contrast=0.15)
        self.wire("Transform_Scale", 0, "Tones_Prep", 0)
        self.add("Buffer_Prep", "buffer", bx, y + ROW * 2, size=0)
        self.wire("Tones_Prep", 0, "Buffer_Prep", 0)

        # --- 02 TILE ---
        self.add("Kaleidoscope_Tile", "kaleidoscope", cx, y, count=6, offset=0)
        self.wire("Buffer_Prep", 0, "Kaleidoscope_Tile", 0)
        self.add("Mirror_Tile", "mirror", cx, y + ROW, direction=0, offset=0.5)
        self.wire("Kaleidoscope_Tile", 0, "Mirror_Tile", 0)
        self.add("Transform_Repeat", "transform", cx, y + ROW * 2, scale_x=1, scale_y=1, repeat=True)
        self.wire("Mirror_Tile", 0, "Transform_Repeat", 0)
        self.add("Shape_Seam", "shape", cx, y + ROW * 3, shape=1, sides=64, radius=0.95, edge=0.15)
        self.add("Blend_Seam", "blend", cx, y + ROW * 4, amount="$SeamBlend", blend_type=9)
        self.wire("Transform_Repeat", 0, "Blend_Seam", 0)
        self.wire("Transform_Repeat", 0, "Blend_Seam", 1)
        self.wire("Shape_Seam", 0, "Blend_Seam", 2)

        tiled = "Blend_Seam"

        # --- 08 NIKKI ---
        self.add("DreamGrade", "colorize", nx, y, gradient=gradient_dream())
        self.wire(tiled, 0, "DreamGrade", 0)
        self.add("Perlin_Sparkle", "perlin", nx, y + ROW, scale_x=32, scale_y=32, iterations=3, persistence=0.6)
        self.add("Translate_Sparkle", "translate", nx, y + ROW * 2, translate_x=f"{phase} * $SparkleDriftSpeed", translate_y=0)
        self.wire("Perlin_Sparkle", 0, "Translate_Sparkle", 0)
        self.add("Blend_Sparkle", "blend", nx, y + ROW * 3, amount=0.35, blend_type=12)
        self.wire("DreamGrade", 0, "Blend_Sparkle", 0)
        self.wire("Translate_Sparkle", 0, "Blend_Sparkle", 1)
        self.add("Blend_Nikki", "blend", nx, y + ROW * 4, amount="$StyleNikki", blend_type=0)
        self.wire(tiled, 0, "Blend_Nikki", 0)
        self.wire("Blend_Sparkle", 0, "Blend_Nikki", 1)

        # --- 22 MADOKA ---
        self.add(
            "Voronoi_Maze",
            "voronoi",
            mx,
            y,
            scale_x="$WitchBarrierWallpaperScale",
            scale_y="$WitchBarrierWallpaperScale",
            randomness="$WitchBarrierMazeTightness",
        )
        self.add("Rotate_Madoka", "rotate", mx, y + ROW, rotate=f"{phase} * $WitchBarrierPhaseSpeed * 360", cx=0.5, cy=0.5)
        self.wire("Voronoi_Maze", 0, "Rotate_Madoka", 0)
        self.add("Warp_Madoka", "warp", mx, y + ROW * 2, amount=0.08, eps=0.05)
        self.wire("Rotate_Madoka", 0, "Warp_Madoka", 0)
        self.add("Colorize_MadokaCute", "colorize", mx, y + ROW * 3, gradient=gradient_madoka_cute())
        self.wire("Warp_Madoka", 0, "Colorize_MadokaCute", 0)
        self.add("Colorize_MadokaCorrupt", "colorize", mx, y + ROW * 4, gradient=gradient_madoka_corrupt())
        self.wire("Warp_Madoka", 0, "Colorize_MadokaCorrupt", 0)
        self.add("Blend_MadokaColors", "blend", mx, y + ROW * 5, amount=0.5, blend_type=0)
        self.wire("Colorize_MadokaCute", 0, "Blend_MadokaColors", 0)
        self.wire("Colorize_MadokaCorrupt", 0, "Blend_MadokaColors", 1)
        self.add("Edge_MadokaVeins", "edge_detect", mx, y + ROW * 6, size=2)
        self.wire("Warp_Madoka", 0, "Edge_MadokaVeins", 0)
        self.add("Blend_Madoka", "blend", mx, y + ROW * 7, amount="$StyleMadoka", blend_type=0)
        self.wire("Blend_Nikki", 0, "Blend_Madoka", 0)
        self.wire("Blend_MadokaColors", 0, "Blend_Madoka", 1)

        # --- 23 ITTO ---
        self.add("Truchet_Itto", "truchet", ix, y, size="$IttoPatternScale", shape=0)
        self.add("Translate_Itto", "translate", ix, y + ROW, translate_x=f"{phase} * 0.05", translate_y=0)
        self.wire("Truchet_Itto", 0, "Translate_Itto", 0)
        self.add("Edge_IttoInk", "edge_detect", ix, y + ROW * 2, size=2)
        self.wire("Translate_Itto", 0, "Edge_IttoInk", 0)
        self.add("Colorize_Itto", "colorize", ix, y + ROW * 3, gradient=gradient_itto())
        self.wire("Translate_Itto", 0, "Colorize_Itto", 0)
        self.add("Blend_Itto", "blend", ix, y + ROW * 4, amount="$StyleItto", blend_type=0)
        self.wire("Blend_Madoka", 0, "Blend_Itto", 0)
        self.wire("Colorize_Itto", 0, "Blend_Itto", 1)

        # --- 14 CELESTIAL ---
        self.add("Image_Hubble", "image", celx, y, image=f"{nasa}/hubble_carina_4k.jpg", fix_ratio=False, clamp=True)
        self.add(
            "Transform_NebulaScroll",
            "transform",
            celx,
            y + ROW,
            scale_x="$CelestialNebulaScale",
            scale_y="$CelestialNebulaScale",
            repeat=True,
        )
        self.wire("Image_Hubble", 0, "Transform_NebulaScroll", 0)
        self.add("Translate_Nebula", "translate", celx, y + ROW * 2, translate_x=f"{phase} * $CelestialNebulaScale", translate_y=0)
        self.wire("Transform_NebulaScroll", 0, "Translate_Nebula", 0)
        self.add("Image_MoonElev", "image", celx, y + ROW * 3, image=f"{nasa}/moon_lro_elevation_2k.png", fix_ratio=False, clamp=True)
        self.add("Image_MarsRough", "image", celx, y + ROW * 4, image=f"{nasa}/mars_mola_2k.png", fix_ratio=False, clamp=True)
        self.add("Image_StarMask", "image", celx, y + ROW * 5, image=f"{nasa}/star_mask.png", fix_ratio=False, clamp=True)
        self.add("Blend_Celestial", "blend", celx, y + ROW * 6, amount="$StyleCelestial", blend_type=9)
        self.wire("Blend_Itto", 0, "Blend_Celestial", 0)
        self.wire("Translate_Nebula", 0, "Blend_Celestial", 1)

        final_color = "Blend_Celestial"

        # --- 05 HEIGHT ---
        self.add("Colorize_HeightBase", "colorize", hx, y, gradient=gradient_bw())
        self.wire(final_color, 0, "Colorize_HeightBase", 0)
        self.add("Blend_HeightMoon", "blend", hx, y + ROW, amount=0.35, blend_type=0)
        self.wire("Colorize_HeightBase", 0, "Blend_HeightMoon", 0)
        self.wire("Image_MoonElev", 0, "Blend_HeightMoon", 1)
        self.add("Blend_HeightItto", "blend", hx, y + ROW * 2, amount="$IttoCrackDepth", blend_type=0)
        self.wire("Blend_HeightMoon", 0, "Blend_HeightItto", 0)
        self.wire("Translate_Itto", 0, "Blend_HeightItto", 1)
        self.add("Blend_HeightMadoka", "blend", hx, y + ROW * 3, amount=0.25, blend_type=0)
        self.wire("Blend_HeightItto", 0, "Blend_HeightMadoka", 0)
        self.wire("Warp_Madoka", 0, "Blend_HeightMadoka", 1)
        self.add("Buffer_Height", "buffer", hx, y + ROW * 4, size=0)
        self.wire("Blend_HeightMadoka", 0, "Buffer_Height", 0)

        # --- 06 PBR MAPS ---
        # Albedo (export desat)
        self.add("Colorize_AlbExport", "colorize", px, y, gradient=gradient_bw())
        self.wire(final_color, 0, "Colorize_AlbExport", 0)
        self.add("Blend_Albedo", "blend", px, y + ROW, amount=0.85, blend_type=0)
        self.wire(final_color, 0, "Blend_Albedo", 0)
        self.wire("Colorize_AlbExport", 0, "Blend_Albedo", 1)

        # Roughness
        self.add("Colorize_Rough", "colorize", px, y + ROW * 2, gradient=gradient_rough())
        self.wire("Buffer_Height", 0, "Colorize_Rough", 0)
        self.add("Blend_RoughMars", "blend", px, y + ROW * 3, amount=0.4, blend_type=0)
        self.wire("Colorize_Rough", 0, "Blend_RoughMars", 0)
        self.wire("Image_MarsRough", 0, "Blend_RoughMars", 1)
        self.add("Tones_RoughBias", "tones", px, y + ROW * 4, value="$RoughnessBias", contrast=0)
        self.wire("Blend_RoughMars", 0, "Tones_RoughBias", 0)

        # Metallic
        self.add("Blend_MetVeins", "blend", px, y + ROW * 5, amount="$WitchBarrierEmissiveVeins", blend_type=0)
        self.wire("Edge_MadokaVeins", 0, "Blend_MetVeins", 0)
        self.wire("Edge_IttoInk", 0, "Blend_MetVeins", 1)
        self.add("Blend_MetStars", "blend", px, y + ROW * 6, amount=0.6, blend_type=0)
        self.wire("Blend_MetVeins", 0, "Blend_MetStars", 0)
        self.wire("Image_StarMask", 0, "Blend_MetStars", 1)
        self.add("Tones_Metallic", "tones", px, y + ROW * 7, value="$MetallicAmount", contrast=0)
        self.wire("Blend_MetStars", 0, "Tones_Metallic", 0)

        # Emission
        self.add("Blend_EmissSparkle", "blend", px, y + ROW * 8, amount=0.5, blend_type=12)
        self.wire("Translate_Sparkle", 0, "Blend_EmissSparkle", 0)
        self.wire("Translate_Nebula", 0, "Blend_EmissSparkle", 1)
        self.add("Blend_EmissVeins", "blend", px, y + ROW * 9, amount="$WitchBarrierEmissiveVeins", blend_type=12)
        self.wire("Blend_EmissSparkle", 0, "Blend_EmissVeins", 0)
        self.wire("Edge_MadokaVeins", 0, "Blend_EmissVeins", 1)

        # AO
        self.add("Blur_AO", "blur", px, y + ROW * 10, variations=1, filter=1, sigma=3)
        self.wire("Buffer_Height", 0, "Blur_AO", 0)
        self.add("Colorize_AO", "colorize", px, y + ROW * 11, gradient=gradient_bw())
        self.wire("Blur_AO", 0, "Colorize_AO", 0)
        self.add("Tones_AO", "tones", px, y + ROW * 12, value="$AOStrength", contrast=0)
        self.wire("Colorize_AO", 0, "Tones_AO", 0)

        # Normal
        self.add("Normal_Map", "normal_map", px, y + ROW * 13, param0=11, param1="$NormalStrength", param2=0, param4=1)
        self.wire("Buffer_Height", 0, "Normal_Map", 0)
        self.add("Convert_NormalDX", "normal_map_convert", px, y + ROW * 14, op=1)
        self.wire("Normal_Map", 0, "Convert_NormalDX", 0)

        # Opacity (barrier holes)
        self.add("Tones_Opacity", "tones", px, y + ROW * 15, value=1, contrast=0.5)
        self.wire("Warp_Madoka", 0, "Tones_Opacity", 0)

        # SSS subtle
        self.add("Blend_SSS", "blend", px, y + ROW * 16, amount=0.12, blend_type=0)
        self.wire("DreamGrade", 0, "Blend_SSS", 0)
        self.wire("Colorize_AlbExport", 0, "Blend_SSS", 1)

        # --- 07 OUTPUT Material ---
        mat_type = "material_dynamic" if self.dynamic else "material"
        self.nodes.append(
            {
                "export_paths": {},
                "name": "Material",
                "node_position": {"x": ox, "y": y + ROW * 2},
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
            }
        )
        self.wire("Blend_Albedo", 0, "Material", P_ALBEDO)
        self.wire("Tones_Metallic", 0, "Material", P_MET)
        self.wire("Tones_RoughBias", 0, "Material", P_ROUGH)
        self.wire("Blend_EmissVeins", 0, "Material", P_EMISS)
        self.wire("Normal_Map", 0, "Material", P_NORM)
        self.wire("Tones_AO", 0, "Material", P_AO)
        self.wire("Buffer_Height", 0, "Material", P_DEPTH)
        self.wire("Tones_Opacity", 0, "Material", P_OPACITY)
        self.wire("Blend_SSS", 0, "Material", P_SSS)

        # Export nodes (Static extra maps)
        if not self.dynamic:
            exports = [
                ("Export_Emission", "Blend_EmissVeins", "$project_emission_$resolution", 0),
                ("Export_Opacity", "Tones_Opacity", "$project_opacity_$resolution", 0),
                ("Export_SSS", "Blend_SSS", "$project_sss_$resolution", 3),
                ("Export_HeightEXR", "Buffer_Height", "$project_height_$resolution", 3),
                ("Export_NormalDX", "Convert_NormalDX", "$project_normal_dx_$resolution", 0),
            ]
            for i, (ename, src, suffix, fmt) in enumerate(exports):
                self.nodes.append(
                    {
                        "name": ename,
                        "node_position": {"x": ox + 280, "y": y + i * 90},
                        "parameters": {"size": "$ExportResolution", "format": fmt, "suffix": suffix},
                        "type": "export",
                    }
                )
                self.wire(src, 0, ename, 0)

        return {
            "type": "graph",
            "name": "MM_Master_SurrealAnimatedPBR",
            "label": "MM Master Surreal Animated PBR",
            "longdesc": "Surreal tileable PBR batch converter — Nikki / Madoka / Itto / Celestial lanes",
            "shortdesc": "",
            "node_position": {"x": 0, "y": 0},
            "parameters": {},
            "nodes": self.nodes,
            "connections": self.connections,
        }


def write_ptex(path: Path, graph: dict) -> None:
    path.write_text(json.dumps(graph, indent="\t") + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(graph['nodes'])} nodes, {len(graph['connections'])} connections)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Surreal Animated PBR master graphs")
    parser.add_argument(
        "--source-image",
        default="NASA_Refs/blue_marble_4k.jpg",
        help="Relative path for SourceImage node (patched by batch script)",
    )
    args = parser.parse_args()

    static = GraphBuilder(dynamic=False, source_image=args.source_image, anim_var="$BakeTime").build()
    dynamic = GraphBuilder(dynamic=True, source_image=args.source_image, anim_var="$time").build()

    write_ptex(OUT_STATIC, static)
    write_ptex(OUT_DYNAMIC, dynamic)


if __name__ == "__main__":
    main()
