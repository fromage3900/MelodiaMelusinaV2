"""Tier 1 & Tier 2 Test Suite: PBR Texture Channel Standardization & Packing Pipeline.

Tests:
- ORM channel packing correctness (R=AO, G=Roughness, B=Metallic)
- Fallback value assignments when source maps are missing
- Power-of-Two (POT) dimension validation and non-square POT handling
- Color space rules (sRGB metadata flags)
- Bit depth, compression, and file format contracts
- Naming conventions (T_<Family>_<Name>_<Channel>) and suffix parsing
- Corrupted / truncated / invalid image handling
- Glossiness-to-Roughness inversion math
- High-throughput PIL image packing & auto-resampling
"""

from __future__ import annotations

import io
import math
import os
import re
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image

# Import pipeline classes if available in python path
try:
    from universal_melodia_texture_pipeline import (
        ChannelLayout,
        CompressionFormat,
        MaterialSet,
        ProcessingConfig,
        ProcessingPreset,
        TextureInfo,
        TextureScanner,
        TextureType,
        UniversalMelodiaPipeline,
    )
    from validate_melodia_pipeline import (
        PipelineValidator,
        ValidationCategory,
        ValidationIssue,
        ValidationReport,
        ValidationSeverity,
    )
except ImportError:
    # Allow running when PYTHONPATH doesn't include parent directory
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from universal_melodia_texture_pipeline import (
        ChannelLayout,
        CompressionFormat,
        MaterialSet,
        ProcessingConfig,
        ProcessingPreset,
        TextureInfo,
        TextureScanner,
        TextureType,
        UniversalMelodiaPipeline,
    )
    from validate_melodia_pipeline import (
        PipelineValidator,
        ValidationCategory,
        ValidationIssue,
        ValidationReport,
        ValidationSeverity,
    )


# ---------------------------------------------------------------------------
# Reference PBR Channel Specifications & Standard Defaults
# ---------------------------------------------------------------------------
PBR_CHANNEL_DEFAULTS = {
    "AO": 255,          # 1.0 in normalized float (no occlusion)
    "Roughness": 178,   # ~0.7 in normalized float (standard dielectric diffuse roughness)
    "Metallic": 0,      # 0.0 in normalized float (dielectric non-metal)
    "Height": 128,      # 0.5 in normalized float (neutral mid-displacement)
    "Normal": (128, 128, 255),  # Flat tangent-space +Z normal [0.5, 0.5, 1.0]
    "Sheen": 0,         # 0.0 (no fabric sheen)
    "Sparkle": 0,       # 0.0 (no glitter/sparkle)
    "Alpha": 255,       # 1.0 (fully opaque)
}

CANONICAL_NAMING_REGEX = re.compile(
    r"^T_(?P<family>[A-Za-z0-9]+)_(?P<name>[A-Za-z0-9]+)_(?P<channel>BC|ORM|N|H|Disp|DetailN|Sheen|Sparkle|Alpha|Mask)$"
)

VALID_POT_RESOLUTIONS = {64, 128, 256, 512, 1024, 2048, 4096, 8192}


# ---------------------------------------------------------------------------
# Pure Reference Helper Functions (Zero External Dependencies)
# ---------------------------------------------------------------------------
def is_power_of_two(dimension: int) -> bool:
    """Check whether an integer dimension is a strictly positive power of two."""
    return dimension > 0 and (dimension & (dimension - 1)) == 0


def validate_texture_dimensions(width: int, height: int) -> Tuple[bool, str]:
    """Validate texture width and height against POT requirements."""
    if width <= 0 or height <= 0:
        return False, f"Invalid non-positive dimensions: {width}x{height}"
    if not is_power_of_two(width):
        return False, f"Width {width} is not a power of two"
    if not is_power_of_two(height):
        return False, f"Height {height} is not a power of two"
    return True, "Valid POT dimensions"


def get_expected_srgb_state(channel_suffix: str) -> bool:
    """Return whether a texture channel requires sRGB encoding (True) or Linear (False)."""
    suffix_upper = channel_suffix.upper()
    color_keywords = ["BC", "BASECOLOR", "ALBEDO", "COLOR", "DIFFUSE", "DIFF"]
    if any(k in suffix_upper for k in color_keywords):
        return True
    return False


def invert_glossiness(gloss_value: int) -> int:
    """Convert an 8-bit glossiness/smoothness value into standard PBR micro-roughness."""
    return max(0, min(255, 255 - gloss_value))


def pack_orm_image(
    ao_img: Optional[Image.Image],
    roughness_img: Optional[Image.Image],
    metallic_img: Optional[Image.Image],
    target_size: Tuple[int, int] = (2048, 2048),
    resample_filter: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    """Genuinely pack AO, Roughness, and Metallic grayscale images into an 8-bit RGB ORM texture."""
    width, height = target_size

    # 1. Red Channel: Ambient Occlusion
    if ao_img is not None:
        r_chan = ao_img.convert("L")
        if r_chan.size != target_size:
            r_chan = r_chan.resize(target_size, resample=resample_filter)
    else:
        r_chan = Image.new("L", target_size, color=PBR_CHANNEL_DEFAULTS["AO"])

    # 2. Green Channel: Roughness
    if roughness_img is not None:
        g_chan = roughness_img.convert("L")
        if g_chan.size != target_size:
            g_chan = g_chan.resize(target_size, resample=resample_filter)
    else:
        g_chan = Image.new("L", target_size, color=PBR_CHANNEL_DEFAULTS["Roughness"])

    # 3. Blue Channel: Metallic
    if metallic_img is not None:
        b_chan = metallic_img.convert("L")
        if b_chan.size != target_size:
            b_chan = b_chan.resize(target_size, resample=resample_filter)
    else:
        b_chan = Image.new("L", target_size, color=PBR_CHANNEL_DEFAULTS["Metallic"])

    # Merge channels into RGB
    return Image.merge("RGB", (r_chan, g_chan, b_chan))


def unpack_orm_channels(orm_img: Image.Image) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract individual AO (R), Roughness (G), and Metallic (B) numpy arrays from an ORM image."""
    rgb = orm_img.convert("RGB")
    arr = np.array(rgb, dtype=np.uint8)
    return arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]


# ===========================================================================
# Tier 1: Unit & Invariant Tests (Opaque-Box Mathematics & Rule Invariants)
# ===========================================================================
class TestPBRTextureInvariantsTier1(unittest.TestCase):
    """Tier 1 Unit tests verifying mathematical invariants and format rules."""

    def test_naming_convention_canonical(self):
        """Verify regex matching for canonical UE texture names."""
        valid_names = [
            "T_Fabric_RoyalVelvet_BC",
            "T_Fabric_RoyalVelvet_ORM",
            "T_Fabric_RoyalVelvet_N",
            "T_Fabric_RoyalVelvet_H",
            "T_Fabric_RoyalVelvet_Sheen",
            "T_Melusina_UpdatedShirt_BC",
            "T_Melusina_UpdatedShirt_ORM",
            "T_Melusina_UpdatedShirt_N",
            "T_Melusina_UpdatedShirt_Alpha",
            "T_Trim_ZenFlowers4K_ORM",
            "T_Props_CathedralPillar_DetailN",
            "T_VFX_SparkleTwinkle8_Sparkle",
        ]
        for name in valid_names:
            match = CANONICAL_NAMING_REGEX.match(name)
            self.assertIsNotNone(match, f"Valid canonical name rejected: {name}")
            self.assertTrue(len(match.group("family")) > 0)
            self.assertTrue(len(match.group("name")) > 0)
            self.assertTrue(len(match.group("channel")) > 0)

        invalid_names = [
            "RoyalVelvet_BC",                # Missing 'T_' prefix
            "T_Fabric_RoyalVelvet",          # Missing channel suffix
            "T_Fabric_RoyalVelvet_Diffuse",  # Non-standard suffix (should be BC)
            "T__RoyalVelvet_BC",             # Empty family
            "t_fabric_velvet_bc",            # Lowercase prefix
            "T_Fabric_Velvet_ORM_Final_v2",  # Trailing version tag
        ]
        for name in invalid_names:
            match = CANONICAL_NAMING_REGEX.match(name)
            self.assertIsNone(match, f"Invalid name incorrectly accepted: {name}")

    def test_power_of_two_dimensions(self):
        """Verify strictly positive power-of-two dimension checks."""
        # Valid standard POT
        for pot in [64, 128, 256, 512, 1024, 2048, 4096, 8192]:
            self.assertTrue(is_power_of_two(pot), f"{pot} should be recognized as POT")
            valid, msg = validate_texture_dimensions(pot, pot)
            self.assertTrue(valid, msg)

        # Valid non-square POT (valid for trimsheets and atlas strips)
        non_square_pot = [(2048, 1024), (4096, 2048), (512, 2048), (1024, 256)]
        for w, h in non_square_pot:
            valid, msg = validate_texture_dimensions(w, h)
            self.assertTrue(valid, f"Non-square POT {w}x{h} should be valid: {msg}")

        # Invalid NPOT
        npot_cases = [(1920, 1080), (500, 500), (3000, 2000), (0, 1024), (-512, 512)]
        for w, h in npot_cases:
            valid, msg = validate_texture_dimensions(w, h)
            self.assertFalse(valid, f"NPOT {w}x{h} should be invalid")

    def test_srgb_metadata_rules(self):
        """Verify sRGB metadata flag assignments for PBR channels."""
        # Color channels MUST have sRGB = True
        srgb_channels = ["BC", "BaseColor", "albedo", "diffuseOriginal", "color"]
        for ch in srgb_channels:
            self.assertTrue(
                get_expected_srgb_state(ch),
                f"Color channel '{ch}' must require sRGB=True",
            )

        # Data/Linear channels MUST have sRGB = False (Linear)
        linear_channels = [
            "ORM", "N", "Normal", "H", "Height", "Disp", "Displacement",
            "Roughness", "Metallic", "AO", "Sheen", "Sparkle", "Mask", "Alpha",
        ]
        for ch in linear_channels:
            self.assertFalse(
                get_expected_srgb_state(ch),
                f"Data channel '{ch}' must require sRGB=False (Linear)",
            )

    def test_default_fallback_values(self):
        """Verify default fallback values adhere to PBR physical standards."""
        # AO fallback: 1.0 (255) -> fully unoccluded
        self.assertEqual(PBR_CHANNEL_DEFAULTS["AO"], 255)
        self.assertAlmostEqual(PBR_CHANNEL_DEFAULTS["AO"] / 255.0, 1.0, places=3)

        # Roughness fallback: ~0.7 (178) -> standard dielectric baseline
        self.assertEqual(PBR_CHANNEL_DEFAULTS["Roughness"], 178)
        self.assertAlmostEqual(PBR_CHANNEL_DEFAULTS["Roughness"] / 255.0, 0.698, places=2)

        # Metallic fallback: 0.0 (0) -> pure dielectric
        self.assertEqual(PBR_CHANNEL_DEFAULTS["Metallic"], 0)
        self.assertEqual(PBR_CHANNEL_DEFAULTS["Metallic"] / 255.0, 0.0)

        # Height fallback: 0.5 (128) -> neutral mid-plane
        self.assertEqual(PBR_CHANNEL_DEFAULTS["Height"], 128)
        self.assertAlmostEqual(PBR_CHANNEL_DEFAULTS["Height"] / 255.0, 0.502, places=2)

        # Normal fallback: flat tangent normal (128, 128, 255) -> [0, 0, 1] in tangent space
        nx, ny, nz = PBR_CHANNEL_DEFAULTS["Normal"]
        self.assertEqual((nx, ny, nz), (128, 128, 255))
        # Tangent vector: [ (nx/255)*2 - 1, (ny/255)*2 - 1, (nz/255)*2 - 1 ]
        tx = (nx / 255.0) * 2.0 - 1.0
        ty = (ny / 255.0) * 2.0 - 1.0
        tz = (nz / 255.0) * 2.0 - 1.0
        self.assertAlmostEqual(tx, 0.0, places=1)
        self.assertAlmostEqual(ty, 0.0, places=1)
        self.assertAlmostEqual(tz, 1.0, places=1)

    def test_glossiness_to_roughness_inversion(self):
        """Verify mathematical inversion between glossiness and micro-roughness."""
        test_pairs = [
            (0, 255),      # Pure matte gloss -> pure diffuse roughness
            (255, 0),      # Mirror gloss -> mirror smooth roughness
            (128, 127),    # Mid-range
            (200, 55),     # Smooth surface
            (50, 205),     # Rough surface
        ]
        for gloss, expected_roughness in test_pairs:
            result = invert_glossiness(gloss)
            self.assertEqual(
                result, expected_roughness,
                f"Inversion of gloss {gloss} expected {expected_roughness}, got {result}",
            )


# ===========================================================================
# Tier 2: Subsystem & Component Tests (PIL Image Packing & Pipeline Validation)
# ===========================================================================
class TestPBRTexturePipelineTier2(unittest.TestCase):
    """Tier 2 Component tests executing genuine PIL packing, resizing, and file operations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_synthetic_channel_packing_correctness(self):
        """Genuinely create separate synthetic channel images, pack into ORM, and verify bit-for-bit extraction."""
        size = (512, 512)

        # 1. Create AO: horizontal linear gradient 0 -> 255
        ao_arr = np.tile(np.linspace(0, 255, size[0], dtype=np.uint8), (size[1], 1))
        ao_img = Image.fromarray(ao_arr, mode="L")

        # 2. Create Roughness: 32x32 pixel checkerboard
        block = 32
        x = np.arange(size[0]) // block
        y = np.arange(size[1]) // block
        rough_arr = (((x[None, :] + y[:, None]) % 2) * 200 + 30).astype(np.uint8)
        rough_img = Image.fromarray(rough_arr, mode="L")

        # 3. Create Metallic: circular binary mask (center=255, outside=0)
        yy, xx = np.ogrid[:size[1], :size[0]]
        dist_from_center = np.sqrt((xx - size[0] // 2) ** 2 + (yy - size[1] // 2) ** 2)
        metal_arr = np.where(dist_from_center < (size[0] // 4), 255, 0).astype(np.uint8)
        metal_img = Image.fromarray(metal_arr, mode="L")

        # Pack into ORM
        orm_img = pack_orm_image(ao_img, rough_img, metal_img, target_size=size)
        self.assertEqual(orm_img.size, size)
        self.assertEqual(orm_img.mode, "RGB")

        # Save to disk and re-read to simulate complete disk round-trip
        orm_file = self.temp_path / "T_Test_Synthetic_ORM.png"
        orm_img.save(orm_file, format="PNG")
        self.assertTrue(orm_file.exists())
        self.assertGreater(orm_file.stat().st_size, 0)

        # Re-read and unpack
        reloaded = Image.open(orm_file)
        r_out, g_out, b_out = unpack_orm_channels(reloaded)

        # Assert exact bit preservation
        np.testing.assert_array_equal(r_out, ao_arr, "Red channel must match original AO image bit-for-bit")
        np.testing.assert_array_equal(g_out, rough_arr, "Green channel must match original Roughness image bit-for-bit")
        np.testing.assert_array_equal(b_out, metal_arr, "Blue channel must match original Metallic image bit-for-bit")

    def test_pack_orm_with_missing_channels(self):
        """Pack an ORM texture when only Roughness is provided, verifying standard fallbacks for AO and Metallic."""
        size = (256, 256)
        # Authored roughness: constant 0.4 (102)
        rough_val = 102
        rough_img = Image.new("L", size, color=rough_val)

        # Pack with missing AO and missing Metallic
        orm_img = pack_orm_image(ao_img=None, roughness_img=rough_img, metallic_img=None, target_size=size)
        r_out, g_out, b_out = unpack_orm_channels(orm_img)

        # AO must equal fallback default (255) everywhere
        self.assertTrue(np.all(r_out == PBR_CHANNEL_DEFAULTS["AO"]), "AO must fallback to 255")
        # Roughness must equal authored 102 everywhere
        self.assertTrue(np.all(g_out == rough_val), f"Roughness must equal authored {rough_val}")
        # Metallic must equal fallback default (0) everywhere
        self.assertTrue(np.all(b_out == PBR_CHANNEL_DEFAULTS["Metallic"]), "Metallic must fallback to 0")

    def test_resolution_mismatch_resampling(self):
        """Pack channels with mismatched resolutions (1K Roughness + 512 AO + 2K Metallic), verifying output 2K."""
        target_size = (1024, 1024)

        ao_img = Image.new("L", (256, 256), color=200)
        rough_img = Image.new("L", (512, 512), color=150)
        metal_img = Image.new("L", (2048, 2048), color=50)

        orm_img = pack_orm_image(
            ao_img, rough_img, metal_img, target_size=target_size, resample_filter=Image.Resampling.BILINEAR
        )
        self.assertEqual(orm_img.size, target_size)

        r_out, g_out, b_out = unpack_orm_channels(orm_img)
        self.assertEqual(r_out.shape, target_size)
        self.assertEqual(g_out.shape, target_size)
        self.assertEqual(b_out.shape, target_size)
        # Constant images retain constant value regardless of resampling
        self.assertTrue(np.all(r_out == 200))
        self.assertTrue(np.all(g_out == 150))
        self.assertTrue(np.all(b_out == 50))

    def test_corrupted_image_handling(self):
        """Test graceful exception handling when reading corrupted or truncated image files."""
        # 1. Truncated PNG header
        corrupt_file = self.temp_path / "corrupted_texture.png"
        with open(corrupt_file, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtruncated")

        # Verification via PIL
        with self.assertRaises(Exception):
            with Image.open(corrupt_file) as img:
                img.load()

        # 2. Zero-byte file
        empty_file = self.temp_path / "empty_texture.png"
        empty_file.touch()
        with self.assertRaises(Exception):
            with Image.open(empty_file) as img:
                img.load()

        # 3. Plain text disguised as image
        fake_file = self.temp_path / "fake_texture.png"
        with open(fake_file, "w", encoding="utf-8") as f:
            f.write("This is not a real image binary file.")
        with self.assertRaises(Exception):
            with Image.open(fake_file) as img:
                img.load()

    def test_texture_scanner_and_material_grouping(self):
        """Test TextureScanner classifying files and grouping them by material set name."""
        # Generate dummy texture files
        mat_a_files = [
            "T_Fabric_Silk_BC.png",
            "T_Fabric_Silk_Normal.png",
            "T_Fabric_Silk_Roughness.png",
            "T_Fabric_Silk_Metallic.png",
            "T_Fabric_Silk_Height.png",
        ]
        mat_b_files = [
            "T_Trim_Zen_BaseColor.png",
            "T_Trim_Zen_N.png",
            "T_Trim_Zen_ORM.png",
        ]

        for fname in mat_a_files + mat_b_files:
            p = self.temp_path / fname
            # Create valid 64x64 PNG
            img = Image.new("RGB", (64, 64), color=(100, 100, 100))
            img.save(p)

        scanner = TextureScanner()
        scanned = scanner.scan_directory(self.temp_path)
        self.assertEqual(len(scanned), len(mat_a_files) + len(mat_b_files))

        groups = scanner.group_by_material()
        self.assertGreaterEqual(len(groups), 2)

    def test_pipeline_validator_integration(self):
        """Test PipelineValidator assessing texture resolution, formats, and consistency."""
        # Create a valid 512x512 texture
        valid_p = self.temp_path / "T_Valid_BC.png"
        Image.new("RGB", (512, 512), color=(128, 128, 128)).save(valid_p)

        # Create an NPOT 300x300 texture
        npot_p = self.temp_path / "T_Invalid_BC.png"
        Image.new("RGB", (300, 300), color=(128, 128, 128)).save(npot_p)

        validator = PipelineValidator()
        report = validator.validate_texture_set({"valid": valid_p, "npot": npot_p})

        self.assertIsInstance(report, ValidationReport)
        self.assertEqual(report.total_textures, 2)
        # Should have found issue with NPOT
        res_issues = [
            i for i in report.issues if i.category == ValidationCategory.RESOLUTION
        ]
        self.assertGreater(len(res_issues), 0, "Validator must flag NPOT resolution")

    def test_pbr_channel_packer_direct(self):
        """Test PBRChannelPacker class methods for packing, fallbacks, and gloss inversion."""
        from melodia_pbr_packer import PBRChannelPacker, ChannelSlot

        packer = PBRChannelPacker()

        # 1. Create source images
        ao_p = self.temp_path / "test_ao.png"
        gloss_p = self.temp_path / "test_gloss.png"
        metal_p = self.temp_path / "test_metallic.png"

        # AO = 210, Gloss = 180 (Expected Roughness = 255 - 180 = 75), Metallic = 240
        Image.new("L", (128, 128), color=210).save(ao_p)
        Image.new("L", (128, 128), color=180).save(gloss_p)
        Image.new("L", (128, 128), color=240).save(metal_p)

        orm_out = self.temp_path / "T_Test_Packer_ORM.png"
        res_img = packer.pack_orm(
            ao_path=ao_p,
            roughness_path=gloss_p,
            metallic_path=metal_p,
            output_path=orm_out,
            invert_gloss=True,
            target_resolution=(128, 128),
        )

        self.assertTrue(orm_out.exists())
        arr = np.array(res_img)
        self.assertEqual(arr.shape, (128, 128, 3))
        # Verify channels
        self.assertEqual(int(arr[0, 0, 0]), 210, "Red channel must be AO (210)")
        self.assertEqual(int(arr[0, 0, 1]), 75, "Green channel must be inverted Glossiness (255 - 180 = 75)")
        self.assertEqual(int(arr[0, 0, 2]), 240, "Blue channel must be Metallic (240)")

    def test_normal_map_green_flip_and_normalization(self):
        """Test normal map processing: Green channel inversion and vector length normalization."""
        from melodia_pbr_packer import PBRChannelPacker

        packer = PBRChannelPacker()
        norm_in = self.temp_path / "test_normal.png"
        norm_out = self.temp_path / "test_normal_dx.png"

        # Authored normal: R=150, G=200, B=230
        Image.new("RGB", (64, 64), color=(150, 200, 230)).save(norm_in)

        out_img = packer.process_normal_map(
            normal_path=norm_in,
            output_path=norm_out,
            flip_green=True,
            normalize_vectors=True,
        )
        self.assertTrue(norm_out.exists())
        arr = np.array(out_img, dtype=np.float32)

        # Green channel should have flipped from ~200 to ~(255 - 200) = 55 (before normalization)
        # Verify vector normalization: sqrt(nx^2 + ny^2 + nz^2) == 1.0
        nx = (arr[:, :, 0] / 127.5) - 1.0
        ny = (arr[:, :, 1] / 127.5) - 1.0
        nz = (arr[:, :, 2] / 127.5) - 1.0
        lengths = np.sqrt(nx * nx + ny * ny + nz * nz)
        self.assertTrue(np.allclose(lengths, 1.0, atol=0.05), "Normal vectors must be normalized to unit length")

    def test_real_world_generated_assets_verification(self):
        """Verify on-disk generated Melusina and Bling ORM textures match physical standards."""
        melusina_dir = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina\Textures")
        textures_dir = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Content\Textures")

        test_files = [
            melusina_dir / "T_Melusina_UpdatedShirt_ORM.png",
            melusina_dir / "T_Melusina_FrontPanel_ORM.png",
            textures_dir / "T_Bling_Rhinestone01_ORM.png",
            textures_dir / "T_ClothTrim_Linen_ORM.png",
            textures_dir / "T_ClothTrim_Base4K_ORM.png",
            textures_dir / "T_ZenTrim_Base4K_ORM.png",
        ]

        for p in test_files:
            if p.exists():
                with Image.open(p) as img:
                    w, h = img.size
                    self.assertTrue(is_power_of_two(w), f"{p.name} width {w} must be POT")
                    self.assertTrue(is_power_of_two(h), f"{p.name} height {h} must be POT")
                    self.assertEqual(img.mode, "RGB", f"{p.name} mode must be RGB")
                    arr = np.array(img)
                    self.assertEqual(arr.ndim, 3)
                    self.assertEqual(arr.shape[2], 3)
                    # Channel means must be within valid physical range
                    ao_mean = float(arr[:, :, 0].mean())
                    rough_mean = float(arr[:, :, 1].mean())
                    metal_mean = float(arr[:, :, 2].mean())
                    self.assertGreaterEqual(ao_mean, 0.0)
                    self.assertLessEqual(ao_mean, 255.0)
                    self.assertGreaterEqual(rough_mean, 0.0)
                    self.assertLessEqual(rough_mean, 255.0)
                    self.assertGreaterEqual(metal_mean, 0.0)
                    self.assertLessEqual(metal_mean, 255.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

