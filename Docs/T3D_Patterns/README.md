# T3D Pattern Library

Parameterised T3D snippets for the wiring shapes this project keeps rebuilding by hand, plus a CLI
that drives Monolith's `inject_nodes_t3d`. One call lands a whole cluster; a bad payload lands
nothing.

**Every pattern here was injected into a live Blueprint, checked for link formation, and compiled
clean before being committed.** They are not sketches.

## Patterns

| Pattern | Nodes | Params | Shape |
|---|---:|---|---|
| `subsystem_call` | 2 | `subsystem_class`, `function` | `GetSubsystem → CallFunction` — the `UseSkillWithRhythm` fix shape |
| `delay_then_call` | 2 | `target_class`, `function`, `duration` | `Delay → CallFunction` — the `BP_KaleidoNaveArrivalTrigger` shape |
| `guarded_call` | 3 | `target_class`, `function` | `IsValid → Branch → CallFunction` — defensive access |
| `sequence_fanout` | 3 | `target_class`, `function_a`, `function_b` | `Sequence → two calls` — the `PlayerWon`/`EnemyWon` shape |
| `probe_print` | 1 | `message`, `duration` | Standalone `PrintString` probe for temporary instrumentation |

`probe_print` reports `linked_pins=0` by design — it is a single node you splice into an existing
exec chain, not a self-contained cluster.

## Usage

```bash
python Docs/T3D_Patterns/t3d.py list
```

Dry run (never mutates):

```bash
python Docs/T3D_Patterns/t3d.py check subsystem_call --asset /Game/Path/BP_Thing --set subsystem_class=/Script/BS_GodFile.MelodiaRhythmCombatSubsystem --set function=ClearPendingDamageMultiplier
```

Apply (prints before/after fingerprint; omit `--go` and it stays a dry run):

```bash
python Docs/T3D_Patterns/t3d.py inject guarded_call --asset /Game/Path/BP_Thing --graph EventGraph --set target_class=/Script/Engine.KismetSystemLibrary --set function=PrintString --go
```

> **Git Bash mangles `/Game/...` and `/Script/...` into Windows paths.** Export
> `MSYS_NO_PATHCONV=1` first, or run from PowerShell. The symptom is
> `Blueprint not found: C:/Program Files/Git/Game/...`.

## Writing a new pattern

1. Wire the shape once by hand in the editor. Select it, `Ctrl+C`, paste into `patterns/<name>.t3d`.
   That clipboard text *is* T3D. (`export_graph` emits JSON — for reading and asserting, not for
   injecting.)
2. Replace every `NodeGuid=` and every pin `PinId=` with `{{GUID:somename}}`. **One distinct name
   mints one guid per call**, so a name reused across a node's `NodeGuid` and another node's
   `LinkedTo=(...)` is exactly what makes the link survive the import. This is the single easiest
   thing to get wrong.
3. Replace class paths, function names and pin defaults with `{{token}}`; the CLI discovers them
   automatically and requires a `--set` for each.
4. Prove it: inject into a throwaway Blueprint and check `linked_pins` is non-zero on every node that
   should be connected, and `compiled_clean=true`. **`valid: true` is not proof** — pre-flight
   checks class and function resolution, not pin names. A typo'd pin name validates fine and silently
   produces an unlinked node.

## Two things that will bite

**Not idempotent.** Injection forces unique `NodeGuid`s (colliding guids break
`get_graph_fingerprint` and the editor's own diffing), so running the same pattern twice gives you
two working copies of the cluster. Delete first, or assert absence with `assert_graph_matches` +
`spec.forbidden_nodes`.

**Nothing is saved.** `inject_nodes_t3d` leaves the asset dirty on purpose, so you can inspect
before committing to it. Save explicitly.

## See also

- `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` — Recipe 16 (authoring) and Recipe 15 (proving it landed)
- `Plugins/Monolith/Docs/specs/SPEC_MonolithBlueprint.md` — full parameter reference
- `Docs/T3D_Baseline/` — the material-side use of T3D: a committed, hash-verified drift gate
