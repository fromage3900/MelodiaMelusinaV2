"""
Author Production-Grade Fantasy Fabric PBR Texture Library (Infinity Nikki Grade)
==================================================================================
Procedural synthesis and zero-loss packing of tileable 4K / 2K PBR texture sets
for Melodia and Melusina wardrobe, following the canonical Melodia ORM standard:
    - BaseColor (_BC): 8-bit RGB (sRGB = True)
    - Packed ORM (_ORM): 8-bit Linear RGB (R=AO, G=Roughness, B=Metallic, sRGB = False)
    - Tangent Normal (_N / _DetailN): 8-bit BC5 DirectX Tangent Normal (sRGB = False)
    - Height (_H): 8-bit Linear Grayscale displacement / POM (sRGB = False)
    - Auxiliary Masks (_Sheen, _Sparkle, _Mask, _Alpha): 8-bit Linear Grayscale

Generates the 6 Core Fantasy Fabric Archetypes:
    1. Royal Velvet: Deep micro-fiber dual-sheen, high roughness body (0.75-0.90), grazing Fresnel sheen.
    2. Gilded Jacquard & Brocade: Metallic gold embroidery over satin weave with height-compete relief and anisotropic split.
    3. Sheer Silk & Chiffon: High anisotropic streak highlights (0.85), fine weave normal perturbation, dual-tone Fresnel shift.
    4. Baroque Filigree Lace: Intricate openwork tracery, alpha-masked open threads, micro-fiber edge fuzziness.
    5. Gold-Threaded Embroidery: Raised 3D bullion thread relief, anisotropic metallic highlight glints.
    6. Iridescent Celestial Weave: View-dependent dual-tone color shift, sparkling diamond micro-dust motes.

Author: Teamwork Fantasy Fabric Worker (Milestone 2)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image, ImageFilter

PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

try:
    from melodia_pbr_packer import PBRChannelPacker
    from validate_melodia_pipeline import PipelineValidator
except ImportError:
    PBRChannelPacker = None
    PipelineValidator = None


class ProceduralMath:
    """Vectorized mathematical utilities for procedural texture synthesis."""

    @staticmethod
    def generate_fbm_noise(
        width: int,
        height: int,
        base_freq: float = 4.0,
        octaves: int = 5,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
        seed: int = 42,
    ) -> np.ndarray:
        """Generate smooth multi-octave 2D fractional Brownian motion noise."""
        np.random.seed(seed)
        grid_y, grid_x = np.mgrid[0:height, 0:width]
        u = grid_x / float(width)
        v = grid_y / float(height)

        accum = np.zeros((height, width), dtype=np.float32)
        amplitude = 1.0
        max_accum = 0.0

        for oct_idx in range(octaves):
            freq = base_freq * (lacunarity ** oct_idx)
            phase_x = np.random.uniform(0.0, 2.0 * math.pi)
            phase_y = np.random.uniform(0.0, 2.0 * math.pi)
            phase_diag = np.random.uniform(0.0, 2.0 * math.pi)

            layer = (
                np.sin(u * freq * 2.0 * math.pi + phase_x) *
                np.cos(v * freq * 2.0 * math.pi + phase_y) +
                np.sin((u + v) * freq * math.pi + phase_diag) * 0.5
            )
            accum += layer * amplitude
            max_accum += amplitude * 1.5
            amplitude *= persistence

        norm = (accum / max_accum) * 0.5 + 0.5
        return np.clip(norm, 0.0, 1.0)

    @staticmethod
    def height_to_normal_map(
        height_map: np.ndarray,
        strength: float = 2.5,
        flip_green: bool = False,
    ) -> np.ndarray:
        """
        Convert a 2D float height map [0..1] into a tangent-space Normal map [0..255] RGB uint8.
        Uses 3x3 Sobel filtering and normalized unit vectors.
        """
        h, w = height_map.shape
        padded = np.pad(height_map, 1, mode="wrap")

        dzdx = (
            (padded[:-2, 2:] + 2.0 * padded[1:-1, 2:] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2.0 * padded[1:-1, :-2] + padded[2:, :-2])
        ) / 8.0

        dzdy = (
            (padded[2:, :-2] + 2.0 * padded[2:, 1:-1] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2.0 * padded[:-2, 1:-1] + padded[:-2, 2:])
        ) / 8.0

        nx = -dzdx * strength
        ny = -dzdy * strength if not flip_green else dzdy * strength
        nz = np.ones_like(nx)

        length = np.sqrt(nx * nx + ny * ny + nz * nz)
        length = np.maximum(length, 1e-6)

        nx /= length
        ny /= length
        nz /= length

        out = np.zeros((h, w, 3), dtype=np.uint8)
        out[:, :, 0] = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
        out[:, :, 1] = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
        out[:, :, 2] = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)

        return out


class FantasyFabricGenerator:
    """High-fidelity procedural PBR texture generator for Infinity Nikki-grade fabrics."""

    def __init__(self, default_resolution: int = 2048):
        self.default_resolution = default_resolution
        self.math = ProceduralMath()

    # =========================================================================
    # 1. Royal Velvet
    # =========================================================================
    def generate_royal_velvet(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Royal Velvet PBR set:
            - Rich royal burgundy/crimson base with subtle micro-fiber tone shifts
            - Deep micro-fiber dual-sheen map
            - High roughness body (0.75-0.90)
            - Dense micro-pile normal perturbation
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        fbm = self.math.generate_fbm_noise(width, height, base_freq=64.0, octaves=4, seed=101)
        twill = np.sin(u * 256.0 * math.pi) * np.sin(v * 256.0 * math.pi) * 0.05
        micro_pile = np.clip(fbm * 0.8 + twill + 0.1, 0.0, 1.0)

        # Height Map
        h_arr = (micro_pile * 0.20 + 0.45)
        img_h = Image.fromarray((h_arr * 255.0).astype(np.uint8), mode="L")

        # Normal Map
        n_arr = self.math.height_to_normal_map(h_arr, strength=3.2)
        img_n = Image.fromarray(n_arr, mode="RGB")

        # BaseColor: Deep royal crimson [118, 14, 38]
        base_r = 118.0
        base_g = 14.0
        base_b = 38.0

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        fiber_mod = (micro_pile - 0.5) * 0.18 + 1.0
        bc_arr[:, :, 0] = np.clip(base_r * fiber_mod, 0, 255).astype(np.uint8)
        bc_arr[:, :, 1] = np.clip(base_g * fiber_mod * 1.1, 0, 255).astype(np.uint8)
        bc_arr[:, :, 2] = np.clip(base_b * fiber_mod * 1.2, 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        # ORM
        ao_arr = np.clip((1.0 - (1.0 - micro_pile) * 0.12) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip((0.75 + micro_pile * 0.14) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.zeros((height, width), dtype=np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        # Sheen
        sheen_arr = np.clip((0.70 + (1.0 - micro_pile) * 0.28) * 255.0, 0, 255).astype(np.uint8)
        img_sheen = Image.fromarray(sheen_arr, mode="L")

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "Sheen": img_sheen,
        }

    # =========================================================================
    # 2. Gilded Jacquard & Brocade
    # =========================================================================
    def generate_gilded_brocade(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Gilded Jacquard & Brocade PBR set:
            - Satin weave base field (midnight royal sapphire)
            - Raised metallic gold/silver damask floral embroidery
            - Height-compete relief and anisotropic split
            - High-frequency detail normal map
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        scale = 3.0
        su = (u * scale) % 1.0
        sv = (v * scale) % 1.0

        dx = su - 0.5
        dy = sv - 0.5
        r = np.sqrt(dx * dx + dy * dy)
        theta = np.arctan2(dy, dx)

        rosette = (
            np.cos(theta * 6.0) * 0.15 +
            np.cos(theta * 12.0) * 0.08 +
            0.28
        )
        damask_mask = np.where(r < rosette, 1.0, 0.0)

        lattice = (
            np.sin(u * scale * 4.0 * math.pi) * np.sin(v * scale * 4.0 * math.pi)
        )
        scroll = np.where((lattice > 0.65) & (r > 0.22), 0.85, 0.0)
        brocade_pattern = np.clip(damask_mask + scroll, 0.0, 1.0)

        brocade_img = Image.fromarray((brocade_pattern * 255.0).astype(np.uint8), mode="L")
        brocade_img = brocade_img.filter(ImageFilter.GaussianBlur(radius=1.5))
        motif_f = np.array(brocade_img, dtype=np.float32) / 255.0

        satin_twill = (
            np.sin(u * 128.0 * 2.0 * math.pi + v * 64.0 * 2.0 * math.pi) * 0.04 + 0.5
        )
        embroidery_stitch = (
            np.sin(u * 256.0 * 2.0 * math.pi) * 0.12 * motif_f
        )

        h_arr = (1.0 - motif_f) * (0.38 + satin_twill * 0.05) + motif_f * (0.75 + embroidery_stitch)
        img_h = Image.fromarray((np.clip(h_arr, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L")

        n_arr = self.math.height_to_normal_map(h_arr, strength=4.5)
        img_n = Image.fromarray(n_arr, mode="RGB")

        detail_h = np.sin(u * 512.0 * math.pi) * np.cos(v * 512.0 * math.pi) * 0.5 + 0.5
        detail_n_arr = self.math.height_to_normal_map(detail_h, strength=1.8)
        img_detail_n = Image.fromarray(detail_n_arr, mode="RGB")

        satin_col = np.array([18.0, 26.0, 52.0])
        gold_col = np.array([238.0, 196.0, 78.0])

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):
            col_chan = (1.0 - motif_f) * satin_col[c] + motif_f * gold_col[c]
            bc_arr[:, :, c] = np.clip(col_chan, 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        ao_arr = np.clip((1.0 - np.abs(motif_f - 0.5) * 0.20) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip(((1.0 - motif_f) * 0.24 + motif_f * 0.20) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.clip(motif_f * 255.0, 0, 255).astype(np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "DetailN": img_detail_n,
        }

    # =========================================================================
    # 3. Sheer Silk & Chiffon
    # =========================================================================
    def generate_sheer_silk(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Sheer Silk & Chiffon PBR set:
            - Ethereal luminescent silk weave with dual-tone pastel shift
            - High anisotropic streak highlights (0.85)
            - Fine directional silk warp/weft normal perturbation
            - Smooth micro-roughness (0.20-0.35)
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        warp = np.sin(u * 128.0 * 2.0 * math.pi) * 0.5 + 0.5
        weft = np.sin(v * 128.0 * 2.0 * math.pi) * 0.5 + 0.5
        silk_weave = (warp * 0.7 + weft * 0.3)

        fbm = self.math.generate_fbm_noise(width, height, base_freq=16.0, octaves=3, seed=202)
        h_arr = np.clip(silk_weave * 0.15 + fbm * 0.10 + 0.45, 0.0, 1.0)
        img_h = Image.fromarray((h_arr * 255.0).astype(np.uint8), mode="L")

        n_arr = self.math.height_to_normal_map(h_arr, strength=2.2)
        img_n = Image.fromarray(n_arr, mode="RGB")

        tint_a = np.array([242.0, 236.0, 248.0])
        tint_b = np.array([252.0, 228.0, 218.0])
        dual_shift = np.sin(u * 4.0 * math.pi + v * 4.0 * math.pi) * 0.5 + 0.5

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):
            val = tint_a[c] * (1.0 - dual_shift) + tint_b[c] * dual_shift
            val = val * (0.95 + silk_weave * 0.08)
            bc_arr[:, :, c] = np.clip(val, 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        ao_arr = np.clip((0.95 + silk_weave * 0.05) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip((0.22 + (1.0 - silk_weave) * 0.10) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.full((height, width), 5, dtype=np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        streak = np.abs(np.sin(u * 64.0 * math.pi)) ** 1.5
        sheen_arr = np.clip((0.60 + streak * 0.35) * 255.0, 0, 255).astype(np.uint8)
        img_sheen = Image.fromarray(sheen_arr, mode="L")

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "Sheen": img_sheen,
        }

    # =========================================================================
    # 4. Baroque Filigree Lace
    # =========================================================================
    def generate_baroque_lace(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Baroque Filigree Lace PBR set:
            - Intricate French needlepoint lace openwork tracery
            - Anti-aliased alpha transparency mask (0 in cutouts, 255 in bullion thread)
            - Cotton lace thread roughness (0.58-0.72)
            - Raised corded lace normal relief
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        scale = 4.0
        su = (u * scale) % 1.0
        sv = (v * scale) % 1.0

        dx = su - 0.5
        dy = sv - 0.5
        r = np.sqrt(dx * dx + dy * dy)
        theta = np.arctan2(dy, dx)

        medallion = np.cos(theta * 8.0) * 0.12 + 0.22
        medallion_mask = np.where(np.abs(r - medallion) < 0.045, 1.0, 0.0)

        center_flower = np.where(r < 0.10, 1.0, 0.0)

        mesh_u = np.sin(u * scale * 16.0 * math.pi)
        mesh_v = np.sin(v * scale * 16.0 * math.pi)
        tulle_mesh = np.where((np.abs(mesh_u) > 0.85) | (np.abs(mesh_v) > 0.85), 0.55, 0.0)

        arch = np.sin(u * scale * 2.0 * math.pi) * np.cos(v * scale * 2.0 * math.pi)
        arch_mask = np.where(np.abs(arch) > 0.70, 0.90, 0.0)

        combined_lace = np.clip(medallion_mask + center_flower + tulle_mesh + arch_mask, 0.0, 1.0)

        lace_img = Image.fromarray((combined_lace * 255.0).astype(np.uint8), mode="L")
        lace_img = lace_img.filter(ImageFilter.GaussianBlur(radius=1.8))
        lace_alpha_f = np.array(lace_img, dtype=np.float32) / 255.0

        img_mask = lace_img

        h_arr = np.clip(lace_alpha_f * 0.85 + (lace_alpha_f > 0.5) * 0.10, 0.0, 1.0)
        img_h = Image.fromarray((h_arr * 255.0).astype(np.uint8), mode="L")

        n_arr = self.math.height_to_normal_map(h_arr, strength=4.8)
        img_n = Image.fromarray(n_arr, mode="RGB")

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        bc_arr[:, :, 0] = np.clip(248.0 * (0.90 + lace_alpha_f * 0.10), 0, 255).astype(np.uint8)
        bc_arr[:, :, 1] = np.clip(244.0 * (0.90 + lace_alpha_f * 0.10), 0, 255).astype(np.uint8)
        bc_arr[:, :, 2] = np.clip(235.0 * (0.90 + lace_alpha_f * 0.10), 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        ao_arr = np.clip((1.0 - (1.0 - lace_alpha_f) * 0.25) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip((0.58 + (1.0 - lace_alpha_f) * 0.14) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.zeros((height, width), dtype=np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "Mask": img_mask,
        }

    # =========================================================================
    # 5. Gold-Threaded Embroidery
    # =========================================================================
    def generate_gold_embroidery(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Gold-Threaded Embroidery PBR set:
            - Heavy 3D bullion gold thread relief over dark royal satin field
            - Anisotropic metallic highlight glints (Metallic 0.95, Roughness 0.22)
            - Spiral wire filament micro-detail normal map
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        scale = 2.0
        su = (u * scale) % 1.0
        sv = (v * scale) % 1.0

        dx = su - 0.5
        dy = sv - 0.5
        r = np.sqrt(dx * dx + dy * dy)
        theta = np.arctan2(dy, dx)

        star_r = (np.abs(np.cos(theta * 4.0)) ** 0.5) * 0.25 + 0.10
        star_mask = np.where(r < star_r, 1.0, 0.0)

        rope_u = np.sin(u * scale * 16.0 * math.pi)
        rope_v = np.cos(v * scale * 16.0 * math.pi)
        border_box = np.where((su < 0.08) | (su > 0.92) | (sv < 0.08) | (sv > 0.92), 1.0, 0.0)
        rope_emboss = np.where(border_box > 0.5, (rope_u * rope_v * 0.5 + 0.5), 0.0)

        combined_emb = np.clip(star_mask + rope_emboss, 0.0, 1.0)
        emb_img = Image.fromarray((combined_emb * 255.0).astype(np.uint8), mode="L")
        emb_img = emb_img.filter(ImageFilter.GaussianBlur(radius=2.0))
        emb_f = np.array(emb_img, dtype=np.float32) / 255.0

        wire_spiral = (np.sin(u * 256.0 * math.pi + v * 256.0 * math.pi) * 0.15) * emb_f

        h_arr = np.clip((1.0 - emb_f) * 0.25 + emb_f * (0.82 + wire_spiral), 0.0, 1.0)
        img_h = Image.fromarray((h_arr * 255.0).astype(np.uint8), mode="L")

        n_arr = self.math.height_to_normal_map(h_arr, strength=5.5)
        img_n = Image.fromarray(n_arr, mode="RGB")

        micro_wire_h = np.sin(u * 512.0 * math.pi) * np.sin(v * 512.0 * math.pi) * 0.5 + 0.5
        detail_n_arr = self.math.height_to_normal_map(micro_wire_h, strength=2.2)
        img_detail_n = Image.fromarray(detail_n_arr, mode="RGB")

        base_col = np.array([22.0, 18.0, 30.0])
        gold_col = np.array([250.0, 208.0, 92.0])

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):
            col_chan = (1.0 - emb_f) * base_col[c] + emb_f * gold_col[c]
            bc_arr[:, :, c] = np.clip(col_chan, 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        ao_arr = np.clip((1.0 - (1.0 - emb_f) * 0.15 - np.abs(emb_f - 0.5) * 0.20) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip(((1.0 - emb_f) * 0.70 + emb_f * 0.24) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.clip(emb_f * 250.0, 0, 255).astype(np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "DetailN": img_detail_n,
        }

    # =========================================================================
    # 6. Iridescent Celestial Weave
    # =========================================================================
    def generate_celestial_weave(
        self, width: int = 2048, height: int = 2048
    ) -> Dict[str, Image.Image]:
        """
        Generate Iridescent Celestial Weave PBR set:
            - Prismatic shot-silk celestial field (nebula gradient)
            - Faceted micro-crystal weave normal perturbation
            - Sparkling diamond micro-dust motes mask
            - Glossy smooth micro-roughness (0.15-0.30)
        """
        gy, gx = np.mgrid[0:height, 0:width]
        u = gx / float(width)
        v = gy / float(height)

        diag_a = np.sin((u + v) * 64.0 * math.pi) * 0.5 + 0.5
        diag_b = np.sin((u - v) * 64.0 * math.pi) * 0.5 + 0.5
        crystal_weave = np.maximum(diag_a, diag_b)

        h_arr = np.clip(crystal_weave * 0.25 + 0.40, 0.0, 1.0)
        img_h = Image.fromarray((h_arr * 255.0).astype(np.uint8), mode="L")

        n_arr = self.math.height_to_normal_map(h_arr, strength=3.0)
        img_n = Image.fromarray(n_arr, mode="RGB")

        grad_u = np.sin(u * 2.0 * math.pi) * 0.5 + 0.5
        grad_v = np.cos(v * 2.0 * math.pi) * 0.5 + 0.5
        shift = (grad_u * 0.6 + grad_v * 0.4)

        col_indigo = np.array([72.0, 88.0, 175.0])
        col_magenta = np.array([195.0, 102.0, 185.0])
        col_aurora = np.array([115.0, 225.0, 240.0])

        bc_arr = np.zeros((height, width, 3), dtype=np.uint8)
        for c in range(3):
            nebula = col_indigo[c] * (1.0 - shift) + col_magenta[c] * shift
            nebula = nebula * (0.92 + crystal_weave * 0.16) + col_aurora[c] * (crystal_weave ** 4) * 0.15
            bc_arr[:, :, c] = np.clip(nebula, 0, 255).astype(np.uint8)
        img_bc = Image.fromarray(bc_arr, mode="RGB")

        ao_arr = np.clip((0.96 + crystal_weave * 0.04) * 255.0, 0, 255).astype(np.uint8)
        rough_arr = np.clip((0.18 + (1.0 - crystal_weave) * 0.10) * 255.0, 0, 255).astype(np.uint8)
        metal_arr = np.full((height, width), 25, dtype=np.uint8)

        img_orm = Image.merge(
            "RGB",
            (
                Image.fromarray(ao_arr, mode="L"),
                Image.fromarray(rough_arr, mode="L"),
                Image.fromarray(metal_arr, mode="L"),
            ),
        )

        np.random.seed(777)
        noise_grid = np.random.uniform(0.0, 1.0, (height, width))
        sparkle_raw = np.where(noise_grid > 0.992, (noise_grid - 0.992) / 0.008, 0.0)
        sparkle_img = Image.fromarray((sparkle_raw * 255.0).astype(np.uint8), mode="L")
        sparkle_img = sparkle_img.filter(ImageFilter.MaxFilter(size=3))
        sparkle_img = sparkle_img.filter(ImageFilter.GaussianBlur(radius=0.8))
        img_sparkle = sparkle_img

        return {
            "BC": img_bc,
            "ORM": img_orm,
            "N": img_n,
            "H": img_h,
            "Sparkle": img_sparkle,
        }

    # =========================================================================
    # Batch Library Generation
    # =========================================================================
    def generate_all_fabric_sets(
        self,
        output_dir: Union[Path, str],
        resolution: int = 2048,
    ) -> Dict[str, Dict[str, Path]]:
        """
        Generate and write all 6 core fantasy fabric archetypes to disk,
        including canonical names and matching aliases.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[MelodiaFabrics] Authoring 6 Core Fantasy Fabric Sets ({resolution}x{resolution}) -> {out_dir}")
        t_start = time.time()

        generator_map = {
            "RoyalVelvet": (self.generate_royal_velvet, ["T_Fabric_RoyalVelvet"]),
            "GildedBrocade": (self.generate_gilded_brocade, ["T_Fabric_GildedBrocade", "T_Fabric_GildedJacquard"]),
            "SheerSilk": (self.generate_sheer_silk, ["T_Fabric_SheerSilk"]),
            "BaroqueLace": (self.generate_baroque_lace, ["T_Fabric_BaroqueLace", "T_Fabric_BaroqueFiligreeLace"]),
            "GoldEmbroidery": (self.generate_gold_embroidery, ["T_Fabric_GoldEmbroidery", "T_Fabric_GoldThreadedEmbroidery"]),
            "CelestialWeave": (self.generate_celestial_weave, ["T_Fabric_CelestialWeave", "T_Fabric_IridescentCelestialWeave"]),
        }

        generated_files: Dict[str, Dict[str, Path]] = {}

        for name, (gen_fn, aliases) in generator_map.items():
            print(f"  -> Synthesizing archetype: '{name}'...")
            maps = gen_fn(width=resolution, height=resolution)
            generated_files[name] = {}

            for base_name in aliases:
                for channel_suffix, img in maps.items():
                    filename = f"{base_name}_{channel_suffix}.png"
                    out_path = out_dir / filename
                    img.save(out_path, format="PNG", compress_level=6)
                    generated_files[name][f"{base_name}_{channel_suffix}"] = out_path

            alias_str = ", ".join(aliases)
            print(f"     [OK] Saved {len(maps)} maps (with aliases: {alias_str})")

        # Also ensure auxiliary Melusina wardrobe textures exist in Character folder
        melusina_tex_dir = out_dir.parent.parent / "Melodia" / "Characters" / "Melusina" / "Textures"
        if not melusina_tex_dir.exists():
            melusina_tex_dir = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina\Textures")

        if melusina_tex_dir.exists():
            print(f"[MelodiaFabrics] Verifying / syncing Melusina auxiliary wardrobe masks in {melusina_tex_dir}...")
            # Frontpanel Sheen
            fp_sheen = melusina_tex_dir / "T_Melusina_FrontPanel_Sheen.png"
            if not fp_sheen.exists() and "RoyalVelvet" in generated_files:
                velvet_sheen = out_dir / "T_Fabric_RoyalVelvet_Sheen.png"
                if velvet_sheen.exists():
                    Image.open(velvet_sheen).save(fp_sheen, format="PNG")
                    Image.open(velvet_sheen).save(melusina_tex_dir / "T_Melusina_Frontpanel_Sheen.png", format="PNG")

            # Sleeve Alpha
            sleeve_alpha = melusina_tex_dir / "T_Melusina_Sleeve_Alpha.png"
            if not sleeve_alpha.exists() and "BaroqueLace" in generated_files:
                lace_mask = out_dir / "T_Fabric_BaroqueLace_Mask.png"
                if lace_mask.exists():
                    Image.open(lace_mask).save(sleeve_alpha, format="PNG")

            # Shirt aliases (T_Melusina_Shirt_* -> T_Melusina_UpdatedShirt_*)
            for sfx in ["BC", "ORM", "N", "H", "Emission", "Mask"]:
                src = melusina_tex_dir / f"T_Melusina_UpdatedShirt_{sfx}.png"
                dst = melusina_tex_dir / f"T_Melusina_Shirt_{sfx}.png"
                if src.exists() and not dst.exists():
                    Image.open(src).save(dst, format="PNG")

        elapsed = time.time() - t_start
        print(f"[MelodiaFabrics] Complete fabric library generated in {elapsed:.2f}s.")
        return generated_files


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Melodia Fantasy Fabric PBR Texture Generator (Infinity Nikki Grade)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=str(PYTHON_DIR.parent / "Textures" / "Fabrics"),
        help="Target output directory for fabric textures",
    )
    parser.add_argument(
        "--resolution", "-r",
        type=int,
        default=2048,
        help="Texture resolution (POT: 1024, 2048, 4096)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run PipelineValidator immediately after generation",
    )
    parser.add_argument(
        "--report",
        default=str(PYTHON_DIR.parent.parent / "Saved" / "Audit" / "author_fantasy_fabrics.json"),
        help="Path to output JSON generation and audit report",
    )

    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    generator = FantasyFabricGenerator(default_resolution=args.resolution)
    generated = generator.generate_all_fabric_sets(output_dir=out_dir, resolution=args.resolution)

    validation_summary = {}
    if args.validate and PipelineValidator:
        print("\n[MelodiaFabrics] Running Melodia Pipeline Quality Validator...")
        validator = PipelineValidator()
        all_textures: Dict[str, Path] = {}
        for p in out_dir.glob("*.png"):
            all_textures[p.stem] = p

        report = validator.validate_texture_set(all_textures)
        validation_summary = {
            "total_textures": report.total_textures,
            "passed": report.passed_textures,
            "failed": report.failed_textures,
            "warnings": report.warning_count,
            "errors": report.error_count,
            "is_valid": report.is_valid(),
        }
        print(f"  Passed: {report.passed_textures}/{report.total_textures} (Errors: {report.error_count}, Warnings: {report.warning_count})")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(out_dir.resolve()),
        "resolution": args.resolution,
        "archetypes": list(generated.keys()),
        "total_files": sum(len(v) for v in generated.values()),
        "validation": validation_summary,
    }
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"[MelodiaFabrics] Audit report saved to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
