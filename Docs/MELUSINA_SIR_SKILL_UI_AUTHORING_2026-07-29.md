# Melusina + Sir Skill and UI Authoring Pass

## Verified live-editor state

- The active Melusina battle unit is `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation`.
- It already owns three Melusina-specific stock-skill children: `BP_MelusinaFocusAttack`, `BP_MelusinaTrueStrike`, and `BP_MelusinaDoubleHit`.
- Sir is staged at `/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit`, but still inherits the stock Swordsman skill set and needs authored display/skills before his reunion gate is treated as playable.
- Main-menu gameplay routing is intentionally limited to named buttons in `/Game/Melodia/UI/WBP_MainMenu`: `Btn_NewGame`, `Btn_Continue`, `Btn_LoadGame`, and `Btn_Settings`.
- The stock battle root remains `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI`. Its command, targeting, turn order, and skill-use delegates must remain stock-owned.

## Hair finding and repair

`SK_Melusina` has 465 bones while `SK_MelusinaHair` has 148. They share **zero** bone names. The current hair AnimBP therefore cannot obtain a body pose from its `Copy Pose From Mesh` node. The compatibility repair staged in `UMelodiaHairComponent` is:

1. detect whether the body and hair skeletons share any names;
2. when they do not, attach the hair component to body bone `head_x`;
3. retain Kawaii Physics below `hair_root`;
4. preserve mesh-root/CopyPose attachment for a future unified export.

### Blender handoff

For the best long-term result, either:

- keep the hair as a separate rig and export its rest root at the head pivot; or
- export it against the body armature with matching shared `head_x` / body-bone names.

Do not rename `hair_root`; it is the approved Kawaii root. After import, verify that the hair and body have a non-zero shared-bone count before choosing a CopyPose-first setup.

## Co-operative skill slice

Use stock `BP_BattleSkillBase` children and its existing `skillAnimation`, `buffs`, MP, targeting, damage, and turn-release flow. No Melodia combat controller, extra damage callback, or rhythm judgement may own outcomes.

| Character | Authored skill | Stock parent | First mechanical reading | Pair relationship |
| --- | --- | --- | --- | --- |
| Melusina | **Petal Cadence** | `BP_MelusinaFocusAttack` | one accurate, moderate-MP opener | applies the stock-owned *Resonance* buff to its target once authored |
| Sir Melodious | **Skybound Refrain** | `BP_FocusAttack` copied under `/Game/MelodiaIntegration/Party/Skills` | one accurate follow-up | gains its authored bonus only when the target has *Resonance* |

The first safe implementation is now authored as presentation + names + stock damage resolution:

- `/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence` is additively mapped to Melusina at level 1.
- `/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain` is additively mapped to Sir at level 1.

The *Resonance* rule remains the next mechanical step. It must be a dedicated child of `BP_BuffBase` and evaluated inside stock skill Blueprint execution; do not store it in UI, MIDI, a subsystem, or a new party manager.

`/Game/MelodiaIntegration/Party/Skills/Buffs/BP_Resonance` is now a true data-only child of `BP_BuffBase`, configured for one turn. `BP_MelusinaPetalCadence` references that exact class in its inherited `buffs` array. This is a live, stock-owned mark/expiry state; only Skybound Refrain's conditional payoff remains to author.

Live graph review confirms the template already supplies the lifecycle needed for this: `BP_BattleSkillBase.ApplyBuffs` spawns or resets buff instances in the target's `activeBuffs`, and `BP_BuffBase` owns turn/action-time expiry and cleanup. The only remaining authored work is the narrow `BP_Resonance` payload and Skybound Refrain's class check before its one stock `DealDamage` call.

### Authoring sequence (after the next closed-editor build)

1. Author Sir's battle mesh, portrait, and `skillAnimation` entry for Skybound Refrain.
2. Duplicate `BP_BuffBase` to `BP_Resonance`; implement only the necessary stock-compatible flag/effect and a one-turn expiry.
3. In `BP_PetalCadence`, append `BP_Resonance` through the inherited `buffs` array.
4. In `BP_SkyboundRefrain`, branch on the stock target buff collection; its true branch uses its existing one-call stock effect and its false branch remains the normal Focus Attack result.
5. Retain the existing additive `battleSkills` entries; do not replace either map wholesale.
6. Test: Petal Cadence once -> Resonance once -> Skybound Refrain once -> damage/turn release once. Also test Sir without Resonance.

## Soft magical-girl UI kit

The safe source palette is already in project:

- Base: `/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment`
- Corners/dividers: `/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_*`
- Motifs: `/Game/Melodia/Magical/T_Magic_Heart` and `T_Magic_Star`
- Structural panels: `/Game/kenney_fantasy-ui-borders/PNG/Default/Panel/*`

The main-menu `Background` now uses the parchment texture with a warm ivory tint. This changes no button binding, menu state, save route, or input behavior.

### Artist-facing rule

Make visual changes only in named presentation widgets or their style assets:

- **Main menu:** `WBP_MainMenu` `Background`, `TitleText`, and `BtnLabel_*` / button brushes.
- **Battle:** add/retheme a dedicated Melodia presentation overlay; do not restructure `BP_BattleUI` or its delegates.
- **Exploration:** keep the existing `MelodiaMinimapPanel` as the one editable presentation panel inside stock `BP_ExploreUI`.

Apply one shared surface language: parchment fill, lilac/blush focus, restrained gold filigree, then one heart/star sparkle accent. Never make a function depend on a texture path or widget name beyond this presentation boundary.

## Validation gates

- Native hair repair builds only after the Editor is closed.
- Compile `WBP_MainMenu` after visual edits; New Game/Continue/Load/Settings bindings must remain unchanged.
- Compile each new skill and `BP_Resonance` individually; no broad template compilation.
- Runtime proof requires one visible Melusina move, one visible Sir move, one target response, and one turn release per command.
