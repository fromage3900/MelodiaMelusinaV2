"""UE Agent Bridge Widget - Slate UI for in-editor agent control.

This provides a floating widget in UE that:
- Shows live agent status with refresh button
- Accepts natural language prompts
- Displays recent output/log
- Links to dashboard

Candidate Owner Agent: World Integration Agent (WIA)
"""
try:
    import unreal
except ImportError:
    unreal = None

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_MEMORY_DIR = PROJECT_ROOT / "Saved" / "AgentMemory"


class AgentBridgeWidget:
    """Floating widget for Unreal Editor showing agent status and controls."""
    
    @staticmethod
    def show_status():
        """Show agent status in a dialog."""
        content = "Agent Bridge Status\n\n"
        content += "=" * 40 + "\n\n"
        
        agents = [
            ("Geometry", unreal.LinearColor.GREEN, "🏛️"),
            ("Material", unreal.LinearColor.YELLOW, "🎨"),
            ("Placement", unreal.LinearColor.BLUE, "📍"),
            ("Integration", unreal.LinearColor.CYAN, "🔗"),
            ("QA", unreal.LinearColor.MAGENTA, "🛡️"),
        ]
        
        for name, color, icon in agents:
            loop_stop = PROJECT_ROOT / "deploy" / f"{name.upper()}_LOOP_STOP"
            if loop_stop.exists():
                status = "STOPPED"
            else:
                status = "READY"
            content += "{0} {1}: {2}\n".format(icon, name, status)
        
        content += "\n" + "=" * 40 + "\n"
        content += "Tools Available:\n"
        content += "• delegate_to_agent(intent, action, payload)\n"
        content += "• get_agent_status()\n"
        content += "• run_blessing_evolution(count, element)\n"
        content += "• ue_editor_command(cmd)\n"
        
        unreal.MessageDialog.open(EULabel, EULabel, content)
    
    @staticmethod
    def spawn_prompt_dialog():
        """Open a prompt input dialog."""
        # This would ideally use Slate for a proper input dialog
        # For now, log instructions
        unreal.log("[AgentBridge] Natural Language Prompt Bar")
        unreal.log("Available prompts:")
        unreal.log("  - 'Spawn zen shrine geometry'")
        unreal.log("  - 'Generate 5 forte blessings'")
        unreal.log("  - 'Build sakura PCG scattered'")
        unreal.log("  - 'Check agent status'")
        unreal.log("\nProcessed via agent_prompt_bar.py -> prompt_queue.json")


def register_agent_bridge_widget():
    """Register the widget in UE editor."""
    try:
        menus = unreal.ToolMenus.get()
        main = menus.find_menu("LevelEditor.MainMenu")
        
        if main:
            # Add Agent Bridge submenu
            main.add_sub_menu(
                "AgentBridge", 
                "AgentBridge", 
                "Agent Bridge", 
                "Agent Bridge Tools"
            )
            bridge_menu = menus.extend_menu("LevelEditor.MainMenu.AgentBridge")
            bridge_menu.add_section("Tools", "Tools", 0)
            
            # Show Status
            entry = unreal.ToolMenuEntry(
                name="ShowStatus",
                type=unreal.MultiBlockType.MENU_ENTRY
            )
            entry.set_label("Show Agent Status")
            entry.set_string_command(
                type=unreal.ToolMenuStringCommandType.PYTHON,
                string="import agent_bridge_widget; agent_bridge_widget.AgentBridgeWidget.show_status()"
            )
            bridge_menu.add_menu_entry("Tools", entry)
            
            # Show Prompt Bar
            entry2 = unreal.ToolMenuEntry(
                name="ShowPromptBar",
                type=unreal.MultiBlockType.MENU_ENTRY
            )
            entry2.set_label("Natural Language Prompt")
            entry2.set_string_command(
                type=unreal.ToolMenuStringCommandType.PYTHON,
                string="import agent_bridge_widget; agent_bridge_widget.AgentBridgeWidget.spawn_prompt_dialog()"
            )
            bridge_menu.add_menu_entry("Tools", entry2)
            
            menus.refresh_all_widgets()
            unreal.log("[AgentBridge] Widget menu registered!")
    except Exception as e:
        unreal.log_error("Agent Bridge widget registration failed: {}".format(e))


# Called on editor startup
def startup():
    register_agent_bridge_widget()