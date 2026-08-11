# Ornament And Filigree Generators

Phases 8 and 9 add deterministic spline-data generators for procedural ornament work.

## Phase 8 Ornament Generator

`UProceduralModelingToolkitOrnamentGenerator::GenerateOrnament` supports:

- spirals
- curves
- symmetrical curls
- vine structures

The Phase 8 generator does not create leaves. It focuses on stable point generation for reusable spline paths.

## Phase 9 Filigree Generator

`GenerateFiligree` expands the same spline path model with:

- leaves
- branching
- floral motifs
- symmetry modes
- seed randomization
- thickness controls
- bevel controls

## Data Model

`FProceduralModelingToolkitSplinePath` stores:

- path name
- ordered points
- closed/open state
- thickness
- bevel

These paths are intentionally asset-neutral so later phases can route them into Editor Utility Widgets, PCG nodes, spline components, Dynamic Mesh generation, or static mesh baking.

## Symmetry

Supported modes:

- none
- mirror X
- mirror Y
- radial

## Tests

`ProceduralModelingToolkit.Ornaments.GenerateStableSplines` validates that ornament and filigree generation produce non-empty spline paths with stable point counts, and that filigree creates closed leaf or floral shapes.
