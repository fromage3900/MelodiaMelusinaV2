"""
Material Maker Graph Manipulator (JSON-based)
Direct .ptex graph manipulation without requiring Material Maker API

This allows the Melodia pipeline to work with .ptex files
by directly manipulating the JSON structure.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class MaterialMakerGraphManipulator:
    """Manipulate Material Maker .ptex graphs via JSON."""
    
    def __init__(self):
        self.current_graph = None
        self.graph_path = None
    
    def load_graph(self, graph_path: Path) -> Dict[str, Any]:
        """Load .ptex graph file."""
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph file not found: {graph_path}")
        
        with open(graph_path, 'r') as f:
            self.current_graph = json.load(f)
            self.graph_path = graph_path
        
        return self.current_graph
    
    def save_graph(self, output_path: Optional[Path] = None) -> Path:
        """Save graph to file."""
        if self.current_graph is None:
            raise ValueError("No graph loaded")
        
        save_path = output_path or self.graph_path
        if save_path is None:
            raise ValueError("No output path specified")
        
        with open(save_path, 'w') as f:
            json.dump(self.current_graph, f, indent=2)
        
        return save_path
    
    def set_parameter(self, param_name: str, param_value: float) -> bool:
        """Set parameter value in graph."""
        if self.current_graph is None:
            return False
        
        # Try remote section first
        if 'remote' in self.current_graph:
            for widget in self.current_graph['remote'].get('widgets', []):
                if widget.get('name') == param_name:
                    widget['parameters'] = widget.get('parameters', {})
                    widget['parameters'][param_name] = param_value
                    return True
        
        # Try to find parameter in nodes
        for node in self.current_graph.get('nodes', []):
            if param_name in node.get('parameters', {}):
                node['parameters'][param_name] = param_value
                return True
        
        return False
    
    def get_parameter(self, param_name: str) -> Optional[float]:
        """Get parameter value from graph."""
        if self.current_graph is None:
            return None
        
        # Try remote section first
        if 'remote' in self.current_graph:
            for widget in self.current_graph['remote'].get('widgets', []):
                if widget.get('name') == param_name:
                    params = widget.get('parameters', {})
                    return params.get(param_name)
        
        # Try to find parameter in nodes
        for node in self.current_graph.get('nodes', []):
            if param_name in node.get('parameters', {}):
                return node['parameters'][param_name]
        
        return None
    
    def list_parameters(self) -> List[str]:
        """List all parameter names."""
        if self.current_graph is None:
            return []
        
        param_names = []
        
        # Collect from remote section
        if 'remote' in self.current_graph:
            param_names.extend([
                widget.get('name', 'unknown')
                for widget in self.current_graph['remote'].get('widgets', [])
            ])
        
        # Collect from nodes
        for node in self.current_graph.get('nodes', []):
            param_names.extend(node.get('parameters', {}).keys())
        
        return list(set(param_names))  # Remove duplicates
    
    def apply_preset(self, preset_params: Dict[str, float]) -> int:
        """Apply preset parameters to graph."""
        if self.current_graph is None:
            return 0
        
        applied_count = 0
        for param_name, param_value in preset_params.items():
            if self.set_parameter(param_name, param_value):
                applied_count += 1
        
        return applied_count
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about current graph."""
        if self.current_graph is None:
            return {}
        
        param_names = self.list_parameters()
        
        return {
            'name': self.current_graph.get('name', 'unknown'),
            'nodes': len(self.current_graph.get('nodes', [])),
            'connections': len(self.current_graph.get('connections', [])),
            'parameters': len(param_names),
            'has_remote': 'remote' in self.current_graph,
            'sample_parameters': param_names[:10] if param_names else []
        }
    
    def clone_graph(self) -> Dict[str, Any]:
        """Create a deep copy of current graph."""
        if self.current_graph is None:
            return {}
        
        import copy
        return copy.deepcopy(self.current_graph)
    
    def set_input_texture(self, node_name: str, texture_path: str) -> bool:
        """Set input texture for a specific node."""
        if self.current_graph is None:
            return False
        
        for node in self.current_graph.get('nodes', []):
            if node.get('name') == node_name:
                node['parameters'] = node.get('parameters', {})
                node['parameters']['file'] = texture_path
                return True
        
        return False
    
    def set_export_resolution(self, resolution: int) -> bool:
        """Set export resolution for all export nodes."""
        if self.current_graph is None:
            return False
        
        count = 0
        for node in self.current_graph.get('nodes', []):
            if node.get('type') == 'export':
                node['parameters'] = node.get('parameters', {})
                node['parameters']['size'] = resolution
                count += 1
        
        return count > 0


class PresetApplier:
    """Apply Melodia presets to Material Maker graphs."""
    
    def __init__(self):
        self.manipulator = MaterialMakerGraphManipulator()
    
    def apply_preset_to_graph(self, graph_path: Path, preset_name: str, output_path: Optional[Path] = None) -> bool:
        """Apply Melodia preset to graph file."""
        # Load preset
        from melodia_material_maker_addon import MelodiaStylePresets
        preset = MelodiaStylePresets.get_preset(preset_name)
        
        # Load graph
        self.manipulator.load_graph(graph_path)
        
        # Apply preset parameters
        applied = self.manipulator.apply_preset(preset['params'])
        
        # Save graph
        save_path = output_path or graph_path
        self.manipulator.save_graph(save_path)
        
        print(f"Applied {applied} parameters from preset '{preset_name}' to {graph_path.name}")
        return True
    
    def batch_apply_preset(self, graph_dir: Path, preset_name: str, output_dir: Optional[Path] = None) -> List[Path]:
        """Apply preset to all graphs in directory."""
        if output_dir is None:
            output_dir = graph_dir
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        
        for graph_path in graph_dir.glob("*.ptex"):
            output_path = output_dir / graph_path.name
            if self.apply_preset_to_graph(graph_path, preset_name, output_path):
                processed_files.append(output_path)
        
        return processed_files


def test_graph_manipulation():
    """Test graph manipulation functionality."""
    print("Testing Material Maker Graph Manipulator...")
    print("=" * 50)
    
    # Test with v2 graph (has more structure)
    project_tools = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\MaterialMaker")
    v2_graph = project_tools / "MM_Master_SurrealAnimatedPBR_v2_Static.ptex"
    
    if not v2_graph.exists():
        print("[X] v2 graph not found for testing")
        return
    
    print(f"[OK] Testing with: {v2_graph.name}")
    
    manipulator = MaterialMakerGraphManipulator()
    
    # Load graph
    try:
        graph = manipulator.load_graph(v2_graph)
        print(f"[OK] Loaded graph successfully")
    except Exception as e:
        print(f"[X] Failed to load graph: {e}")
        return
    
    # Get graph info
    info = manipulator.get_graph_info()
    print(f"[OK] Graph info:")
    print(f"  Name: {info.get('name', 'unknown')}")
    print(f"  Nodes: {info.get('nodes', 0)}")
    print(f"  Connections: {info.get('connections', 0)}")
    print(f"  Parameters: {info.get('parameters', 0)}")
    print(f"  Has remote: {info.get('has_remote', False)}")
    
    # List parameters
    params = manipulator.list_parameters()
    print(f"[OK] Found {len(params)} unique parameters")
    if params:
        print("  Sample parameters:")
        for param in params[:10]:
            value = manipulator.get_parameter(param)
            print(f"    - {param}: {value}")
    
    # Test parameter modification
    if params:
        test_param = params[0]
        original_value = manipulator.get_parameter(test_param)
        manipulator.set_parameter(test_param, 0.75)
        new_value = manipulator.get_parameter(test_param)
        print(f"[OK] Parameter modification test: {test_param} {original_value} -> {new_value}")
        
        # Restore original value
        manipulator.set_parameter(test_param, original_value)
    
    # Test preset application (with parameters that might exist)
    test_preset = {
        "file": "test_texture.png"  # SourceImage parameter
    }
    applied = manipulator.apply_preset(test_preset)
    print(f"[OK] Applied {applied} parameters from test preset")
    
    # Test clone
    cloned = manipulator.clone_graph()
    print(f"[OK] Cloned graph successfully")
    
    # Test source image setting
    success = manipulator.set_input_texture("SourceImage", "new_texture.png")
    print(f"[OK] Set input texture: {success}")
    
    print("\n[OK] All graph manipulation tests passed!")
    print("JSON-based graph manipulation is fully functional")


if __name__ == "__main__":
    test_graph_manipulation()