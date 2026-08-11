"""
Unreal Engine Integration for Melodia Pipeline
Import processed textures and create material instances

Usage:
    from unreal_melodia_integration import UnrealTextureImporter
    
    importer = UnrealTextureImporter()
    importer.import_texture_set(material_set, "/Game/EnvSandbox/Textures")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Unreal Engine Python API
try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False
    print("Unreal Engine Python API not available")


@dataclass
class ImportSettings:
    """Texture import settings for Unreal Engine."""
    compression: str = "BC7"
    srgb: bool = True
    mipmaps: bool = True
    max_texture_size: int = 4096
    streaming: bool = False
    lod_bias: int = 0
    filter: str = "Default"
    address_x: str = "Wrap"
    address_y: str = "Wrap"
    address_z: str = "Wrap"


@dataclass
class MaterialAssignment:
    """Material texture assignment configuration."""
    master_material: str = "/Game/EnvSandbox/Materials/Masters/M_Universal_Default"
    instance_path: str = ""
    texture_assignments: Dict[str, str] = field(default_factory=dict)
    parameter_overrides: Dict[str, float] = field(default_factory=dict)


class UnrealTextureImporter:
    """Import processed textures into Unreal Engine."""
    
    def __init__(self):
        self.imported_textures: Dict[str, str] = {}
        self.import_report: Dict = {}
    
    def import_texture(self, source_path: Path, ue_path: str, settings: ImportSettings = None) -> Optional[str]:
        """Import single texture into Unreal Engine."""
        if not UNREAL_AVAILABLE:
            print("Unreal Engine API not available")
            return None
        
        if settings is None:
            settings = ImportSettings()
        
        try:
            # Convert source path to Unreal asset path
            source_path_str = str(source_path).replace("\\", "/")
            
            # Create import task
            import_task = unreal.AssetImportTask()
            import_task.filename = source_path_str
            import_task.destination_path = ue_path
            import_task.replace_existing = True
            # `async` is a Python keyword, so use Unreal reflection rather
            # than attribute syntax for this UPROPERTY.
            import_task.set_editor_property("async", False)
            
            # Configure texture settings
            texture_factory = unreal.TextureFactory()
            
            # Apply import settings
            self._apply_import_settings(texture_factory, settings)
            
            import_task.options = texture_factory
            
            # Execute import
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            imported_asset = asset_tools.import_asset_task(import_task)
            
            if imported_asset:
                asset_path = imported_asset.get_path_name()
                self.imported_textures[source_path_str] = asset_path
                print(f"Imported: {source_path} -> {asset_path}")
                return asset_path
            
            return None
        
        except Exception as e:
            print(f"Failed to import {source_path}: {e}")
            return None
    
    def _apply_import_settings(self, texture_factory, settings: ImportSettings):
        """Apply import settings to texture factory."""
        # Placeholder - actual implementation depends on Unreal API structure
        # This would set compression, sRGB, mipmaps, etc.
        pass
    
    def import_material_set(self, material_set: Dict[str, Path], base_path: str) -> Dict[str, str]:
        """Import complete material texture set."""
        imported_paths = {}
        
        for texture_type, texture_path in material_set.items():
            if texture_path and texture_path.exists():
                # Generate Unreal path
                texture_name = texture_path.stem
                ue_path = f"{base_path}/{texture_name}"
                
                # Import texture
                imported_path = self.import_texture(texture_path, ue_path)
                if imported_path:
                    imported_paths[texture_type] = imported_path
        
        return imported_paths
    
    def batch_import_directory(self, source_dir: Path, ue_base_path: str) -> Dict[str, str]:
        """Batch import all textures from directory."""
        imported_paths = {}
        
        supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.exr', '.tga'}
        
        for ext in supported_formats:
            for texture_path in source_dir.rglob(f"*{ext}"):
                texture_name = texture_path.stem
                ue_path = f"{ue_base_path}/{texture_name}"
                
                imported_path = self.import_texture(texture_path, ue_path)
                if imported_path:
                    imported_paths[str(texture_path)] = imported_path
        
        return imported_paths


class MaterialInstanceGenerator:
    """Generate material instances from imported textures."""
    
    def __init__(self):
        self.created_instances: List[str] = []
    
    def create_instance(self, assignment: MaterialAssignment) -> Optional[str]:
        """Create material instance from assignment."""
        if not UNREAL_AVAILABLE:
            print("Unreal Engine API not available")
            return None
        
        try:
            # Load master material
            master_material = unreal.load_asset(assignment.master_material)
            if not master_material:
                print(f"Master material not found: {assignment.master_material}")
                return None
            
            # Create instance
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            
            # Generate instance path if not provided
            if not assignment.instance_path:
                master_name = master_material.get_name()
                assignment.instance_path = f"{assignment.master_material}_Instance"
            
            # Create material instance
            instance = asset_tools.create_asset(
                asset_name=assignment.instance_path.split("/")[-1],
                package_path="/".join(assignment.instance_path.split("/")[:-1]),
                asset_class=unreal.MaterialInstanceConstant,
                factory=unreal.MaterialInstanceConstantFactory()
            )
            
            if instance:
                # Set parent material
                instance.set_parent_editor_only(master_material)
                
                # Assign textures
                self._assign_textures(instance, assignment.texture_assignments)
                
                # Set parameter overrides
                self._set_parameter_overrides(instance, assignment.parameter_overrides)
                
                self.created_instances.append(instance.get_path_name())
                print(f"Created instance: {instance.get_path_name()}")
                return instance.get_path_name()
            
            return None
        
        except Exception as e:
            print(f"Failed to create material instance: {e}")
            return None
    
    def _assign_textures(self, instance, texture_assignments: Dict[str, str]):
        """Assign textures to material instance parameters."""
        # Common texture parameter names
        texture_parameters = {
            "BaseColor": "albedo",
            "Normal": "normal", 
            "Roughness": "roughness",
            "Metallic": "metallic",
            "AmbientOcclusion": "ao",
            "Height": "height",
            "Emissive": "emissive",
            "Opacity": "opacity"
        }
        
        for param_name, texture_type in texture_parameters.items():
            if texture_type in texture_assignments:
                texture_path = texture_assignments[texture_type]
                texture = unreal.load_asset(texture_path)
                
                if texture:
                    instance.set_editor_property(param_name, texture)
                    print(f"  Assigned {param_name}: {texture_path}")
    
    def _set_parameter_overrides(self, instance, parameter_overrides: Dict[str, float]):
        """Set scalar parameter overrides."""
        for param_name, param_value in parameter_overrides.items():
            try:
                instance.set_scalar_parameter_value(param_name, param_value)
                print(f"  Set parameter {param_name}: {param_value}")
            except Exception as e:
                print(f"  Failed to set parameter {param_name}: {e}")
    
    def batch_create_instances(self, assignments: List[MaterialAssignment]) -> List[str]:
        """Batch create material instances."""
        created_paths = []
        
        for assignment in assignments:
            instance_path = self.create_instance(assignment)
            if instance_path:
                created_paths.append(instance_path)
        
        return created_paths


class UnrealMelodiaIntegration:
    """Complete integration pipeline for Unreal Engine."""
    
    def __init__(self):
        self.texture_importer = UnrealTextureImporter()
        self.instance_generator = MaterialInstanceGenerator()
        self.integration_report: Dict = {}
    
    def integrate_material_pipeline(self, processed_dir: Path, ue_base_path: str) -> Dict:
        """Complete integration from processed textures to Unreal materials."""
        print(f"Starting Unreal integration: {processed_dir} -> {ue_base_path}")
        
        # Phase 1: Import textures
        print("Phase 1: Importing textures...")
        imported_textures = self.texture_importer.batch_import_directory(processed_dir, ue_base_path)
        print(f"Imported {len(imported_textures)} textures")
        
        # Phase 2: Group textures by material
        print("Phase 2: Grouping textures by material...")
        material_groups = self._group_textures_by_material(imported_textures)
        print(f"Found {len(material_groups)} material groups")
        
        # Phase 3: Create material instances
        print("Phase 3: Creating material instances...")
        created_instances = []
        for material_name, texture_paths in material_groups.items():
            assignment = MaterialAssignment(
                instance_path=f"{ue_base_path}/Instances/{material_name}",
                texture_assignments=texture_paths
            )
            instance_path = self.instance_generator.create_instance(assignment)
            if instance_path:
                created_instances.append(instance_path)
        
        print(f"Created {len(created_instances)} material instances")
        
        # Generate report
        self.integration_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processed_dir": str(processed_dir),
            "ue_base_path": ue_base_path,
            "imported_textures": len(imported_textures),
            "material_groups": len(material_groups),
            "created_instances": len(created_instances),
            "imported_texture_paths": imported_textures,
            "created_instance_paths": created_instances
        }
        
        return self.integration_report
    
    def _group_textures_by_material(self, imported_textures: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Group imported textures by material name."""
        material_groups = {}
        
        for source_path, ue_path in imported_textures.items():
            # Extract material name from texture name
            texture_name = Path(source_path).stem
            material_name = self._extract_material_name(texture_name)
            
            # Determine texture type
            texture_type = self._determine_texture_type(texture_name)
            
            if material_name not in material_groups:
                material_groups[material_name] = {}
            
            material_groups[material_name][texture_type] = ue_path
        
        return material_groups
    
    def _extract_material_name(self, texture_name: str) -> str:
        """Extract material name from texture name."""
        # Remove common suffixes
        suffixes = [
            '_albedo', '_diffuse', '_color', '_base',
            '_normal', '_nrm', '_rough', '_roughness',
            '_metal', '_metallic', '_ao', '_ambient',
            '_height', '_disp', '_displacement',
            '_emissive', '_emit', '_opacity', '_alpha',
            '_sss', '_subsurface', '_thickness'
        ]
        
        name = texture_name
        for suffix in suffixes:
            if name.lower().endswith(suffix):
                name = name[:-len(suffix)]
        
        return name
    
    def _determine_texture_type(self, texture_name: str) -> str:
        """Determine texture type from name."""
        name_lower = texture_name.lower()
        
        if any(keyword in name_lower for keyword in ['albedo', 'diffuse', 'color', 'base']):
            return "albedo"
        elif any(keyword in name_lower for keyword in ['normal', 'nrm']):
            return "normal"
        elif any(keyword in name_lower for keyword in ['rough', 'roughness']):
            return "roughness"
        elif any(keyword in name_lower for keyword in ['metal', 'metallic']):
            return "metallic"
        elif any(keyword in name_lower for keyword in ['ao', 'ambient', 'occlusion']):
            return "ao"
        elif any(keyword in name_lower for keyword in ['height', 'disp', 'displacement']):
            return "height"
        elif any(keyword in name_lower for keyword in ['emissive', 'emit', 'glow']):
            return "emissive"
        elif any(keyword in name_lower for keyword in ['opacity', 'alpha', 'mask']):
            return "opacity"
        
        return "albedo"  # Default
    
    def save_integration_report(self, output_path: Path):
        """Save integration report to file."""
        with open(output_path, 'w') as f:
            json.dump(self.integration_report, f, indent=2)


# Convenience function for command-line usage
def main():
    """Command-line interface for Unreal integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unreal Engine Integration for Melodia Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Processed texture directory")
    parser.add_argument("--ue-path", "-u", required=True, help="Unreal Engine base path")
    parser.add_argument("--output", "-o", help="Output integration report path")
    
    args = parser.parse_args()
    
    integrator = UnrealMelodiaIntegration()
    report = integrator.integrate_material_pipeline(Path(args.input), args.ue_path)
    
    print(f"\nIntegration Report:")
    print(f"Imported textures: {report['imported_textures']}")
    print(f"Material groups: {report['material_groups']}")
    print(f"Created instances: {report['created_instances']}")
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        integrator.save_integration_report(output_path)
        print(f"Report saved to {output_path}")


if __name__ == "__main__":
    main()
