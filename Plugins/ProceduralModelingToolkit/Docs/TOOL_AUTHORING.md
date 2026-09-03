# Procedural Tool Authoring Guide

This plugin currently provides framework only.

Do not add Geometry Script mesh generation, PCG graph mutation, or asset baking logic without a reviewed design for that tool.

## Approved Extension Pattern

1. Add durable editor services in C++.
2. Expose stable commands to Blueprint or Python only after the C++ API is clear.
3. Keep artist controls in Editor Utility Widgets or lightweight Slate panels.
4. Keep batch processing in Python scripts that call plugin APIs.
5. Write generated assets to project content paths, not plugin source folders.

## Initial Stability Rules

- Keep the editor module loadable without requiring a level.
- Register menus through `UToolMenus`.
- Register dockable panels through `FGlobalTabmanager`.
- Log lifecycle events through `LogProceduralModelingToolkit`.
- Avoid direct Geometry Script dependencies until the geometry module is introduced.
