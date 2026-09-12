# Editor instability — diagnosed 2026-08-08

**Status:** root cause identified. A mitigation is **already applied** in the working tree —
see "Mitigation already in place" below before doing anything. No asset was modified to
produce this diagnosis.

> **Corrected minutes after writing.** The first version of this file recommended steps
> that were partly already taken. The working tree shows `bIndexEnabled=True -> False` in
> `Plugins/Monolith/Config/MonolithSettings.ini`, which disables the exact subsystem in the
> crash stack. Whoever did that had already reached the same conclusion empirically. The
> steps below are re-ordered accordingly.

## Symptom

The editor restarted four times in roughly one hour (13:25, 13:41, 14:15, 14:24) with no
user action. Sessions ended without warning and Monolith's port 9316 went quiet each time.

## Crash record

`Saved/Crashes/` holds five reports from today:

| Time | Type | Message |
|---|---|---|
| 14:23:44 | Ensure | `DefaultStructInstance.IsValid()` — `S_RoomSettings_BS` |
| 14:16:33 | **Fatal** | `EXCEPTION_STACK_OVERFLOW` |
| 13:28:11 | Ensure | `DefaultStructInstance.IsValid()` — `S_RoomSettings_BS` |
| 13:25:23 | **Fatal** | `EXCEPTION_ACCESS_VIOLATION reading 0x0` |
| 13:25:18 | Ensure | `this->Array.Num() == InitialNum` |

## Root cause

The recurring ensure names both the asset and the code that trips over it:

```
Ensure condition failed: DefaultStructInstance.IsValid()
[UserDefinedStruct.cpp:498]
DefaultStructInstance is invalid for
  '/Game/_PROJECT/Tools/Global/DemoRoom/Misc/S_RoomSettings_BS.S_RoomSettings'
Stack: ... UnrealEditor-MonolithIndex.dll!FUserDefinedStructIndexer::IndexAsset()
```

**A User Defined Struct with an invalid default instance is being walked by Monolith's own
indexer at startup.** The asset is on disk at
`Content/_PROJECT/Tools/Global/DemoRoom/Misc/S_RoomSettings_BS.uasset` (14.8 KB, dated
2026-06-19).

Note the name mismatch in the path: the package is `S_RoomSettings_BS` while the object
inside is `S_RoomSettings`. That divergence usually comes from a rename or duplicate that
did not fully apply, and is consistent with a struct whose default instance never rebuilt.

## Why this is more than a warning

An `Ensure` is non-fatal on its own — it reports and continues. But it fires from a
**struct indexer**, and struct resolution is recursive. A struct whose default instance
cannot be constructed is a strong candidate for the `EXCEPTION_STACK_OVERFLOW` fourteen
minutes later: unbounded recursion is exactly what a malformed self-referential or
unresolvable struct produces in a walker that assumes termination.

That link is **inferred, not proven** — the stack-overflow report carries no callstack and
no log, so the shared frame could not be confirmed. Treat it as the leading hypothesis,
not a finding.

## Mitigation already in place

`Plugins/Monolith/Config/MonolithSettings.ini` now carries `bIndexEnabled=False`
(uncommitted at time of writing). That switches off `MonolithIndex`, the module whose
`FUserDefinedStructIndexer::IndexAsset` appears in the crash stack, so the struct is no
longer walked at startup and the crashes should stop.

Two consequences worth knowing:

- This is a **workaround, not a fix.** The malformed struct is still on disk and anything
  else that resolves it may still trip. Decide deliberately whether to keep the indexer
  off or repair the asset and turn it back on.
- Losing the index costs whatever Monolith actions depend on it. If an action starts
  reporting missing data, this flag is the first thing to check — a disabled subsystem
  fails by returning nothing, which reads as "no results" rather than "not running".

## Unrelated but concurrent

`BS_GodFile.uproject` has gained `VRM4U` (enabled), alongside edits to
`Content/Python/gmm/npc/vrm4u_import.py`, `vrm_registry.json`, `vrm_source.py` and
`import_zundamon.py`. Enabling a plugin requires an editor restart, so **some of today's
four restarts were expected and not crashes.** The five crash reports are real and
separate; do not attribute all four restarts to the struct.

## Suggested next steps, in order

1. Decide on the indexer flag above — keep it off, or repair and re-enable. Either is
   defensible; leaving it undecided and uncommitted is not.
2. Open `S_RoomSettings_BS` in the editor. If it opens, resave it — that rebuilds the
   default instance and may be the entire fix.
3. If it will not open or resave, check whether anything still references it:
   `python Tools/bp_live_path.py /Game/_PROJECT/Tools/Global/DemoRoom/Misc/S_RoomSettings_BS`
   Remember `ORPHAN` from that tool means *prove it before deleting*, never *safe to
   delete* — it cannot see soft references or `.umap` actor references.
3. If it is genuinely unreferenced demo-room content, deleting it removes the asset the
   indexer chokes on. **Ask before deleting** — `Content/_PROJECT/` is not in the
   never-touch table but it is not obviously disposable either.
4. If the crashes continue after that, the indexer itself needs a guard. It is our plugin,
   in `Plugins/Monolith/Source/MonolithIndex`, so a depth limit or an `IsValid()` check in
   `FUserDefinedStructIndexer::IndexAsset` is a legitimate fix.

## Update 15:20 — the mitigation is NOT sufficient

Three further crash reports after `bIndexEnabled=False` appeared in the tree, and they are
no longer all the same fault:

| Time | Message |
|---|---|
| 14:31:33 | `Ensure: DefaultStructInstance.IsValid()` — the original struct fault, **still firing** |
| 14:55:33 | `Ensure: false` — `Engine/Source/Runtime/`**`Dataflow/Core`** |
| 15:16:21 | `Ensure: false` — `Engine/Source/Runtime/CoreUObject` |

Two conclusions that matter for whoever picks this up:

1. **Disabling the indexer did not stop the struct ensure.** Either the flag was set after
   14:31, or something besides `FUserDefinedStructIndexer` also resolves that struct. Check
   the flag's actual value against these timestamps before concluding either way.
2. **`Dataflow/Core` is an unrelated subsystem.** That points to a second, independent fault
   rather than one root cause with several faces. Attributing every crash today to
   `S_RoomSettings_BS` would be wrong.

All three post-date the three-concurrent-editor incident (resolved by 14:30), so editor
contention does not explain them either.

Least-explained item, and the best next diagnostic: capture the full `ErrorMessage` and
stack for the 14:55 Dataflow report. It is the one least likely to share a cause with the
other two.

## Operational note

Separately, an earlier freeze the same day was **not** a crash: an FBX import dialog for
`SK_Melusina_FIXED.fbx` was open and modal, which blocks the game thread and makes
Monolith unresponsive and Windows report the process as "Not Responding". The log line
`MODAL_OPEN` names that case explicitly. Check for it before concluding the editor has
hung — killing the process there costs every unsaved package for nothing.
