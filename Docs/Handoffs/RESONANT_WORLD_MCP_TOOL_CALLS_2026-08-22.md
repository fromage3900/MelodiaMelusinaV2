# Resonant World MCP Tool Calls — 2026-08-22

The Melodia MCP server exposes the Resonant World authoring/read-model surface
through four read/verify tools. They never write Saved/Audit files, assets, maps,
save data, or editor state.

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

All four tools are declared in:

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
