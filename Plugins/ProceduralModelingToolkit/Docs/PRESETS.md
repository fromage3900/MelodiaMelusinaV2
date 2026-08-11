# Presets

Phase 6 adds versioned JSON preset serialization for modifier stacks.

## Storage

By default, relative preset paths resolve under:

`Saved/ProceduralModelingToolkit/Presets`

Absolute paths are also supported. Missing extensions are written as `.json`.

## JSON Contents

Each preset stores:

- preset document version
- toolkit version string
- preset name
- ordered modifier list
- modifier class path
- enabled state
- modifier ID
- display name
- generic parameter struct

The modifier class path allows new modifier classes to be restored without hard-coded switch statements.

## Supported Operations

`UProceduralModelingToolkitPresetLibrary` exposes:

- `SavePreset`
- `LoadPreset`
- `DuplicatePreset`
- `DeletePreset`
- `GetDefaultPresetDirectory`

## Versioning

Preset documents currently use `Version = 1`. Loading rejects non-positive versions. Future migrations should happen inside `DocumentToStack` before modifier objects are created.

## Tests

`ProceduralModelingToolkit.Presets.RoundTrip` saves a stack, loads it, verifies modifier state, duplicates the preset, and deletes both files.
