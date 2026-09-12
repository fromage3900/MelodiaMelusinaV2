# Kiro gameplay systems accounting — 2026-08-01

**Scope:** Kiro-owned traversal, Quill/UI/input, and Melody Token presentation seams for the First Dream core loop.  
**Protected:** `MelodiaHairComponent.cpp` not read/edited; `ZenForestTest` not loaded/saved; locked PPV/material/Niagara work not modified.

## Changes completed

### Traversal obeys input authority

`UMelodiaTraversalComponent` now queries `UMelodiaInputContextSubsystem::IsMovementAllowed()` before accepting jump/glide input and on every active traversal tick.

- Exploration/None: jump and double-tap glide remain available.
- Dialogue/Battle/Menu/Cinematic: new jump/glide input is rejected.
- If a restrictive context begins during a glide, glide ends immediately, original gravity/air control are restored, and the double-tap window clears.
- Current authored traversal remains jump + double-tap glide. No climb mechanic exists; none was invented without an authored requirement.

### Quill owns a scoped Dialogue input context

`UMelodiaQuillDialogWidget` and `UMelodiaQuillSelectionWidget` now:

- push one `Dialogue` context when presentation starts;
- reuse their existing handle on repeated `Play` calls;
- release only their own handle during `NativeDestruct`;
- remain safe if travel already cleared the stack;
- preserve existing first-valid-choice focus, original `FStatement`, and one-shot advance/selection guards.

Nested dialog/selection contexts are intentional: out-of-order handles allow the selection to release without destroying an underlying dialog or menu owner.

### Melody Token presentation registry aligned

`Content/Melodia/DataStuctures/DT_MelodiaTokens.json` now references Claude's released Universal-master material instances:

- Heart → `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart`
- Star → `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star`
- Swirl → `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl`
- Water → `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water`

Heart's broken texture path is corrected to `/Game/EnvSandbox/Textures/melodsytoken/Textures/T_MelodyToken_Heart_BaseColor`. Stone/Gale/Umbral and mana-orb remain explicit Heart-art fallbacks rather than fake authored variants.

## Validation evidence

| Check | Result |
|---|---|
| Live Coding | Success; patch applied; 0 errors, 0 warnings |
| GMM contract suite | 285 tests passed |
| `Melodia.Integration` automation | 5/5 passed |
| Token registry JSON parse | Passed |
| Heart/Star/Swirl/Water direct path assertions | 4/4 matched |
| Released token MI disk/readback | 4/4 exist |
| Token MI parent dependency | 4/4 depend on `M_Master_Toon_Universal` |
| Star/Swirl/Water displacement dependency | 3/3 present |
| Diff whitespace check | Passed |

The five integration tests cover narrative migration/defaults/save flags, no-clock guards, and presentation rhythm. They do not replace PIE traversal/focus testing.

## Core-system matrix

| System | Authority | Current state | Remaining proof/owner |
|---|---|---|---|
| Traversal | `UMelodiaTraversalComponent` + InputContext permission | Jump/glide implemented; restrictive contexts now stop/reject traversal | PIE: ground jump, rising/falling glide, landing restore, dialogue/battle/menu suppression — Kiro/manual |
| Input/focus | `UMelodiaInputContextSubsystem` | Canonical stack; Quill now pushes/pops Dialogue; travel clears leaks | PIE keyboard/mouse/gamepad focus and nested menu-over-dialogue — Kiro/manual |
| Quill narrative | QuillScript + `UMelodiaNarrativeSubsystem` | Melodia adapters compile/read back; original statements and one-shot guards preserved | NPC runtime binding, exact single advance/selection — Claude + Kiro/manual |
| Persona/social stat | Narrative record + Persona subsystem | Harmony intent and quest-2 gate authored/read back | Choice → Harmony 1 → restart idempotence — Claude |
| Quest/markers | Persona gate predicate | Quest data and marker definitions authored | Runtime eligibility/visibility before and after both prerequisites — Claude/manual |
| Battle/results | Stock JRPG + Melodia adapter | Adapter/overlay seams exist; Kiro did not alter authority | Runtime widget identity and Victory/Defeat/Fled/unavailable matrix — Cline |
| Battle UI | Stock-derived UI + non-authoritative overlays | Existing focus/readability polish retained | Mouse/keyboard/controller parity and disabled state — Kiro + Cline/manual |
| Rhythm | MusicClock + presentation rhythm component | Presentation-only; integration test passes | Live clock, readable prompts, disable A/B with unchanged gameplay — Cline/manual |
| Travel | `UMelodiaTravelSubsystem` | Allowlisted authored travel, spawn tag, context clear implemented | PIE `MELODIA_TRAVEL_ARRIVED ... placed=1`, portal/death routes — Cline |
| Save/restart | Canonical JRPG/narrative save authority | Narrative SaveGame flags pass automation | Full process exit/relaunch state equivalence — Claude |
| Melody Token definitions | GMM | Direct paths released; 285 tests pass | None for Python contract |
| Melody Token materials | Claude's Universal-master instances | Four assets exist; variant displacement dependencies present | Close-shot visual parallax validation — Claude/manual |
| Melody Token wallet | GMM arithmetic + Claude's canonical persistence seam | Python wallet/idempotent battle fixture exists | Authoritative Unreal provider/snapshot and full restart persistence — Claude |
| Token pickup/HUD | Kiro presentation lane | Registry ready; no counterfeit wallet/pickup/HUD created | Blocked until Claude exposes authoritative Unreal wallet snapshot/transaction provider |
| Main menu/Orrery | Existing menu game mode/registry | Authority preserved | Runtime focus, New/Continue/Load, confirm-only travel — Kiro/Cline/manual |
| Packaging | Existing staged build | Package exists | Executable launch and shortest route — Cline |
| Automation | Live editor Monolith | Targeted 5/5 passes | Full 49-test baseline 46/3 when Cline's run window opens |

## Token provider handoff required from Claude

Kiro's pickup/HUD implementation starts when Claude releases a typed Unreal seam that can:

1. return an authoritative wallet snapshot (`shards[7]`, mana current/max, golden tokens, total collected);
2. accept or reject a collection/spend request;
3. publish one wallet-changed event after an accepted transaction;
4. persist through the canonical save record;
5. reject duplicate pickup/battle-instance grants.

Kiro will not implement arithmetic, reward grants, or persistence in a widget/pickup actor. Until this provider exists, building those assets would either be nonfunctional or create a forbidden second wallet.

## PIE checklist for Kiro's next safe window

1. Confirm no protected dirty map/package would be disturbed.
2. Enter exploration: jump; second-press glide while rising and falling; land and verify gravity/air control restore.
3. Begin glide, open Quill dialogue, and verify glide stops immediately.
4. During dialogue, verify walk/jump/glide/interact suppression and mouse/keyboard/controller dialogue input.
5. Open a selection: first valid choice focused; disabled choice cannot submit; rapid/double input emits one selection.
6. Close dialogue: movement and cursor state restore; no `MELODIA_INPUT_LEAK`.
7. Open menu over dialogue, close each out of order, and verify the remaining owner retains focus/input.
8. Travel after dialogue and confirm context clear plus `placed=1` without a stuck cursor.

## Stop conditions

- Do not save `ZenForestTest` without explicit owner approval.
- Do not touch hair or locked look-development assets.
- Do not add climb, wall-run, stamina, or another traversal system without an authored requirement.
- Do not create a local token wallet, save field, reward grant, or battle outcome path.
- Do not repair/use stale `WBP_Battle_Rhythm` as battle authority.
- Any fourth failure beyond the known full-suite 46/3 baseline is a regression.
