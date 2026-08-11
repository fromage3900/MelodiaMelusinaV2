# Soft-Storybook Prototype Audit

## Current evidence

- **Input:** `Tilde` is the sole keyboard `OpenMenu` binding; `SpaceBar` is reserved for `MelodiaTraversalJump`. The traversal component performs one grounded jump, then starts glide only on a second press after apex. This is a clean ownership split.
- **Save:** the main-menu route uses `MelodiaSaveSlotLibrary`, which creates/loads the template `BP_JRPGSaveGame` and assigns the template GameInstance fields. It is a thin adapter, not another save owner.
- **Battle:** the narrative adapter and the external exploration bridge both invoke the same reflected stock `StartBattle` contract. They must remain mutually exclusive by entry source; do not run both for one encounter.
- **SFX:** the authored project SFX inventory currently exposes `A_UI_Bubble`; MelodiaCore rhythm feedback still generates tone waves at runtime. Do not present those tones as the soft-storybook UI language.
- **Redirect debt:** several live Melusina assets still serialize `/Game/Characters/Melusina/...` references and depend on `DefaultEngine.ini` redirects. `SK_Melusina_OLD` is also retained in content. Treat this as a post-prototype migration/packaging audit, not an in-session asset cleanup.
- **Universal Master health (disk audit):** all 7 blessed masters exist and 246 material instances have no missing material parent. Three missing texture references are isolated to `MI_Landscape_WitchGarden` and `MI_Universal_MossStone` (old grass diffuse/normal paths). Keep backup/scratch masters out of new authoring: `*_BACKUP_20260728`, `*_Inst*`, and `_Scratch_WaveScaleFixTest`.

## Visual kit

Use these as the sole prototype surface language:

- Base: `T_Melodia_SoftMG_Parchment` for large cards and `T_Melodia_SoftMG_PillowChip` for controls.
- Accent: `T_Melodia_SoftMG_Hitline` as a thin lilac divider/selection glow, not a full-screen meter.
- Ornament: `T_Melodia_FiligreeCrestBaroque`, `T_Melodia_FiligreeCornerBaroque`, and `T_Melodia_FiligreeBraceVolute`; use one crest or pair of corners per card.
- Gameplay punctuation: `T_Magic_Heart`, `T_Magic_Star`, and `T_Melodia_SheenSweep` only for confirmations and capture frames.
- Kenney: use transparent-center panels as low-contrast outer framing only; do not combine Kenney borders and Melodia filigree on the same card.

Palette: ivory `#F7F0E7`, blush `#F4C9D7`, lilac `#BBA8E8`, muted gold `#D5B66D`, ink `#42354C`.

## UMG migration specification

### Main menu

- Keep Melusina/world composition unobscured in the left two-thirds; pin the menu card to the right third, 8% inset, maximum 420 px at 1080p.
- Use a parchment card with two baroque corners and a small crest. `New Game` is the primary pillow-chip, `Continue` is secondary and disabled/visually muted when the canonical slot is absent.
- Show one compact line beneath buttons: `A new chapter awaits` or `Continue: <slot>`. Focus is a 1.04 scale plus lilac hitline, never a hard outline.
- Play `A_UI_Bubble` once on confirmed selection only. Do not add UI loops or synthetic rhythm tones.

### Exploration HUD

- Persistent: one compact minimap/status anchor at upper right, capped at 17% screen width.
- Reactive: quest card enters at upper left, 5% inset; 460 px max width; title, one-line objective, tiny heart/star marker; fades after 4 seconds unless explicitly pinned.
- Interaction prompt sits lower center above the safe area and contains only icon, verb, subject. It must not coexist with a quest card unless there is enough vertical separation.
- Journal, codex, and dialogue retain parchment surfaces; full-screen menus dim the world with a soft translucent lilac veil rather than opaque black.

### Battle

- Keep the stock turn/action flow. Restyle action chips and turn order using pillow-chip/parchment with a single lilac selection ring.
- Before a skill: a 200 ms non-interactive sheen/crest emphasis on Melusina's selected action. At the existing 4.5 s notify: one small star/heart burst at the target and one target HP/UI pulse. No additional damage event.
- Hide the standalone rhythm prompt unless an authored rhythm encounter explicitly owns it.

## Screenshot checklist (16:9)

1. **Main menu:** Melusina/world silhouette on left, menu card on right, `New Game` focused, no cursor and no debug text.
2. **Exploration:** Zen Forest or morning opening; third-person camera pitched 8–12 degrees down, player on lower-left third, landmark on right third, only minimap visible; capture a second frame during a quest-card reveal.
3. **Battle:** camera framed on Melusina three-quarter view at anticipation, then a second frame exactly around the 4.5 s impact; no duplicate mesh, no rhythm highway, one readable target response.

## Closed-editor implementation order

1. Finish the pending DLL link, then open and compile the touched battle/map assets.
2. Apply the above layout to `WBP_MainMenu`, `BP_ExploreUI`, `BP_MelodiaActionButton`, `BP_MelodiaTurnOrderList`, and `BP_MelodiaBattleUI`.
3. Add one non-blocking quest/collectible notification widget using the existing visual kit and `A_UI_Bubble` confirmation hook.
4. Verify input/save/battle once each, then capture the three screenshot surfaces using `UMelodiaPrototypeCaptureSubsystem`.

## Long-term presentation contract

- `MPC_Portfolio_Audio` is the single runtime audio-reactivity bus. `UMelodiaAudioReactivePresentationSubsystem` publishes only presentation values (`GlobalReactivity`, frequency bands, and `BeatPhase`); it does not start battles, own input, schedule damage, or play replacement audio.
- The external JRPG bridge broadcasts battle start/end solely so passive presentation can reset itself. Stock JRPG remains responsible for command resolution, impact, target reaction, and turn release.
- Rhythm encounters use their Quartz clock when it is available. Stock JRPG encounters use a local visual-only 120 BPM fallback, so a missing music clock can never block or alter battle gameplay.
- The universal landscape master upgrade is staged in `setup_landscape_height_blend.py`: `AudioReactiveStrength` samples `MPC_Portfolio_Audio` into the existing sparkle pulse. Its default is `0.0`, so no existing landscape changes until an approved material instance opts in. Rebuild the master only with the editor closed, using the existing backup-first force workflow; then run `organize_landscape_groups.py` to expose the parameter under `13 | Audio Reactive`.
