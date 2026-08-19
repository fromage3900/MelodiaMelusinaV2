> **TOP 2026-08-18 ~11:00 ET — read first:** overall status + next-agent handoff is
> [`Docs/Handoffs/OVERALL_STATUS_2026-08-18.md`](Docs/Handoffs/OVERALL_STATUS_2026-08-18.md).
> Studio registry **173/12** (toggleables P1-P4 + Komikaze tiler + audit engine added 08-17).
> AppData is **not** synced (CHANGELOG still v2.68.0). Hung: blender **45856**,
> UnrealEditor **2320** (both new 08-18, unknown responding). Do not spawn Blender/UE. Do not save v22.
> Game HEAD `02910d70` is **12 ahead** of origin `d37fde7f`.
> Live site https://fromage3900.github.io/my-site/ (PR #1+#2). Rhythm/Quill locked. MCP 9876.
> This 08-16 Melusina/Oceanology body below is still the UE SSOT; it does not include Studio 173.

# Session Handoff — 2026-08-16 (Melusina locomotion staged, editor-blocked)

**Nothing was written to any `.uasset` this session.** The interactive editor was never
available — a `--pack all --force` underwater/kitbash ingest held the machine for the
whole window and then died. All Melusina work is authored, dry-run verified, and waiting
on an editor. Treat every claim below as offline-derived unless marked owner-verified.

---

## 1. Root cause of the Melusina animation failure — identified

`Content/Exports/battle_anim_ui_export/2_ABP_Melusina_Current_state_machines.json` shows
`MelusinaLocomotion` holding exactly four states:

    Idle -> JumpStart -> Airborne -> Land -> Idle

**There is no ground-locomotion state, and `BS_Melusina_Locomotion` is not referenced by
the AnimGraph at all.** Walk/run cannot trigger because nothing consumes velocity. This
is one defect, not two — the T-pose is the same wound one layer up.

Caveat: only `_state_machines.json` in that export directory holds real data. Its
siblings (`_abp_info`, `_variables`, `_graphs`, `_linked_layers`) are all Monolith
connection-error stubs. Do not trust them; Phase 0 re-reads live.

## 2. Three review findings that changed the work

1. **The input blocker in `.kiro/specs/.../bugfix.md` is STALE.** That spec names missing
   `MoveForward`/`MoveRight` mappings as the strongest cause. `Config/DefaultInput.ini:79–84`
   now defines both (W/S/A/D + gamepad `LeftY`/`LeftX`), 10 axis mappings total. Input
   reaches the pawn. The animation layer is the remaining blocker. **Do not re-chase the
   input path.**

2. **The T-pose is probably a bad idle binding, not an empty state.**
   `melusina_idle_restore_mocap_2026-08-13.md` names `A_Melusina_Idle_Mocap_RootX` as the
   owner-approved speed-0 clip, restored because the prior sample was "collapsed / wrong
   pose". `melusina_idle_retarget_rca_2026-08-13.md` explains why mocap is the only chain
   that reaches `SK_Melusina_Skeleton` correctly (via `RTG_Mocap_to_Melusina`); direct Lane
   A imports miss the contract on four axes at once. Yet `A_Melusina_Idle` (unsuffixed,
   dated **2026-08-08**, older than both the 08-13 restore and the 08-14 mocap asset) is
   what currently sits at speed 0. All specs now point at the mocap clip.

3. **The approved idle is 0.5s**, so baked blinks are impossible (5 blinks = 10/second).
   Blinks on a short loop need an AnimBP randomised timer driving `eyesCloseL/R`. Noted,
   not built.

## 3. Morph-target naming trap (worth keeping)

Only 68 of 103 morph targets carry real deltas; the 52-key ARKit block is bit-identical to
Basis and Unreal discards it. Two names that look right are inert:

| Looks right | Actually imports |
|---|---|
| `eyeBlinkLeft` / `eyeBlinkRight` | `eyesCloseL` / `eyesCloseR` |
| `browInnerUp` | `innerBrowRaiserL` / `innerBrowRaiserR` |

A curve on an ARKit name compiles clean and does nothing. `--check-names` now hard-blocks
this before any write.

## 4. Leader Pose / KawaiiPhysics — answered, no code change needed

`MelodiaWardrobeComponent.cpp:136` and `MelodiaOutfitComponent.cpp:35` call
`SetLeaderPoseComponent(BodyMesh)` unconditionally. Leader-posed children do not evaluate
their own AnimInstance, so a garment can never simulate its own physics. But `c_kilt_*`
lives in the 465-bone **body** skeleton, so simulating it in the **body ABP** propagates
through leader pose to every garment automatically. That is the correct architecture and
it scales to more outfits. Hair stays separate (distinct 148-bone skeleton; it already
sets leader pose to `nullptr` deliberately).

## 5. Staged work — 5 drivers, all dry-run clean, 0 applied

| Script | Steps | Owns |
|---|---|---|
| `Tools/build_melusina_locomotion_stack.py` | 34 | State machine, `Locomotion` state, `JumpWindup`, `DefaultSlot`, variables, blendspace axis |
| `Tools/build_melusina_foot_ik.py` | 9 | `IK_Melusina_Body` chains/solver/goals + graph pass |
| `Tools/wire_melusina_quaternius_actions.py` | 20 | 7 montages rebound, 3 created |
| `Tools/build_melusina_idle_life.py` | 8 | Blink + brow curves (guards short loops) |
| `Tools/wire_melusina_jump_windup.py` | 6 | Pawn-side `bJumpWindup` events |

Specs: `specs/anim_presets/melusina_locomotion_state_machine.json` (new),
`melusina_locomotion_blend.json` (**fixed**: pointed at `Animations/Mocap_RootX/`, a
directory that has never existed, and at the wrong blendspace path — every sample write
was failing silently; axis max also raised 630 → 750 so the 714 uu/s sprint gate stops
clamping).

**Jump wind-up requirement (owner, explicit):** the *initial hold* of SpaceBar triggers the
wind-up. `MelodiaTraversalJump` is on SpaceBar (`DefaultInput.ini:115`). Press sets
`bJumpWindup` and does **not** call `Jump()`; the `JumpLaunch` notify inside
`A_Q_Melusina_Jump_Start` does. State entry keys on `bJumpWindup`, **not** `bIsFalling` —
keying off IsFalling means the wind-up can only start after she has already left the ground.

## 6. Run order

    python Tools/build_melusina_locomotion_stack.py --preflight
    python Tools/build_melusina_locomotion_stack.py --measure --apply --verify
    python Tools/build_melusina_foot_ik.py --inspect --apply
    python Tools/wire_melusina_quaternius_actions.py --apply
    python Tools/build_melusina_idle_life.py --check-names --breath-only --apply
    python Tools/wire_melusina_jump_windup.py --live-path --apply

**Standing risk:** action names came from live tool enumeration; **parameter schemas were
guessed**. Expect the first `--apply` of each script to abort on a schema mismatch. That is
designed for — mutations abort on the first failure, print the `describe_query
action_schema` call to run, and leave the graph untouched. Correct the params from the real
schema; do not guess twice.

**Known gap:** `wire_melusina_jump_windup.py --apply` spawns the event nodes but cannot
blind-wire the Set/Cast/Jump pins — `connect_pins` needs node ids that only exist after the
events spawn. Run `--emit-contract` for the exact target shape, then wire from a graph read
or capture by hand per MONOLITH_GUIDE Recipe 16.

## 7. Underwater / KitBash3D ingest — one crash, one run in flight

- `--pack all --force` (PID 42388, 23:24–00:16) died of **OutOfMemory**:
  `CrashType: OutOfMemory`, 68.5 GB total, 0.72 GB free at crash, 35 GB working set.
  Nothing saved. Crash dump: `Saved/Crashes/UECC-Windows-D8BFC1A5...`.
- `--pack atlantis --force` relaunched with stdout captured to
  `Saved/Logs/atlantis_ingest_stdout.log` and was actively triangulating KB3D_ATL meshes at
  handoff. **Kenney's 6,059 files must run as a separate process**, possibly split further —
  that pack is what blew the memory ceiling.
- The script hands args to the child editor via `UNDERWATER_INGEST_ARGS`
  (`ingest_aaa_underwater_packs.py:623`, set at `:657`), so the child's `sys.argv` is empty
  by design. Reading it as a dry-run is wrong; check `Saved/Audit/ingest_bootstrap.txt`.
- `-log=` never produces a file when `-stdout` is set; the output goes to the launching
  process's pipe. Always redirect stdout or you get no log.

## 7b. Water gameplay is NOT blocked on Oceanology — they are different layers

Read this before treating the Oceanology port as a water blocker.

A complete water **gameplay authority** already exists in native C++ under
`Source/BS_GodFile/MelodiaIntegration/`, and it is compiled and current (it lives in
`UnrealEditor-BS_GodFile.dll`, rebuilt 2026-08-16 01:04):

- `UMelodiaWaterGameplaySubsystem`, `UMelodiaWaterGameplayControllerComponent`
- `UMelodiaPCGWaterGameplayBridgeComponent`
- `AMelodiaWaterPlatform` + `UMelodiaWaterPlatformMotionComponent`
- `UMelodiaWaterBuoyancyComponent` (gated on `HasAuthoritativeWaterSample`)
- water snapshot capture/restore through the canonical save adapter

`Docs/T3D_Patterns/INTEGRATED_PCG_WATER_GAMEPLAY_MANIFEST_2026-08-10.md` defines an
11-target T3D wiring lane over it, implemented by `Tools/melodia_water_gameplay_t3d.py`
(2026-08-10). Two of those targets are exactly the water↔spatial-puzzle bridge:

- `pattern_completed_puzzle` → bridge `HandlePatternCompleted` → `OnPuzzleSolved` fires
  once, optional route opens
- `platform_route_activation` → `AMelodiaWaterPlatform` gate/pressure/flow response

**Oceanology is a rendering/simulation layer, not the gameplay authority.** Its own
provenance file says as much: keep its ocean surface shader as the simulation authority,
apply `TP_*` toon profiles at the material-instance layer, and let its underwater
post-process *coexist* with `UMelodiaWaterUnderwaterPostProcessComponent`.

So the 5.4 → 5.8 port gates ocean *look and simulation*, not water *gameplay*. The puzzle
and platform wiring can proceed now against the native authority. Do not wait on the port,
and do not rebuild any of this inside Oceanology when it lands.

## 7c. Oceanology 5.4 → 5.8 port — in progress, converging

Plugin is at `Plugins/Oceanology_Plugin` (11 GB, 1500 files, Binaries/Intermediate
deliberately not copied). **`"Enabled": false` in the uproject** — re-enable only to test a
build, and disable again before starting an editor, because a missing-modules modal blocks
the game thread (this cost one wedged editor on 2026-08-16).

First build: 90 error instances / 34 unique / 7 files. Applied since:

| Fix | Sites | Killed |
|---|---|---|
| Removed legacy IWYU tails `#if defined(UE_ENABLE_INCLUDE_ORDER_DEPRECATED_IN_5_2)` — macro retired after 5.4, warnings-as-errors made each one fatal | 5 | 21 × C4668 |
| `CreateShaderResourceView(buf, stride, format)` → `FRHIViewDesc::CreateBufferSRV()...` (5.5+ form) in `OceanologyWaterVertexFactory.h` | 1 | ~11 arg-count errors |
| `FRHITexture2D*` → `FRHITexture*` and dropped `->GetTexture2D()` in `OceanologyRVTBaker.cpp` (5.5 unified the RHI texture hierarchy) | 2 | ~40 RVTBaker instances, incl. the cascaded `GetRenderTarget`/`GetStagingTexture`/`CopyTexture` failures |

Verified NOT broken (checked against `Engine/Source/Runtime/RHI/Public/RHICommandList.h:5351`):
`RHIAsyncCreateTexture2D`'s 10-arg signature is unchanged in 5.8 and the call site matches.
Do not "fix" it.

### Buffer/RHI layer — DONE (2026-08-16, all verified against 5.8 engine headers)

Every replacement below was checked against
`Engine/Source/Runtime/RHI/Public/RHIResources.h` or the engine's own usage in
`RenderCore/Private/GlobalRenderResources.cpp` — none were written from memory.

| Site | Change |
|---|---|
| `WaterInstanceDataBuffer.h` ×2 (init + resize) | `CreateVertexBuffer(size,usage,CreateInfo)` → `CreateBuffer(FRHIBufferCreateDesc::CreateVertex(name,size).AddUsage(BUF_Dynamic).DetermineInitialState())` |
| `WaterVertexFactory.h` index buffer | `CreateIndexBuffer(Stride,Size,BUF_Static,CreateInfo)` → `CreateIndex(name,Size,Stride).AddUsage(BUF_Static).SetInitActionResourceArray(&Indices).DetermineInitialState()` |
| `WaterVertexFactory.h` vertex buffer | old 5-arg `CreateBuffer` overload → `CreateVertex(...).AddUsage(...).SetInitialState(...)` |
| `WaterVertexFactory.h` SRV | `.SetType(Typed).SetFormat(PF_R32_FLOAT)` — **no `SetStride`**; format implies it for a Typed view, matching engine usage |
| `RVTBaker.cpp` ×2 | `FRHITexture2D*`/`GetTexture2D()` → `FRHITexture*` + the ref itself |

Residual sweep is clean: 0 × `CreateVertexBuffer(`, `CreateIndexBuffer(Stride`,
`FRHIResourceCreateInfo`, `FRHITexture2D`, `GetTexture2D()`, `UE_ENABLE_INCLUDE_ORDER`.

Note: the index/vertex-buffer sites never appeared in the first build log — compilation
aborted before reaching them. They were found by sweeping for removed APIs rather than by
waiting for the next build round.

### What is left — ray tracing only

Not a rename; the API was restructured:

```cpp
// plugin (5.4)
GetDynamicRayTracingInstances(FRayTracingMaterialGatheringContext& Context,
                              TArray<FRayTracingInstance>& OutRayTracingInstances)
// engine 5.8  (PrimitiveSceneProxy.h:458)
GetDynamicRayTracingInstances(FRayTracingInstanceCollector& Collector)
```

Two parameters collapsed into one collector. The body is a **168-line function** in
`OceanologyWaterMeshSceneProxy.cpp` with six touchpoints to migrate:

| Current | Needs |
|---|---|
| `Context.ReferenceView` | collector equivalent |
| `Context.GraphBuilder.RHICmdList` | collector equivalent |
| `Context.RayTracingMeshResourceCollector` | collector equivalent |
| `OutRayTracingInstances.Add(...)` | `Collector.AddRayTracingInstance(...)` |
| `Context.DynamicRayTracingGeometriesToUpdate.Add(...)` | collector equivalent |
| `FRayTracingDynamicGeometryUpdateParams{...}` init-list | struct changed shape |

**Do not compile the RT path out.** `Config/DefaultEngine.ini:37` sets `r.RayTracing=True`,
so `#if 0`-ing it would silently degrade water rendering rather than port it. That is the
"add a mechanism to cancel a mechanism" failure the working agreement forbids.

This edit was deliberately NOT made blind — it cannot be compile-checked while the editor
holds the build lock, and a wrong rendering port is worse than a clearly-marked unported
one. Apply it in a session that can build and verify in the same pass.

Pattern so far: ~11 lines of edit removed ~80% of 90 error instances. The remainder is one
contained rendering migration, not a rewrite.

## 7d. Editor accepted edits but persisted NOTHING — read before trusting any 08-16 claim

The editor (PID 45436, started 04:56) never reached `Responding = True`. Monolith answered
and executed graph edits correctly, but **no package write ever completed**.

`ABP_Melusina_Current.uasset` is still **2026-08-14 20:04, 458641 bytes** after a full
locomotion repair. All six spatial-puzzle assets exist in the asset registry at their
correct `/Game/...` paths and are absent from disk. `save_asset` returned
`{"saved": true, "was_dirty": true}` every time. **That response is not proof of a write.**

So the 08-16 AnimGraph work is real but **in-memory only** and dies with the process.
It is cheap to redo: every schema is now encoded in the driver.

### Three tooling bugs found and fixed (2026-08-16)

1. **Silent failures.** `call()` only raised when the response *string* began with
   `ERROR:`. A JSON body carrying `success:false` / `ok:false` passed as success, so three
   `--apply` runs reported clean while leaving the graph half-authored. Now raises on
   `success`/`ok` false or a populated `error` field.
2. **`add_transition` is not idempotent.** Re-running apply after a partial abort produced
   **3 duplicate transitions** (`Idle->Locomotion`, `Airborne->Land`, `Land->Idle`). Each
   duplicate compiles to *"will never be taken"* because only one of the pair carries the
   rule. Two of those pairs already existed in the baseline. The driver now reads existing
   pairs from preflight and skips them; `--verify` asserts none exist.
3. **Save was never verified against the artifact.** `--apply` now stats the `.uasset` and
   fails the run if it was not written in the last 10 minutes, printing that the work is
   in-memory only.

### Monolith schemas (discovered the hard way — do not guess these)

| Wrong | Right |
|---|---|
| `blueprint_path` | `asset_path` (everywhere except `create_blueprint` → `save_path`, `spawn_blueprint_actor` → `blueprint`) |
| `variable_name` / `variable_type` | `name` / `type` |
| `state_machine` | `machine_name` |
| `animation` | `anim_asset_path` |
| `position: [x,y]` | `position_x`, `position_y` |
| `axis: "horizontal"` | `axis: "X"` |
| `min_value`/`max_value` | `min`/`max` |
| rule as `"Speed > 10.0"` | `{"kind":"compare","lhs":"Speed","op":">","rhs":10.0}` — also `{"kind":"bool","variable":"X"}`, `{"kind":"auto"}`, `{"kind":"expression",...}` |

`set_anim_state_always_reset_on_entry` does not exist in the `animation` namespace.
`describe_query action_schema` needs `target_action`, not `target`.

### The 42 Quaternius clips do not load

`Content/.../QuaterniusRetargeted/A_Q_Melusina_*.uasset` — 42 files, ~883 KB each, real
binary (not LFS pointers). The asset registry finds **zero** of them, and
`project_query refresh_assets` on that directory returns `packages_scanned: 0`. The editor
cannot see them as packages at all.

Consequence: the jump states were repointed to the registered
`A_Melusina_JumpStart/JumpLoop/Land_Mocap_RootX` clips, and
`Tools/wire_melusina_quaternius_actions.py` (10 montages) is built on unloadable assets and
**needs rework before use**. Root cause of the unloadable packages is not yet established.

## 8. Not done / deliberately out of scope

- No `.uasset` written, no compile, no PIE, no owner runtime verification.
- ARKit shapekey completion (52 empty keys) — deferred by owner decision.
- Quaternius clips left unwired on purpose: Driving, Fixing_Kneeling, Pistol_*, Punch_*,
  Push, Swim, Sitting, Walk_Formal, Idle_Torch, Crouch, Spell_Simple_Enter/Exit/Idle.
- Blendspace sample repositioning onto measured root speeds — `--measure` needs the editor.
- Nothing committed. Working tree carries 142 dirty paths, mostly pre-existing `.uasset`
  material edits from earlier sessions that are **not** this session's work. Branch:
  `feature/repo-lockin-20260813`.
