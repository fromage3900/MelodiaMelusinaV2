# Resonant World MCP Tool Calls — 2026-08-22

The Melodia MCP server exposes the Resonant World authoring/read-model surface
through eight read/verify tools. They never write Saved/Audit files, assets, maps,
save data, or editor state. The chronicle tool projects long-lived world memory
but leaves canonical save ownership with `UMelodiaNarrativeSubsystem`.

## Tools

### `melodia_resonant_world_get_atlas`

Returns the project-wide family inventory and authored movement IDs.

```json
{"name":"melodia_resonant_world_get_atlas","arguments":{}}
```

### `melodia_resonant_world_compile_passage`

Compiles an in-memory passage. Use `movement_id: "all"` for the six-movement
portfolio.

```json
{"name":"melodia_resonant_world_compile_passage","arguments":{"seed":3900,"movement_id":"petal_cantata","archetype_id":"SakuraDreamer"}}
{"name":"melodia_resonant_world_compile_passage","arguments":{"seed":3900,"movement_id":"all"}}
```

### `melodia_resonant_world_get_constellation`

Resolves existing project assets into one deterministic chunk read model and
includes role coverage, quantum selection provenance, Echo/PIE handoff gates,
and runtime boundaries.

```json
{"name":"melodia_resonant_world_get_constellation","arguments":{"seed":3900,"movement_id":"petal_cantata","chunk_x":0,"chunk_y":0,"archetype_id":"SakuraDreamer"}}
```

### `melodia_resonant_world_get_score`

Composes the replayable 16-beat phrase, route seam, four stage transitions, and
asset voicing without applying traversal or gameplay state.

```json
{"name":"melodia_resonant_world_get_score","arguments":{"seed":3900,"movement_id":"petal_cantata","chunk_x":0,"chunk_y":0,"archetype_id":"SakuraDreamer"}}
```

### `melodia_resonant_world_project_chronicle`

Projects append-only discoveries, movement attunements, completed scores, style
voicings, and sparse voxel edits. Event IDs and the chronicle ID are replayable;
same-cell edits use last-write-wins. This is a read model only.

```json
{"name":"melodia_resonant_world_project_chronicle","arguments":{"seed":3900,"movement_id":"petal_cantata","events":[{"sequence":0,"event_type":"discovery","chunk":[0,0],"payload":{"movement_id":"star_loom"}}]}}
```

### `melodia_resonant_world_get_capture_manifest`

Returns the isolated `/Game/_PROJECT/Levels/RenderTests/` lookdev contract,
absolute source references, intended camera/material state, and evidence gates.
It does not render or publish; clean PNG promotion remains lookdev-owned.

```json
{"name":"melodia_resonant_world_get_capture_manifest","arguments":{"seed":3900,"movement_id":"all","chunk_x":0,"chunk_y":0}}
```

### `melodia_resonant_world_get_handoff`

Returns the proof envelope and handoff document paths. `target` accepts `all`,
`ui`, `gameplay`, `quantum`, or `tool_calls`.

```json
{"name":"melodia_resonant_world_get_handoff","arguments":{"target":"all"}}
```

### `melodia_resonant_world_validate`

Runs read-only validation over the asset atlas, in-memory six-passage portfolio,
saved PCG plan, and saved proof handoff.

```json
{"name":"melodia_resonant_world_validate","arguments":{}}
```

## Policy

All eight tools are declared in:

- `specs/mcp/melodia_mcp_tools.v1.json`
- `specs/mcp_tool_policy.v1.json`

They require no approval and declare `mutates: false`. The compiler tool is also
authorized for `verify`, because its result is an in-memory validation/read model.

## CLI calls that produced the current artifacts

These authoring commands remain the reproducible source of the saved handoffs:

```powershell
python Content/Python/resonant_world_asset_atlas.py --output Saved/Audit/resonant_world_asset_atlas.json
python Content/Python/resonant_world_phrase_bridge.py --midi Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid --seed 3900 --output Saved/Audit/resonant_world_phrase_128bpm.json
python Content/Python/resonant_world_magic_passage.py --seed 3900 --all-movements --atlas Saved/Audit/resonant_world_asset_atlas.json --phrase Saved/Audit/resonant_world_phrase_128bpm.json --output Saved/Audit/resonant_magic_passage_portfolio_3900.json
python Content/Python/resonant_world_pcg_adapter.py --seed 3900 --radius 1 --atlas Saved/Audit/resonant_world_asset_atlas.json --phrase Saved/Audit/resonant_world_phrase_128bpm.json --wardrobe Saved/Audit/resonant_wardrobe_voicing_sakura_3900.json --magic-passage Saved/Audit/resonant_magic_passage_petal_3900.json --output Saved/Audit/resonant_world_pcg_plan_3900.json
python Content/Python/resonant_world_proof_handoff.py --plan Saved/Audit/resonant_world_pcg_plan_3900.json --output Saved/Audit/resonant_world_proof_handoff_3900.json
```

The final two steps are pure validation/flattening. Editor application remains a
separate single-editor operation and is currently reported as `performed: false`.
