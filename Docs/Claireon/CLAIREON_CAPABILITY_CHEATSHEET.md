# Claireon Capability Cheat-Sheet

Curated pointers to Claireon MCP tools/patterns that are real, available, and easy to miss —
not a duplicate of the generated catalogs (`Plugins/Claireon/Content/ApplySpecCatalog.json`,
`BPAuthoringPatterns.json`), which are the full reference once you know what to look for.

## Batch edits: `*_apply_spec` / `*_apply_delta`

18 asset families (bp, animbp, material, widgetbp, niagara, pcg, statetree, behaviortree, and
more) have a paired `<family>_apply_spec` / `<family>_apply_delta` tool that authors or patches a
whole graph/asset in one call, instead of one node/property at a time. A prior session burned
roughly 90 round-trips authoring a single event body node-by-node before this was discovered —
check `ApplySpecCatalog.json` for the family you're touching before doing anything repetitive by
hand. Gotchas vary per family (documented per-entry in the catalog) — e.g. `bp_apply_spec` is the
only one that auto-creates the target asset; PCG pin names must match exactly, no fuzzy matching.

## Reaching protected/transient fields: `uobject_set_property` + `component_reregister`

`uobject_inspect` (read) has a write counterpart, `uobject_set_property`, that reaches fields
`EditAnywhere`/Blueprint exposure doesn't cover — protected, transient, or otherwise
non-Blueprint-visible properties — on assets, CDOs, and live PIE instances. After a raw property
write like this, call `component_reregister` to resync any engine-derived state that doesn't
automatically follow a direct property set.

## PIE waiting: `pie_wait_for` / `pie_wait_poll`

`pie_tick` and `pie_sleep` were removed (unfixable: a game-thread tool call can never advance the
world from inside `python_execute`). Use `pie_wait_for(condition, conditionParams, ...)` instead
— it waits for a real condition (map load, PIE ready, actor valid, init state, duration) without
blocking the editor, returning a `wait_id` to poll via `pie_wait_poll` if it doesn't resolve
immediately.

## `pie_set_paused(bool)` — explicit, not a toggle

Prefer this over `console_execute(command='pause')`, which toggles state and can silently leave
PIE paused if called from a stale assumption about current state. `pie_set_paused` reports both
the previous and new state, so a no-op is visible instead of silent.

## Trust but verify

Claireon's own changelog documents real "silent success" bugs that shipped and were later fixed:
dead nodes reported as successfully created, struct property reads silently omitting explicitly-
set defaults, a world-transition Python purge that had never actually executed since inception.
None of these were loud failures — they looked like success until someone checked. This is
exactly why `_AGENT_WORKING_AGREEMENT.md`'s Blueprint verification loop
(`export_graph -> get_graph_fingerprint` before, mutate, `compile_blueprint`,
`assert_graph_matches`, `get_graph_fingerprint` after, then `save_asset`) is mandatory rather than
optional — a tool call reporting success is not the same as the graph actually matching what you
asked for.
