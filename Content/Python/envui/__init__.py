"""Environment UI (EnvUI) scaffolding.

This package provides:
  - a command registry (`envui.commands`)
  - stable output paths (`envui.paths`)
  - menu wiring for Unreal ToolMenus (`envui.menu`)

Keep this layer editor-safe and additive: it should never mutate content by
import side-effects. Menu actions call explicit commands.
"""

