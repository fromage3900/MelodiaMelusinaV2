# Kitbash Generator

Phase 11 adds a procedural kitbash placement system for surreal architecture workflows.

## Features

- socket matching
- part metadata
- rule-based placement
- rotation rules
- weighted selection
- scale variation
- architectural style filtering

## Data Model

`FProceduralModelingToolkitKitbashPart` stores:

- part id
- optional Static Mesh reference
- metadata
- sockets

`FProceduralModelingToolkitKitbashSocket` stores:

- socket name
- socket type
- compatible socket types
- local transform

`FProceduralModelingToolkitKitbashRule` controls:

- source socket type
- target socket type
- required architectural style
- required tags
- rotation rule
- fixed rotation
- scale range
- max placements

## Output

`GenerateKitbash` returns ordered placements. Each placement includes:

- selected part id
- mesh reference
- world transform
- source socket
- target socket
- copied metadata

The system currently produces placement data and does not spawn actors or bake meshes. That keeps it reusable by Editor Utility Widgets, batch tools, and PCG.

## Tests

`ProceduralModelingToolkit.Kitbash.GeneratePlacements` validates socket compatibility, rule filtering, weighted candidate placement, and max placement limits.
