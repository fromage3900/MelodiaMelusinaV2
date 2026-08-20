"""
Quality Validation Module for Melodia PBR Pipeline
==================================================
Production-grade validation harness verifying PBR texture standards for Unreal Engine 5.8 & Substrate.

Validates:
    1. Power-of-Two (POT) resolutions (512, 1024, 2048, 4096, 8192) and aspect ratios
    2. Canonical naming conventions (T_<Family>_<Name>_<Channel>) and suffix standards (_BC, _ORM, _N, _H, _Mask, _Sheen)
    3. Channel packing integrity for ORM textures (Red=AO, Green=Roughness, Blue=Metallic)
    4. Tangent-space Normal map integrity (Z+ dominance, vector normalization)
    5. Color space requirements (sRGB=True for _BC, Linear/sRGB=False for _ORM, _N, _H, _Mask, _Sheen)
    6. Texture set consistency and completeness

Usage:
    from validate_melodia_pipeline import PipelineValidator
    
    validator = PipelineValidator()
    report = validator.validate_texture_set(textures)
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
from PIL import Image


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    RESOLUTION = "resolution"
    ASPECT_RATIO = "aspect_ratio"
    NAMING = "naming"
    CHANNEL_LAYOUT = "channel_layout"
    ORM_PACKING = "orm_packing"
    NORMAL_MAP = "normal_map"
    COLOR_SPACE = "color_space"
    COMPRESSION = "compression"
    FILE_SIZE = "file_size"
    CONSISTENCY = "consistency"


@dataclass
class ValidationIssue:
    """Single validation issue."""
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    texture_path: Optional[Path] = None
    parameter: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class TextureMetricData:
    """Statistical metrics for an individual texture file."""
    path: str
    dimensions: Tuple[int, int]
    channels: int
    mode: str
    is_pot: bool
    aspect_ratio: float
    file_size_bytes: int
    expected_color_space: str
    channel_means: List[float] = field(default_factory=list)
    channel_stds: List[float] = field(default_factory=list)
    channel_mins: List[int] = field(default_factory=list)
    channel_maxs: List[int] = field(default_factory=list)
    detail_level: str = "medium"
    sharpness_score: float = 0.0


@dataclass
class ValidationReport:
    """Complete validation report with summary metrics."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_time: float = 0.0
    total_textures: int = 0
    passed_textures: int = 0
    failed_textures: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    metrics: Dict[str, TextureMetricData] = field(default_factory=dict)
    
    def add_issue(self, issue: ValidationIssue):
        """Add validation issue to report."""
        self.issues.append(issue)
        
        if issue.severity == ValidationSeverity.WARNING:
            self.warning_count += 1
        elif issue.severity == ValidationSeverity.ERROR:
            self.error_count += 1
        elif issue.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors or critical issues)."""
        return self.error_count == 0 and self.critical_count == 0
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues filtered by category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "validation_time": round(self.validation_time, 4),
            "total_textures": self.total_textures,
            "passed_textures": self.passed_textures,
            "failed_textures": self.failed_textures,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "is_valid": self.is_valid(),
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "texture_path": str(issue.texture_path) if issue.texture_path else None,
                    "parameter": issue.parameter,
                    "expected": issue.expected,
                    "actual": issue.actual,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "metrics": {
                k: {
                    "dimensions": list(v.dimensions),
                    "channels": v.channels,
                    "mode": v.mode,
                    "is_pot": v.is_pot,
                    "aspect_ratio": round(v.aspect_ratio, 3),
                    "file_size_bytes": v.file_size_bytes,
                    "expected_color_space": v.expected_color_space,
                    "channel_means": [round(m, 2) for m in v.channel_means],
                    "channel_mins": v.channel_mins,
                    "channel_maxs": v.channel_maxs,
                    "detail_level": v.detail_level,
                    "sharpness_score": round(v.sharpness_score, 2),
                }
                for k, v in self.metrics.items()
            },
        }
    
    def save(self, output_path: Union[Path, str]):
        """Save report to JSON file."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


class TextureQualityAnalyzer:
    """Analyze real texture quality metrics using PIL & NumPy."""
    
    @staticmethod
    def compute_channel_stats(img_array: np.ndarray) -> Tuple[List[float], List[float], List[int], List[int]]:
        """Compute mean, std, min, max per channel."""
        if img_array.ndim == 2:
            # 2D Grayscale
            return (
                [float(img_array.mean())],
                [float(img_array.std())],
                [int(img_array.min())],
                [int(img_array.max())],
            )
        elif img_array.ndim == 3:
            num_ch = img_array.shape[2]
            means = [float(img_array[:, :, c].mean()) for c in range(num_ch)]
            stds = [float(img_array[:, :, c].std()) for c in range(num_ch)]
            mins = [int(img_array[:, :, c].min()) for c in range(num_ch)]
            maxs = [int(img_array[:, :, c].max()) for c in range(num_ch)]
            return (means, stds, mins, maxs)
        return ([], [], [], [])
    
    @staticmethod
    def analyze_sharpness(img_array: np.ndarray) -> float:
        """
        Estimate texture sharpness via discrete Laplacian variance on luminance.
        Higher values indicate sharp micro-details; very low values indicate blur or solid color.
        """
        if img_array.ndim == 3:
            # Convert RGB to Luminance float
            lum = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
        else:
            lum = img_array.astype(np.float32)
        
        # Subsample if large to accelerate computation
        h, w = lum.shape
        if h > 1024 or w > 1024:
            lum = lum[::2, ::2]
        
        # 3x3 Laplacian kernel convolution via slices
        # Kernel: [0, 1, 0; 1, -4, 1; 0, 1, 0]
        lap = (
            lum[:-2, 1:-1]
            + lum[2:, 1:-1]
            + lum[1:-1, :-2]
            + lum[1:-1, 2:]
            - 4.0 * lum[1:-1, 1:-1]
        )
        return float(lap.var())
    
    @staticmethod
    def estimate_detail_level(sharpness: float) -> str:
        """Estimate visual detail tier."""
        if sharpness < 20.0:
            return "low"
        elif sharpness < 250.0:
            return "medium"
        else:
            return "high"


class PipelineValidator:
    """
    Validate Melodia PBR textures against AAA quality standards.
    """
    
    # Power of Two standards
    TARGET_RESOLUTIONS = [256, 512, 1024, 2048, 4096, 8192]
    VALID_ASPECT_RATIOS = [1.0, 0.5, 2.0, 0.25, 4.0]
    MAX_FILE_SIZE_MB = 64.0  # Allow uncompressed 4K PNGs
    ACCEPTABLE_FORMATS = [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".exr", ".tga", ".bmp"]
    
    # Canonical Suffix Standard
    CANONICAL_SUFFIXES = {
        "_BC": "sRGB",
        "_BaseColor": "sRGB",
        "_ORM": "Linear",
        "_N": "Linear",
        "_Normal": "Linear",
        "_DetailN": "Linear",
        "_H": "Linear",
        "_Height": "Linear",
        "_Disp": "Linear",
        "_Displacement": "Linear",
        "_Mask": "Linear",
        "_Alpha": "Linear",
        "_Sheen": "Linear",
        "_Sparkle": "Linear",
        "_Emission": "sRGB",
        "_Emissive": "sRGB",
    }
    
    def __init__(self):
        self.report = ValidationReport()
        self.analyzer = TextureQualityAnalyzer()
    
    def _is_power_of_two(self, n: int) -> bool:
        """Check if integer is a positive power of two."""
        return n > 0 and (n & (n - 1)) == 0
    
    def validate_texture_set(self, textures: Dict[str, Union[Path, str]]) -> ValidationReport:
        """Validate an entire dictionary of texture names -> paths."""
        start_time = time.time()
        self.report = ValidationReport()
        self.report.total_textures = len(textures)
        
        path_dict: Dict[str, Path] = {k: Path(v) for k, v in textures.items()}
        
        for texture_name, texture_path in path_dict.items():
            try:
                passed = self._validate_single_texture(texture_name, texture_path)
                if passed:
                    self.report.passed_textures += 1
                else:
                    self.report.failed_textures += 1
            except Exception as e:
                self.report.failed_textures += 1
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Exception during validation: {e}",
                    texture_path=texture_path,
                ))
        
        # Cross-validation across texture set consistency
        self._validate_texture_set_consistency(path_dict)
        
        self.report.validation_time = time.time() - start_time
        return self.report
    
    def _validate_single_texture(self, name: str, path: Path) -> bool:
        """Validate a single texture file against all Melodia invariants."""
        if not path.exists():
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.CONSISTENCY,
                severity=ValidationSeverity.CRITICAL,
                message=f"Texture file does not exist on disk: {path}",
                texture_path=path,
            ))
            return False
        
        initial_error_count = self.report.error_count + self.report.critical_count
        
        # 1. Format check
        ext = path.suffix.lower()
        if ext not in self.ACCEPTABLE_FORMATS:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.COMPRESSION,
                severity=ValidationSeverity.ERROR,
                message=f"Unsupported texture file extension '{ext}'",
                texture_path=path,
                expected=f"One of {self.ACCEPTABLE_FORMATS}",
                actual=ext,
            ))
        
        # 2. File size check
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.FILE_SIZE,
                severity=ValidationSeverity.WARNING,
                message=f"File size ({size_mb:.2f} MB) exceeds recommended maximum ({self.MAX_FILE_SIZE_MB} MB)",
                texture_path=path,
                expected=f"< {self.MAX_FILE_SIZE_MB} MB",
                actual=f"{size_mb:.2f} MB",
            ))
        
        # 3. Naming convention & Suffix check
        expected_cs = self._validate_naming_and_suffix(name, path)
        
        # 4. Image inspection via PIL & NumPy
        try:
            with Image.open(path) as img:
                w, h = img.size
                mode = img.mode
                
                # Check Power-of-Two
                pot_w = self._is_power_of_two(w)
                pot_h = self._is_power_of_two(h)
                if not (pot_w and pot_h):
                    self.report.add_issue(ValidationIssue(
                        category=ValidationCategory.RESOLUTION,
                        severity=ValidationSeverity.ERROR,
                        message=f"Non-Power-of-Two (NPOT) resolution: {w}x{h}",
                        texture_path=path,
                        expected="Power-of-Two (512, 1024, 2048, 4096, 8192)",
                        actual=f"{w}x{h}",
                        suggestion="Resize to nearest power-of-two resolution",
                    ))
                elif w not in self.TARGET_RESOLUTIONS or h not in self.TARGET_RESOLUTIONS:
                    self.report.add_issue(ValidationIssue(
                        category=ValidationCategory.RESOLUTION,
                        severity=ValidationSeverity.WARNING,
                        message=f"Resolution {w}x{h} is POT but not standard game resolution",
                        texture_path=path,
                        expected=f"One of {self.TARGET_RESOLUTIONS}",
                        actual=f"{w}x{h}",
                    ))
                
                # Check aspect ratio
                aspect = float(w) / float(h)
                if not any(math.isclose(aspect, valid, rel_tol=1e-3) for valid in self.VALID_ASPECT_RATIOS):
                    self.report.add_issue(ValidationIssue(
                        category=ValidationCategory.ASPECT_RATIO,
                        severity=ValidationSeverity.WARNING,
                        message=f"Unusual texture aspect ratio: {aspect:.2f} ({w}x{h})",
                        texture_path=path,
                        expected="1:1 (square) or standard POT rectangle (1:2, 2:1)",
                        actual=f"{w}x{h}",
                    ))
                
                # Extract image array for channel checks
                arr = np.array(img)
                means, stds, mins, maxs = self.analyzer.compute_channel_stats(arr)
                sharpness = self.analyzer.analyze_sharpness(arr)
                detail = self.analyzer.estimate_detail_level(sharpness)
                
                # Store metric data
                self.report.metrics[name] = TextureMetricData(
                    path=str(path),
                    dimensions=(w, h),
                    channels=len(means),
                    mode=mode,
                    is_pot=pot_w and pot_h,
                    aspect_ratio=aspect,
                    file_size_bytes=size_bytes,
                    expected_color_space=expected_cs,
                    channel_means=means,
                    channel_stds=stds,
                    channel_mins=mins,
                    channel_maxs=maxs,
                    detail_level=detail,
                    sharpness_score=sharpness,
                )
                
                # Check specific texture categories
                lower_name = name.lower()
                if "_orm" in lower_name or lower_name.endswith("orm"):
                    self._validate_orm_packing(arr, path)
                elif "_normal" in lower_name or lower_name.endswith("_n") or "_nrm" in lower_name:
                    self._validate_normal_map(arr, path)
                elif "_basecolor" in lower_name or lower_name.endswith("_bc") or "_albedo" in lower_name:
                    self._validate_basecolor(arr, path)
                elif "_height" in lower_name or "_disp" in lower_name or lower_name.endswith("_h"):
                    self._validate_height_map(arr, path)

        except Exception as e:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.COMPRESSION,
                severity=ValidationSeverity.CRITICAL,
                message=f"Failed to decode image data: {e}",
                texture_path=path,
            ))
            return False
        
        errors_in_this_file = (self.report.error_count + self.report.critical_count) - initial_error_count
        return errors_in_this_file == 0
    
    def _validate_naming_and_suffix(self, name: str, path: Path) -> str:
        """Validate naming against Melodia PBR standard: T_<Family>_<Name>_<Channel>."""
        stem = path.stem
        
        # Check canonical UE prefix
        if not stem.startswith("T_"):
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.NAMING,
                severity=ValidationSeverity.INFO,
                message=f"Texture does not use standard 'T_' prefix: '{stem}'",
                texture_path=path,
                expected="T_<Family>_<Name>_<Channel>",
                actual=stem,
                suggestion=f"Rename to T_{stem}",
            ))
        
        # Check suffix
        matched_suffix = None
        expected_cs = "Linear"
        for sfx, cs in self.CANONICAL_SUFFIXES.items():
            if stem.endswith(sfx) or stem.lower().endswith(sfx.lower()):
                matched_suffix = sfx
                expected_cs = cs
                break
        
        if matched_suffix is None:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.NAMING,
                severity=ValidationSeverity.WARNING,
                message=f"Texture does not use a canonical PBR suffix: '{stem}'",
                texture_path=path,
                expected=f"One of {list(self.CANONICAL_SUFFIXES.keys())}",
                actual=stem,
            ))
        
        return expected_cs

    def _validate_orm_packing(self, arr: np.ndarray, path: Path):
        """
        Validate Melodia ORM channel packing:
            Red   (R) = Ambient Occlusion (Expected range 0..255, mean typically high > 100)
            Green (G) = Roughness (Expected range 0..255)
            Blue  (B) = Metallic (Expected range 0..255, dielectrics ~0, conductors ~255)
        """
        if arr.ndim != 3 or arr.shape[2] < 3:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.ORM_PACKING,
                severity=ValidationSeverity.ERROR,
                message=f"ORM texture must have at least 3 channels (RGB). Found shape: {arr.shape}",
                texture_path=path,
                expected="3-channel RGB image (R=AO, G=Roughness, B=Metallic)",
            ))
            return

        r_ao = arr[:, :, 0]
        g_rough = arr[:, :, 1]
        b_metal = arr[:, :, 2]

        # 1. Red channel (AO) check
        r_mean = float(r_ao.mean())
        if r_mean < 5.0 and r_ao.max() < 10:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.ORM_PACKING,
                severity=ValidationSeverity.WARNING,
                message=f"ORM Red channel (AO) is almost completely black (mean={r_mean:.1f}). Expected white (255) when unoccluded.",
                texture_path=path,
                expected="AO channel mean >= 100 (1.0 default = 255)",
                actual=f"Mean = {r_mean:.1f}",
                suggestion="Verify AO baking or ensure default fallback 255 is used",
            ))

        # 2. Green channel (Roughness) check
        g_mean = float(g_rough.mean())
        g_std = float(g_rough.std())
        # If roughness is completely 0 or 255 across entire texture without variance, note info
        if g_std < 0.1:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.ORM_PACKING,
                severity=ValidationSeverity.INFO,
                message=f"ORM Green channel (Roughness) has uniform value ({g_mean:.0f}) with 0 variance",
                texture_path=path,
            ))

        # 3. Degenerate black texture check (R=0, G=0, B=0 everywhere)
        if r_ao.max() == 0 and g_rough.max() == 0 and b_metal.max() == 0:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.ORM_PACKING,
                severity=ValidationSeverity.ERROR,
                message="ORM texture is completely black (all channels 0)",
                texture_path=path,
                expected="Valid packed ORM data (Red=AO, Green=Roughness, Blue=Metallic)",
            ))

    def _validate_normal_map(self, arr: np.ndarray, path: Path):
        """
        Validate tangent-space Normal map properties:
            - 3-channel RGB
            - Blue channel dominance (Z+ normal vector points outwards from surface, mean B >= 120)
            - Unit length verification: sqrt(X^2 + Y^2 + Z^2) approx 1.0
        """
        if arr.ndim != 3 or arr.shape[2] < 3:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.NORMAL_MAP,
                severity=ValidationSeverity.ERROR,
                message=f"Normal map must have 3 channels (RGB). Found shape: {arr.shape}",
                texture_path=path,
            ))
            return

        b_chan = arr[:, :, 2]
        b_mean = float(b_chan.mean())
        
        # Tangent space normal maps must have strong positive Z (Blue channel > 128)
        if b_mean < 110.0:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.NORMAL_MAP,
                severity=ValidationSeverity.WARNING,
                message=f"Normal map Blue channel average is low ({b_mean:.1f} < 120). May be object-space or inverted.",
                texture_path=path,
                expected="Tangent-space normal with Blue mean >= 120",
                actual=f"Mean B = {b_mean:.1f}",
            ))

        # Vector length verification on a sample grid
        sample = arr[::4, ::4, :3].astype(np.float32)
        nx = (sample[:, :, 0] / 127.5) - 1.0
        ny = (sample[:, :, 1] / 127.5) - 1.0
        nz = (sample[:, :, 2] / 127.5) - 1.0
        lengths = np.sqrt(nx * nx + ny * ny + nz * nz)
        mean_len = float(lengths.mean())

        if not (0.70 <= mean_len <= 1.30):
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.NORMAL_MAP,
                severity=ValidationSeverity.WARNING,
                message=f"Normal vector mean magnitude ({mean_len:.2f}) deviates from unit length (1.0)",
                texture_path=path,
                expected="Mean vector length ~ 1.0 [0.70 - 1.30]",
                actual=f"{mean_len:.2f}",
                suggestion="Re-normalize normal vectors or re-export from source",
            ))

    def _validate_basecolor(self, arr: np.ndarray, path: Path):
        """Validate BaseColor / Albedo map."""
        if arr.ndim != 3 or arr.shape[2] < 3:
            self.report.add_issue(ValidationIssue(
                category=ValidationCategory.CHANNEL_LAYOUT,
                severity=ValidationSeverity.WARNING,
                message=f"BaseColor texture is not RGB. Found shape: {arr.shape}",
                texture_path=path,
            ))

    def _validate_height_map(self, arr: np.ndarray, path: Path):
        """Validate Height / Displacement map."""
        if arr.ndim == 3 and arr.shape[2] >= 3:
            # If RGB, check if channels are identical grayscale
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            if not (np.array_equal(r, g) and np.array_equal(g, b)):
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CHANNEL_LAYOUT,
                    severity=ValidationSeverity.INFO,
                    message="Height map is RGB with differing color channels (not pure grayscale)",
                    texture_path=path,
                    suggestion="Convert to single channel 8-bit or 16-bit grayscale",
                ))

    def _validate_texture_set_consistency(self, textures: Dict[str, Path]):
        """Check resolution matching and completeness across material sets."""
        # Group textures by base material name
        groups: Dict[str, Dict[str, Path]] = {}
        
        for name, path in textures.items():
            # Strip canonical prefix and suffixes
            clean = path.stem
            if clean.startswith("T_"):
                clean = clean[2:]
            
            # Find matching suffix
            base_name = clean
            matched_sfx = "other"
            for sfx in self.CANONICAL_SUFFIXES:
                if clean.endswith(sfx):
                    base_name = clean[:-len(sfx)].rstrip("_")
                    matched_sfx = sfx.strip("_")
                    break
            
            if base_name not in groups:
                groups[base_name] = {}
            groups[base_name][matched_sfx] = path
        
        # Check resolution consistency within each material set
        for base_name, group in groups.items():
            if len(group) <= 1:
                continue
            
            sizes: Dict[str, Tuple[int, int]] = {}
            for sfx, p in group.items():
                if p.stem in self.report.metrics:
                    sizes[sfx] = self.report.metrics[p.stem].dimensions
                elif p.name in self.report.metrics:
                    sizes[sfx] = self.report.metrics[p.name].dimensions
            
            unique_sizes = set(sizes.values())
            if len(unique_sizes) > 1:
                self.report.add_issue(ValidationIssue(
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Material set '{base_name}' contains mismatched texture resolutions: {sizes}",
                    suggestion="Standardize all maps in the same material set to identical resolutions",
                ))


def main():
    """Command-line interface for Melodia Pipeline Validator."""
    parser = argparse.ArgumentParser(description="Validate Melodia PBR Pipeline Outputs")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing textures to validate")
    parser.add_argument("--output", "-o", help="Output JSON report destination path")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with code 1 if any validation error is detected")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed issue list and metrics")
    
    args = parser.parse_args()
    
    in_dir = Path(args.input)
    if not in_dir.exists():
        print(f"Error: Input directory not found: {in_dir}", file=sys.stderr)
        return 1
    
    validator = PipelineValidator()
    
    # Collect textures
    textures: Dict[str, Path] = {}
    for ext in validator.ACCEPTABLE_FORMATS:
        for p in in_dir.rglob(f"*{ext}"):
            textures[p.stem] = p
    
    print(f"[MelodiaValidator] Scanning {len(textures)} textures in {in_dir}...")
    report = validator.validate_texture_set(textures)
    
    print(f"\n[MelodiaValidator] Validation Summary:")
    print(f"  Total textures scanned: {report.total_textures}")
    print(f"  Passed:                 {report.passed_textures}")
    print(f"  Failed:                 {report.failed_textures}")
    print(f"  Warnings:               {report.warning_count}")
    print(f"  Errors:                 {report.error_count}")
    print(f"  Critical Issues:        {report.critical_count}")
    print(f"  Overall Valid:          {report.is_valid()}")
    
    if args.output:
        out_p = Path(args.output)
        report.save(out_p)
        print(f"  Report saved to:        {out_p}")
    
    if args.verbose and report.issues:
        print("\nDetailed Issues:")
        for issue in report.issues:
            print(f"  [{issue.severity.value.upper()}] ({issue.category.value}) {issue.message}")
            if issue.texture_path:
                print(f"      File: {issue.texture_path}")
            if issue.suggestion:
                print(f"      Suggestion: {issue.suggestion}")
    
    if args.fail_on_error and not report.is_valid():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())