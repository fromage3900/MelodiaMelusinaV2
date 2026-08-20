# Active Vertical Slice Scope — First Dream

**Status:** convergence — integrate the four pillars onto the two authority layers
**Authority:** [`../PROJECT.md`](../PROJECT.md), then `Docs/MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md`
**Playable route (current target):** `L_MelusinaMorning` → `/Game/EnvSandbox/Environments/L_KaleidoNave`
**Real paths:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` → `/Game/EnvSandbox/Environments/L_KaleidoNave`
**KaleidoNave transition:** Travel node retargeted from `/Game/ZenForestTest`; Dreamstate content was merged into KaleidoNave on 2026-08-10 and `+MapsToCook` was added to `DefaultGame.ini`. `L_Melodia_Dreamstate` is not a live route. Open item: KaleidoNave's merged Dreamstate BPs don't function on arrival (`_DECISION_LOG.md` 021b) — diagnose before routing the playtest through it.

> **Scope change 2026-08-20 — the paradigm shift.** This document previously deferred
> **"Wardrobe platform"** and **"Rhythm as required battle authority"**. Both are now **core
> pillars**, per the owner's direction and [`../PROJECT.md`](../PROJECT.md). The game is a
> rhythm-JRPG with a wardrobe pillar: OMORI's shape, Zelda's music-as-key, Infinity Nikki's
> visual bar. QuillScript and the TurnBased JRPG template remain **absolute authority** — the
> musical layer rides on top of the JRPG command scaffolding, it does not replace it.
>
> The old deferral lines are preserved in git history. The reason they were deferred (avoid
> parallel authorities) was correct; the answer is convergence, not deferral.

> **Corrected 2026-07-31.** This line previously read *"DefaultGame.ini intentionally NOT modified."*
> That is no longer true: `+MapsToCook=(FilePath="/Game/EnvSandbox/Environments/L_KaleidoNave")` **was**
> added to `DefaultGame.ini` (see `_SESSION_HANDOFF.md`, "Route change"). The intent behind the
> original sentence still holds — the Blueprint travel node, not the config, decides the
> *destination*; `MapsToCook` only ensures the cook covers the route however it is sequenced.
> The current route lines above target KaleidoNave after the 2026-08-10 content
> merge; the open item is the arrival-side BP fallout (021b), not the destination itself.

> This document supersedes the historical Phase 2/SakuraDream/MelodiaCore scope. That plan predated the working JRPG/Quill route and is not an active implementation instruction.

## Product goal

Ship a compact rhythm-JRPG loop whose mechanics are readable, intentional, and enjoyable:

```text
sanctuary conversation
  -> authored departure
  -> dream traversal (music opens the way)
  -> one JRPG encounter, rhythm-timed
  -> typed terminal result
  -> narrative consequence
  -> stable checkpoint/save
```

The loop is allowed to stay small. If a mechanic does not improve the player's decisions,
feedback, attachment, or flow, remove or defer it.

### What each pillar owes the loop

| Pillar | The minimum this slice needs | Not this slice |
|---|---|---|
| **Rhythm** | Timing on JRPG command input changes one battle outcome. One highway, correct lane legend. | A full song library, difficulty tiers, or rhythm as the *only* input path |
| **Wardrobe** | One outfit equips, persists across a save/restart, and makes one observable gameplay difference | 38 gacha outfits, dye, evolution stages, photo mode |
| **UI** | One writer per surface. No widget written by two owners in one frame. | A full settings/inventory/quest/party UI suite |
| **World puzzle** | One world object responds to one played phrase | A puzzle system, a phrase grammar, or a second traversal authority |

## Proven now

- Morning Sir interaction presents visible Quill dialogue.
- Dialogue completion gates the single native departure/travel path.
- Dreamstate loads under `BP_MelodiaJRPGGameMode` and is traversable.
- The route reached `/Game/ZenForestTest` in continuous PIE; destination retargeted to `L_KaleidoNave` on 2026-07-30, whose arrival-side BP fallout (`_DECISION_LOG.md` 021b) is the open item.
- Dreamstate has one tagged stock `BP_InteractionBattle` root and its required spawn cluster.
- `BP_MelodiaJRPGGameInstance` is selected by project configuration, and asset export confirms narrative sync/restore nodes exist in its stock-derived graph; runtime call order and persistence are not yet proven.
- `WBP_MainMenu` Kenney/Soft-MG presentation is **in progress, not complete** (checked against the live widget tree via Monolith 2026-07-31: it was a bare `CanvasPanel` with a plain `Image` background and stock `Button`s, no Kenney border, no custom texture, until this session started applying one — `Background` image is now set to `T_Melodia_SoftMG_Parchment`, but buttons are not yet styled). Next step: brush treatment for buttons across all 4 states (Normal/Hover/Pressed/Disabled). Real graph chains exist for New Game, Continue, and opening Save/Load. Continue and Load Game remain disabled until canonical slot and Save/Load-screen PIE gates pass.

> **Corrected 2026-08-06.** Per the project owner's live verification on 2026-08-06, the "Proven now"
> bullets above are **NOT currently reproducible**: Quill dialogue is not visible, battle systems are
> non-functional, and the game is unplayable. The known-good state behind these bullets predates the
> Melodia integration and the UI overhaul. Until PIE proof is recorded, every bullet above is
> re-tagged as **unverified** — treat none of them as current runtime fact. The bullets themselves are
> left unchanged as the historical record; do not rewrite them.
>
> **Updated 2026-08-12.** Owner-locked PIE proof now exists for the rhythm highway and QuillScript
> resume-once paths: `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` and
> `Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md`. This does not retroactively verify the historical
> "Proven now" bullets above, but it does mean rhythm and Quill are no longer P0 unknowns.
>
> **Updated 2026-08-13.** The `runtime` gate passed with real keyboard input
> (ledger `[PASS] runtime 2026-08-13`, session `owner-realkey-20260813`). Owner-locked. Do not reopen.

## Foundation gate before combat expansion

All items below are binary gates:

- [ ] Identify the instantiated stock battle widget package at runtime.
- [ ] Prove Attack/Skill/Item/Flee mouse, keyboard, and controller parity without duplicate execution.
- [ ] Pass Victory, Defeat, Fled, and unavailable; each resumes/aborts Quill exactly once.
- [x] Create and load a canonical `BP_JRPGSaveGame` slot across a full process restart. — ledger `save_load` **PASS 2026-08-14**, owner-verified (`owner-verified-20260814`). Do not reopen.
- [x] Prove one narrative flag and one reward restore without duplication. — ledger `repeat_consume` **PASS 2026-08-14** (`session-894e8f57`): authored Priestess Quill first occurrence + canonical SaveToSlot ResumeScript replay; stat and quest intent remained exactly once after reload.
- [ ] Load the canonical JRPG slot with Quill unavailable and preserve all JRPG-owned state.
- [ ] Route a missing/unknown script or checkpoint to an explicit authored safe location without erasing valid current state.
- [ ] Test interpreter invalidation during terminal-result broadcast; retain a recoverable pending result if Quill resume fails.
- [ ] Keep manual saving disabled or unavailable during an active narrative battle.
- [ ] Wire Main Menu New Game, Continue, and Load to the canonical JRPG GameInstance before making it a startup screen.
- [ ] Repair or intentionally revise the `Morning_RoomShell` validator contract.
- [x] Identify/isolate the overlong or invalid serialized name causing cook exit 25. — `PCGEx_PathTesselate.uasset`, invalid name at index 411; Decision 022, 2026-07-30.
- [x] Package the proven three-map route. — `Saved/StagedBuilds_20260730/`, 2.1 GB, all five maps, `Success - 0 error(s)`.
- [x] **Launch**-test the packaged route outside the editor. — ledger `package_launch` **PASS 2026-08-14**: UE 5.8 packaged Gauntlet ran outside the editor, mounted a 2782-package IoStore, loaded `MelodiaMainMenu` and added `WBP_MainMenu` to viewport across map cycles. An earlier same-day FAIL row (cook failed before stage/pak) is superseded.

> **Ledger reconciliation 2026-08-20.** The foundation gates above were checked against
> `Saved/gate_ledger.json`, not against prose. Three items this document had listed as open
> (`save_load`, `repeat_consume`, `package_launch`) have had PASS rows since 2026-08-14 — two of
> them owner-verified. The doc was six days stale. **The shipping gates are closed.**
>
> Still genuinely open and unchecked above: the runtime battle-widget identification, input
> parity, the result matrix, Quill-unavailable load, safe-location routing, interpreter
> invalidation, mid-battle save lockout, Main Menu wiring, and the `Morning_RoomShell` validator.
>
> Separately, `static_gates` is **FAIL 2026-08-14** — `verify_baseline` drift on
> `M_Master_Simple_Universal` (25→26 nodes) and `M_Master_Toon_Landscape_HeightBlend`
> (290→304 nodes). The other four sub-gates passed.

## Orchestra convergence gates (2026-08-20)

The four pillars must converge onto the two authority layers before pillar scope expands. Each
is a binary gate with a ledger row. Full detail:
[`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) and
[`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`](Docs/ORCHESTRA_CONTRACT_2026-08-20.md).

- [ ] `rhythm_owner` — exactly one rhythm path reaches the JRPG damage calculation; MelodiaCore's rhythm classes have zero live callers.
- [ ] `hud_single_writer` — one writer owns the battle HUD; no widget written by both stock `BP_BattleUI` and a Melodia overlay in the same frame.
- [ ] `wardrobe_equip_roundtrip` — equip → save → process restart → load → correct outfit and correct materials, through the `MelodiaWardrobeSubsystem` API only.
- [ ] `rhythm_grade_to_result` — a real-key rhythm grade demonstrably changes a JRPG battle result, and Quill resumes exactly once.
- [ ] `music_world_key` — one world object responds to one played phrase.
- [ ] `wardrobe_gameplay_hook` — one outfit produces one gameplay difference the player can observe.

## Co-op skill gates (2026-07-29)

- [x] `BP_MelusinaPetalCadence` — stock `BP_BattleSkillBase` child, mapped to Melusina at level 1, applies Resonance buff.
- [x] `BP_SirSkyboundRefrain` — stock `BP_FocusAttack` child, mapped to Sir at level 1.
- [x] `BP_Resonance` — stock `BP_BuffBase` child, one-turn duration, referenced in Petal Cadence's `buffs` array.
- [ ] Wire Skybound Refrain's conditional bonus when Resonance is present on target.
- [ ] Author Sir's battle mesh, portrait, and `skillAnimation` entry for Skybound Refrain.
- [ ] PIE-test: Petal Cadence once → Resonance applied → Skybound Refrain once → bonus damage → turn release. Also test Sir without Resonance (normal damage).

## Hair fix gates (2026-07-29) — resolved 2026-07-31, do not re-touch

- [x] Hair bone analysis: body (465 bones) and hair (148 bones) share zero bone names — Copy Pose From Mesh cannot work.
- [x] Native C++ fallback staged in `UMelodiaHairComponent`: attach hair to `head_x`, retain Kawaii Physics below `hair_root`.
- [x] "Hair only" combat body visibility fix staged: defer redirect by one tick so battle Blueprint hides mannequin before visible Melusina mesh becomes montage target.
- [x] Run closed-editor native build to bake both fixes. — build green 2026-07-31.
- [x] Verify hair attaches to `head_x` in PIE. — `MELUSINA_HAIR_SOCKET` verified 2026-07-31 (`_ROADBLOCKS_2026-07-31.md` C6); do not re-apply correction properties.
- [ ] Verify Melusina's full body is visible in combat (not just hair). — still open; folds into the PIE route test.
- [ ] Long-term: re-export hair against body armature with matching bone names for CopyPose-first setup.

## Combat-expansion slice

After the foundation gate and the orchestra convergence gates pass, expansion is limited to:

1. Make the active stock command UI readable, focusable, and visually consistent.
2. Preserve the stock JRPG controller as turn, target, damage, result, inventory, and save authority.
3. Add one meaningful combat decision at a time and playtest it before adding another.
4. Improve hit, damage, break, result, and companion feedback.
5. Keep one enemy/encounter until its complete decision loop is fun.
6. Add tests to the result matrix when a new terminal path is introduced.

## Explicitly deferred

- A second combat or save framework
- Procedural roguelike/run authority
- Broad enemy roster or boss pipeline
- Open-world/environment expansion
- Crafting, achievements, or multiplayer
- Wardrobe **breadth** — the 38 remaining gacha outfits, dye state, evolution stages, photo poses,
  lookbook/share-card output. The pillar is core; its catalog is not this slice.
- Rhythm **breadth** — a song library, difficulty tiers, or rhythm as the sole input path. The
  pillar is core; JRPG command input remains the authority it rides on.
- Broad settings, inventory, quest, or party UI suites
- Front-end map replacement before menu behavior passes

## Flow/QOL priorities

1. Deterministic focus and input-mode transitions.
2. No stale dialogue, battle HUD, cursor, or movement input after transitions.
3. Stable pre-battle and post-result checkpoints; no mid-battle save.
4. Continue is disabled when no canonical slot exists and explains why.
5. Short transitions, skip-safe dialogue, and no duplicated confirmation steps.
6. Clear result/reward feedback before returning control.

## Stop rule

Combat expansion stops whenever a new mechanic fails to make the existing encounter more readable or more enjoyable. Fix, simplify, or remove it before adding scope.

**Convergence corollary (2026-08-20):** if a pillar's work would create a *second* implementation
of something that already exists, stop. Converge onto the named owner instead. Building it twice
is what put the project here.
