# specs/npcs — NPC scaffold specs

Specs in this directory drive `Content/Python/scaffold_npc.py`, which creates (or
updates) the standard NPC pair for a character:

    /Game/Melodia/Gameplay/NPC/Blueprints/BP_<AssetName>_NPC   (parent: AMelodiaNPCBase)
    /Game/Melodia/Gameplay/NPC/Definitions/DA_<AssetName>     (MelodiaNPCDefinitionAsset)

The Blueprint gets one `MelodiaNPCInteractionComponent` (variable name `Interaction`)
with `npc_id` / `speaker_name` defaults set on its template, and its CDO
`npc_definition` is pointed at the definition asset. The tool is idempotent:
re-running a spec updates the existing pair instead of duplicating components.

## Run it (editor must be open; Monolith on 9316)

    # in-editor:
    editor_query run_python:
      __file__ = r'C:/EnvironmentPortfolio/BS_GodFile/Content/Python/scaffold_npc.py'
      exec(open(__file__, encoding='utf-8').read())

    # single spec override:
    MELODIA_NPC_SPEC=specs/npcs/ellettra_vell.v1.json

Reports land in `Saved/Audit/npc_scaffold/<npc_id>.json`.

## Spec schema — `melodia.npc_scaffold.v1`

    {
      "schema": "melodia.npc_scaffold.v1",
      "npc_id": "ellettra_vell",              // required, no spaces (FName)
      "asset_name": "EllettraVell",           // optional; derived from npc_id if absent
      "display_name": "Ellettra Vell",        // FText on the definition
      "role": "Ambient",                      // EMelodiaNPCRole: Ambient|Companion|... (see MelodiaNPCData.h)
      "skeletal_mesh": "/Game/.../SK_X.SK_X", // optional; loaded, then stored as TSoftObjectPtr
      "static_mesh": null,                    // optional
      "dialogue_keys": [],                    // optional; Quill ids stay authored in QuillScript
      "behavior_tag": null,                   // optional FGameplayTag-style tag
      "notes": "free text"
    }

## Ownership rules this tool respects

- `AMelodiaNPCBase` is the actor contract; `UMelodiaNPCInteractionComponent` is the
  talk surface; QuillScript owns dialogue content. This tool never authors dialogue,
  quests, or a second interaction authority.
- Only these two assets are created. No level actors are placed; that stays a
  deliberate lookdev step.

## Known editor-API pitfalls (2026-09-20, UE 5.8)

- `TSoftObjectPtr` setters reject `unreal.SoftObjectPath` — load the object and pass it.
- `SubobjectData` hides its fields from Python (`to_dict()` is empty); the component's
  identity/paths come from `export_text()`.
- `delete_subobject(context_handle, subobject_to_delete, bp_context)` needs the context
  handle first; `rename_subobject(handle, new_name)` takes `Text`.
- Compile before any CDO write; compile wipes CDO overrides.

## VRM intake — `Content/Python/npc_vrm_intake.py` (added 2026-09-20)

The front door for staged VRM characters. It reads
`Content/Python/gmm/npc/vrm_registry.json`, resolves the `.vrm` on disk, imports it
through VRM4U, finds the SkeletalMesh, writes/refreshes this directory's spec, then
hands the spec to `scaffold_npc.py` — one source at a time:

    registry -> resolve .vrm -> VRM4U import to /Game/NPCs/Imported/{archetype}/{source_id}
             -> find the SkeletalMesh -> write specs/npcs/<npc_id>.v1.json
             -> scaffold_npc(spec)  -> Saved/Audit/npc_vrm_intake.json

    # dry run: registry + files + spec construction, no editor, never imports unreal
    python Content/Python/npc_vrm_intake.py --source-id SD_02_PetalPriestess --dry-run
    python Content/Python/npc_vrm_intake.py --list
    python Content/Python/npc_vrm_intake.py --all --dry-run        # every staged source

    # live (one editor open; Monolith :9316 or the editor console)
    import sys; sys.path.insert(0, r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python")
    import npc_vrm_intake; npc_vrm_intake.run(source_id="SD_02_PetalPriestess")

Rules this tool follows:

- `npc_id` is snake_case with no spaces: the registry's `npc_id` wins, otherwise it is
  derived from `source_id` (`SD_02_PetalPriestess` -> `sd_02_petal_priestess`).
  `asset_name` keeps the source_id's own tokens — acronym and CamelCase preserved —
  so the BP stays traceable to its source (`SD_02_PetalPriestess` ->
  `SD02PetalPriestess`; the scaffolder's own fallback would collapse it to
  `Sd02Petalpriestess`).
- Spec file: `specs/npcs/<npc_id>.v1.json`. Re-runs refresh it in place; the audit
  records the previous sha256 so a changed spec is visible.
- Destination is always `/Game/NPCs/Imported/{archetype}/{source_id}`. A re-run skips
  the import when a SkeletalMesh is already there (`--force-import` overrides).
- The scaffolder is invoked by exec'ing `scaffold_npc.py` into a fresh namespace with
  `MELODIA_NPC_SCAFFOLD_AUTORUN=0` set first and `__file__` present — otherwise its
  last line runs `main()` over every spec in this directory. The dry run proves that
  namespace contract (with a stub `unreal`) without running `main()`.
- Attribution is load-bearing: the three staged VRMs are VRoid Hub downloads whose
  terms require credit and disallow redistribution. The registry carries the credit
  line; the generated spec's `notes` repeats it, and the audit flags any source whose
  creator is still unidentified (`MD_01_TwilightDancer` at the time of writing).
- Audit: `Saved/Audit/npc_vrm_intake.json`, merged per `source_id` (last run wins per
  source), `mode` recorded per entry, plus an `editor_only_gaps` list of what only the
  editor can prove. Exit code: `0` = ok/deferred, `1` = failed or needs attention.

**UNVERIFIED — the VRM4U import call itself.** This tool was authored in a file-only
lane with no editor access, so it discovers the VRM4U Python surface at runtime
(scanning `dir(unreal)` for `vrm` symbols and probing factory/import candidates) instead
of hardcoding a class name. `gmm/npc/vrm4u_import.py` is a reference, not truth. Every
run records `"adapter_verified": false` and the exact exceptions of the candidates it
tried until the parallel editor lane reports which one works.

**Registry ownership:** `gmm/npc/vrm_source.py` keeps a parallel hardcoded copy of these
sources and its `export_registry()` rewrites `vrm_registry.json` *without* the
`on_disk` / `sha256` / `attribution` / `verification` fields. Treat the JSON as the
intake authority; re-apply the provenance fields if that exporter is ever run.
