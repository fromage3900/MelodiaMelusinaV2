import bpy


class ToolsPackageBase:
    "Base class for all tools"

    __tools__: dict[str, "ToolsPackageBase"] = {}
    __exclude_tool_names__: set[str] = {"draw_pref_props", "register", "unregister"}
    __pref_props__: dict = {}

    @classmethod
    def get_all_tool_packages(cls) -> list["ToolsPackageBase"]:
        return cls.__subclasses__()

    @classmethod
    def get_all_tool_packages_names(cls) -> list[str]:
        return [t.__name__ for t in cls.get_all_tool_packages()]

    @classmethod
    def get_package(cls, name: str) -> "ToolsPackageBase":
        if name not in cls.__tools__:
            for t in cls.get_all_tool_packages():
                cls.__tools__[t.__name__] = t
        return cls.__tools__.get(name)

    @classmethod
    def get_enum_items(cls):
        return [(t.__name__, t.__name__, t.__doc__.strip() or "", 1 << i) for i, t in enumerate(cls.get_all_tool_packages())]

    @classmethod
    def get_tool_pref_props(cls):
        props = {}
        for t in cls.get_all_tool_packages():
            props.update(t.__pref_props__)
        return props

    @classmethod
    def draw_pref_props(cls, pref, layout: bpy.types.UILayout):
        pass

    @classmethod
    def get_pref(cls):
        from ...preference import get_pref
        return get_pref()

    @classmethod
    def get_all_tools(cls):
        tools = []
        for pname in cls.__dict__:
            if pname.startswith("__"):
                continue
            if pname in cls.__exclude_tool_names__:
                continue
            p = getattr(cls, pname)
            if not callable(p):
                continue
            # 只添加函数
            tools.append(p)
        return tools

    @classmethod
    def register(cls):
        for t in cls.get_all_tool_packages():
            try:
                t.register()
            except Exception as e:
                print(e)

    @classmethod
    def unregister(cls):
        for t in cls.get_all_tool_packages():
            try:
                t.unregister()
            except Exception as e:
                print(e)