"""
Create UE5 Widget Blueprints from Scaffold JSON
Uses UE5 Python API to auto-create widgets when editor is open
Run this script from within UE5 Editor (File > Execute Python Script)
"""

import json
import unreal
from pathlib import Path

# Paths
SCAFFOLD_DIR = unreal.SystemLibrary.get_project_directory() + "Content/Melodia/UI/WidgetScaffolds/"
WIDGET_OUTPUT_DIR = "/Game/Melodia/UI/"
TEXTURE_PATH = "/Game/Melodia/UI/Textures/Generated/"

def load_scaffold(scaffold_name):
    """Load scaffold JSON file"""
    scaffold_path = Path(SCAFFOLD_DIR) / f"{scaffold_name}_scaffold.json"
    
    if not scaffold_path.exists():
        unreal.log_error(f"Scaffold not found: {scaffold_path}")
        return None
    
    with open(scaffold_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_widget_blueprint(widget_name, scaffold):
    """Create a widget blueprint from scaffold"""
    # Create the widget blueprint
    widget_path = f"{WIDGET_OUTPUT_DIR}{widget_name}"
    
    # Check if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(widget_path):
        unreal.log_warning(f"Widget already exists: {widget_path}")
        return None
    
    # Create new widget blueprint
    factory = unreal.WidgetBlueprintFactory()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    try:
        new_widget = asset_tools.create_asset(
            asset_name=widget_name,
            package_path=WIDGET_OUTPUT_DIR,
            asset_class=unreal.WidgetBlueprint,
            factory=factory
        )
        
        unreal.log(f"✓ Created widget: {widget_path}")
        return new_widget
        
    except Exception as e:
        unreal.log_error(f"Failed to create widget {widget_name}: {str(e)}")
        return None

def add_widget_slot(widget_bp, slot_name, slot_type, properties=None):
    """Add a widget slot to the blueprint"""
    # Get the widget tree
    widget_tree = widget_bp.widget_tree
    
    if not widget_tree:
        unreal.log_error("Widget tree not found")
        return None
    
    # Create the widget based on type
    if slot_type == "Border":
        new_widget = widget_tree.construct_widget(unreal.Border)
    elif slot_type == "CanvasPanel":
        new_widget = widget_tree.construct_widget(unreal.CanvasPanel)
    elif slot_type == "SizeBox":
        new_widget = widget_tree.construct_widget(unreal.SizeBox)
    elif slot_type == "TextBlock":
        new_widget = widget_tree.construct_widget(unreal.TextBlock)
    elif slot_type == "Image":
        new_widget = widget_tree.construct_widget(unreal.Image)
    elif slot_type == "Overlay":
        new_widget = widget_tree.construct_widget(unreal.Overlay)
    else:
        new_widget = widget_tree.construct_widget(unreal.CanvasPanel)
    
    # Set the widget name
    new_widget.set_name(slot_name)
    
    # Apply properties if provided
    if properties:
        for prop_name, prop_value in properties.items():
            try:
                # Handle special property types
                if prop_name == "BrushColor" and isinstance(prop_value, str):
                    # Parse color from string like "{GameColors.ParchmentField}"
                    if prop_value.startswith("{GameColors."):
                        color_key = prop_value[13:-1]  # Extract key
                        # Would need to load from design tokens data asset
                        # For now, use default
                        new_widget.set_editor_property("BrushColor", unreal.LinearColor(0.95, 0.9, 0.8, 0.92))
                elif prop_name == "Opacity":
                    new_widget.set_editor_property("Opacity", float(prop_value))
                elif prop_name == "CornerRadius":
                    new_widget.set_editor_property("CornerRadius", float(prop_value))
                elif prop_name == "BorderThickness":
                    new_widget.set_editor_property("BorderThickness", float(prop_value))
                elif prop_name == "WidthOverride":
                    new_widget.set_editor_property("WidthOverride", float(prop_value))
                elif prop_name == "HeightOverride":
                    new_widget.set_editor_property("HeightOverride", float(prop_value))
                else:
                    new_widget.set_editor_property(prop_name, prop_value)
            except Exception as e:
                unreal.log_warning(f"Failed to set property {prop_name}: {str(e)}")
    
    return new_widget

def build_widget_structure(widget_bp, structure_node, parent_widget=None):
    """Recursively build widget structure from scaffold"""
    if not isinstance(structure_node, dict):
        return
    
    node_type = structure_node.get("type", "CanvasPanel")
    node_name = structure_node.get("name", "Unnamed")
    properties = structure_node.get("properties", {})
    optional = structure_node.get("optional", False)
    
    # Skip optional nodes if marked
    if optional and properties.get("Visibility") == "Collapsed":
        return
    
    # Create the widget
    new_widget = add_widget_slot(widget_bp, node_name, node_type, properties)
    
    if not new_widget:
        return
    
    # Add to parent if provided
    if parent_widget:
        try:
            if isinstance(parent_widget, unreal.CanvasPanel):
                slot = parent_widget.add_child_to_canvas(new_widget)
            elif isinstance(parent_widget, unreal.Border):
                slot = parent_widget.add_child_to_border(new_widget)
            elif isinstance(parent_widget, unreal.Overlay):
                slot = parent_widget.add_child_to_overlay(new_widget)
            elif isinstance(parent_widget, unreal.SizeBox):
                slot = parent_widget.add_child_to_size_box(new_widget)
            else:
                slot = parent_widget.add_child(new_widget)
        except Exception as e:
            unreal.log_warning(f"Failed to add {node_name} to parent: {str(e)}")
    
    # Recursively build children
    children = structure_node.get("children", [])
    for child in children:
        build_widget_structure(widget_bp, child, new_widget)

def add_widget_variables(widget_bp, properties):
    """Add variables to the widget blueprint"""
    for prop_name, prop_def in properties.items():
        prop_type = prop_def.get("type", "FText")
        default_value = prop_def.get("default", None)
        
        # Create variable based on type
        if prop_type == "FText":
            widget_bp.add_variable(prop_name, unreal.Text, default_value)
        elif prop_type == "bool":
            widget_bp.add_variable(prop_name, bool, default_value)
        elif prop_type == "float":
            widget_bp.add_variable(prop_name, float, default_value)
        elif prop_type == "FLinearColor":
            widget_bp.add_variable(prop_name, unreal.LinearColor, default_value)
        elif prop_type == "TEnum":
            # For enums, create as string for now
            widget_bp.add_variable(prop_name, str, default_value)
        else:
            widget_bp.add_variable(prop_name, str, default_value)
        
        # Make variable editable and BlueprintReadWrite
        widget_bp.set_variable_property(prop_name, "EditAnywhere", True)
        widget_bp.set_variable_property(prop_name, "BlueprintReadWrite", True)

def create_menu_button():
    """Create WBP_MenuButton from scaffold"""
    scaffold = load_scaffold("WBP_MenuButton")
    if not scaffold:
        return False
    
    widget_bp = create_widget_blueprint("WBP_MenuButton", scaffold)
    if not widget_bp:
        return False
    
    # Build structure
    root = scaffold.get("structure", {}).get("root", {})
    build_widget_structure(widget_bp, root)
    
    # Add variables
    properties = scaffold.get("properties", {})
    add_widget_variables(widget_bp, properties)
    
    # Save the blueprint
    unreal.EditorAssetLibrary.save_loaded_asset(widget_bp)
    unreal.log("✓ WBP_MenuButton created successfully")
    return True

def create_parchment_panel():
    """Create WBP_ParchmentPanel from scaffold"""
    scaffold = load_scaffold("WBP_ParchmentPanel")
    if not scaffold:
        return False
    
    widget_bp = create_widget_blueprint("WBP_ParchmentPanel", scaffold)
    if not widget_bp:
        return False
    
    # Build structure
    root = scaffold.get("structure", {}).get("root", {})
    build_widget_structure(widget_bp, root)
    
    # Add variables
    properties = scaffold.get("properties", {})
    add_widget_variables(widget_bp, properties)
    
    # Save the blueprint
    unreal.EditorAssetLibrary.save_loaded_asset(widget_bp)
    unreal.log("✓ WBP_ParchmentPanel created successfully")
    return True

def create_keybind_badge():
    """Create WBP_KeybindBadge from scaffold"""
    scaffold = load_scaffold("WBP_KeybindBadge")
    if not scaffold:
        return False
    
    widget_bp = create_widget_blueprint("WBP_KeybindBadge", scaffold)
    if not widget_bp:
        return False
    
    # Build structure
    root = scaffold.get("structure", {}).get("root", {})
    build_widget_structure(widget_bp, root)
    
    # Add variables
    properties = scaffold.get("properties", {})
    add_widget_variables(widget_bp, properties)
    
    # Save the blueprint
    unreal.EditorAssetLibrary.save_loaded_asset(widget_bp)
    unreal.log("✓ WBP_KeybindBadge created successfully")
    return True

def create_sparkle_fx():
    """Create WBP_SparkleFX from scaffold"""
    scaffold = load_scaffold("WBP_SparkleFX")
    if not scaffold:
        return False
    
    widget_bp = create_widget_blueprint("WBP_SparkleFX", scaffold)
    if not widget_bp:
        return False
    
    # Build structure
    root = scaffold.get("structure", {}).get("root", {})
    build_widget_structure(widget_bp, root)
    
    # Add variables
    properties = scaffold.get("properties", {})
    add_widget_variables(widget_bp, properties)
    
    # Save the blueprint
    unreal.EditorAssetLibrary.save_loaded_asset(widget_bp)
    unreal.log("✓ WBP_SparkleFX created successfully")
    return True

def create_filigree_border():
    """Create WBP_FiligreeBorder from scaffold"""
    scaffold = load_scaffold("WBP_FiligreeBorder")
    if not scaffold:
        return False
    
    widget_bp = create_widget_blueprint("WBP_FiligreeBorder", scaffold)
    if not widget_bp:
        return False
    
    # Build structure
    root = scaffold.get("structure", {}).get("root", {})
    build_widget_structure(widget_bp, root)
    
    # Add variables
    properties = scaffold.get("properties", {})
    add_widget_variables(widget_bp, properties)
    
    # Save the blueprint
    unreal.EditorAssetLibrary.save_loaded_asset(widget_bp)
    unreal.log("✓ WBP_FiligreeBorder created successfully")
    return True

def create_all_widgets():
    """Create all widgets from scaffolds"""
    unreal.log("=== Creating Melodia UI Widgets from Scaffolds ===\n")
    
    results = {
        "WBP_MenuButton": create_menu_button(),
        "WBP_ParchmentPanel": create_parchment_panel(),
        "WBP_KeybindBadge": create_keybind_badge(),
        "WBP_SparkleFX": create_sparkle_fx(),
        "WBP_FiligreeBorder": create_filigree_border()
    }
    
    # Summary
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    unreal.log(f"\n=== Widget Creation Summary ===")
    unreal.log(f"Created: {success_count}/{total_count} widgets")
    
    for widget_name, success in results.items():
        status = "✓" if success else "✗"
        unreal.log(f"{status} {widget_name}")
    
    return results

def main():
    """Main execution"""
    # Ensure we're in editor mode
    if not unreal.EditorScriptingLibrary.is_editor():
        unreal.log_error("This script must be run from within the UE5 Editor")
        return
    
    # Create output directory if it doesn't exist
    if not unreal.EditorAssetLibrary.does_directory_exist(WIDGET_OUTPUT_DIR):
        unreal.EditorAssetLibrary.make_directory(WIDGET_OUTPUT_DIR)
    
    # Create all widgets
    create_all_widgets()
    
    unreal.log("\n=== Widget Creation Complete ===")
    unreal.log("Next steps:")
    unreal.log("1. Open each widget in the editor")
    unreal.log("2. Assign textures to Image widgets")
    unreal.log("3. Set up animations and event graphs")
    unreal.log("4. Test widgets in PIE")

if __name__ == "__main__":
    main()
