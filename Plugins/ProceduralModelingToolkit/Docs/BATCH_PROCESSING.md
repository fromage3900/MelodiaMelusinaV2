# Batch Processing

Phase 7 adds a reusable batch processor for applying any modifier stack to Static Mesh assets.

## Entry Points

`UProceduralModelingToolkitBatchProcessor` exposes:

- `ProcessSelectedAssets`
- `ProcessFolders`
- `ProcessCollections`
- `ProcessBatch`

## Sources

The batch settings struct can gather meshes from:

- explicit `StaticMeshAssets`
- Content Browser selected Static Mesh assets
- entire content folders
- named project collections

`NameContains` provides a simple asset-name filter for folder and collection workflows.

## Processing

Each asset is passed to `FProceduralModelingToolkitDynamicMeshPipeline::ProcessStaticMesh` with the supplied modifier stack.

The pipeline still preserves the original source mesh by duplicating it into the project-generated output folder before conversion.

## Progress And Cancellation

Batch runs use `FScopedSlowTask`.

If `bAllowCancel` is enabled, the editor shows a cancelable progress dialog and the result records `bCancelled`.

## Result Data

Batch results include:

- total asset count
- processed asset count
- success count
- failure count
- cancellation state
- per-asset source path
- per-asset output path
- per-asset message

## Limitations

The processor is editor-only and synchronous. Long-running remesh or simplify stacks should be used with cancellation enabled until a future async job layer is added.
