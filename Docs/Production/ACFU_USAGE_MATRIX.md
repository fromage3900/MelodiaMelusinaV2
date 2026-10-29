# ACFU Usage Matrix — Hybrid Combat Lane (FLOW/SEQUENCE promotion) — 2026-10-28

**Status: durable contract.** Owner directive 2026-10-28 night ("Yes please… do it all overnight"):
this file is the standing subsystem contract for *what ACFU may be used for and how*. It operates
**under** the OWNER CANON (turn-based ARPG / ACFU hybrid, `CURRENT_STATE.md` 2026-10-11 section and the
four ownership questions) and never overrides it. Any agent or cron loop advancing hybrid combat work
follows this matrix; the lane ledger lives at `Saved/Audit/HybridOvernight_20261029/ledger.json`;
the guard runner is `deploy/hybrid_overnight.py`.

Audited evidence basis (2026-10-28): direct read of `Plugins/AscentCombatFramework` v4.3.5 — 48 modules
(`Source/*/Public` headers) and its `Content/` tree — plus every `Source/BS_GodFile` reference to ACF
classes. Web sources were unavailable that night; this file is deliberately built only from what is
vendored in-repo.

---

## 1. Consumption today (verified, not aspirational)

| ACFU surface | How Melodia uses it | Law that keeps it safe |
|---|---|---|
| `CollisionsManager` — `ACMCollisionManagerComponent::PerformSwipeTraceShot_Local` | scythe swing trace, via `FindObject`+`ProcessEvent` reflection (`MelodiaWaveHarpCombatComponent`) | `bAutoApplyDamage=False` — **Phoenix produces every number** |
| `AscentTargetingSystem` — `ATSTargetingComponent` | T-key magnetic lock (`EMagneticLockYawOnly`) | lock is targeting state, not damage |
| `MotionWarping` (engine) | lock approach step `RootMotionModifier_SkewWarp` | presentation/spacing only |
| `ActionsSystem` — `UACFAbilitySystemComponent` + `UACFActionAbility` | **landing now:** the G-key dodge, `TriggerAction(tag, priority, bCanBeStored)` via reflection | ability owns animation lifecycle + buffer + cooldown; damage authority stays the bridge subsystem |
| `AscentDialogueSystem` (ACF-family plugin) | `MelodiaLiveVoiceSubsystem` unvoiced-line speech | module-linked in `BS_GodFile.Build.cs`; Quill stays narrative authority |
| Attached-but-idle on the pawn (Oct 17): `ACFCombo`, `ACFVault`, `ACFLedgeClimbing` | not driven yet | steps 3 and 6 below drive or justify them |
| Faraway chime enemies: `ACF_NPCController_BP` | staged 2026-10-26; **no attack, no team, no Hybrid component** | step 2 closes exactly that |

## 2. Forbidden as authorities (do not import, regardless of what the plugin ships)

`AscentSaveSystem` (saves: `BP_JRPGSaveGame` + `melodiaNarrativeRecord` own saves) ·
`AscentQuestSystem`/`AscentMoralitySystem` (Quill owns narrative facts) ·
`MusicManager` (`UMelodiaMusicClockSubsystem` is the single timebase — a second clock is the worst
possible fork here) · `AdvancedRPGSystem` HP/attributes **as an HP owner** (encounter actor owns HP;
a new *stamina-like* resource is allowed only after owner ratification, bridged the way
`ResolveWorldFlowAttack` is) · `UnitsSystem` / ACF turn layers (Phoenix owns turns) ·
`ACFPlayerCharacterBP` reparenting (ACF arrives as components on the canonical pawn) ·
ACF `GameMode`s on any production boot · ACFU `ANS_*` widget kit inside production UI surfaces
(one-writer UI law; token system in `Docs/…` ui_style_audit).

## 3. The eight steps (P0 gameplay progression) — with gates and evidence level

Every step ends in: exact-path git commit + `Saved/Audit/HybridOvernight_20261029/*.json` receipt +
ledger `mark` + (for changed `Content/`) **p4 STAGING only** — exact paths checked out via
`deploy/hybrid_overnight.py p4-open`, assets saved, the pending changelist written into the receipt.
**Perforce submits require explicit owner permission (binding front-door rule) — the loop never
submits.** **Never** the default p4 change for staging either (reopen into a dedicated CL or leave
in default and say so in the receipt), **never** bulk-save, **never** a claim above the evidence tier
earned. This lane is the FLOW/SEQUENCE promotion lane of hybrid combat; it is **not** the Poitou P0
Golden Walk route (the walk has no combat beat and this lane does not add one), and Choral Sheep
remains uncoupled.

| # | Step | Definition of done | Evidence tier when done |
|---|---|---|---|
| **1** | **Dodge as a real ACFU action ability** (code landed 2026-10-28: `TriggerDodge` on `G`, reflection `TriggerAction`, `EHigh` priority, ACFU input-buffer `bCanBeStored=true`, beat phase sampled at the press; `NotifyDodgedAttack(Attacker)` resolves one counter through `ResolveWorldFlowAttack` and spends the window). Remaining: closed-editor build → author `BP_MelodiaDodgeAction` (parent `/Script/ActionsSystem.ACFActionAbility`, montage `AM_Melusina_Roll`, `ERootMotionScaled`, cooldown 0.5–0.6) + `DA_MelodiaFlowActions` (ability set, `TriggeringTag=Actions.Melodia.Dodge` native tag) → attach `ACF Ability System` component on `BP_MelusinaJRPGCharacter` (DefaultAbilitySet + `bAutoInit`) → PIE: dodge fires, ASC current-action tag reads back, counter tunes the First Resonance slime (log + HP + resonance) | `Melodia.Hybrid`/`Melodia.WaveHarp.*` automation green incl. new `CounterWindowIsTheDodgeSpan`; PIE function-injection proof (documented, **not** raw-key packaged input) |
| **2** | **One real ACF melee exchange**: Faraway chime creatures get team config (`AscentTeams`; copy `DA_ACFTeamsConfig` pattern into /Game lane asset), a granted attack action (ACFU content attack action child with a creature montage), `MelodiaHybridEncounterComponent` + a collision-master presence; enemy attacks the canonical pawn in PIE; the pawn's dodge window can then **answer a real attack** (`NotifyDodgedAttack` called from the hit side) | PIE proof of attack event + one dodge-intercepted counter; the "missing dealer ASC / team config" log class eliminated or explained |
| **3** | **Scythe 3-step onto the action system**: author the chain as ability-set rows (`Actions.Combat.Scythe1..3` or combo graph), replacing the hand-coded `ScytheStep` counter, keeping ACFU buffering/cancel windows; `ACFCombo` finally driven or removed | same tier as step 1 (automation + PIE) |
| **4** | **Perfect-grade execution**: phrase resolving `grade=Perfect` on a locked target may trigger `ACFExecutorComponent`/CAS-synced finisher — *presentation first*; the number still comes from the Phoenix resolver | PIE + screenshot; packaged stays OPEN |
| **5** | **Hit FX routed through ACM events**: `OnCollisionDetected`/`OnActorDamaged` + `ACMImpactGameplayCue` as the single hit-event writer feeding `BroadcastHit`/PulseImpact (fold, don't duplicate); sweep the 24 invalid ACF tag warnings | log readbacks + `bp_sweep`-style static gate + PIE spot check |
| **6** | **Vault/ledge driven on one authored run** (Orrery plaza is the showcase stage): `ACFVaultComponent`/`ACFLedgeClimbingComponent` + grip points on a single named route, FLOW traversal test | PIE traversal proof on that route only |
| **7** | **Live key-prompt WBP from the ability set**: `UMelodiaWaveHarpHUDWidget` reads granted abilities + their triggering tags/priorities (data source: `UACFInputConfigDataAsset`-style bindings or our own table) so prompts appear/gray with real capability. Painter remains the one existing widget | PIE visual + prompt-census readback |
| **8** | **Owner ratification bundle**: the four CANON questions + (new) player-HP-in-FLOW owner + stamina-as-bridged-resource + execution-as-presentation decisions + the correction that **CANON gate 2 ("ACF melee → ResolveWorldFlowAttack") was closed 2026-10-17/22** by the scythe work | CURRENT_STATE OWNER-CANON table edit — **owner action, never self-ratified** |

Overnight loop order is strictly 1→2→3→…; a step that cannot complete cleanly is `mark`-ed
**blocked** with the reason and skipped to the next **mechanical** step (2 and 5 are safe to enter
mid-stream; anything needing creative judgment stops at the ledger note instead of guessing).

## 4. Reflection law (why nothing links ActionsSystem)

`BS_GodFile` deliberately has **no compile-time dependency** on `ActionsSystem/CollisionsManager/…`
(only `AscentDialogueSystem` links, for voice). ACFU is reached by `FindObject` class-path +
`ProcessEvent` with name-driven parameter buffers (`deploy`/component code, added 2026-10-28 for the
dodge). Consequences: plugin updates cannot break our compile; missing ACFU degrades gracefully
(dodge logs `acf=missing`, nothing else changes); parameter drift must fail loudly (name lookup,
not hand-copied struct layout). Keep this property for every future step; a hard module link requires
an owner-noted amendment to this file.

## 5. Overnight cron contract

* Job: `acf-hybrid-overnight-lane` (hermes cron, interval; pinned `deepseek-v4.1-flash` @ `opencode-go`
  per `Tools/model_router.py pick cpp`).
* Every cycle: `python deploy/hybrid_overnight.py preflight --json` must return `GO`
  (one editor, no UBT running, log idle, PIE not owned by another run, dirty packages ⊆ lane allowlist,
  C: free > 2 GB, Monolith /health ok). `WAIT` → exit. `BLOCK` → `mark` blocked, exit.
* One bounded action per cycle; receipts to `Saved/Audit/HybridOvernight_20261029/`; exact-path git
  commits; **p4 staging only** (`p4-open` of exact lane paths + saves + the pending CL recorded in
  the receipt) — submits are an owner action and the loop has no authority to run them.
  Owner pre-authorization 2026-10-28 night covers lane files: `Source/BS_GodFile/MelodiaIntegration/*`,
  `deploy/hybrid_overnight.py`, this file, `Content/MelodiaIntegration/Hybrid/*` (new),
  `BP_MelusinaJRPGCharacter.uasset` staging+saves, `Saved/Audit/HybridOvernight_20261029/*`.
  Anything outside that list → blocked-note, not action.
* Banned in-lane (absolute): `git clean`/`checkout -- .`, submitting any p4 change (owner-gated),
  default-CL confusion, bulk saves,
  skill-Blueprint Python loads, reparenting to ACF types, booting ACF GameModes, editing `Config/`,
  `.gitignore`, or a second UI/HUD/palette writer.
* Loop self-retires when steps 1–7 are done-or-blocked (it pauses its own job id) leaving step 8 + a
  CURRENT_STATE line for the owner.
* **Vendor recovery (2026-10-29):** WormholePortal + TouchEngine were restored from the intact G: copy;
  WP is staged in pending p4 CL 316 (do NOT submit — owner gate; do NOT touch `Plugins/Marketplace/**`
  or `Plugins/TouchEngine/**` from this lane). WP is EnabledByDefault and **re-enters the next
  closed-editor build**; if the WP module fails to compile, mark the step blocked with the UBT error
  excerpt and leave the plugin alone — deletion is an owner decision, never a build convenience.

## 6. What the loop must NOT do

Do not treat "attached component" as "used system"; audit claims must match this file's evidence tiers.
Do not adopt ACFU content assets into /Game without reading their skeletons/tags (ACF skeletons are not
Melusina's; montages/ability BPs are authored or re-targeted on our side). Do not revive the retired
trial web (promote/retire decision lives in step 8). Do not extend ACFU's `Actions.AbilitySystem.*`
native tag usage into damage — tags are states, damage is Phoenix's.
