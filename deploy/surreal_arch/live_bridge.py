"""Live Bridge Dashboard ΓÇö unified BlenderΓåöUnreal communication scaffold.

Surfaces all four bridge pathways in one panel under Melodia Studio:
  Port 9876 ΓÇö LiveLink TCP (FBX + textures + animation streaming)
  Port 9317 ΓÇö Blender MCP HTTP (genome/agent control)  
  Port 9316 ΓÇö UE Monolith MCP (Python execution in Unreal)

Wraps the existing livelink_bridge.py, blender_mcp.py, and monolith_mcp_client.py.
"""

from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup

from ..branding import N_PANEL_CATEGORY


# Material bridge cross-integration
def _get_material_crosswalk_status() -> str:
    """Read the material crosswalk file and return a status summary."""
    try:
        from ..material_bridge import load_crosswalk, _crosswalk_path
        cw = load_crosswalk()
        path = _crosswalk_path()
        stem = os.path.basename(path) if os.path.isfile(path) else "no file"
        if cw:
            # Check how many scene materials are mapped
            mapped = sum(1 for m in bpy.data.materials if m.name in cw)
            return f"{mapped}/{len(bpy.data.materials)} materials mapped ({stem})"
        return f"0 mappings ({stem})"
    except Exception:
        return "bridge not loaded"


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Property group ΓÇö bridge state
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class BRIB_SceneSettings(PropertyGroup):
    """Bridge dashboard state persisted on the scene."""

    live_sync_enabled: BoolProperty(
        name="Live Sync",
        default=False,
        description="Continuously sync scene changes to Unreal",
    )
    sync_interval: FloatProperty(
        name="Sync Interval (s)",
        default=2.0, min=0.5, max=60.0,
        description="Seconds between live sync checks",
    )
    last_status_check: StringProperty(
        name="Last Check",
        default="Never",
    )
    expand_livelink: BoolProperty(name="Expand LiveLink", default=True)
    expand_mcp: BoolProperty(name="Expand MCP", default=False)
    expand_actions: BoolProperty(name="Expand Actions", default=True)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Port pinger helper
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def _ping_port(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    """Check if a TCP port is accepting connections."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, "open"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return False, str(e)


def _ping_http(url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """Quick HTTP GET to check an API endpoint."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, json.dumps(data, indent=None)[:100]
    except Exception as e:
        return False, str(e)


def _get_livelink_status() -> dict:
    """Get LiveLink (port 9876) bridge status."""
    try:
        from ..livelink_bridge import is_connected, get_status, ensure_livelink
        available = ensure_livelink()
        connected = is_connected() if available else False
        status_str = get_status() if available else "Not installed"
        return {
            "available": available,
            "connected": connected,
            "status": status_str,
            "port": 9876,
        }
    except Exception:
        return {"available": False, "connected": False, "status": "Bridge module error", "port": 9876}


def _get_blender_mcp_status() -> dict:
    """Check if Blender MCP (port 9317) is running."""
    ok, detail = _ping_port("127.0.0.1", 9317, timeout=1.0)
    if ok:
        ok2, resp = _ping_http("http://127.0.0.1:9317/api/ping", timeout=1.5)
        return {"running": ok2, "detail": resp if ok2 else detail, "port": 9317}
    return {"running": False, "detail": detail, "port": 9317}


def _get_ue_mcp_status() -> dict:
    """Check if UE Monolith MCP (port 9316) is reachable."""
    ok, detail = _ping_port("127.0.0.1", 9316, timeout=1.5)
    return {"running": ok, "detail": detail, "port": 9316}


def _get_bridge_summary() -> dict:
    """Aggregate status for all 3 bridge ports."""
    return {
        "livelink": _get_livelink_status(),
        "blender_mcp": _get_blender_mcp_status(),
        "ue_mcp": _get_ue_mcp_status(),
        "timestamp": datetime.now().isoformat(),
    }


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Operators
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class BRIB_OT_refresh_status(Operator):
    """Ping all bridge ports and refresh status."""

    bl_idname = "brib.refresh_status"
    bl_label = "Refresh Bridge Status"
    bl_options = {"REGISTER"}

    def execute(self, context):
        summary = _get_bridge_summary()
        settings = context.scene.brib_bridge
        settings.last_status_check = datetime.now().strftime("%H:%M:%S")

        # Store in scene for the panel to display
        context.scene["_brib_livelink"] = summary["livelink"]
        context.scene["_brib_blender_mcp"] = summary["blender_mcp"]
        context.scene["_brib_ue_mcp"] = summary["ue_mcp"]

        connected = sum(
            1 for s in [summary["livelink"]["connected"],
                         summary["blender_mcp"]["running"],
                         summary["ue_mcp"]["running"]]
            if s
        )
        self.report({"INFO"}, f"Bridge: {connected}/3 services online")
        return {"FINISHED"}


class BRIB_OT_start_livelink(Operator):
    """Start the LiveLink TCP server on port 9876."""

    bl_idname = "brib.start_livelink"
    bl_label = "Start LiveLink"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from ..livelink_bridge import ensure_livelink, start_server
            ensure_livelink()
            result = start_server()
            if result:
                self.report({"INFO"}, "LiveLink server started on port 9876")
            else:
                self.report({"WARNING"}, "LiveLink start returned False")
        except Exception as e:
            self.report({"ERROR"}, f"LiveLink start failed: {e}")
            return {"CANCELLED"}
        # Refresh status
        bpy.ops.brib.refresh_status()
        return {"FINISHED"}


class BRIB_OT_stop_livelink(Operator):
    """Stop the LiveLink TCP server."""

    bl_idname = "brib.stop_livelink"
    bl_label = "Stop LiveLink"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from ..livelink_bridge import stop_server
            stop_server()
            self.report({"INFO"}, "LiveLink server stopped")
        except Exception as e:
            self.report({"ERROR"}, f"LiveLink stop failed: {e}")
            return {"CANCELLED"}
        bpy.ops.brib.refresh_status()
        return {"FINISHED"}


class BRIB_OT_send_scene(Operator):
    """Send the full Blender scene to Unreal via LiveLink."""

    bl_idname = "brib.send_scene"
    bl_label = "Send Full Scene"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from ..livelink_bridge import ensure_livelink, send_scene_to_unreal, is_connected
            ensure_livelink()
            if not is_connected():
                self.report({"WARNING"}, "LiveLink not connected. Start it first.")
                return {"CANCELLED"}
            send_scene_to_unreal(is_live=False)
            self.report({"INFO"}, "Scene sent to Unreal")
        except Exception as e:
            self.report({"ERROR"}, f"Send failed: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class BRIB_OT_send_selected(Operator):
    """Send selected objects to Unreal via LiveLink."""

    bl_idname = "brib.send_selected"
    bl_label = "Send Selected"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        try:
            from ..livelink_bridge import ensure_livelink, send_selected_to_unreal, is_connected
            ensure_livelink()
            if not is_connected():
                self.report({"WARNING"}, "LiveLink not connected. Start it first.")
                return {"CANCELLED"}
            send_selected_to_unreal()
            self.report({"INFO"}, f"Sent {len(context.selected_objects)} objects to Unreal")
        except Exception as e:
            self.report({"ERROR"}, f"Send failed: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class BRIB_OT_send_outfit(Operator):
    """Send Melusina outfit genome config to Unreal."""

    bl_idname = "brib.send_outfit"
    bl_label = "Send Outfit Config"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from ..livelink_bridge import ensure_livelink, send_melusina_outfit, is_connected
            ensure_livelink()
            if not is_connected():
                self.report({"WARNING"}, "LiveLink not connected. Start it first.")
                return {"CANCELLED"}
            send_melusina_outfit(context)
            self.report({"INFO"}, "Outfit config sent to Unreal")
        except Exception as e:
            self.report({"ERROR"}, f"Send failed: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class BRIB_OT_toggle_live_sync(Operator):
    """Toggle live sync mode ΓÇö continuously streams changes to Unreal."""

    bl_idname = "brib.toggle_live_sync"
    bl_label = "Toggle Live Sync"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = context.scene.brib_bridge
        settings.live_sync_enabled = not settings.live_sync_enabled

        if settings.live_sync_enabled:
            try:
                from ..livelink_bridge import ensure_livelink, start_server
                ensure_livelink()
                start_server()
                self.report({"INFO"}, f"Live sync enabled ({settings.sync_interval}s interval)")
            except Exception as e:
                settings.live_sync_enabled = False
                self.report({"ERROR"}, str(e))
                return {"CANCELLED"}
        else:
            self.report({"INFO"}, "Live sync disabled")
        return {"FINISHED"}


class BRIB_OT_ue_ping(Operator):
    """Quick HTTP ping to UE Monolith MCP on port 9316."""

    bl_idname = "brib.ue_ping"
    bl_label = "Ping UE MCP"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ok, detail = _ping_port("127.0.0.1", 9316, timeout=2.0)
        if ok:
            # Try the /api/status endpoint
            ok2, resp = _ping_http("http://127.0.0.1:9316/api/status", timeout=2.0)
            if ok2:
                self.report({"INFO"}, f"UE MCP online: {resp}")
            else:
                self.report({"WARNING"}, f"UE port 9316 open but API not responding: {detail}")
        else:
            self.report({"WARNING"}, f"UE MCP offline: {detail}")
        bpy.ops.brib.refresh_status()
        return {"FINISHED"}


class BRIB_OT_send_with_materials(Operator):
    """Auto-crosswalk materials, then send scene to Unreal."""

    bl_idname = "brib.send_with_materials"
    bl_label = "Send + Materials"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from ..material_bridge import auto_crosswalk_object, save_crosswalk

        all_map: dict[str, str] = {}
        for o in context.scene.objects:
            if hasattr(o, "material_slots") and o.material_slots:
                m = auto_crosswalk_object(o)
                all_map.update(m)
        if all_map:
            save_crosswalk(all_map)
            self.report({"INFO"}, f"Auto-mapped {len(all_map)} materials")
        else:
            self.report({"INFO"}, "No new material mappings found")

        from ..livelink_bridge import ensure_livelink, send_scene_to_unreal, is_connected
        ensure_livelink()
        if not is_connected():
            self.report({"WARNING"}, "LiveLink not connected. Start it first.")
            return {"CANCELLED"}
        send_scene_to_unreal(is_live=False)
        self.report({"INFO"}, "Scene sent with material crosswalk")
        return {"FINISHED"}


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Panel UI
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class BRIB_PT_bridge_dashboard(Panel):
    """Live Bridge ΓÇö Blender Γåö Unreal communication dashboard."""

    bl_label = "Live Bridge"
    bl_idname = "BRIB_PT_bridge_dashboard"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 15

    def draw(self, context):
        layout = self.layout
        settings = context.scene.brib_bridge

        # ΓöÇΓöÇ Status Bar ΓöÇΓöÇ
        self._draw_status_bar(layout, context)

        # ΓöÇΓöÇ LiveLink Section ΓöÇΓöÇ
        self._draw_livelink_section(layout, context, settings)

        # ΓöÇΓöÇ MCP Section ΓöÇΓöÇ
        self._draw_mcp_section(layout, context, settings)

        # ΓöÇΓöÇ Quick Actions ΓöÇΓöÇ
        self._draw_actions(layout, context, settings)

        # ΓöÇΓöÇ Material Bridge quick link ΓöÇΓöÇ
        layout.separator()
        row = layout.row(align=True)
        row.label(text="Material mapping:", icon="MATERIAL")
        cw = _get_material_crosswalk_status()
        row.label(text=cw, icon="INFO")

        # ΓöÇΓöÇ Timestamp ΓöÇΓöÇ
        if settings.last_status_check and settings.last_status_check != "Never":
            layout.separator()
            layout.label(text=f"Last check: {settings.last_status_check}", icon="TIME")

    # ΓöÇΓöÇ Sub-drawing ΓöÇΓöÇ

    def _draw_status_bar(self, layout, context):
        """Compact status row showing all 3 bridge ports."""
        ll = context.scene.get("_brib_livelink", {})
        bm = context.scene.get("_brib_blender_mcp", {})
        um = context.scene.get("_brib_ue_mcp", {})

        row = layout.row(align=True)
        # LiveLink 9876
        if ll.get("connected"):
            row.label(text="", icon="CHECKBOX_HLT")
            row.label(text="LiveLink")
        else:
            row.label(text="", icon="CHECKBOX_DEHLT")
            row.label(text="LiveLink")

        # Blender MCP 9317
        if bm.get("running"):
            row.label(text="", icon="CHECKBOX_HLT")
            row.label(text="BL MCP")
        else:
            row.label(text="", icon="CHECKBOX_DEHLT")
            row.label(text="BL MCP")

        # UE MCP 9316
        if um.get("running"):
            row.label(text="", icon="CHECKBOX_HLT")
            row.label(text="UE MCP")
        else:
            row.label(text="", icon="CHECKBOX_DEHLT")
            row.label(text="UE MCP")

    def _draw_livelink_section(self, layout, context, settings):
        """LiveLink (port 9876) ΓÇö FBX/texture/animation streaming."""
        ll = context.scene.get("_brib_livelink", {})

        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "expand_livelink", text="",
                 icon="DOWNARROW_HLT" if settings.expand_livelink else "RIGHTARROW",
                 emboss=False)
        row.label(text="LiveLink  :9876", icon="NETWORK_DRIVE")
        if ll.get("connected"):
            row.label(text="CONNECTED", icon="CHECKBOX_HLT")
        else:
            row.label(text="OFFLINE", icon="CHECKBOX_DEHLT")

        if settings.expand_livelink:
            col = box.column(align=True)
            # Start/Stop
            row = col.row(align=True)
            if ll.get("connected"):
                row.operator("brib.stop_livelink", text="Stop Server",
                            icon="PAUSE", depress=True)
            else:
                row.operator("brib.start_livelink", text="Start Server",
                            icon="PLAY")

            # Status text
            status = ll.get("status", "Unknown")
            col.label(text=f"Status: {status}", icon="INFO")

            # Live Sync toggle
            row = col.row(align=True)
            op = row.operator("brib.toggle_live_sync",
                             text="Live Sync ON" if settings.live_sync_enabled else "Live Sync OFF",
                             icon="FILE_REFRESH",
                             depress=settings.live_sync_enabled)
            if settings.live_sync_enabled:
                row.prop(settings, "sync_interval")

    def _draw_mcp_section(self, layout, context, settings):
        """MCP servers ΓÇö Blender (9317) and Unreal (9316)."""
        bm = context.scene.get("_brib_blender_mcp", {})
        um = context.scene.get("_brib_ue_mcp", {})

        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "expand_mcp", text="",
                 icon="DOWNARROW_HLT" if settings.expand_mcp else "RIGHTARROW",
                 emboss=False)
        row.label(text="MCP Servers", icon="TOOL_SETTINGS")

        if settings.expand_mcp:
            col = box.column(align=True)
            # Blender MCP 9317
            sub = col.box()
            sr = sub.row(align=True)
            if bm.get("running"):
                sr.label(text="Blender MCP  :9317", icon="CHECKBOX_HLT")
            else:
                sr.label(text="Blender MCP  :9317", icon="CHECKBOX_DEHLT")
            if bm.get("detail"):
                sub.label(text=f"  {bm['detail'][:80]}", icon="DOT")

            # UE MCP 9316
            sub = col.box()
            sr = sub.row(align=True)
            if um.get("running"):
                sr.label(text="Unreal MCP   :9316", icon="CHECKBOX_HLT")
            else:
                sr.label(text="Unreal MCP   :9316", icon="CHECKBOX_DEHLT")
            if um.get("detail"):
                sub.label(text=f"  {um['detail'][:80]}", icon="DOT")
            sr.operator("brib.ue_ping", text="", icon="FILE_REFRESH")

    def _draw_actions(self, layout, context, settings):
        """Quick-send and utility buttons."""
        ll = context.scene.get("_brib_livelink", {})

        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "expand_actions", text="",
                 icon="DOWNARROW_HLT" if settings.expand_actions else "RIGHTARROW",
                 emboss=False)
        row.label(text="Quick Actions", icon="EXPORT")

        if settings.expand_actions:
            col = box.column(align=True)

            # Send buttons
            row = col.row(align=True)
            row.operator("brib.send_scene", text="Send Scene",
                        icon="SCENE_DATA")
            row.operator("brib.send_selected", text="Send Selected",
                        icon="RESTRICT_SELECT_OFF")

            row = col.row(align=True)
            row.operator("brib.send_outfit", text="Send Outfit",
                        icon="MATCLOTH")

            # Send with materials
            row = col.row(align=True)
            row.operator("brib.send_with_materials", text="Send + Materials",
                        icon="MATERIAL")

            # Refresh status
            row = col.row(align=True)
            row.operator("brib.refresh_status", text="Refresh Status",
                        icon="FILE_REFRESH")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Registration
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

CLASSES = [
    BRIB_SceneSettings,
    BRIB_OT_refresh_status,
    BRIB_OT_start_livelink,
    BRIB_OT_stop_livelink,
    BRIB_OT_send_scene,
    BRIB_OT_send_selected,
    BRIB_OT_send_outfit,
    BRIB_OT_send_with_materials,
    BRIB_OT_toggle_live_sync,
    BRIB_OT_ue_ping,
    BRIB_PT_bridge_dashboard,
]


def register_props():
    bpy.types.Scene.brib_bridge = PointerProperty(type=BRIB_SceneSettings)


def unregister_props():
    try:
        del bpy.types.Scene.brib_bridge
    except AttributeError:
        pass
