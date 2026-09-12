# Claude lane session report — 2026-08-15

**Producer:** Claude (C++ / Python tooling / docs lane)
**Inputs:** `Docs/Handoffs/CONTINUATION_2026-08-14_NIGHT.md`, `CODEX_WARDROBE_CORE_CPP_INTEGRATION_REVIEW_2026-08-15.md`, `CODEX_GAMEPLAY_RESEARCH_HANDOFF_2026-08-15.md`, `MELODIA_UE_JRPG_WORKFLOW_RESEARCH_2026-08-15.md`, live Monolith reads, live Blender reads
**Result:** wardrobe C++ hardened (7 fixes); Melusina retarget root cause found and proven; 2 new offline gates; contract floor 17 → 19
**Blockers:** UnrealEditor owns the checkout (no compile); BlenderMCP addon not started (no weight fix)
**Next action:** close the editor → closed-editor build; start the Blender addon → run `Tools/fix_melusina_eye_weights.py --apply`

---

## 1. Melusina retarget — root cause (the headline)

Three sessions treated corneas-leaving-the-head as an iris **material/UV** defect, then as a
**retargeter tuning** problem. It is neither. It is a **skinning topology** defect.

### The finding

The 100-vertex cornea section of the body is skinned to the bone `eyes`:

```
eyes   -> MCH-eyes_parent -> root      (a sibling of the entire spine)
head_x -> neck_x -> spine_03_x -> spine_02_x -> spine_01_x -> root_x -> c_traj -> c_pos -> root
```

`MCH-eyes_parent` is a Rigify eye-aim target driven by a **Blender constraint**. Constraints do not
survive FBX export, so in Unreal it is a plain child of `root` — not a descendant of the pelvis.

At the reference pose everything is coincident, which is why every **static** capture passed. The
moment a clip animates `head_x`, the head moves and the eyes do not.

The warped fingers are the identical shape: phalanges 2–3 are skinned to ARP controllers
(`c_index2_l`, `c_thumb3_r`, …) that the export also flattens onto `root`.

### Why V1 clips masked it for months

V1 mocap was **baked in Blender with constraints evaluated**, so those clips explicitly key `eyes`
and the controllers. A freshly retargeted clip keys only the 19 chained deform bones. The existing
audit had already measured this without knowing what it meant:

> V1 reference: **22** changing deform/**controller** tracks · fresh retarget: **18** deform-only

### Verified evidence (live, not inferred)

| Probe | Result |
|---|---|
| `get_retargeter_info` on `RTG_Mocap_to_Melusina_Current` | 5 ops, 19 chains, `Brennan_Hips → root_x`, `Brennan_Root → root` |
| `list_bone_tracks` on `A_Mocap_FairyWand` | **465 tracks** incl. `eyes`, `eye_l/r`, `master_eye_l`, every `def-lid_*`, `brow_*`, all `c_*` |
| `get_bone_ref_pose` on `SK_Melusina_Skeleton` | 465 bones; **202 are `c_*` controllers**; `eyes → MCH-eyes_parent → root` |
| Blender weight scan on `simply_coll` | `eyes` = **100 verts @ ~1.0**; **34 controller groups carry weight** |
| Side split | `faceit_left_eyes_other (50) ∪ faceit_right_eyes_other (50) == eyes`, **zero overlap** |

### Consequences

1. **No retargeter setting can fix this.** Pose alignment, pelvis ops, chain settings cannot reach a
   bone that is in no chain. The isolated-retargeter-variant work is the wrong layer.
2. **No purchased pack fixes it.** Digital Kinetics, AAA Motion, Rokoko, Mixamo all fail identically.
   Sourcing clips before the skin fix buys more expensive tearing.
3. The earlier `Material.020` iris texture remap treated a symptom. It was not wrong, it was
   unrelated.

### Defect surface — exactly 41 orphan-skinned bones

| Mesh | Violations |
|---|---|
| `EXPORT_Body` | 21 (20 finger controllers + `eyes`) |
| `EXPORT_Accessories` | 20 (finger controllers) |
| Boots / Shirt / Skirt | **0** — all kilt bones are correctly under `root_x` |

---

## 2. The fix

**`Tools/fix_melusina_eye_weights.py`** — moves the 100 cornea verts off `eyes` onto
`DEF_eye.L` / `DEF_eye.R`, which already exist and already sit correctly under
`head.x` (`DEF_eye.L → MCH-eye.L → master_eye.L → ORG-face → head.x`).

Weight transfer only: no skeleton change, no retargeter change, no animation change — so **V1 clips
keep working**. It makes the static-vs-animated discrepancy structurally impossible rather than
dependent on what a clip happens to key.

Safety: dry-run by default; verifies the exact 50/50 side split and **refuses rather than guessing a
midline** if it ever stops holding; writes a weight backup; never saves the `.blend`.

**Not yet applied** — the BlenderMCP addon is not running (see §5).

### The finger half needs one decision

In Blender the `c_index2.l` controllers **are** correctly parented under `hand.l`; it is the FBX
export that orphans them (the intermediate `*_rot` bones are not exported). So the finger fix is
either:

- **(a)** re-weight onto the `*_ref` chain (`index2_ref.l → index1_ref.l → index1_base_ref.l → hand_ref.l`),
  which is what the contract renames into UE's deform skeleton (`index2_ref_l → index2_l`); or
- **(b)** an export-config change that preserves the `c_*` parent chain.

These produce different results. **Not guessed** — to be settled with one live Blender query.

---

## 3. New gates

### `Tools/test_melusina_skin_topology_contract.py` (new)

Rule: **every skinned bone must be a descendant of `root_x`.** A bone outside the pelvis subtree can
only move if an animation explicitly keys it — which is precisely how this defect hid behind V1
clips for months.

Pure data check: reads `specs/anim_presets/melusina_contract_hierarchy.json` (465-bone `parent_map`)
and the exported skin contract. No Blender, no editor, no network.

41 pre-existing violations recorded in `specs/melusina_skin_topology_baseline.json` following the
`art_gates_baseline.json` accepted-debt pattern — **only new violations fail**; `--strict` shows the
true state. This is the gate that would have caught the bug three sessions ago.

### `Tools/test_melodia_wardrobe_transaction_contract.py` (new)

45 assertions locking validate-before-mutate ordering, the slot broadcast, component
registration/collision/mesh ordering, the skeleton gate, and "no reach into the quarantined save
authority."

**Negative-tested:** three invariants were deliberately regressed and each was caught; sources
restored byte-for-byte. A suite that has never failed proves nothing.

`Tools/run_contract_tests.py`: **17 → 19 suites, floor 19, 19/19 passing.**

---

## 4. Wardrobe C++ — 7 fixes

All six handed-off items were **verified in source before acting**; all six were real. A seventh was
found during verification.

| # | Fix | Verified defect |
|---|---|---|
| 1 | Catalog-first, fail-closed grant/equip via new `FindGrantableRecord` seam (`no_catalog` / `unknown_id` / `unauthored_mesh`) | `GrantCosmetic` wrote `OwnedCosmeticIds` with **zero** catalog validation — an unknown id became a permanent unresolvable entry in the canonical save |
| 2 | Broadcast the cosmetic's real catalog slot | `Broadcast(EMelodiaWardrobeSlot::Body, …)` hardcoded — every hat grant read as a body change |
| 3 | `AddInstanceComponent`, collision + overlaps off, `CanCharacterStepUpOn = ECB_No`, **mesh set before** `SetLeaderPoseComponent` | `NewObject` + `RegisterComponent` with no instance registration; default query+physics collision on cosmetic garments; leader pose bound to an empty component |
| 4 | `ApplyWardrobeState()` (BlueprintCallable); `BeginPlay` delegates to it; unclaimed slots hidden | `BeginPlay` was the **only** restore path — a mid-session save load left the previous save's garments on |
| 5 | Ownership as the durable idempotency guard; already-owned returns true **without re-broadcasting** | Header promised "idempotent per GrantId" but `ConsumedGrantIds` is runtime-only — empty after restart, unlike the wallet's persisted set. A duplicate gacha pull read as a new acquisition |
| 6 | Gacha returns the actual `EquipCosmetic` result | Returned true whenever the component merely existed, discarding the result |
| 7 | Catalog cached in a rooted `UPROPERTY` | `GetCatalog()` ran `StaticLoadObject` per call and kept no reference — unrooted and collectable, on the traversal query path |

Also caught by hand-audit (no compiler available): `TObjectPtr<const T>` is not reflectable by UHT —
corrected to non-const with const accessors. Engine API usage verified against UE 5.8 headers
(`USkeletalMesh::GetSkeleton() const` at `SkeletalMesh.h:757`; `AActor::AddInstanceComponent`).

**Status: authored, contract-tested, NOT compiler-verified.** Swept into git by another lane's batch
commit (`FindGrantableRecord` present in HEAD).

---

## 5. Blockers

| Blocker | Evidence | Unblocks |
|---|---|---|
| UnrealEditor owns the checkout | `melodia_rebuild_preflight.py`: `safe_to_compile: false`, `MODAL_OPEN` | Closed-editor build → verifies §4 |
| BlenderMCP addon not started | port 9876 not listening after relaunch | `fix_melusina_eye_weights.py --apply` → fixes §1 |

**Note on the Blender restart:** the previous instance (PID 17744) was wedged — `Responding=False`,
~1% CPU, blocked not computing — and was force-killed at the owner's request. A force-kill writes no
`quit.blend`, so **Auto Save is the only recovery route** for work after the 12:46 save. No autosave
was found in `%TEMP%`, `%LOCALAPPDATA%\Temp`, or the 5.2 config dir; the configured temp path lives
inside `userpref.blend`, so `File → Recover → Auto Save` from inside Blender is the authoritative
check. **This cost should have been stated before the kill, not after.**

The interrupted in-editor attempt mutated **nothing** — the weight backup (written before any edit)
never appeared, proving it died in the read phase.

---

## 6. BlendSpace integration prep

Full spec: **`Docs/Plans/MELUSINA_ANIMATION_BLENDSPACE_INTEGRATION_2026-08-15.md`**

Read live from `BS_Melusina_Locomotion_Hybrid`:

- **7 samples, 4 unique clips** — Walk at 150 *and* 180, Run at 300 *and* 420, Sprint at 540 *and*
  630. Duplicates create a plateau, then cram all visual change into the gap.
- Every sample: `root_motion_speed_known: false` — *"root motion disabled (root-locked) — authored
  speed is unknowable."* **All seven X positions are guesses.**
- Axis max **650** vs recorded sprint speed **714 uu/s** → sprint currently clamps.
- Walk and Run share an identical duration (1.1667 s) — possibly one clip retimed.
- Each clip already carries **2 sync markers**, so foot-phase alignment does not need building.

Governing rule: **X is measured from the clip, never chosen by hand** (`get_root_motion_speed`),
which requires retargeting locomotion **with root motion preserved** rather than root-locked.

Only locomotion is BlendSpace work. Jump/land are state-machine one-shots; dodge/bard/combat are
montages; **swim has no valid source** (only the rejected Quaternius clips) — a real sourcing gap.

---

## 7. Architecture findings from the systems study

The project's signature defect — *"a mechanic that is callable and never called"* — is **fractal**.
It recurs at eight layers, and the integration layer reproduces it against itself:

| Layer | Exists | Nothing calls it |
|---|---|---|
| UI | `UMelodiaTokenCatalog`, wardrobe gating, wallet shard API | No wardrobe/shop/wallet WBP spec exists (13 bound / 6 bindable-unbound / 4 no-backing) |
| Spec | 11 UI specs (2026-07-22) | They target `UMelodiaBattleSession`, **quarantined**; shipping UI derives from stock JRPG |
| Gameplay | Wardrobe capability queries + single-provider registry | `UMelodiaTraversalComponent` does not consult them |
| Data | 8 authored JSON DataTables | Only **3** `DT_*.uasset` exist project-wide |
| Content | 22 rooms, 26 blessings, 21 burdens, 48 enemies, 24 skill charts | **Zero** C++/BP consumers |
| Equipment | `AddEquipmentToInventory` / `WearEquipmentOnUnit` | String reflection; previously no else branch |
| CI | Full Gauntlet lane in `BuildGraph/MelodiaBuildGraph.xml` | Ledger rows hand-asserted (`echo_gates.yml:117`) |
| Evidence | `evidence_envelope.v1.json` **and** `Tools/evidence_envelope.py` | `record_gate.py`, the only ledger writer, references neither |

**The highest-leverage open item:** `specs/echo_pipeline.json` declares
`"automatic_ledger_writes": false` and 9 gates that must report **HOLD** without an editor —
but `record_gate.py` accepts only `pass|fail` and takes any free-text claim with no commit SHA, no
artifact hash, no run linkage. The doctrine is written and **unrepresentable**. This is why §5.5 of
the 08-14 handoff has to ask for gates to be re-recorded.

Two "looks real, is not" traps worth naming:

- **`Plugins/MelodiaTokenWallet/` is inert** — no `Modules` array in the `.uplugin`, `Build.cs` in
  the wrong directory subclassing `UEBuildModule`, header with `GENERATED_BODY()` and no `UCLASS()`,
  and absent from the `.uproject`. The live wallet is `UMelodiaTokenWalletSubsystem` in MelodiaCore.
- **VRM4U** has 8 modules on disk and is **not declared in the `.uproject`**. Any claim that the VRM
  avatar stack is live is wrong.

Flagged, not acted on: root `.mcp.json` holds two live-looking API keys in plaintext (OpenRouter
under `deepseek-v4`, TokenRouter under `kimi-k3`). Intentional per `Tools/model_router.py`, but if
`.mcp.json` is tracked they are in git history and want rotating.

---

## 8. Files

**Created**
- `Tools/fix_melusina_eye_weights.py`
- `Tools/test_melusina_skin_topology_contract.py`
- `Tools/test_melodia_wardrobe_transaction_contract.py`
- `specs/melusina_skin_topology_baseline.json`
- `Docs/Plans/MELUSINA_ANIMATION_BLENDSPACE_INTEGRATION_2026-08-15.md`
- `Docs/Reports/CLAUDE_SESSION_REPORT_2026-08-15.md` (this file)

**Modified**
- `Tools/run_contract_tests.py` (2 suites registered, floor 17 → 19)
- `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/{Public,Private}/MelodiaWardrobe{Subsystem,Component}.{h,cpp}`, `MelodiaWardrobeGachaSubsystem.cpp`

**Untouched:** `_TASK_QUEUE.md`, Melusina V2 mesh/ABP/BlendSpace/Kawaii/material assets,
`.gitignore`, `Config/`, `deploy/run_verify.ps1`, any `.uasset`.

---

## 9. Sequencing

```
skin topology fix (eyes + finger decision)
  -> re-export + reimport V2 body/accessories
  -> retarget WITH root motion preserved
  -> measure speeds -> place samples -> sync group -> bake
  -> gates -> swap locomotion authority
```

Sourcing external animation packs is **step 3 at the earliest**.

**No gate row was recorded by this lane. No PIE, visual, or runtime-proof claim is made anywhere in
this report.** Everything above is either source-verified, live-read read-only, or explicitly marked
as authored-and-unproven.
