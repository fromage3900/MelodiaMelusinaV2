# type: ignore
import bpy
import json
import traceback
from pathlib import Path
from .i18n.translations.zh_HANS import PROP_TCTX, PANEL_TCTX, OPS_TCTX
from .server.tools import ToolsPackageBase


class AddonPreferences(bpy.types.AddonPreferences):
    __annotations__ = ToolsPackageBase.get_tool_pref_props()
    bl_idname = __package__.split(".")[0]
    config = {}
    config_cache = {}

    def load_cache(self):
        cache_file = Path(__file__).parent / "config_cache.json"
        if not cache_file.exists():
            return
        try:
            json_data = json.loads(cache_file.read_text(encoding="utf-8"))
            self.config_cache.update(json_data)
            self.update_provider(None)
        except Exception:
            traceback.print_exc()

    def save_cache(self):
        try:
            current_config = self.dump_base_config()
            current_config["model"] = self.model
            old_config = self.config_cache.get(self.provider, {})
            old_config.update(current_config)
            self.config_cache[self.provider] = old_config
            cache_file = Path(__file__).parent / "config_cache.json"
            cache_file.write_text(json.dumps(self.config_cache, indent=4, ensure_ascii=False), encoding="utf-8")
        except Exception:
            traceback.print_exc()

    def refresh_cache(self):
        if not self.provider:
            return
        old_config = self.config_cache.get(self.provider)
        new_config = self.dump_all_config()
        if old_config == new_config:
            return
        self.config_cache[self.provider] = new_config
        self.save_cache()

    def dump_all_config(self):
        client = self.get_client_by_name(self.provider)
        models = client.get().models if client.get() else []
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "models": models,
        }

    def refresh_models_check(self):
        config = self.dump_base_config()
        if config != self.config:
            self.config.update(config)
            self.should_refresh_models = True

    use_history_message: bpy.props.BoolProperty(default=False, name="Use History Message", translation_context=PROP_TCTX)

    def get_tools_items(self, context):
        from .server.tools import ToolsPackageBase

        return ToolsPackageBase.get_enum_items()

    tools: bpy.props.EnumProperty(
        items=get_tools_items,
        name="ToolPackage",
        options={"ENUM_FLAG"},
        default=0b11110,
        translation_context=PROP_TCTX,
    )

    def get_provider_items(self, context):
        from .client import MCPClientBase

        return MCPClientBase.get_enum_items()

    def update_provider(self, context):
        # 从config_cache加载配置
        config = self.config_cache.get(self.provider, {})
        if not config:
            # 从MCP Client中加载
            client = self.get_client_by_name(self.provider)
            config = client.default_config()
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "")
        try:
            self.model = config.get("model", "")
        except Exception:
            pass

    provider: bpy.props.EnumProperty(
        items=get_provider_items,
        name="LLM Provider",
        update=update_provider,
        translation_context=PROP_TCTX,
    )

    api_key: bpy.props.StringProperty(default="", name="API Key", translation_context=PROP_TCTX)

    base_url: bpy.props.StringProperty(
        default="https://api.deepseek.com",
        name="Base URL",
        translation_context=PROP_TCTX,
    )

    def dump_base_config(self):
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url,
        }

    def get_model_items(self, context):
        client = self.get_client_by_name(self.provider)
        models = client.get().models if client.get() else []
        models = [(m, m, "") for m in models]
        if not models:
            models = self.config_cache.get(self.provider, {}).get("models", [])
        return models or [("None", "None", "")]

    model: bpy.props.EnumProperty(items=get_model_items, name="Model", translation_context=PROP_TCTX)

    def search_model(self, context, text):
        client = self.get_client_by_name(self.provider)
        models = client.get().models if client.get() else []
        if not models:
            models = self.config_cache.get(self.provider, {}).get("models", [])
        t = text.lower()
        return [m for m in models if t in m.lower()]

    model: bpy.props.StringProperty(
        default="",
        name="Model",
        search=search_model,
        search_options={"SORT"},
        translation_context=PROP_TCTX,
    )

    should_refresh_models: bpy.props.BoolProperty(default=True, name="Should Refresh Models", translation_context=PROP_TCTX)

    def get_client_by_name(self, name):
        from .client import MCPClientBase

        return MCPClientBase.get_client_by_name(name)

    def draw(self, context):
        layout = self.layout
        layout.column().prop(self, "tools", expand=True)
        box = layout.box()
        self.draw_ex(box)
        self.draw_tools_props(box)

    def draw_ex(self, layout: bpy.types.UILayout):
        row = layout.row(align=True)
        row.label(text="API Settings", text_ctxt=PANEL_TCTX)
        row.alert = self.should_refresh_models
        row.operator(RefreshModels.bl_idname, text="", icon="FILE_REFRESH", text_ctxt=OPS_TCTX)
        row.alert = False
        row.operator(SaveConfig.bl_idname, text="", icon="FILE_TICK", text_ctxt=OPS_TCTX)
        layout.prop(self, "provider")
        provider = self.get_client_by_name(self.provider)
        if not provider:
            return
        provider.draw(layout)

    def draw_tools_props(self, layout: bpy.types.UILayout):
        for t in ToolsPackageBase.get_all_tool_packages():
            t.draw_pref_props(self, layout)


class RefreshModels(bpy.types.Operator):
    bl_idname = "mcp.refresh_models"
    bl_label = "Refresh Models"
    bl_description = "Refresh Models"
    bl_translation_context = OPS_TCTX

    def execute(self, context):
        from .client import MCPClientBase

        pref = get_pref()
        # 先停止所有非当前客户端
        for clientclass in MCPClientBase.get_all_clients():
            cname = clientclass.__name__
            client: MCPClientBase = pref.get_client_by_name(cname)
            if not client:
                continue
            if cname != pref.provider:
                client.stop_client()
                continue
        client = pref.get_client_by_name(pref.provider)
        if not client.get():
            client.try_start_client()
        if not client.get():
            return {"FINISHED"}
        models = client.get().fetch_models(force=True)
        pref.refresh_cache()
        if models:
            pref.should_refresh_models = False
        return {"FINISHED"}


class SaveConfig(bpy.types.Operator):
    bl_idname = "mcp.save_config"
    bl_label = "Save Config"
    bl_description = "Save Config"
    bl_translation_context = OPS_TCTX

    def execute(self, context):
        pref = get_pref()
        pref.save_cache()
        return {"FINISHED"}


def get_pref() -> AddonPreferences:
    return bpy.context.preferences.addons[AddonPreferences.bl_idname].preferences


@bpy.app.handlers.persistent
def init_config(scene):
    pref = get_pref()
    pref.load_cache()


def config_checker():
    pref = get_pref()
    pref.refresh_models_check()
    return 1


clss = [
    RefreshModels,
    SaveConfig,
    AddonPreferences,
]


reg, unreg = bpy.utils.register_classes_factory(clss)


def register():
    reg()
    bpy.app.handlers.load_post.append(init_config)
    bpy.app.timers.register(config_checker, first_interval=1, persistent=True)


def unregister():
    unreg()
    bpy.app.timers.unregister(config_checker)
    bpy.app.handlers.load_post.remove(init_config)
