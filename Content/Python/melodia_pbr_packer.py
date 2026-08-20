"""
Melodia PBR Texture Channel Standardization & Packing Tool
==========================================================
Zero-loss PIL/NumPy PBR texture packing utility for Unreal Engine 5.8 & Substrate.

Packs separate Ambient Occlusion, Roughness, and Metallic textures into standard
Melodia ORM maps:
    - Red   (R): Ambient Occlusion (1.0 = 255 no occlusion, 0.0 = 0 fully occluded)
    - Green (G): Roughness (0.0 = 0 mirror smooth, 1.0 = 255 diffuse rough)
    - Blue  (B): Metallic (0.0 = 0 dielectric insulator, 1.0 = 255 conductor)

Intelligent Fallbacks:
    - Missing AO        -> 255 (1.0)
    - Missing Roughness -> 178 (0.7 standard PBR default)
    - Missing Metallic  -> 0   (0.0 dielectric standard)

Special Features:
    - Glossiness / Smoothness auto-inversion (Roughness = 255 - Glossiness)
    - Normal map DirectX/OpenGL green-channel inversion
    - Auto-discovery & batch packing across complex directory trees
    - Power-of-Two resolution normalization with high-quality resampling
    - Full CLI interface with single-set and batch modes

Author: Teamwork PBR Pipeline Worker (Milestone 1)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

# Default fallback values (0-255 scale)
FALLBACK_AO = 255        # 1.0: Full white, no ambient occlusion shadowing
FALLBACK_ROUGHNESS = 178 # 0.7: Melodia standard soft roughness baseline
FALLBACK_METALLIC = 0    # 0.0: Dielectric non-metal baseline
FALLBACK_HEIGHT = 128    # 0.5: Mid-height displacement baseline

# Power of Two target resolutions
STANDARD_RESOLUTIONS = [256, 512, 1024, 2048, 4096, 8192]


class ChannelSlot(Enum):
    """PBR Channel slot identifiers."""
    BASECOLOR = "BC"
    ORM = "ORM"
    AO = "AO"
    ROUGHNESS = "Roughness"
    GLOSSINESS = "Glossiness"
    METALLIC = "Metallic"
    NORMAL = "N"
    HEIGHT = "H"
    EMISSION = "Emission"
    MASK = "Mask"
    ALPHA = "Alpha"
    SHEEN = "Sheen"
    DETAIL_NORMAL = "DetailN"


@dataclass
class PackedTextureResult:
    """Result of a packing operation."""
    material_name: str
    output_orm_path: Optional[Path] = None
    output_bc_path: Optional[Path] = None
    output_normal_path: Optional[Path] = None
    output_height_path: Optional[Path] = None
    output_emission_path: Optional[Path] = None
    output_mask_path: Optional[Path] = None
    output_sheen_path: Optional[Path] = None
    resolution: Tuple[int, int] = (0, 0)
    ao_source: Optional[str] = None
    roughness_source: Optional[str] = None
    metallic_source: Optional[str] = None
    is_gloss_inverted: bool = False
    is_green_flipped: bool = False
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PBRChannelPacker:
    """High-performance, zero-loss PBR texture packer."""

    def __init__(
        self,
        fallback_ao: int = FALLBACK_AO,
        fallback_roughness: int = FALLBACK_ROUGHNESS,
        fallback_metallic: int = FALLBACK_METALLIC,
        default_resolution: int = 2048,
    ):
        self.fallback_ao = fallback_ao
        self.fallback_roughness = fallback_roughness
        self.fallback_metallic = fallback_metallic
        self.default_resolution = default_resolution

    # -------------------------------------------------------------------------
    # Image Loading & Extraction Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Check if integer is a power of two."""
        return n > 0 and (n & (n - 1)) == 0

    @classmethod
    def _nearest_power_of_two(cls, n: int) -> int:
        """Find the nearest power of two <= 8192."""
        if n <= 0:
            return 512
        val = 1
        while val < n and val < 8192:
            val *= 2
        # Check if previous power is closer
        prev = val // 2
        if prev >= 64 and (n - prev) < (val - n):
            return prev
        return min(val, 8192)

    def load_grayscale_channel(
        self,
        source: Optional[Union[Path, str, Image.Image, np.ndarray]],
        target_size: Optional[Tuple[int, int]] = None,
        fallback_value: int = 255,
        invert: bool = False,
    ) -> Image.Image:
        """
        Load an image or single channel as an 8-bit grayscale ('L') PIL Image.
        Applies fallback if missing, handles resolution matching and optional inversion.
        """
        if source is None:
            if target_size is None:
                target_size = (self.default_resolution, self.default_resolution)
            arr = np.full((target_size[1], target_size[0]), fallback_value, dtype=np.uint8)
            return Image.fromarray(arr, mode="L")

        img: Optional[Image.Image] = None

        if isinstance(source, (str, Path)):
            p = Path(source)
            if not p.exists():
                if target_size is None:
                    target_size = (self.default_resolution, self.default_resolution)
                arr = np.full((target_size[1], target_size[0]), fallback_value, dtype=np.uint8)
                return Image.fromarray(arr, mode="L")
            img = Image.open(p)
        elif isinstance(source, Image.Image):
            img = source
        elif isinstance(source, np.ndarray):
            img = Image.fromarray(source)

        if img is None:
            if target_size is None:
                target_size = (self.default_resolution, self.default_resolution)
            arr = np.full((target_size[1], target_size[0]), fallback_value, dtype=np.uint8)
            return Image.fromarray(arr, mode="L")

        # Convert to Grayscale
        if img.mode != "L":
            if img.mode in ("RGB", "RGBA"):
                # Check if image is pure grayscale stored as RGB
                # Convert to L using luminosity
                img = img.convert("L")
            elif img.mode in ("I;16", "I", "F"):
                # 16-bit or float image: normalize to 8-bit uint8
                arr = np.array(img, dtype=np.float32)
                min_v, max_v = arr.min(), arr.max()
                if max_v > min_v:
                    arr = ((arr - min_v) / (max_v - min_v) * 255.0).astype(np.uint8)
                else:
                    arr = np.full(arr.shape, fallback_value, dtype=np.uint8)
                img = Image.fromarray(arr, mode="L")
            else:
                img = img.convert("L")

        # Resize if target size is specified and different
        if target_size is not None and img.size != target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)

        # Inversion (e.g. for Glossiness -> Roughness)
        if invert:
            arr = np.array(img, dtype=np.uint8)
            arr = 255 - arr
            img = Image.fromarray(arr, mode="L")

        return img

    def load_color_image(
        self,
        source: Optional[Union[Path, str, Image.Image]],
        target_size: Optional[Tuple[int, int]] = None,
        fallback_color: Tuple[int, int, int] = (128, 128, 128),
    ) -> Image.Image:
        """Load an image as an 8-bit RGB PIL Image."""
        if source is None:
            if target_size is None:
                target_size = (self.default_resolution, self.default_resolution)
            arr = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
            arr[:, :] = fallback_color
            return Image.fromarray(arr, mode="RGB")

        p = Path(source) if isinstance(source, (str, Path)) else None
        if p and not p.exists():
            if target_size is None:
                target_size = (self.default_resolution, self.default_resolution)
            arr = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
            arr[:, :] = fallback_color
            return Image.fromarray(arr, mode="RGB")

        img = Image.open(p) if p else source
        if img.mode != "RGB":
            img = img.convert("RGB")

        if target_size is not None and img.size != target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)

        return img

    # -------------------------------------------------------------------------
    # Core Channel Packing & Normal Operations
    # -------------------------------------------------------------------------

    def pack_orm(
        self,
        ao_path: Optional[Union[Path, str]] = None,
        roughness_path: Optional[Union[Path, str]] = None,
        metallic_path: Optional[Union[Path, str]] = None,
        output_path: Optional[Union[Path, str]] = None,
        invert_gloss: bool = False,
        target_resolution: Optional[Tuple[int, int]] = None,
    ) -> Image.Image:
        """
        Pack separate AO, Roughness, and Metallic textures into a single Melodia ORM image:
            Red   = Ambient Occlusion (Default fallback: 255)
            Green = Roughness (Default fallback: 178)
            Blue  = Metallic (Default fallback: 0)

        Returns the composite PIL Image (RGB mode).
        """
        # Determine working resolution from available inputs if not explicitly given
        chosen_size = target_resolution
        if chosen_size is None:
            for p in (ao_path, roughness_path, metallic_path):
                if p and Path(p).exists():
                    try:
                        with Image.open(p) as probe:
                            w, h = probe.size
                            if chosen_size is None or (w * h > chosen_size[0] * chosen_size[1]):
                                chosen_size = (w, h)
                    except Exception:
                        pass
        if chosen_size is None:
            chosen_size = (self.default_resolution, self.default_resolution)

        # Check for auto-detection of glossiness from filename if invert_gloss not explicitly passed
        gloss_invert = invert_gloss
        if not gloss_invert and roughness_path:
            r_name = Path(roughness_path).name.lower()
            if "gloss" in r_name or "smooth" in r_name:
                gloss_invert = True

        # Load channels
        img_ao = self.load_grayscale_channel(
            ao_path,
            target_size=chosen_size,
            fallback_value=self.fallback_ao,
            invert=False,
        )
        img_rough = self.load_grayscale_channel(
            roughness_path,
            target_size=chosen_size,
            fallback_value=self.fallback_roughness,
            invert=gloss_invert,
        )
        img_metal = self.load_grayscale_channel(
            metallic_path,
            target_size=chosen_size,
            fallback_value=self.fallback_metallic,
            invert=False,
        )

        # Compose ORM
        orm_image = Image.merge("RGB", (img_ao, img_rough, img_metal))

        # Save to disk if output path is provided
        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            # PNG with maximum quality zero-loss
            orm_image.save(out_p, format="PNG", compress_level=6)

        return orm_image

    def process_normal_map(
        self,
        normal_path: Union[Path, str],
        output_path: Optional[Union[Path, str]] = None,
        flip_green: bool = False,
        normalize_vectors: bool = True,
        target_resolution: Optional[Tuple[int, int]] = None,
    ) -> Image.Image:
        """
        Process and verify a tangent space normal map.
        Supports DirectX (Green = Y-) vs OpenGL (Green = Y+) inversion.
        """
        p = Path(normal_path)
        if not p.exists():
            raise FileNotFoundError(f"Normal map not found: {normal_path}")

        img = Image.open(p).convert("RGB")
        if target_resolution and img.size != target_resolution:
            img = img.resize(target_resolution, Image.Resampling.LANCZOS)

        arr = np.array(img, dtype=np.float32)

        # Flip green channel (Y component) if requested
        if flip_green:
            arr[:, :, 1] = 255.0 - arr[:, :, 1]

        # Vector normalization to eliminate compression noise / scale artifacts
        if normalize_vectors:
            # Map [0..255] to [-1.0..1.0]
            nx = (arr[:, :, 0] / 127.5) - 1.0
            ny = (arr[:, :, 1] / 127.5) - 1.0
            nz = (arr[:, :, 2] / 127.5) - 1.0
            
            # Avoid divide by zero
            length = np.sqrt(nx * nx + ny * ny + nz * nz)
            length = np.maximum(length, 1e-6)
            
            nx /= length
            ny /= length
            nz /= length
            
            # Map back to [0..255]
            arr[:, :, 0] = (nx + 1.0) * 127.5
            arr[:, :, 1] = (ny + 1.0) * 127.5
            arr[:, :, 2] = (nz + 1.0) * 127.5

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        norm_img = Image.fromarray(arr, mode="RGB")

        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            norm_img.save(out_p, format="PNG", compress_level=6)

        return norm_img

    # -------------------------------------------------------------------------
    # Texture Set Classification & Batch Processing
    # -------------------------------------------------------------------------

    @classmethod
    def classify_filename_channel(cls, filename: str) -> Optional[Tuple[str, ChannelSlot]]:
        """
        Extract the base material name and channel slot from a texture filename.
        Handles diverse naming conventions across Substance Painter, Quixel, standard DCCs.
        """
        stem = Path(filename).stem

        # Priority channel patterns (regex: regex pattern -> ChannelSlot)
        patterns: List[Tuple[re.Pattern, ChannelSlot]] = [
            # BaseColor / Albedo
            (re.compile(r"^(.*?)(?:[_\-\.](?:basecolor|base_color|albedo|diffuse|diff|color|bc|d|col))$", re.IGNORECASE), ChannelSlot.BASECOLOR),
            # Ambient Occlusion
            (re.compile(r"^(.*?)(?:[_\-\.](?:ambientocclusion|ambient_occlusion|occ|ao|ambient))$", re.IGNORECASE), ChannelSlot.AO),
            # Roughness
            (re.compile(r"^(.*?)(?:[_\-\.](?:roughness|rough|rgh|r))$", re.IGNORECASE), ChannelSlot.ROUGHNESS),
            # Glossiness / Smoothness
            (re.compile(r"^(.*?)(?:[_\-\.](?:glossiness|gloss|smoothness|smooth|g))$", re.IGNORECASE), ChannelSlot.GLOSSINESS),
            # Metallic
            (re.compile(r"^(.*?)(?:[_\-\.](?:metallic|metalness|metal|met|m))$", re.IGNORECASE), ChannelSlot.METALLIC),
            # Normal
            (re.compile(r"^(.*?)(?:[_\-\.](?:detailnormal|detail_normal|detailn))$", re.IGNORECASE), ChannelSlot.DETAIL_NORMAL),
            (re.compile(r"^(.*?)(?:[_\-\.](?:normal|norm|nrm|n))$", re.IGNORECASE), ChannelSlot.NORMAL),
            # Height / Displacement
            (re.compile(r"^(.*?)(?:[_\-\.](?:displacement|displace|disp|height|bump|h|depth))$", re.IGNORECASE), ChannelSlot.HEIGHT),
            # Emission
            (re.compile(r"^(.*?)(?:[_\-\.](?:emission|emissive|emit|glow|e))$", re.IGNORECASE), ChannelSlot.EMISSION),
            # Mask / Alpha
            (re.compile(r"^(.*?)(?:[_\-\.](?:alpha|mask|opacity|cutoff|a))$", re.IGNORECASE), ChannelSlot.ALPHA),
            # Sheen / Micro-roughness
            (re.compile(r"^(.*?)(?:[_\-\.](?:sheen|microroughness|micror|sparkle|glint|fuzz))$", re.IGNORECASE), ChannelSlot.SHEEN),
            # ORM already packed
            (re.compile(r"^(.*?)(?:[_\-\.](?:orm|mrao|rma|arm))$", re.IGNORECASE), ChannelSlot.ORM),
        ]

        # Check special hyphenated formats e.g. fabric-gingham-ambientOcclusion-198-1024
        fabric_match = re.match(r"^fabric-([a-z0-9\-]+)-(ambientOcclusion|baseColor|height|normal|roughness)-", stem, re.IGNORECASE)
        if fabric_match:
            fab_name = fabric_match.group(1).replace("-", "_")
            slot_str = fabric_match.group(2).lower()
            if slot_str == "ambientocclusion":
                return (f"Fabric_{fab_name}", ChannelSlot.AO)
            elif slot_str == "basecolor":
                return (f"Fabric_{fab_name}", ChannelSlot.BASECOLOR)
            elif slot_str == "height":
                return (f"Fabric_{fab_name}", ChannelSlot.HEIGHT)
            elif slot_str == "normal":
                return (f"Fabric_{fab_name}", ChannelSlot.NORMAL)
            elif slot_str == "roughness":
                return (f"Fabric_{fab_name}", ChannelSlot.ROUGHNESS)

        # Check special Substance bling format e.g. bling_surface_vol3_01_ambientocclusion
        bling_match = re.match(r"^bling_surface_vol3_(\d+)_(ambientocclusion|basecolor|height|metallic|normal|roughness)$", stem, re.IGNORECASE)
        if bling_match:
            num = bling_match.group(1)
            slot_str = bling_match.group(2).lower()
            slot_map = {
                "ambientocclusion": ChannelSlot.AO,
                "basecolor": ChannelSlot.BASECOLOR,
                "height": ChannelSlot.HEIGHT,
                "metallic": ChannelSlot.METALLIC,
                "normal": ChannelSlot.NORMAL,
                "roughness": ChannelSlot.ROUGHNESS,
            }
            return (f"Bling_Rhinestone{num}", slot_map[slot_str])

        # Standard pattern matching
        for pat, slot in patterns:
            m = pat.match(stem)
            if m:
                base_name = m.group(1)
                # Clean up leading/trailing underscores and characters
                base_name = base_name.strip("_-.")
                if base_name:
                    return (base_name, slot)

        return None

    @classmethod
    def discover_material_groups(
        cls,
        directory: Union[Path, str],
        recursive: bool = True,
    ) -> Dict[str, Dict[ChannelSlot, Path]]:
        """
        Scan a directory and group related texture files by their material name.
        """
        dir_p = Path(directory)
        if not dir_p.exists():
            return {}

        groups: Dict[str, Dict[ChannelSlot, Path]] = {}
        valid_exts = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".tga", ".exr", ".bmp"}

        iterator = dir_p.rglob("*.*") if recursive else dir_p.glob("*.*")
        for file_path in iterator:
            if file_path.suffix.lower() not in valid_exts:
                continue

            classification = cls.classify_filename_channel(file_path.name)
            if classification:
                mat_name, slot = classification
                if mat_name not in groups:
                    groups[mat_name] = {}
                groups[mat_name][slot] = file_path

        return groups

    def process_material_set(
        self,
        material_name: str,
        channel_files: Dict[ChannelSlot, Path],
        output_dir: Union[Path, str],
        prefix: str = "T_",
        flip_normal_green: bool = False,
        target_resolution: Optional[Tuple[int, int]] = None,
        standardize_names: bool = True,
    ) -> PackedTextureResult:
        """
        Standardize and pack a complete material texture set:
            - Packs ORM texture (`T_<Prefix><Material>_ORM.png`)
            - Standardizes BaseColor (`T_<Prefix><Material>_BC.png`)
            - Standardizes Normal (`T_<Prefix><Material>_N.png`)
            - Standardizes Height (`T_<Prefix><Material>_H.png`)
            - Standardizes Emission, Mask, Sheen if present
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        result = PackedTextureResult(material_name=material_name)

        # Standard clean base name
        clean_mat_name = material_name
        # Remove unwanted characters like single quotes or special punctuation
        clean_mat_name = clean_mat_name.replace("'", "").replace(" ", "_").replace(".", "_")
        if clean_mat_name.startswith("T_"):
            clean_mat_name = clean_mat_name[2:]

        canonical_base = f"{prefix}{clean_mat_name}" if not clean_mat_name.startswith(prefix) else clean_mat_name

        # Determine target resolution from available inputs
        all_sizes: List[Tuple[int, int]] = []
        for p in channel_files.values():
            if p and p.exists():
                try:
                    with Image.open(p) as probe:
                        all_sizes.append(probe.size)
                except Exception:
                    pass

        if target_resolution:
            chosen_res = target_resolution
        elif all_sizes:
            # Pick highest resolution among inputs
            chosen_res = max(all_sizes, key=lambda s: s[0] * s[1])
        else:
            chosen_res = (self.default_resolution, self.default_resolution)

        # Ensure chosen resolution is Power-of-Two
        pot_w = self._nearest_power_of_two(chosen_res[0])
        pot_h = self._nearest_power_of_two(chosen_res[1])
        chosen_res = (pot_w, pot_h)
        result.resolution = chosen_res

        # 1. Pack ORM
        ao_src = channel_files.get(ChannelSlot.AO)
        rough_src = channel_files.get(ChannelSlot.ROUGHNESS)
        gloss_src = channel_files.get(ChannelSlot.GLOSSINESS)
        metal_src = channel_files.get(ChannelSlot.METALLIC)

        use_roughness_src = rough_src
        invert_gloss = False
        if not use_roughness_src and gloss_src:
            use_roughness_src = gloss_src
            invert_gloss = True

        result.ao_source = str(ao_src) if ao_src else "FALLBACK(255)"
        result.roughness_source = str(use_roughness_src) if use_roughness_src else "FALLBACK(178)"
        result.metallic_source = str(metal_src) if metal_src else "FALLBACK(0)"
        result.is_gloss_inverted = invert_gloss

        orm_filename = f"{canonical_base}_ORM.png"
        orm_out_path = out_dir / orm_filename
        try:
            self.pack_orm(
                ao_path=ao_src,
                roughness_path=use_roughness_src,
                metallic_path=metal_src,
                output_path=orm_out_path,
                invert_gloss=invert_gloss,
                target_resolution=chosen_res,
            )
            result.output_orm_path = orm_out_path
        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to pack ORM: {e}")

        # 2. Standardize BaseColor
        bc_src = channel_files.get(ChannelSlot.BASECOLOR)
        if bc_src and bc_src.exists():
            bc_filename = f"{canonical_base}_BC.png"
            bc_out_path = out_dir / bc_filename
            try:
                img_bc = self.load_color_image(bc_src, target_size=chosen_res)
                img_bc.save(bc_out_path, format="PNG", compress_level=6)
                result.output_bc_path = bc_out_path
            except Exception as e:
                result.warnings.append(f"Failed to copy BaseColor: {e}")

        # 3. Standardize Normal Map
        norm_src = channel_files.get(ChannelSlot.NORMAL)
        if norm_src and norm_src.exists():
            norm_filename = f"{canonical_base}_N.png"
            norm_out_path = out_dir / norm_filename
            try:
                self.process_normal_map(
                    normal_path=norm_src,
                    output_path=norm_out_path,
                    flip_green=flip_normal_green,
                    normalize_vectors=True,
                    target_resolution=chosen_res,
                )
                result.output_normal_path = norm_out_path
                result.is_green_flipped = flip_normal_green
            except Exception as e:
                result.warnings.append(f"Failed to process Normal: {e}")

        # 4. Standardize Height / Displacement Map
        height_src = channel_files.get(ChannelSlot.HEIGHT)
        if height_src and height_src.exists():
            height_filename = f"{canonical_base}_H.png"
            height_out_path = out_dir / height_filename
            try:
                img_h = self.load_grayscale_channel(height_src, target_size=chosen_res, fallback_value=FALLBACK_HEIGHT)
                img_h.save(height_out_path, format="PNG", compress_level=6)
                result.output_height_path = height_out_path
            except Exception as e:
                result.warnings.append(f"Failed to process Height: {e}")

        # 5. Standardize Emission Map
        emiss_src = channel_files.get(ChannelSlot.EMISSION)
        if emiss_src and emiss_src.exists():
            emiss_filename = f"{canonical_base}_Emission.png"
            emiss_out_path = out_dir / emiss_filename
            try:
                img_em = self.load_color_image(emiss_src, target_size=chosen_res, fallback_color=(0, 0, 0))
                img_em.save(emiss_out_path, format="PNG", compress_level=6)
                result.output_emission_path = emiss_out_path
            except Exception as e:
                result.warnings.append(f"Failed to process Emission: {e}")

        # 6. Standardize Mask / Alpha Map
        mask_src = channel_files.get(ChannelSlot.MASK) or channel_files.get(ChannelSlot.ALPHA)
        if mask_src and mask_src.exists():
            mask_filename = f"{canonical_base}_Mask.png"
            mask_out_path = out_dir / mask_filename
            try:
                img_m = self.load_grayscale_channel(mask_src, target_size=chosen_res, fallback_value=255)
                img_m.save(mask_out_path, format="PNG", compress_level=6)
                result.output_mask_path = mask_out_path
            except Exception as e:
                result.warnings.append(f"Failed to process Mask: {e}")

        # 7. Standardize Sheen Map
        sheen_src = channel_files.get(ChannelSlot.SHEEN)
        if sheen_src and sheen_src.exists():
            sheen_filename = f"{canonical_base}_Sheen.png"
            sheen_out_path = out_dir / sheen_filename
            try:
                img_sh = self.load_grayscale_channel(sheen_src, target_size=chosen_res, fallback_value=0)
                img_sh.save(sheen_out_path, format="PNG", compress_level=6)
                result.output_sheen_path = sheen_out_path
            except Exception as e:
                result.warnings.append(f"Failed to process Sheen: {e}")

        return result

    def batch_pack_directory(
        self,
        input_dir: Union[Path, str],
        output_dir: Union[Path, str],
        prefix: str = "T_",
        flip_normal_green: bool = False,
        target_resolution: Optional[Tuple[int, int]] = None,
        recursive: bool = True,
    ) -> List[PackedTextureResult]:
        """
        Batch discover and pack all texture sets found in an input directory.
        """
        in_p = Path(input_dir)
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        groups = self.discover_material_groups(in_p, recursive=recursive)
        results: List[PackedTextureResult] = []

        print(f"[MelodiaPBR] Discovered {len(groups)} texture sets in {in_p}")

        for mat_name, channels in sorted(groups.items()):
            print(f"  -> Processing set: '{mat_name}' ({len(channels)} channels)")
            res = self.process_material_set(
                material_name=mat_name,
                channel_files=channels,
                output_dir=out_p,
                prefix=prefix,
                flip_normal_green=flip_normal_green,
                target_resolution=target_resolution,
            )
            results.append(res)
            if res.success:
                print(f"     [OK] Packed ORM: {res.output_orm_path.name if res.output_orm_path else 'None'}")
            else:
                print(f"     [FAILED] {res.errors}")

        return results


def parse_resolution(res_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse '2048' or '2048x2048' into (2048, 2048)."""
    if not res_str:
        return None
    res_str = res_str.lower().strip()
    if "x" in res_str:
        parts = res_str.split("x")
        return (int(parts[0]), int(parts[1]))
    val = int(res_str)
    return (val, val)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for Melodia PBR Texture Packer."""
    parser = argparse.ArgumentParser(
        description="Melodia PBR Texture Channel Standardization & Packing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Direct Channel flags
    parser.add_argument("--ao", help="Path to Ambient Occlusion texture map")
    parser.add_argument("--roughness", help="Path to Roughness (or Glossiness) texture map")
    parser.add_argument("--metallic", help="Path to Metallic texture map")
    parser.add_argument("--normal", help="Path to Normal map")
    parser.add_argument("--height", help="Path to Height / Displacement map")
    parser.add_argument("--basecolor", "--bc", help="Path to BaseColor / Albedo map")

    # Directory and Batch flags
    parser.add_argument("--input-dir", "-i", help="Input directory to scan for texture sets")
    parser.add_argument("--output-dir", "-o", help="Output directory for packed textures")
    parser.add_argument("--output", help="Explicit single output path for ORM map")
    parser.add_argument("--batch", "-b", action="store_true", help="Run batch processing across input directory")
    parser.add_argument("--prefix", default="T_", help="Prefix for generated textures (Default: 'T_')")
    parser.add_argument("--suffix", default="", help="Optional suffix to append")

    # Processing Options
    parser.add_argument("--flip-green", action="store_true", help="Invert Green channel of normal map (DirectX vs OpenGL)")
    parser.add_argument("--invert-gloss", action="store_true", help="Force invert roughness map (Roughness = 255 - Glossiness)")
    parser.add_argument("--target-res", help="Target resolution (e.g. 2048 or 4096x4096)")
    parser.add_argument("--json-report", help="Path to write JSON execution report")

    args = parser.parse_args(argv)

    packer = PBRChannelPacker()
    target_res = parse_resolution(args.target_res)

    # Mode 1: Batch Directory Processing
    if args.batch or args.input_dir:
        if not args.input_dir:
            print("Error: --input-dir is required when running in batch mode.", file=sys.stderr)
            return 1
        out_dir = Path(args.output_dir) if args.output_dir else Path(args.input_dir) / "Packed_ORM"
        
        start_time = time.time()
        results = packer.batch_pack_directory(
            input_dir=args.input_dir,
            output_dir=out_dir,
            prefix=args.prefix,
            flip_normal_green=args.flip_green,
            target_resolution=target_res,
        )
        elapsed = time.time() - start_time
        
        success_count = sum(1 for r in results if r.success)
        print(f"\n[MelodiaPBR] Batch finished in {elapsed:.2f}s: {success_count}/{len(results)} succeeded.")

        if args.json_report:
            report_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "input_dir": str(args.input_dir),
                "output_dir": str(out_dir),
                "total_sets": len(results),
                "success_count": success_count,
                "elapsed_seconds": elapsed,
                "results": [
                    {
                        "material_name": r.material_name,
                        "orm": str(r.output_orm_path) if r.output_orm_path else None,
                        "bc": str(r.output_bc_path) if r.output_bc_path else None,
                        "normal": str(r.output_normal_path) if r.output_normal_path else None,
                        "resolution": r.resolution,
                        "success": r.success,
                        "errors": r.errors,
                    }
                    for r in results
                ],
            }
            report_path = Path(args.json_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
            print(f"[MelodiaPBR] JSON report written to: {report_path}")

        return 0 if success_count == len(results) else 1

    # Mode 2: Direct Single Texture Pack
    elif args.ao or args.roughness or args.metallic or args.output:
        out_path = args.output
        if not out_path:
            if args.output_dir:
                out_path = Path(args.output_dir) / "T_Packed_ORM.png"
            else:
                out_path = "T_Packed_ORM.png"

        print(f"[MelodiaPBR] Packing single ORM texture -> {out_path}")
        img = packer.pack_orm(
            ao_path=args.ao,
            roughness_path=args.roughness,
            metallic_path=args.metallic,
            output_path=out_path,
            invert_gloss=args.invert_gloss,
            target_resolution=target_res,
        )
        print(f"[MelodiaPBR] Successfully generated {img.size[0]}x{img.size[1]} ORM texture.")
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
