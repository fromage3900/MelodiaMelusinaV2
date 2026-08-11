"""
Universal Melodia Texture Pipeline
Core module for texture conversion and processing

Usage:
    from universal_melodia_texture_pipeline import UniversalMelodiaPipeline
    
    pipeline = UniversalMelodiaPipeline({
        'preset': 'photo_to_pbr',
        'resolution': 2048,
        'style': 'nikki'
    })
    
    pipeline.run_pipeline(
        input_dir=Path("Textures_Raw/Source"),
        output_dir=Path("Textures_Processed")
    )
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
TOOLS = PROJECT_ROOT / "Tools" / "MaterialMaker"


class TextureType(Enum):
    """Texture classification types."""
    ALBEDO = "albedo"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ambient_occlusion"
    HEIGHT = "height"
    DISPLACEMENT = "displacement"
    EMISSIVE = "emissive"
    OPACITY = "opacity"
    SSS = "subsurface_scattering"
    THICKNESS = "thickness"
    MASK = "mask"
    UNKNOWN = "unknown"


class ChannelLayout(Enum):
    """Channel layout configurations."""
    RGB = "rgb"
    RGBA = "rgba"
    GRAYSCALE = "grayscale"
    RGB_A = "rgb_with_alpha"


class ProcessingPreset(Enum):
    """Processing preset configurations."""
    PHOTO_TO_PBR = "photo_to_pbr"
    STYLIZED_NIKKI = "stylized_nikki"
    STYLIZED_MADOKA = "stylized_madoka"
    STYLIZED_ITTO = "stylized_itto"
    CELESTIAL = "celestial"
    SAKURA = "sakura"
    CUSTOM = "custom"


class CompressionFormat(Enum):
    """Texture compression formats."""
    BC7 = "bc7"
    ASTC_4x4 = "astc_4x4"
    ASTC_6x6 = "astc_6x6"
    EXR = "exr"
    PNG = "png"
    TGA = "tga"


@dataclass
class TextureInfo:
    """Information about a texture file."""
    path: Path
    texture_type: TextureType
    resolution: Tuple[int, int]
    channels: int
    channel_layout: ChannelLayout
    is_power_of_two: bool
    file_size: int
    estimated_roughness: Optional[float] = None
    estimated_metallic: Optional[float] = None


@dataclass
class MaterialSet:
    """Complete set of textures for a material."""
    name: str
    albedo: Optional[Path] = None
    normal: Optional[Path] = None
    roughness: Optional[Path] = None
    metallic: Optional[Path] = None
    ao: Optional[Path] = None
    height: Optional[Path] = None
    emissive: Optional[Path] = None
    opacity: Optional[Path] = None
    sss: Optional[Path] = None
    thickness: Optional[Path] = None
    
    def get_missing_maps(self) -> List[str]:
        """Return list of missing texture maps."""
        missing = []
        if not self.albedo: missing.append("albedo")
        if not self.normal: missing.append("normal")
        if not self.roughness: missing.append("roughness")
        if not self.metallic: missing.append("metallic")
        return missing


@dataclass
class ProcessingConfig:
    """Configuration for texture processing."""
    preset: ProcessingPreset = ProcessingPreset.PHOTO_TO_PBR
    resolution: int = 2048
    format: CompressionFormat = CompressionFormat.BC7
    style: str = "neutral"
    generate_height: bool = True
    generate_normal: bool = True
    estimate_roughness: bool = True
    estimate_metallic: bool = True
    optimize: bool = True
    generate_mipmaps: bool = True
    
    # Style-specific parameters
    anim_speed: float = 0.15
    anim_offset: float = 0.0
    tile_repeat: float = 2.0
    seam_blend: float = 0.35
    
    # Nikki parameters
    style_nikki: float = 0.5
    dream_saturation: float = 0.18
    pastel_lift: float = 0.22
    sparkle_drift_speed: float = 0.3
    
    # Madoka parameters
    style_madoka: float = 0.0
    witch_barrier_phase_speed: float = 0.45
    witch_barrier_wallpaper_scale: float = 4.0
    witch_barrier_maze_tightness: float = 0.5
    witch_barrier_emissive_veins: float = 0.35
    
    # Itto parameters
    style_itto: float = 0.0
    itto_pattern_scale: float = 3.0
    itto_crack_depth: float = 0.4
    itto_ink_strength: float = 0.6
    
    # Celestial parameters
    style_celestial: float = 0.0
    celestial_nebula_scale: float = 0.42
    celestial_twinkle: float = 0.5
    
    # Material parameters
    height_scale: float = 0.25
    normal_strength: float = 0.8


@dataclass
class PipelineReport:
    """Report from pipeline execution."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    input_dir: Path = field(default_factory=Path)
    output_dir: Path = field(default_factory=Path)
    total_textures: int = 0
    processed_textures: int = 0
    failed_textures: int = 0
    skipped_textures: int = 0
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generated_materials: List[MaterialSet] = field(default_factory=list)
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_textures == 0:
            return 0.0
        return (self.processed_textures / self.total_textures) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "total_textures": self.total_textures,
            "processed_textures": self.processed_textures,
            "failed_textures": self.failed_textures,
            "skipped_textures": self.skipped_textures,
            "processing_time": self.processing_time,
            "success_rate": self.success_rate(),
            "errors": self.errors,
            "warnings": self.warnings,
            "generated_materials": [
                {
                    "name": mat.name,
                    "missing_maps": mat.get_missing_maps()
                }
                for mat in self.generated_materials
            ]
        }
    
    def save(self, output_path: Path):
        """Save report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class TextureScanner:
    """Scan and classify texture files."""
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.exr', '.tga'}
    TARGET_RESOLUTIONS = [512, 1024, 2048, 4096]
    
    def __init__(self):
        self.scanned_textures: List[TextureInfo] = []
    
    def scan_directory(self, directory: Path) -> List[TextureInfo]:
        """Scan directory for texture files."""
        self.scanned_textures = []
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        for ext in self.SUPPORTED_FORMATS:
            self.scanned_textures.extend(
                self._analyze_texture(path)
                for path in directory.rglob(f"*{ext}")
            )
        
        # Filter out failed analyses
        self.scanned_textures = [t for t in self.scanned_textures if t is not None]
        
        return self.scanned_textures
    
    def _analyze_texture(self, path: Path) -> Optional[TextureInfo]:
        """Analyze single texture file."""
        try:
            # Use PIL or similar to get image info
            # For now, return basic info
            resolution = self._get_resolution(path)
            channels = self._get_channel_count(path)
            
            return TextureInfo(
                path=path,
                texture_type=self._classify_texture(path, channels),
                resolution=resolution,
                channels=channels,
                channel_layout=self._determine_channel_layout(channels),
                is_power_of_two=self._is_power_of_two(resolution),
                file_size=path.stat().st_size
            )
        except Exception as e:
            print(f"Failed to analyze {path}: {e}")
            return None
    
    def _get_resolution(self, path: Path) -> Tuple[int, int]:
        """Get texture resolution."""
        # Placeholder - implement with PIL/Pillow
        return (1024, 1024)
    
    def _get_channel_count(self, path: Path) -> int:
        """Get number of channels."""
        # Placeholder - implement with PIL/Pillow
        return 3
    
    def _classify_texture(self, path: Path, channels: int) -> TextureType:
        """Classify texture by filename and content."""
        filename_lower = path.name.lower()
        
        # Filename-based classification
        if any(keyword in filename_lower for keyword in ['albedo', 'diffuse', 'color', 'base']):
            return TextureType.ALBEDO
        elif any(keyword in filename_lower for keyword in ['normal', 'nrm']):
            return TextureType.NORMAL
        elif any(keyword in filename_lower for keyword in ['rough', 'roughness']):
            return TextureType.ROUGHNESS
        elif any(keyword in filename_lower for keyword in ['metal', 'metallic']):
            return TextureType.METALLIC
        elif any(keyword in filename_lower for keyword in ['ao', 'ambient', 'occlusion']):
            return TextureType.AO
        elif any(keyword in filename_lower for keyword in ['height', 'disp', 'displacement']):
            return TextureType.HEIGHT
        elif any(keyword in filename_lower for keyword in ['emissive', 'emit', 'glow']):
            return TextureType.EMISSIVE
        elif any(keyword in filename_lower for keyword in ['opacity', 'alpha', 'mask']):
            return TextureType.OPACITY
        elif any(keyword in filename_lower for keyword in ['sss', 'subsurface']):
            return TextureType.SSS
        elif any(keyword in filename_lower for keyword in ['thickness']):
            return TextureType.THICKNESS
        
        # Default to albedo for unknown
        return TextureType.ALBEDO
    
    def _determine_channel_layout(self, channels: int) -> ChannelLayout:
        """Determine channel layout from channel count."""
        if channels == 1:
            return ChannelLayout.GRAYSCALE
        elif channels == 3:
            return ChannelLayout.RGB
        elif channels == 4:
            return ChannelLayout.RGBA
        else:
            return ChannelLayout.RGB
    
    def _is_power_of_two(self, resolution: Tuple[int, int]) -> bool:
        """Check if resolution is power of two."""
        width, height = resolution
        return (width & (width - 1) == 0) and (height & (height - 1) == 0)
    
    def group_by_material(self) -> Dict[str, List[TextureInfo]]:
        """Group textures by material name."""
        material_groups: Dict[str, List[TextureInfo]] = {}
        
        for texture in self.scanned_textures:
            # Extract material name from filename
            material_name = self._extract_material_name(texture.path)
            
            if material_name not in material_groups:
                material_groups[material_name] = []
            
            material_groups[material_name].append(texture)
        
        return material_groups
    
    def _extract_material_name(self, path: Path) -> str:
        """Extract material name from texture path."""
        # Remove common suffixes and extensions
        name = path.stem
        
        # Remove common texture type suffixes
        suffixes = [
            '_albedo', '_diffuse', '_color', '_base',
            '_normal', '_nrm', '_rough', '_roughness',
            '_metal', '_metallic', '_ao', '_ambient',
            '_height', '_disp', '_displacement',
            '_emissive', '_emit', '_opacity', '_alpha',
            '_sss', '_subsurface', '_thickness'
        ]
        
        for suffix in suffixes:
            if name.lower().endswith(suffix):
                name = name[:-len(suffix)]
        
        return name


class UniversalMelodiaPipeline:
    """Universal texture conversion pipeline for Melodia design system."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.scanner = TextureScanner()
        self.report = PipelineReport()
    
    def run_pipeline(self, input_dir: Path, output_dir: Path) -> PipelineReport:
        """Execute full pipeline from input to output."""
        import time
        
        start_time = time.time()
        self.report.input_dir = input_dir
        self.report.output_dir = output_dir
        
        print(f"Starting Melodia Pipeline: {input_dir} -> {output_dir}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Phase 1: Scan textures
        print("Phase 1: Scanning textures...")
        textures = self.scanner.scan_directory(input_dir)
        self.report.total_textures = len(textures)
        print(f"Found {len(textures)} textures")
        
        # Phase 2: Group by material
        print("Phase 2: Grouping textures by material...")
        material_groups = self.scanner.group_by_material()
        print(f"Found {len(material_groups)} material groups")
        
        # Phase 3: Process each material set
        print("Phase 3: Processing material sets...")
        for material_name, texture_list in material_groups.items():
            try:
                material_set = self._process_material_set(material_name, texture_list, output_dir)
                self.report.generated_materials.append(material_set)
                self.report.processed_textures += len(texture_list)
            except Exception as e:
                self.report.failed_textures += len(texture_list)
                self.report.errors.append(f"Failed to process {material_name}: {e}")
                print(f"Error processing {material_name}: {e}")
        
        # Calculate processing time
        self.report.processing_time = time.time() - start_time
        
        print(f"Pipeline complete in {self.report.processing_time:.2f}s")
        print(f"Success rate: {self.report.success_rate():.1f}%")
        
        return self.report
    
    def _process_material_set(self, name: str, textures: List[TextureInfo], output_dir: Path) -> MaterialSet:
        """Process single material set."""
        material_set = MaterialSet(name=name)
        
        # Assign textures to material set
        for texture in textures:
            if texture.texture_type == TextureType.ALBEDO:
                material_set.albedo = texture.path
            elif texture.texture_type == TextureType.NORMAL:
                material_set.normal = texture.path
            elif texture.texture_type == TextureType.ROUGHNESS:
                material_set.roughness = texture.path
            elif texture.texture_type == TextureType.METALLIC:
                material_set.metallic = texture.path
            elif texture.texture_type == TextureType.AO:
                material_set.ao = texture.path
            elif texture.texture_type == TextureType.HEIGHT:
                material_set.height = texture.path
            elif texture.texture_type == TextureType.EMISSIVE:
                material_set.emissive = texture.path
            elif texture.texture_type == TextureType.OPACITY:
                material_set.opacity = texture.path
            elif texture.texture_type == TextureType.SSS:
                material_set.sss = texture.path
            elif texture.texture_type == TextureType.THICKNESS:
                material_set.thickness = texture.path
        
        # Generate missing maps if needed
        if self.config.generate_normal and not material_set.normal and material_set.height:
            print(f"Generating normal map for {name}...")
            # material_set.normal = self._generate_normal(material_set.height, output_dir)
        
        if self.config.estimate_roughness and not material_set.roughness and material_set.albedo:
            print(f"Estimating roughness for {name}...")
            # material_set.roughness = self._estimate_roughness(material_set.albedo, output_dir)
        
        if self.config.estimate_metallic and not material_set.metallic and material_set.albedo:
            print(f"Estimating metallic for {name}...")
            # material_set.metallic = self._estimate_metallic(material_set.albedo, output_dir)
        
        return material_set
    
    def _generate_normal(self, height_map: Path, output_dir: Path) -> Path:
        """Generate normal map from height map."""
        # Placeholder for Material Maker integration
        output_path = output_dir / f"{height_map.stem}_normal.png"
        return output_path
    
    def _estimate_roughness(self, albedo: Path, output_dir: Path) -> Path:
        """Estimate roughness from albedo."""
        # Placeholder for Material Maker integration
        output_path = output_dir / f"{albedo.stem}_roughness.png"
        return output_path
    
    def _estimate_metallic(self, albedo: Path, output_dir: Path) -> Path:
        """Estimate metallic from albedo."""
        # Placeholder for Material Maker integration
        output_path = output_dir / f"{albedo.stem}_metallic.png"
        return output_path


# Convenience function for command-line usage
def main():
    """Command-line interface for pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Melodia Texture Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Input texture directory")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--preset", "-p", default="photo_to_pbr", help="Processing preset")
    parser.add_argument("--resolution", "-r", type=int, default=2048, help="Target resolution")
    parser.add_argument("--style", "-s", default="neutral", help="Style preset")
    
    args = parser.parse_args()
    
    config = ProcessingConfig(
        preset=ProcessingPreset(args.preset),
        resolution=args.resolution,
        style=args.style
    )
    
    pipeline = UniversalMelodiaPipeline(config)
    report = pipeline.run_pipeline(Path(args.input), Path(args.output))
    
    # Save report
    report_path = Path(args.output) / "pipeline_report.json"
    report.save(report_path)
    
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()