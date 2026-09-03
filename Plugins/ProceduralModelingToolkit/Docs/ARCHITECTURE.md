# Procedural Modeling Toolkit Architecture

The Procedural Modeling Toolkit is an editor-only plugin framework for long-term procedural modeling work in this project.

This first implementation deliberately contains no Geometry Script generation logic. It establishes the plugin boundary, editor module, toolbar entry, dockable tab, logging category, and content/script/documentation folders.

## Modules

- `ProceduralModelingToolkitEditor`: editor module that owns startup, shutdown, ToolMenus registration, and the dockable toolkit tab.

Future approved modules may include:

- `ProceduralModelingToolkitRuntime`: shared data types and runtime-safe preset definitions.
- `ProceduralModelingToolkitGeometry`: Geometry Script-backed mesh generation services.
- `ProceduralModelingToolkitPCG`: PCG graph templates, PCG utilities, and custom PCG settings.
- `ProceduralModelingToolkitPython`: Python bridge helpers for batch generation and audits.

## Current UI

- Toolbar button: `Procedural Toolkit`
- Window menu entry: `Window > Procedural Modeling Toolkit`
- Dockable tab: `Procedural Modeling Toolkit`
- Dynamic Mesh round-trip action: `Process Selected Static Meshes`

## Logging

The editor module defines `LogProceduralModelingToolkit`.

Use this category for framework lifecycle events, validation, generation status, and future tool diagnostics.

## Folder Policy

- `Content/Editor`: Editor Utility Widgets and plugin editor-only UI assets.
- `Content/PCG`: PCG graph templates and subgraphs owned by the toolkit.
- `Content/Presets`: future data assets for procedural recipes.
- `Content/Materials`: preview materials used by toolkit-generated assets.
- `Scripts/Python`: batch automation that calls stable plugin APIs.
- `Docs`: architecture, tool authoring, and maintenance notes.

Project-specific generated outputs should remain outside the plugin, under `/Game/EnvSandbox/Procedural/`, unless a future phase explicitly promotes them to reusable plugin content.

## Mesh Processing Pipeline

See `DYNAMIC_MESH_PIPELINE.md`.

The first pipeline duplicates selected Static Mesh assets, converts the source mesh into a transient Dynamic Mesh, writes that Dynamic Mesh back into the duplicate, saves the duplicate, and validates the result. This provides the stable insertion point for future modifiers without touching original assets.

## Modifier Framework

See `MODIFIER_FRAMEWORK.md`.

The modifier framework defines an abstract modifier base class, generic parameter storage, enable/disable state, stack ordering, reordering, stack execution, and serialization hooks. Concrete modifiers are intentionally deferred to later phases.

## Phase 4 Modifiers

See `PHASE4_MODIFIERS.md`.

The first concrete modifiers are now available as independent stack items: Translate, Rotate, Scale, Mirror, Noise, Smooth, and Recompute Normals.

## Phase 5 Modifiers

See `PHASE5_MODIFIERS.md`.

The advanced modeling modifiers are available as independent stack items: Extrude, Inset, Remesh, Simplify, Twist, Bend, and Inflate.

## Presets

See `PRESETS.md`.

Modifier stacks can be saved, loaded, duplicated, and deleted as versioned JSON documents. Presets store ordered modifier class paths, enabled state, display metadata, and generic parameter values for future compatibility.

## Batch Processing

See `BATCH_PROCESSING.md`.

The batch processor applies any modifier stack to selected assets, explicit asset lists, folders, or project collections with progress reporting and cancellation.

## Ornament And Filigree Generators

See `ORNAMENT_GENERATORS.md`.

The ornament generators produce deterministic spline path data for spirals, curves, symmetrical curls, vines, leaves, branching, floral motifs, symmetry modes, thickness, and bevel metadata.

## PCG Integration

See `PCG_INTEGRATION.md`.

Custom PCG nodes invoke the toolkit for ornament generation, mesh modification, spline processing, transient Dynamic Mesh generation, and Static Mesh output while preserving graph pass-through behavior for the first integration pass.

## Kitbash Generator

See `KITBASH_GENERATOR.md`.

The kitbash generator produces rule-based placement data from sockets, metadata, architectural styles, weighted selection, rotation rules, and scale variation.

## Surface Effects

See `SURFACE_EFFECTS.md`.

Surface effects are reusable modifier-stack items for cracks, damage, edge wear, dirt, moss, rust, snow, and generic vertex painting.
