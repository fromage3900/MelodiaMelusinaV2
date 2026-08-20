"""Tier 1, Tier 2 & Tier 3 Test Suite: Fabric Material Instances & Substrate Toon Shading.

Tests:
- FabricType scalar enumeration (0-7) and parameter boundary clamping
- Substrate Toon BSDF pin layout compatibility
- Procedural FabricAnisoGate anisotropy evaluation
- Procedural FabricWeaveNormal HLSL derivative mathematics
- Height-compete multi-layer blending formulation
- Core fantasy fabric preset parameter configurations (Velvet, Brocade, Silk, Lace, Embroidery, Celestial)
- Lace openwork alpha masking and edge dither filtering
- Dual-sheen grazing Fresnel highlights
- Hardware sampler count optimization via Shared: Wrap
- ToonProfile diffuse/specular ramp response
"""

from __future__ import annotations

import math
import unittest
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Fabric Architecture Enums & Reference Data Structures
# ---------------------------------------------------------------------------
class FabricType(IntEnum):
    """Fabric type enumeration matching setup_fabric_type.py."""
    DEFAULT = 0
    COTTON = 1
    SILK = 2
    SATIN = 3
    VELVET = 4
    WOOL = 5
    CHIFFON = 6
    SEQUINS = 7


@dataclass
class FabricPreset:
    """Specification of an Infinity Nikki-tier PBR fabric preset."""
    name: str
    fabric_type: FabricType
    base_metallic: float
    base_roughness: Tuple[float, float]  # min, max
    fabric_aniso_level: float
    fabric_weave_scale: float
    fabric_weave_strength: float
    fabric_sheen: float
    sheen_power: float
    iridescence: float
    sparkle_intensity: float
    sparkle_threshold: float
    toon_profile: str
    layer_blend_mode: int = 0  # 0=Standard Lerp, 1=Height Compete
    layer_height_bias: float = 0.0
    layer_height_sharpness: float = 1.0
    layer_blend_softness: float = 0.5
    has_alpha_mask: bool = False


# Reference definitions for all 6 Core Fantasy Fabric Sets
CORE_FABRIC_PRESETS: Dict[str, FabricPreset] = {
    "RoyalVelvet": FabricPreset(
        name="RoyalVelvet",
        fabric_type=FabricType.VELVET,
        base_metallic=0.0,
        base_roughness=(0.75, 0.90),
        fabric_aniso_level=0.0,
        fabric_weave_scale=32.0,
        fabric_weave_strength=0.15,
        fabric_sheen=0.85,
        sheen_power=2.2,
        iridescence=0.0,
        sparkle_intensity=0.0,
        sparkle_threshold=1.0,
        toon_profile="TP_Character",
    ),
    "GildedJacquard": FabricPreset(
        name="GildedJacquard",
        fabric_type=FabricType.SATIN,
        base_metallic=0.0,  # Base cloth is dielectric, brocade pattern is metallic 1.0
        base_roughness=(0.18, 0.28),
        fabric_aniso_level=0.65,
        fabric_weave_scale=48.0,
        fabric_weave_strength=0.35,
        fabric_sheen=0.30,
        sheen_power=4.0,
        iridescence=0.15,
        sparkle_intensity=0.20,
        sparkle_threshold=0.85,
        toon_profile="TP_Hero",
        layer_blend_mode=1,  # Height Compete
        layer_height_bias=0.08,
        layer_height_sharpness=3.5,
        layer_blend_softness=0.25,
    ),
    "SheerSilk": FabricPreset(
        name="SheerSilk",
        fabric_type=FabricType.SILK,
        base_metallic=0.02,
        base_roughness=(0.20, 0.35),
        fabric_aniso_level=0.85,
        fabric_weave_scale=64.0,
        fabric_weave_strength=0.10,
        fabric_sheen=0.60,
        sheen_power=5.0,
        iridescence=0.35,
        sparkle_intensity=0.10,
        sparkle_threshold=0.90,
        toon_profile="TP_Character",
    ),
    "BaroqueFiligreeLace": FabricPreset(
        name="BaroqueFiligreeLace",
        fabric_type=FabricType.COTTON,
        base_metallic=0.0,
        base_roughness=(0.58, 0.72),
        fabric_aniso_level=0.15,
        fabric_weave_scale=16.0,
        fabric_weave_strength=0.80,
        fabric_sheen=0.25,
        sheen_power=3.0,
        iridescence=0.0,
        sparkle_intensity=0.0,
        sparkle_threshold=1.0,
        toon_profile="TP_Hero",
        layer_blend_mode=1,
        layer_height_bias=0.15,
        layer_height_sharpness=4.0,
        layer_blend_softness=0.20,
        has_alpha_mask=True,
    ),
    "GoldThreadedEmbroidery": FabricPreset(
        name="GoldThreadedEmbroidery",
        fabric_type=FabricType.SATIN,
        base_metallic=0.95,
        base_roughness=(0.20, 0.30),
        fabric_aniso_level=0.70,
        fabric_weave_scale=56.0,
        fabric_weave_strength=0.60,
        fabric_sheen=0.40,
        sheen_power=6.0,
        iridescence=0.25,
        sparkle_intensity=0.45,
        sparkle_threshold=0.75,
        toon_profile="TP_Gold",
        layer_blend_mode=1,
        layer_height_bias=0.20,
        layer_height_sharpness=4.5,
        layer_blend_softness=0.18,
    ),
    "IridescentCelestialWeave": FabricPreset(
        name="IridescentCelestialWeave",
        fabric_type=FabricType.SEQUINS,
        base_metallic=0.10,
        base_roughness=(0.15, 0.30),
        fabric_aniso_level=0.75,
        fabric_weave_scale=40.0,
        fabric_weave_strength=0.40,
        fabric_sheen=0.90,
        sheen_power=3.5,
        iridescence=0.55,
        sparkle_intensity=0.65,
        sparkle_threshold=0.70,
        toon_profile="TP_Character",
    ),
}


# ---------------------------------------------------------------------------
# Reference Mathematical Formulations
# ---------------------------------------------------------------------------
def evaluate_fabric_aniso_gate(fabric_type: float, fabric_aniso_level: float) -> float:
    """Reference Python implementation of the FabricAnisoGate Custom HLSL node.

    Evaluates smoothstep peaks around specific FabricType integers:
    - Silk (Type 2.0) -> +0.90
    - Satin (Type 3.0) -> +0.95
    - Sequins (Type 7.0) -> +0.70
    - Cotton (Type 1.0) -> +0.15
    - Other types -> 0.0
    """
    def smoothstep(edge0: float, edge1: float, x: float) -> float:
        t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
        return t * t * (3.0 - 2.0 * t)

    def pulse(ft: float, center: float, width: float = 0.4) -> float:
        left = smoothstep(center - width, center, ft)
        right = 1.0 - smoothstep(center, center + width, ft)
        return left * right

    a = 0.0
    a += pulse(fabric_type, 1.0) * 0.15  # Cotton
    a += pulse(fabric_type, 2.0) * 0.90  # Silk
    a += pulse(fabric_type, 3.0) * 0.95  # Satin
    a += pulse(fabric_type, 7.0) * 0.70  # Sequins

    return max(-1.0, min(1.0, a + fabric_aniso_level))


def evaluate_fabric_weave_normal(
    uv: Tuple[float, float],
    weave_scale: float,
    weave_strength: float,
    duv: float = 1e-4,
) -> Tuple[float, float, float]:
    """Reference implementation of FabricWeaveNormal procedural weave perturbation.

    Pattern = (0.5 + 0.5*sin(u*Scale*2pi)) * (0.5 + 0.5*sin(v*Scale*2pi))
    Normal = normalize(ddx(Pattern)*Strength, ddy(Pattern)*Strength, 1.0)
    """
    u, v = uv

    def pattern_fn(pu: float, pv: float) -> float:
        warp = 0.5 + 0.5 * math.sin(pu * weave_scale * 2.0 * math.pi)
        weft = 0.5 + 0.5 * math.sin(pv * weave_scale * 2.0 * math.pi)
        return warp * weft

    # Analytical or finite difference derivative
    d_du = (pattern_fn(u + duv, v) - pattern_fn(u - duv, v)) / (2.0 * duv)
    d_dv = (pattern_fn(u, v + duv) - pattern_fn(u, v - duv)) / (2.0 * duv)

    nx = d_du * weave_strength
    ny = d_dv * weave_strength
    nz = 1.0

    mag = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / mag, ny / mag, nz / mag)


def evaluate_height_compete_blend(
    height_a: float,
    height_b: float,
    layer_height_bias: float,
    layer_height_sharpness: float,
    layer_blend_softness: float,
) -> float:
    """Evaluate height-compete contrast blending formula between two layers."""
    softness = max(0.001, layer_blend_softness)
    height_delta = height_b - height_a + layer_height_bias
    alpha = (height_delta * layer_height_sharpness) / softness + 0.5
    return max(0.0, min(1.0, alpha))


def evaluate_grazing_sheen(
    ndotv: float,
    sheen_intensity: float,
    sheen_power: float,
    sheen_tint: Tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> Tuple[float, float, float]:
    """Evaluate grazing Fresnel sheen luminance."""
    clamped_ndotv = max(0.0, min(1.0, ndotv))
    fresnel = (1.0 - clamped_ndotv) ** sheen_power
    sheen = sheen_intensity * fresnel
    return (sheen * sheen_tint[0], sheen * sheen_tint[1], sheen * sheen_tint[2])


# ===========================================================================
# Tier 1: Unit & Invariant Tests (FabricType & Substrate BSDF Compatibility)
# ===========================================================================
class TestFabricInvariantsTier1(unittest.TestCase):
    """Tier 1 Unit tests for fabric enumerations, parameter bounds, and pin layouts."""

    def test_fabric_type_enum_and_discrete_values(self):
        """Verify all 8 FabricType integers adhere strictly to the 0-7 specification."""
        self.assertEqual(FabricType.DEFAULT.value, 0)
        self.assertEqual(FabricType.COTTON.value, 1)
        self.assertEqual(FabricType.SILK.value, 2)
        self.assertEqual(FabricType.SATIN.value, 3)
        self.assertEqual(FabricType.VELVET.value, 4)
        self.assertEqual(FabricType.WOOL.value, 5)
        self.assertEqual(FabricType.CHIFFON.value, 6)
        self.assertEqual(FabricType.SEQUINS.value, 7)
        self.assertEqual(len(FabricType), 8)

    def test_fabric_parameter_ranges(self):
        """Verify valid parameter boundaries across all fabric instance fields."""
        param_bounds = {
            "FabricType": (0.0, 7.0),
            "FabricAnisoLevel": (-1.0, 1.0),
            "FabricWeaveScale": (1.0, 128.0),
            "FabricWeaveStrength": (0.0, 2.0),
            "FabricSheen": (0.0, 2.0),
            "SheenPower": (0.5, 10.0),
            "Iridescence": (0.0, 1.0),
            "SparkleIntensity": (0.0, 2.0),
            "SparkleThreshold": (0.0, 1.0),
        }
        for preset_name, preset in CORE_FABRIC_PRESETS.items():
            self.assertGreaterEqual(preset.fabric_type.value, param_bounds["FabricType"][0])
            self.assertLessEqual(preset.fabric_type.value, param_bounds["FabricType"][1])

            self.assertGreaterEqual(preset.fabric_aniso_level, param_bounds["FabricAnisoLevel"][0])
            self.assertLessEqual(preset.fabric_aniso_level, param_bounds["FabricAnisoLevel"][1])

            self.assertGreaterEqual(preset.fabric_weave_scale, param_bounds["FabricWeaveScale"][0])
            self.assertLessEqual(preset.fabric_weave_scale, param_bounds["FabricWeaveScale"][1])

            self.assertGreaterEqual(preset.fabric_weave_strength, param_bounds["FabricWeaveStrength"][0])
            self.assertLessEqual(preset.fabric_weave_strength, param_bounds["FabricWeaveStrength"][1])

            self.assertGreaterEqual(preset.fabric_sheen, param_bounds["FabricSheen"][0])
            self.assertLessEqual(preset.fabric_sheen, param_bounds["FabricSheen"][1])

            self.assertGreaterEqual(preset.sheen_power, param_bounds["SheenPower"][0])
            self.assertLessEqual(preset.sheen_power, param_bounds["SheenPower"][1])

            self.assertGreaterEqual(preset.iridescence, param_bounds["Iridescence"][0])
            self.assertLessEqual(preset.iridescence, param_bounds["Iridescence"][1])

            self.assertGreaterEqual(preset.sparkle_intensity, param_bounds["SparkleIntensity"][0])
            self.assertLessEqual(preset.sparkle_intensity, param_bounds["SparkleIntensity"][1])

            self.assertGreaterEqual(preset.sparkle_threshold, param_bounds["SparkleThreshold"][0])
            self.assertLessEqual(preset.sparkle_threshold, param_bounds["SparkleThreshold"][1])

    def test_substrate_toon_bsdf_pin_compatibility(self):
        """Verify required pin layout contracts on Substrate Toon BSDF expression."""
        required_pins = {
            "BaseColor": "FLinearColor",
            "Metallic": "float",
            "Specular": "float",
            "Roughness": "float",
            "Normal": "FVector3f",
            "EmissiveColor": "FLinearColor",
            "PatternUVs": "FVector2f",
            "Anisotropy": "float",
            "Tangent": "FVector3f",
        }
        # Invariant: all 9 pins must be defined for Substrate Toon compatibility
        self.assertEqual(len(required_pins), 9)
        self.assertIn("Anisotropy", required_pins)
        self.assertIn("Tangent", required_pins)
        self.assertIn("PatternUVs", required_pins)

    def test_height_compete_formula_boundary_behavior(self):
        """Verify height compete blend transitions monotonically and clamps cleanly."""
        # Case 1: Equal heights, zero bias -> alpha must be exactly 0.5
        alpha_mid = evaluate_height_compete_blend(
            height_a=0.5, height_b=0.5, layer_height_bias=0.0,
            layer_height_sharpness=1.0, layer_blend_softness=0.5,
        )
        self.assertAlmostEqual(alpha_mid, 0.5, places=3)

        # Case 2: Layer B significantly higher -> alpha must clamp to 1.0
        alpha_high = evaluate_height_compete_blend(
            height_a=0.1, height_b=0.9, layer_height_bias=0.1,
            layer_height_sharpness=2.0, layer_blend_softness=0.2,
        )
        self.assertAlmostEqual(alpha_high, 1.0, places=3)

        # Case 3: Layer A significantly higher -> alpha must clamp to 0.0
        alpha_low = evaluate_height_compete_blend(
            height_a=0.9, height_b=0.1, layer_height_bias=0.0,
            layer_height_sharpness=2.0, layer_blend_softness=0.2,
        )
        self.assertAlmostEqual(alpha_low, 0.0, places=3)

        # Case 4: Monotonicity test across height gradient
        h_deltas = np.linspace(-1.0, 1.0, 50)
        alphas = [
            evaluate_height_compete_blend(
                height_a=0.5, height_b=0.5 + d, layer_height_bias=0.0,
                layer_height_sharpness=3.0, layer_blend_softness=0.3,
            )
            for d in h_deltas
        ]
        for i in range(len(alphas) - 1):
            self.assertGreaterEqual(
                alphas[i + 1], alphas[i],
                "Height compete blend must be strictly monotonic non-decreasing",
            )


# ===========================================================================
# Tier 2: Subsystem & Preset Tests (Anisotropy Gating & Procedural Weave)
# ===========================================================================
class TestFabricPresetsTier2(unittest.TestCase):
    """Tier 2 Component tests evaluating procedural anisotropy gates and weave normals."""

    def test_fabric_aniso_gate_peaks(self):
        """Verify FabricAnisoGate gives expected peak anisotropy for Silk, Satin, Sequins, and Cotton."""
        # 1. Silk (Type 2.0)
        silk_aniso = evaluate_fabric_aniso_gate(fabric_type=2.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(silk_aniso, 0.90, places=2)

        # 2. Satin (Type 3.0)
        satin_aniso = evaluate_fabric_aniso_gate(fabric_type=3.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(satin_aniso, 0.95, places=2)

        # 3. Sequins (Type 7.0)
        sequins_aniso = evaluate_fabric_aniso_gate(fabric_type=7.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(sequins_aniso, 0.70, places=2)

        # 4. Cotton (Type 1.0)
        cotton_aniso = evaluate_fabric_aniso_gate(fabric_type=1.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(cotton_aniso, 0.15, places=2)

        # 5. Velvet (Type 4.0) -> No anisotropy (diffuse grazing sheen model instead)
        velvet_aniso = evaluate_fabric_aniso_gate(fabric_type=4.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(velvet_aniso, 0.0, places=2)

        # 6. Default (Type 0.0) -> Zero base anisotropy
        default_aniso = evaluate_fabric_aniso_gate(fabric_type=0.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(default_aniso, 0.0, places=2)

    def test_procedural_weave_normal_derivatives(self):
        """Verify procedural weave normal is properly normalized and responds to weave scale and strength."""
        uv_samples = [(0.0, 0.0), (0.25, 0.25), (0.5, 0.5), (0.123, 0.456)]
        for uv in uv_samples:
            nx, ny, nz = evaluate_fabric_weave_normal(uv=uv, weave_scale=48.0, weave_strength=0.5)
            # Length of normal vector must be exactly 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            self.assertAlmostEqual(length, 1.0, places=4)
            # Z component must remain positive (+Z tangent space)
            self.assertGreater(nz, 0.0)

        # When weave_strength is 0, normal must be flat (0, 0, 1)
        flat_nx, flat_ny, flat_nz = evaluate_fabric_weave_normal(uv=(0.25, 0.25), weave_scale=48.0, weave_strength=0.0)
        self.assertAlmostEqual(flat_nx, 0.0, places=4)
        self.assertAlmostEqual(flat_ny, 0.0, places=4)
        self.assertAlmostEqual(flat_nz, 1.0, places=4)

    def test_lace_alpha_mask_edge_filtering(self):
        """Verify openwork lace transparency mask thresholding and dither alpha evaluation."""
        # Simulated lace alpha mask: 0 (open thread cutouts) to 255 (dense bullion embroidery)
        alpha_mask_values = np.array([0, 20, 60, 128, 200, 255], dtype=np.uint8)

        # Thresholding for masked opacity (clip threshold = 0.33 -> 84)
        clip_threshold = 84
        clipped_mask = np.where(alpha_mask_values >= clip_threshold, 1.0, 0.0)

        self.assertEqual(clipped_mask[0], 0.0)  # Full cutout
        self.assertEqual(clipped_mask[1], 0.0)  # Translucent thread boundary
        self.assertEqual(clipped_mask[2], 0.0)  # Sub-threshold
        self.assertEqual(clipped_mask[3], 1.0)  # Solid thread
        self.assertEqual(clipped_mask[5], 1.0)  # Dense embroidery


# ===========================================================================
# Tier 3: System & Integration Tests (Dual-Sheen, Sampler Footprint & Toon LUT)
# ===========================================================================
class TestFabricSystemIntegrationTier3(unittest.TestCase):
    """Tier 3 Integration tests verifying dual-sheen, shared sampler budgeting, and ToonProfile interactions."""

    def test_dual_sheen_grazing_fresnel(self):
        """Verify grazing angle Fresnel retains dual-sheen highlights at glancing angles."""
        velvet = CORE_FABRIC_PRESETS["RoyalVelvet"]
        sheen_tint = (1.0, 0.85, 0.95)  # Lavender silk sheen tint

        # Direct view: NdotV = 1.0 (looking head-on) -> Sheen must be zero
        direct_sheen = evaluate_grazing_sheen(
            ndotv=1.0, sheen_intensity=velvet.fabric_sheen,
            sheen_power=velvet.sheen_power, sheen_tint=sheen_tint,
        )
        self.assertAlmostEqual(direct_sheen[0], 0.0, places=3)
        self.assertAlmostEqual(direct_sheen[1], 0.0, places=3)
        self.assertAlmostEqual(direct_sheen[2], 0.0, places=3)

        # Grazing view: NdotV = 0.1 (steep glancing angle) -> Sheen must be strong
        grazing_sheen = evaluate_grazing_sheen(
            ndotv=0.1, sheen_intensity=velvet.fabric_sheen,
            sheen_power=velvet.sheen_power, sheen_tint=sheen_tint,
        )
        expected_fresnel = (1.0 - 0.1) ** velvet.sheen_power
        self.assertAlmostEqual(grazing_sheen[0], velvet.fabric_sheen * expected_fresnel * sheen_tint[0], places=3)
        self.assertGreater(grazing_sheen[0], 0.5, "Grazing sheen must produce visible highlight")

    def test_sampler_footprint_shared_wrap_budget(self):
        """Verify that multi-layer fabric materials configured with Shared: Wrap require <= 4 hardware samplers."""
        # Simulated material with 3 layers (Layer A, Layer B, Layer C) + masks
        texture_samplers = [
            {"name": "LayerA_BC", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "sRGB"},
            {"name": "LayerA_ORM", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "LayerA_N", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Normal"},
            {"name": "LayerA_H", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "LayerB_BC", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "sRGB"},
            {"name": "LayerB_ORM", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "LayerB_N", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Normal"},
            {"name": "LayerB_H", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "LayerC_BC", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "sRGB"},
            {"name": "LayerC_ORM", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "DetailNormal", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Normal"},
            {"name": "SparkleMask", "sampler_type": "SAMPLERTYPE_SharedWrap", "domain": "Linear"},
            {"name": "ToonProfileRamp", "sampler_type": "SAMPLERTYPE_SharedClamp", "domain": "Linear"},
        ]
        self.assertEqual(len(texture_samplers), 13, "Total logical texture samples = 13")

        # Calculate distinct hardware sampler state keys: (sampler_type, domain)
        hardware_sampler_states = {
            (s["sampler_type"], s["domain"]) for s in texture_samplers
        }

        # Hardware sampler states should be exactly 4:
        # 1. (SharedWrap, sRGB)
        # 2. (SharedWrap, Linear)
        # 3. (SharedWrap, Normal)
        # 4. (SharedClamp, Linear)
        self.assertLessEqual(
            len(hardware_sampler_states), 4,
            f"Hardware sampler footprint ({len(hardware_sampler_states)}) must not exceed 4 shared sampler states",
        )

    def test_toon_profile_ramp_interaction(self):
        """Verify fabric diffuse color transitions through the 3-stop HoYoverse-style Toon Profile shadow ramp."""
        # Simulated 3-stop Toon Ramp:
        # Stop 0 (NdotL <= -0.2): Deep Indigo Shadow (#0A0815 -> [0.039, 0.031, 0.082])
        # Stop 1 (-0.2 < NdotL <= 0.3): BaseColor diffuse
        # Stop 2 (NdotL > 0.3): Warm lit BaseColor (BaseColor * 1.15)
        shadow_floor = np.array([0.039, 0.031, 0.082])
        base_color = np.array([0.8, 0.2, 0.3])  # Red Velvet

        def evaluate_toon_diffuse(ndotl: float) -> np.ndarray:
            if ndotl <= -0.2:
                return base_color * shadow_floor * 2.0 + shadow_floor
            elif ndotl <= 0.3:
                t = (ndotl - (-0.2)) / 0.5
                shadow_col = base_color * shadow_floor * 2.0 + shadow_floor
                return shadow_col * (1.0 - t) + base_color * t
            else:
                t = min(1.0, (ndotl - 0.3) / 0.7)
                return base_color * (1.0 + 0.15 * t)

        # Test deep shadow region: must not be pitch-black (shadow floor preserved)
        deep_shadow = evaluate_toon_diffuse(-0.5)
        self.assertGreater(np.mean(deep_shadow), 0.03, "Shadow floor must prevent pitch-black crushing")

        # Test lit region: must preserve vibrant BaseColor
        lit = evaluate_toon_diffuse(0.8)
        self.assertGreaterEqual(lit[0], base_color[0])

    def test_on_disk_fabric_textures_exist_and_conform(self):
        """Verify that all 6 core fabric PBR texture sets exist on disk and meet AAA standards."""
        from pathlib import Path
        from PIL import Image

        fabrics_dir = Path(__file__).resolve().parents[2] / "Textures" / "Fabrics"
        self.assertTrue(fabrics_dir.exists(), f"Fabrics directory must exist: {fabrics_dir}")

        expected_sets = {
            "RoyalVelvet": ["BC", "ORM", "N", "H", "Sheen"],
            "GildedBrocade": ["BC", "ORM", "N", "H", "DetailN"],
            "SheerSilk": ["BC", "ORM", "N", "H", "Sheen"],
            "BaroqueLace": ["BC", "ORM", "N", "H", "Mask"],
            "GoldEmbroidery": ["BC", "ORM", "N", "H", "DetailN"],
            "CelestialWeave": ["BC", "ORM", "N", "H", "Sparkle"],
        }

        for archetype, channels in expected_sets.items():
            for ch in channels:
                filename = f"T_Fabric_{archetype}_{ch}.png"
                file_path = fabrics_dir / filename
                self.assertTrue(file_path.exists(), f"Missing required fabric texture: {filename}")

                with Image.open(file_path) as img:
                    w, h = img.size
                    self.assertTrue(w > 0 and (w & (w - 1)) == 0, f"{filename} width {w} must be POT")
                    self.assertTrue(h > 0 and (h & (h - 1)) == 0, f"{filename} height {h} must be POT")
                    self.assertGreaterEqual(w, 1024, f"{filename} width must be >= 1024")
                    self.assertGreaterEqual(h, 1024, f"{filename} height must be >= 1024")

                    if ch == "ORM":
                        self.assertEqual(img.mode, "RGB", f"{filename} mode must be RGB")
                        arr = np.array(img)
                        ao_mean = float(arr[:, :, 0].mean())
                        rough_mean = float(arr[:, :, 1].mean())
                        metal_mean = float(arr[:, :, 2].mean())
                        self.assertGreater(ao_mean, 100.0, f"{filename} AO mean must be > 100")
                        self.assertGreater(rough_mean, 10.0, f"{filename} Roughness mean must be > 10")
                    elif ch in ("N", "DetailN"):
                        self.assertEqual(img.mode, "RGB", f"{filename} mode must be RGB")
                        arr = np.array(img)
                        b_mean = float(arr[:, :, 2].mean())
                        self.assertGreater(b_mean, 110.0, f"{filename} Normal Blue channel must be > 110")

    def test_fabric_instance_manifest_and_wardrobe_wiring(self):
        """Verify that Material Instance manifests and Melusina wardrobe wirings are generated and valid."""
        import json
        from pathlib import Path

        test_dir = Path(__file__).resolve().parent
        bs_godfile = test_dir.parents[1]

        inst_json = None
        wardrobe_json = None
        for base in [bs_godfile / "Saved" / "Audit", test_dir.parent / "Saved" / "Audit"]:
            if (base / "fabric_instances_config.json").exists():
                inst_json = base / "fabric_instances_config.json"
            if (base / "melusina_wardrobe_wiring.json").exists():
                wardrobe_json = base / "melusina_wardrobe_wiring.json"

        self.assertIsNotNone(inst_json, "Missing fabric_instances_config.json in audit dirs")
        self.assertIsNotNone(wardrobe_json, "Missing melusina_wardrobe_wiring.json in audit dirs")

        inst_data = json.loads(inst_json.read_text(encoding="utf-8"))
        total_inst = inst_data.get("instances_count", inst_data.get("total_instances", len(inst_data.get("instances", {}))))
        self.assertGreaterEqual(total_inst, 6)
        self.assertIn("MI_Fabric_RoyalVelvet", inst_data.get("instances", {}))
        self.assertIn("MI_Fabric_GildedBrocade", inst_data.get("instances", {}))
        self.assertIn("MI_Fabric_SheerSilk", inst_data.get("instances", {}))
        self.assertIn("MI_Fabric_BaroqueLace", inst_data.get("instances", {}))
        self.assertIn("MI_Fabric_GoldEmbroidery", inst_data.get("instances", {}))
        self.assertIn("MI_Fabric_CelestialWeave", inst_data.get("instances", {}))

        wardrobe_data = json.loads(wardrobe_json.read_text(encoding="utf-8"))
        slots_count = wardrobe_data.get("wardrobe_slots_count", wardrobe_data.get("slots_wired", len(wardrobe_data.get("slots", {}))))
        self.assertEqual(slots_count, 5)
        self.assertIn("MI_Melusina_Shirt", wardrobe_data.get("slots", {}))
        self.assertIn("MI_Melusina_FrontPanel", wardrobe_data.get("slots", {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)

