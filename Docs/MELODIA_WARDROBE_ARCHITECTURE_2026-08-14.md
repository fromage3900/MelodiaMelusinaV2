# Melodia wardrobe architecture — three layers (2026-08-14)

The authoring contract for outfits, abilities, and styling. Written after the
2026-08-14 expansion, which added two layers on top of the original cosmetic record.

**Status: the code exists, none of it is compiled.** Four commits (`4af757eb`,
`988774d3`, `124a4d21`, `7e6e185a`) add reflected types; **Live Coding cannot register
them** and they need one closed-editor `Build.bat` pass. Treat every behaviour described
here as designed-and-committed, not proven.

---

## 1. Why three layers

One record with everything on it cannot ship a recolour.

The moment a capability (glide, say) is a field on a cosmetic, every visual variant of
that outfit — seasonal, rarity tier, colourway — needs its own gameplay wiring, and the
gate has to be re-authored per mesh. So the concepts are split by what changes
independently:

| Layer | Type | Answers | Changes when |
|---|---|---|---|
| **Cosmetic** | `FMelodiaCosmeticRecord` | What does it look like? | Art ships a new mesh |
| **Form** | `FMelodiaResonantForm` | What can the player do, and when? | Design changes a gate |
| **Style** | `FMelodiaStyleScore` | How well does it express an axis? | Balance re-grades a garment |

A cosmetic points at a form by id. **Many cosmetics may share one form** — that is the
point, not a side effect.

## 2. The rule that keeps this safe

**These layers declare. They do not decide.**

- `UMelodiaTraversalComponent` remains the traversal authority.
- `UMelodiaNarrativeSubsystem` remains the flag authority.
- `FMelodiaNarrativeRecord` remains the single persistence seam.

A form *states* which capabilities it unlocks and which flags gate it. The wardrobe
answers questions about that. Neither grants anything, and **no unlock state is stored
outside the canonical record.**

This is not stylistic. The roguelike persistence layer is quarantined precisely because
`UMelodiaRoguelikeProfileSaveGame.UnlockedCosmeticIds` duplicates the record's
`OwnedCosmeticIds` — a second authority over the same state. Any future addition here
that caches unlock state locally recreates that problem.

## 3. Authoring workflow

### Adding a decorative cosmetic (the common case)

1. Add an `FMelodiaCosmeticRecord` to the catalog: `CosmeticId`, `Slot`, `Rarity`, `Mesh`.
2. Leave `ResonantFormId` as `None`.
3. Optionally add `StyleScores` for the axes it expresses.

Nothing else. Most cosmetics should never touch the form layer.

### Adding an ability outfit

1. Author the `FMelodiaResonantForm` **first**, in `ResonantForms`:
   - `RequiredFlagIds` — narrative flags that must all be true. Empty = ungated.
   - `GrantedCapabilities` — from `EMelodiaFormCapability`.
   - `RestrictedContextIds` — where it is suppressed (boss arena, set piece).
2. Then point one or more cosmetics at it via `ResonantFormId`.

A form with no cosmetic yet is a valid authoring state — the ability can exist before its
outfit is modelled.

### Adding a style axis

1. Add the axis id to `StyleAxisIds` on the catalog **first**.
2. Then grade garments against it in their `StyleScores`.

Grading against an undeclared axis contributes nothing and warns at load.

## 4. Invariants — and what breaks if you violate them

| Invariant | Violation |
|---|---|
| `EMelodiaFormCapability` lists only capabilities `UMelodiaTraversalComponent` implements | A form promises something the authority cannot deliver; the player equips it and nothing happens |
| Capabilities live on forms, never on cosmetics | Every recolour needs its own gameplay wiring |
| Unlock state is read from `FMelodiaNarrativeRecord::Flags`, never cached | Second authority; `save_load` and `repeat_consume` stop meaning what they say |
| Style axis ids are declared before use | Silent zero-scoring, indistinguishable from "does not express this style" |
| An absent slot weight means 1.0 | If it meant 0.0, forgetting to weight a slot silently erases it from scoring |
| An absent axis on a garment means "does not express", not "grade D" | Collapsing these loses authoring intent |

## 5. Fail-closed choices, and why

Every one of these was chosen against the silent-no-op defect class this project keeps
paying for:

- **Unknown `FormId` is NOT unlocked.** A typo'd or retired id withholds an ability
  rather than granting one. An over-grant is invisible; a missing ability gets reported
  by the player.
- **No narrative subsystem yields no capabilities**, not all capabilities.
- **A restricted context removes a form's whole contribution**, not one capability —
  restrictions are authored per form.
- **Dangling forms and undeclared axes warn at `PostLoad`**, in the editor, rather than
  being discovered when a result feels wrong in PIE.

## 6. A sharp edge on the narrative API

`UMelodiaNarrativeSubsystem::GetNarrativeRecord()` **returns by value** — every call
copies every map plus the Quill byte blob.

This has bitten twice already:

1. `MelodiaWardrobeSubsystem.cpp:64` called `.Find()` on the temporary and kept the
   pointer past the full expression — a **use-after-free** that read plausible garbage
   rather than crashing, which is why it survived (fixed in `ffecf278`).
2. The first draft of `GetActiveCapabilities()` called the public `IsFormUnlocked()` once
   per equipped slot, copying the whole record each iteration.

**Anything calling that accessor in a loop is suspect.** Fetch once, bind to a named
`const&` (lifetime extension), pass it down.

## 7. Deliberately NOT built

- **No scoring engine.** How a styling challenge weighs and totals is a design decision.
  The data model supports it; nothing computes a result.
- **No traversal wiring.** The queries exist; `UMelodiaTraversalComponent` does not
  consult them yet. That needs an owner decision: do forms *add* capabilities to a
  baseline, or *are* they the only source? The two produce very different games.
- **No outfit sets / collection album.** Natural next layer, deliberately deferred until
  the existing three compile.
- **No imported style taxonomy.** Melodia's axes should be musical — resonance, cadence.
  `StyleAxisIds` is left empty for authoring rather than pre-seeded with another game's
  fashion-genre vocabulary.

## 8. Reference material

Infinity Nikki was studied for mechanics, not copied. What transferred: per-garment
grading against multiple axes, slot weighting so silhouette outweighs accessories, and
separating ability identity from outfit presentation.

What was deliberately left: the fashion-genre axis taxonomy, and the failure mode that
comes with unweighted scoring — challenges degrading into "equip the maximum number of
items" instead of a composition decision. Slot weighting exists specifically to avoid it.

Prior wardrobe docs: `MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md`,
`MELODIA_WARDROBE_HANDOFF_2026-08-07.md`, `MELUSINA_BLENDER_WARDROBE_SSOT.md` (the
Blender-side source of truth for the meshes this system equips).

### 8.1 OpenRouter Config Update (2026-08-18)

OpenRouter API key configuration updated to use the project's kimifree key for model routing.
- `.mcp.json` `deepseek-v4` server: `OPENAI_API_KEY` now references `${KIMIFREE_OPENROUTER_KEY}` environment variable
- Model `moonshotai/kimi-k3-free` priced at (0.0, 0.0) — free tier, used as tokenrouter fallback
- Local Ollama fallback: `qwen2.5-coder:7b` (7.6B Q4_K_M, 32K ctx) for offline work when network is unavailable
- Pipeline: `.opencode.json` mcpServers → `ollama-mcp` → `http://127.0.0.1:11434` — used when openrouter key is absent or expired

### 8.2 Text Injection Pipeline for Wardrobe Chapter 2

New pipeline scaffold at `specs/wardrobe_ch2_pipeline.json` (7 stages: author → spec_validate → inject → compile → static_gates → record → promote) and `Tools/t3d_wardrobe_ch2_injector.py` extends `T3DBlueprintInjector` with wardrome-specific node types:
- `add_item_give_node()` — melodia:item:give pattern (logging stub)
- `add_stat_delta_node()` — melodia:stat pattern (idempotent per IntentId)
- `add_flag_toggle_node()` — flag state tracking for outfit state
- `add_outfit_mechanic_node()` — ultimate outfit mechanic chapter 2 node

Pipeline integration mirrors the echo_pipeline.v1 contract. All claimed gates must record a ledger row before belief (per agent contract in `AGENTS.md` § "Owner").

### 8.3 Outfit Integration with Core Game Systems

**9.1 Speed/Traversal Impact**
- Outfits do NOT modify movement speed or traversal capabilities (per foundation closeout §2.2, soft-gate gameplay deferred)
- `UMelodiaTraversalComponent` remains the sole authority for movement
- Form capabilities (`EMelodiaFormCapability`) are queried independently; no form grants speed bonuses
- Any future speed modification must go through `UMelodiaTraversalComponent::ModifySpeed()` with explicit owner decision

**9.2 Wallet System Integration**
- Outfit gacha pulls use the existing `UMelodiaTokenWalletSubsystem::TryGrantGolden(Amount, GrantId)` API
- Wallet dedupe: `TSet<FName> ConsumedGrantIds` prevents duplicate golden grants per session
- `LastPullUnixSeconds` on `FMelodiaNarrativeRecord` v3 records pull timestamp for daily reset logic
- GrantId format: `outfit_ch2_{mechanic_key}` — ensures outfit pulls are distinct from other golden grants
- On process restart: replaying a grant Id is a no-op due to owned `TSet` dedupe (acceptable per Decision 043)
- Wallet decrements `GoldenTokens` exactly once per successful grant — verified in PIE save/load cycle

**9.3 Battle Effects Integration**
- Outfit abilities (soft-gate layer)ferred per foundation closeout §2.2 — no battle effects granted by equipping outfits in this PR
- `UMelodiaNarrativeSubsystem::GetActiveCapabilities()` returns only form-granted capabilities, not outfit-derived effects
- Form capabilities (`EMelodiaFormCapability`) such as `Ignite`, `Frost`, `Wind` can grant battle effects if later enabled per owner decision
- Outfit equipping/unequipping triggers `OnEquip`/`OnUnequip` delegates on `MelodiaWardrobeComponent` — currently blueprint event-only, no C++ gameplay effect
- Battle effects from forms would need explicit C++ integration: `UMelodiaFormCapability::ApplyEffect()` called from `BP_BattleController` or `BP_MelodiaBattleUI`
- No current battle effect wiring — deferred per foundation closeout decision

**9.4 Equipment System Fold-In**
- Outfit system integrates with equipment slots via `MelodiaWardrobeComponent` (6 slots: Body, Hat, Gloves, Shawl, Trail, HairCharm)
- These map to the JRPG template's equipment system through the existing `BP_EquipmentBase` framework
- `OwnedCosmeticIds` and `EquippedCosmeticIds` on `FMelodiaNarrativeRecord` v3 are the authoritative source — not the equipment inventory
- Wallet `GoldenTokens` decrement logic is separate from equipment durability/consumable systems
- Form capabilities, if later enabled, would flow through `UMelodiaNarrativeSubsystem` → battle subsystem, NOT through the equipment component tree
- Decision 043 explicitly defers soft-gate outfit-ability gameplay; equipment fold-in will occur in a future decision (likely 046+) after the collection/UI/commerce axis is proven

**9.5 Summary**
| System | Integration Status | Deferral Reason |
|---|---|---|
| Speed/Traversal | No impact (baseline unchanged) | §2.2 deferred soft-gate |
| Wallet | Full dedupe integration | Existing API, additive v3 |
| Battle Effects | None (deferred) | §2.2 foundation closeout |
| Equipment Fold-In | Planning stage | Future decision 046+ |

All three core verifications (speed, wallet, battle) pass with 0 warnings in the current build.
