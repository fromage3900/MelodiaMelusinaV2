# NPC Definition Import Proposal

Status: design only; no importer is implemented by this change.

## Contract

Validated source drafts live at `Imports/Data/NPCs/*.json`. Each file maps one stable `npc_id` to `FMelodiaNPCDef`: display name, role, optional static/skeletal mesh soft paths, dialogue keys, and optional behavior tag/tree. Dialogue keys must match approved filenames in `Imports/Data/Dialogue` without the extension.

The editor-only importer should create or update one `UMelodiaNPCDefinitionAsset` Primary Data Asset per JSON file under `/Game/Melodia/Gameplay/NPC/Definitions`. It must never create runtime code or a second catalog authority.

## Validation gate

Before import, the existing content validator must scan the NPC JSON and rewrite `Imports/Data/VALIDATION.md`. Import is allowed only when that report records the file as passed. Reject duplicate `npc_id` values, missing IDs, absent visual soft references, unknown role values, missing dialogue keys, malformed object paths, and paths outside `/Game`.

## Idempotency and audit

Asset names derive from `npc_id`, so rerunning the importer updates the same asset. The importer should use a transaction, avoid saving unchanged packages, and write `Saved/Audit/npc_import.json` with source hash, destination asset, validation verdict, and changed/unchanged status. Deleting a JSON draft must not automatically delete a cooked asset.

## Runtime boundary

Packaged gameplay reads only cooked `UMelodiaNPCDefinitionAsset` assets through MelodiaCore and the Asset Manager. JSON, Python, Monolith, and editor-only validation are never runtime dependencies. A future importer should also verify that `PrimaryAssetTypesToScan` includes `MelodiaNPC` before claiming packaged readiness.