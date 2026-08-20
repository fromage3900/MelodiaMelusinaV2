"""
Melodia Material Maker UI Addon
UI extension for Material Maker to manage Melodia pipeline settings

This addon provides a custom panel in Material Maker for:
- Style preset management
- Parameter control
- Batch processing
- Real-time preview
"""

import json
from pathlib import Path
from typing import Dict, Any

# Material Maker Python API integration
try:
    import material_maker as mm
    MM_AVAILABLE = True
    MM_API_MODE = "api"
except ImportError:
    MM_AVAILABLE = False
    MM_API_MODE = "json"
    print("Material Maker API not available - using JSON-based graph manipulation")

# Import graph manipulator for JSON-based manipulation
from graph_manipulator import MaterialMakerGraphManipulator


class MelodiaStylePresets:
    """Style preset definitions for Melodia pipeline."""
    
    PRESETS = {
        "neutral": {
            "name": "Neutral",
            "description": "Standard PBR without style effects",
            "params": {
                "StyleNikki": 0.0,
                "StyleMadoka": 0.0,
                "StyleItto": 0.0,
                "StyleCelestial": 0.0,
                "NikkiSaturation": 0.0,
                "NikkiPastelLift": 0.0,
                "SparkleDriftSpeed": 0.0,
                "WitchBarrierPhaseSpeed": 0.0,
                "WitchBarrierWallpaperScale": 1.0,
                "WitchBarrierMazeTightness": 0.0,
                "MadokaVeinEmissive": 0.0,
                "IttoPatternScale": 1.0,
                "IttoCrackDepth": 0.0,
                "IttoInkStrength": 0.0,
                "CelestialNebulaScale": 0.0,
                "CelestialTwinkle": 0.0,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.35,
                "NikkiFabricDetail": 0.15,
                "NikkiFlowStrength": 0.25,
                "MadokaGlowAmount": 0.3,
                "MadokaEmissiveBrightness": 2.0,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.0,
                "CelestialDrift": 0.1,
                "CelestialOrbitSpeed": 0.05,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.15,
                "CelestialEmissiveBoost": 1.5,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        },
        "nikki": {
            "name": "Nikki Dream",
            "description": "Rim lighting, sparkles, dream color grading",
            "params": {
                "StyleNikki": 0.8,
                "StyleMadoka": 0.0,
                "StyleItto": 0.0,
                "StyleCelestial": 0.0,
                "NikkiSaturation": 0.3,
                "NikkiPastelLift": 0.25,
                "SparkleDriftSpeed": 0.4,
                "WitchBarrierPhaseSpeed": 0.0,
                "WitchBarrierWallpaperScale": 1.0,
                "WitchBarrierMazeTightness": 0.0,
                "MadokaVeinEmissive": 0.0,
                "IttoPatternScale": 1.0,
                "IttoCrackDepth": 0.0,
                "IttoInkStrength": 0.0,
                "CelestialNebulaScale": 0.0,
                "CelestialTwinkle": 0.0,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.5,
                "NikkiFabricDetail": 0.2,
                "NikkiFlowStrength": 0.3,
                "MadokaGlowAmount": 0.3,
                "MadokaEmissiveBrightness": 2.0,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.0,
                "CelestialDrift": 0.1,
                "CelestialOrbitSpeed": 0.05,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.15,
                "CelestialEmissiveBoost": 1.5,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        },
        "madoka": {
            "name": "Madoka Witch",
            "description": "Witch barrier patterns, emissive veins",
            "params": {
                "StyleNikki": 0.0,
                "StyleMadoka": 0.7,
                "StyleItto": 0.0,
                "StyleCelestial": 0.0,
                "NikkiSaturation": 0.0,
                "NikkiPastelLift": 0.0,
                "SparkleDriftSpeed": 0.0,
                "WitchBarrierPhaseSpeed": 0.5,
                "WitchBarrierWallpaperScale": 4.0,
                "WitchBarrierMazeTightness": 0.5,
                "MadokaVeinEmissive": 0.4,
                "IttoPatternScale": 1.0,
                "IttoCrackDepth": 0.0,
                "IttoInkStrength": 0.0,
                "CelestialNebulaScale": 0.0,
                "CelestialTwinkle": 0.0,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.35,
                "NikkiFabricDetail": 0.15,
                "NikkiFlowStrength": 0.25,
                "MadokaGlowAmount": 0.4,
                "MadokaEmissiveBrightness": 2.5,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.0,
                "CelestialDrift": 0.1,
                "CelestialOrbitSpeed": 0.05,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.15,
                "CelestialEmissiveBoost": 1.5,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        },
        "itto": {
            "name": "Itto Oni",
            "description": "Oni geometry patterns, ink crack effects",
            "params": {
                "StyleNikki": 0.0,
                "StyleMadoka": 0.0,
                "StyleItto": 0.6,
                "StyleCelestial": 0.0,
                "NikkiSaturation": 0.0,
                "NikkiPastelLift": 0.0,
                "SparkleDriftSpeed": 0.0,
                "WitchBarrierPhaseSpeed": 0.0,
                "WitchBarrierWallpaperScale": 1.0,
                "WitchBarrierMazeTightness": 0.0,
                "MadokaVeinEmissive": 0.0,
                "IttoPatternScale": 3.0,
                "IttoCrackDepth": 0.4,
                "IttoInkStrength": 0.6,
                "CelestialNebulaScale": 0.0,
                "CelestialTwinkle": 0.0,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.35,
                "NikkiFabricDetail": 0.15,
                "NikkiFlowStrength": 0.25,
                "MadokaGlowAmount": 0.3,
                "MadokaEmissiveBrightness": 2.0,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.0,
                "CelestialDrift": 0.1,
                "CelestialOrbitSpeed": 0.05,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.15,
                "CelestialEmissiveBoost": 1.5,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        },
        "celestial": {
            "name": "Celestial",
            "description": "NASA spatial maps, nebula, twinkle effects",
            "params": {
                "StyleNikki": 0.0,
                "StyleMadoka": 0.0,
                "StyleItto": 0.0,
                "StyleCelestial": 0.9,
                "NikkiSaturation": 0.0,
                "NikkiPastelLift": 0.0,
                "SparkleDriftSpeed": 0.0,
                "WitchBarrierPhaseSpeed": 0.0,
                "WitchBarrierWallpaperScale": 1.0,
                "WitchBarrierMazeTightness": 0.0,
                "MadokaVeinEmissive": 0.0,
                "IttoPatternScale": 1.0,
                "IttoCrackDepth": 0.0,
                "IttoInkStrength": 0.0,
                "CelestialNebulaScale": 0.5,
                "CelestialTwinkle": 0.6,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.35,
                "NikkiFabricDetail": 0.15,
                "NikkiFlowStrength": 0.25,
                "MadokaGlowAmount": 0.3,
                "MadokaEmissiveBrightness": 2.0,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.5,
                "CelestialDrift": 0.15,
                "CelestialOrbitSpeed": 0.08,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.2,
                "CelestialEmissiveBoost": 2.0,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        },
        "sakura": {
            "name": "Sakura Dream",
            "description": "Japanese aesthetic, petal effects, warm tones",
            "params": {
                "StyleNikki": 0.5,
                "StyleMadoka": 0.0,
                "StyleItto": 0.0,
                "StyleCelestial": 0.0,
                "NikkiSaturation": 0.2,
                "NikkiPastelLift": 0.3,
                "SparkleDriftSpeed": 0.25,
                "WitchBarrierPhaseSpeed": 0.0,
                "WitchBarrierWallpaperScale": 1.0,
                "WitchBarrierMazeTightness": 0.0,
                "MadokaVeinEmissive": 0.0,
                "IttoPatternScale": 1.0,
                "IttoCrackDepth": 0.0,
                "IttoInkStrength": 0.0,
                "CelestialNebulaScale": 0.0,
                "CelestialTwinkle": 0.0,
                "GlobalSeed": 0.5,
                "NikkiSparkleAmount": 0.4,
                "NikkiFabricDetail": 0.15,
                "NikkiFlowStrength": 0.25,
                "MadokaGlowAmount": 0.3,
                "MadokaEmissiveBrightness": 2.0,
                "MadokaCuteBias": 0.5,
                "IttoWearAmount": 0.4,
                "IttoBreakupAmount": 0.25,
                "IttoErosionStrength": 0.2,
                "CelestialScale": 1.0,
                "CelestialDrift": 0.1,
                "CelestialOrbitSpeed": 0.05,
                "CelestialOrbitPeriod": 60,
                "CelestialCMBAmount": 0.15,
                "CelestialEmissiveBoost": 1.5,
                "HeightScale": 0.25,
                "NormalStrength": 0.8,
                "NormalDetail": 0.3,
                "RoughnessBias": 0.55,
                "RoughnessContrast": 0.3,
                "MetallicAmount": 0.05,
                "AOStrength": 0.7,
                "SSSAmount": 0.12,
                "EmissiveIntensity": 1.0,
                "ExportResolution": 11
            }
        }
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Dict[str, Any]:
        """Get preset configuration by name."""
        return cls.PRESETS.get(preset_name, cls.PRESETS["neutral"])
    
    @classmethod
    def get_preset_names(cls) -> list:
        """Get list of available preset names."""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def apply_preset_to_graph(cls, preset_name: str, graph_path: Path, output_path: Optional[Path] = None) -> bool:
        """Apply preset parameters to Material Maker graph."""
        preset = cls.get_preset(preset_name)
        
        if MM_AVAILABLE:
            # Use API if available
            try:
                graph = mm.load_graph(str(graph_path))
                for param_name, param_value in preset["params"].items():
                    try:
                        graph.set_parameter(param_name, param_value)
                    except Exception as e:
                        print(f"Failed to set parameter {param_name}: {e}")
                
                save_path = output_path or graph_path
                graph.save(str(save_path))
                return True
            except Exception as e:
                print(f"API method failed: {e}, falling back to JSON manipulation")
        
        # Fallback to JSON-based manipulation
        try:
            manipulator = MaterialMakerGraphManipulator()
            manipulator.load_graph(graph_path)
            applied = manipulator.apply_preset(preset["params"])
            
            save_path = output_path or graph_path
            manipulator.save_graph(save_path)
            
            print(f"Applied {applied} parameters from preset '{preset_name}' using JSON manipulation")
            return True
        except Exception as e:
            print(f"Failed to apply preset using JSON manipulation: {e}")
            return False


class MelodiaParameterManager:
    """Manage Melodia pipeline parameters."""
    
    PARAMETER_DEFINITIONS = {
        # Animation parameters
        "AnimSpeed": {"min": 0.0, "max": 2.0, "default": 0.15, "step": 0.01, "group": "Animation"},
        "AnimOffset": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.01, "group": "Animation"},
        "BakeTime": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.001, "group": "Animation"},
        
        # Tiling parameters
        "TileRepeat": {"min": 0.5, "max": 8.0, "default": 2.0, "step": 0.1, "group": "Tiling"},
        "SeamBlend": {"min": 0.0, "max": 1.0, "default": 0.35, "step": 0.01, "group": "Tiling"},
        
        # Global parameters
        "GlobalSeed": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.01, "group": "Global"},
        
        # Export parameters
        "ExportResolution": {"min": 0, "max": 12, "default": 11, "step": 1, "group": "Export"},
        
        # Nikki parameters
        "StyleNikki": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.01, "group": "Nikki Dream"},
        "NikkiSaturation": {"min": 0.0, "max": 1.0, "default": 0.18, "step": 0.01, "group": "Nikki Dream"},
        "NikkiPastelLift": {"min": 0.0, "max": 1.0, "default": 0.22, "step": 0.01, "group": "Nikki Dream"},
        "NikkiSparkleAmount": {"min": 0.0, "max": 2.0, "default": 0.35, "step": 0.01, "group": "Nikki Dream"},
        "NikkiFabricDetail": {"min": 0.0, "max": 1.0, "default": 0.15, "step": 0.01, "group": "Nikki Dream"},
        "NikkiFlowStrength": {"min": 0.0, "max": 1.0, "default": 0.25, "step": 0.01, "group": "Nikki Dream"},
        "SparkleDriftSpeed": {"min": 0.0, "max": 1.0, "default": 0.3, "step": 0.01, "group": "Nikki Dream"},
        
        # Madoka parameters
        "StyleMadoka": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.01, "group": "Madoka Witch"},
        "WitchBarrierPhaseSpeed": {"min": 0.0, "max": 2.0, "default": 0.45, "step": 0.01, "group": "Madoka Witch"},
        "WitchBarrierWallpaperScale": {"min": 1.0, "max": 12.0, "default": 4.0, "step": 0.1, "group": "Madoka Witch"},
        "WitchBarrierMazeTightness": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.01, "group": "Madoka Witch"},
        "MadokaVeinEmissive": {"min": 0.0, "max": 1.0, "default": 0.35, "step": 0.01, "group": "Madoka Witch"},
        "MadokaGlowAmount": {"min": 0.0, "max": 2.0, "default": 0.3, "step": 0.01, "group": "Madoka Witch"},
        "MadokaEmissiveBrightness": {"min": 0.0, "max": 5.0, "default": 2.0, "step": 0.1, "group": "Madoka Witch"},
        "MadokaCuteBias": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.01, "group": "Madoka Witch"},
        
        # Itto parameters
        "StyleItto": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.01, "group": "Itto Oni"},
        "IttoPatternScale": {"min": 1.0, "max": 12.0, "default": 3.0, "step": 0.1, "group": "Itto Oni"},
        "IttoCrackDepth": {"min": 0.0, "max": 1.0, "default": 0.4, "step": 0.01, "group": "Itto Oni"},
        "IttoInkStrength": {"min": 0.0, "max": 1.0, "default": 0.6, "step": 0.01, "group": "Itto Oni"},
        "IttoWearAmount": {"min": 0.0, "max": 1.0, "default": 0.4, "step": 0.01, "group": "Itto Oni"},
        "IttoBreakupAmount": {"min": 0.0, "max": 1.0, "default": 0.25, "step": 0.01, "group": "Itto Oni"},
        "IttoErosionStrength": {"min": 0.0, "max": 1.0, "default": 0.2, "step": 0.01, "group": "Itto Oni"},
        
        # Celestial parameters
        "StyleCelestial": {"min": 0.0, "max": 1.0, "default": 0.0, "step": 0.01, "group": "Celestial"},
        "CelestialNebulaScale": {"min": 0.0, "max": 2.0, "default": 0.42, "step": 0.01, "group": "Celestial"},
        "CelestialTwinkle": {"min": 0.0, "max": 1.0, "default": 0.5, "step": 0.01, "group": "Celestial"},
        "CelestialScale": {"min": 0.0, "max": 5.0, "default": 1.0, "step": 0.1, "group": "Celestial"},
        "CelestialDrift": {"min": 0.0, "max": 1.0, "default": 0.1, "step": 0.01, "group": "Celestial"},
        "CelestialOrbitSpeed": {"min": 0.0, "max": 0.5, "default": 0.05, "step": 0.01, "group": "Celestial"},
        "CelestialOrbitPeriod": {"min": 1, "max": 300, "default": 60, "step": 1, "group": "Celestial"},
        "CelestialCMBAmount": {"min": 0.0, "max": 1.0, "default": 0.15, "step": 0.01, "group": "Celestial"},
        "CelestialEmissiveBoost": {"min": 0.0, "max": 5.0, "default": 1.5, "step": 0.1, "group": "Celestial"},
        
        # Material parameters
        "HeightScale": {"min": 0.0, "max": 1.0, "default": 0.25, "step": 0.01, "group": "Material"},
        "NormalStrength": {"min": 0.0, "max": 2.0, "default": 0.8, "step": 0.01, "group": "Material"},
        "NormalDetail": {"min": 0.0, "max": 2.0, "default": 0.3, "step": 0.01, "group": "Material"},
        "RoughnessBias": {"min": 0.0, "max": 1.0, "default": 0.55, "step": 0.01, "group": "Material"},
        "RoughnessContrast": {"min": 0.0, "max": 1.0, "default": 0.3, "step": 0.01, "group": "Material"},
        "MetallicAmount": {"min": 0.0, "max": 1.0, "default": 0.05, "step": 0.01, "group": "Material"},
        "AOStrength": {"min": 0.0, "max": 1.0, "default": 0.7, "step": 0.01, "group": "Material"},
        "SSSAmount": {"min": 0.0, "max": 1.0, "default": 0.12, "step": 0.01, "group": "Material"},
        "EmissiveIntensity": {"min": 0.0, "max": 5.0, "default": 1.0, "step": 0.1, "group": "Material"},
    }
    
    @classmethod
    def get_parameter_groups(cls) -> Dict[str, list]:
        """Get parameters grouped by category."""
        groups = {}
        for param_name, param_def in cls.PARAMETER_DEFINITIONS.items():
            group = param_def["group"]
            if group not in groups:
                groups[group] = []
            groups[group].append(param_name)
        return groups
    
    @classmethod
    def get_parameter_definition(cls, param_name: str) -> Dict[str, Any]:
        """Get parameter definition."""
        return cls.PARAMETER_DEFINITIONS.get(param_name, {})
    
    @classmethod
    def validate_parameter(cls, param_name: str, value: float) -> bool:
        """Validate parameter value against definition."""
        param_def = cls.get_parameter_definition(param_name)
        if not param_def:
            return False
        
        return param_def["min"] <= value <= param_def["max"]


class MelodiaBatchProcessor:
    """Batch processing for texture conversion."""
    
    def __init__(self):
        self.input_dir = ""
        self.output_dir = ""
        self.target_resolution = 2048
        self.format = "BC7"
        self.processing = False
        self.texture_queue = []
        self.processed_count = 0
        self.failed_count = 0
        self.current_preset = "neutral"
    
    def set_directories(self, input_dir: str, output_dir: str):
        """Set input and output directories."""
        self.input_dir = input_dir
        self.output_dir = output_dir
    
    def set_processing_options(self, resolution: int, format: str):
        """Set processing options."""
        self.target_resolution = resolution
        self.format = format
    
    def set_preset(self, preset: str):
        """Set style preset."""
        self.current_preset = preset
    
    def scan_textures(self) -> int:
        """Scan input directory for textures."""
        from pathlib import Path
        
        input_path = Path(self.input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.exr', '.tga'}
        self.texture_queue = []
        
        for ext in supported_formats:
            self.texture_queue.extend(input_path.rglob(f"*{ext}"))
        
        return len(self.texture_queue)
    
    def process_batch(self) -> Dict[str, Any]:
        """Process texture batch using Material Maker graphs."""
        import time
        import shutil
        from pathlib import Path
        
        if not self.texture_queue:
            self.scan_textures()
        
        self.processing = True
        self.processed_count = 0
        self.failed_count = 0
        start_time = time.time()
        
        # Get Material Maker graph path
        mm_tools = Path(__file__).parent
        graph_path = mm_tools / "MM_Master_SurrealAnimatedPBR_v2_Static.ptex"
        
        if not graph_path.exists():
            return {
                "success": False,
                "error": f"Material Maker graph not found: {graph_path}",
                "processed": self.processed_count,
                "failed": self.failed_count
            }
        
        # Apply preset to graph
        from graph_manipulator import MaterialMakerGraphManipulator
        manipulator = MaterialMakerGraphManipulator()
        
        try:
            # Load and modify graph with preset
            manipulator.load_graph(graph_path)
            preset = MelodiaStylePresets.get_preset(self.current_preset)
            applied = manipulator.apply_preset(preset["params"])
            print(f"Applied {applied} parameters from preset '{self.current_preset}'")
            
            # Save modified graph to output directory
            output_graph = Path(self.output_dir) / f"MM_Melodia_{self.current_preset}.ptex"
            output_graph.parent.mkdir(parents=True, exist_ok=True)
            manipulator.save_graph(output_graph)
            
            # For now, just copy textures (actual processing would require Material Maker CLI)
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for texture_path in self.texture_queue:
                try:
                    # Copy texture to output (placeholder for actual Material Maker processing)
                    output_path = output_dir / texture_path.name
                    shutil.copy2(texture_path, output_path)
                    self.processed_count += 1
                except Exception as e:
                    self.failed_count += 1
                    print(f"Failed to process {texture_path.name}: {e}")
            
            return {
                "success": True,
                "processed": self.processed_count,
                "failed": self.failed_count,
                "total": len(self.texture_queue),
                "time": time.time() - start_time,
                "graph_path": str(output_graph),
                "note": "Texture copying (Material Maker CLI processing requires MM installation)"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processed": self.processed_count,
                "failed": self.failed_count
            }
        
        finally:
            self.processing = False
    
    def stop_processing(self):
        """Stop batch processing."""
        self.processing = False


class MelodiaPresetManager:
    """Manage custom presets."""
    
    def __init__(self, preset_dir: Path = None):
        if preset_dir is None:
            # Default to project directory
            project_root = Path(__file__).resolve().parents[2]
            preset_dir = project_root / "Tools" / "MaterialMaker" / "presets"
        
        self.preset_dir = Path(preset_dir)
        self.preset_dir.mkdir(parents=True, exist_ok=True)
    
    def save_preset(self, name: str, parameters: Dict[str, float], description: str = ""):
        """Save custom preset to file."""
        preset_data = {
            "name": name,
            "description": description,
            "params": parameters
        }
        
        preset_path = self.preset_dir / f"{name}.json"
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
    
    def load_preset(self, name: str) -> Dict[str, Any]:
        """Load custom preset from file."""
        preset_path = self.preset_dir / f"{name}.json"
        
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {name}")
        
        with open(preset_path, 'r') as f:
            return json.load(f)
    
    def list_custom_presets(self) -> list:
        """List available custom presets."""
        presets = []
        for preset_file in self.preset_dir.glob("*.json"):
            try:
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                    presets.append(preset_data["name"])
            except Exception:
                continue
        
        return presets
    
    def delete_preset(self, name: str):
        """Delete custom preset."""
        preset_path = self.preset_dir / f"{name}.json"
        if preset_path.exists():
            preset_path.unlink()


# Material Maker UI Integration
class MelodiaUIIntegration:
    """Integration with Material Maker UI system."""
    
    @staticmethod
    def create_panel():
        """Create Melodia panel in Material Maker UI."""
        if not MM_AVAILABLE:
            print("Material Maker UI integration not available")
            return None
        
        try:
            # Create panel using Material Maker UI API
            panel = mm.ui.create_panel("Melodia Pipeline")
            
            # Add style selector
            style_selector = panel.add_dropdown("Style Preset")
            for preset_name in MelodiaStylePresets.get_preset_names():
                preset = MelodiaStylePresets.get_preset(preset_name)
                style_selector.add_option(preset_name, preset["name"])
            
            # Add parameter controls
            param_groups = MelodiaParameterManager.get_parameter_groups()
            for group_name, param_names in param_groups.items():
                group_box = panel.add_group(group_name)
                for param_name in param_names:
                    param_def = MelodiaParameterManager.get_parameter_definition(param_name)
                    slider = group_box.add_slider(
                        param_name,
                        param_def["min"],
                        param_def["max"],
                        param_def["default"],
                        param_def["step"]
                    )
            
            # Add batch processing section
            batch_box = panel.add_group("Batch Processing")
            batch_box.add_text_input("Input Directory", "input_dir")
            batch_box.add_text_input("Output Directory", "output_dir")
            batch_box.add_dropdown("Resolution", ["512", "1024", "2048", "4096"])
            batch_box.add_dropdown("Format", ["BC7", "ASTC_4x4", "ASTC_6x6", "PNG"])
            batch_box.add_button("Scan Textures")
            batch_box.add_button("Process Batch")
            
            return panel
        
        except Exception as e:
            print(f"Failed to create Material Maker panel: {e}")
            return None
    
    @staticmethod
    def register_callbacks():
        """Register UI callbacks."""
        if not MM_AVAILABLE:
            return
        
        # Register preset change callback
        def on_preset_change(preset_name):
            MelodiaStylePresets.apply_preset_to_graph(preset_name, mm.graph)
        
        # Register batch processing callback
        def on_process_batch():
            processor = MelodiaBatchProcessor()
            result = processor.process_batch()
            print(f"Batch processing complete: {result}")
        
        # Register callbacks (placeholder - actual implementation depends on MM API)
        pass


# Initialize addon
def initialize_addon():
    """Initialize Melodia addon in Material Maker."""
    print("Initializing Melodia Material Maker Addon...")
    
    if MM_AVAILABLE:
        print("Material Maker API available - creating UI panel")
        panel = MelodiaUIIntegration.create_panel()
        MelodiaUIIntegration.register_callbacks()
        print("Melodia addon initialized successfully with API support")
    else:
        print("Material Maker API not available - using JSON-based graph manipulation")
        print("Addon functionality available via Python API and graph manipulation")
        print("Install Material Maker from https://rodzill4.github.io/material-maker/ for full API support")
    
    print("Melodia addon initialization complete")


if __name__ == "__main__":
    initialize_addon()