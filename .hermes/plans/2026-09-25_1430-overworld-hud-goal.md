# GOAL — Overworld HUD from the Figma, live in PIE (2026-09-25, owner: "relaunch, set a goal, execute")

**Source:** `Content/UI/Canonical gameplay HUD.svg` (layout, owner-approved "Figma as drawn") + `HUD system and states.svg` (materials/states). Crops: `Saved/Staging/HUD_Figma_20260925/`.
**Rules:** one new widget = the one writer for the overworld HUD surface; hidden while `WBP_Battle_Rhythm` owns the screen; read existing authorities (Phoenix HP, mana economy, DA_MelodiaSongs, persona quests), never duplicate them. Monolith is the only mutating surface. Save each asset as soon as it's verified.

## Progress 2026-09-26
- H1 DONE (14 textures saved). H2 DONE — built via `build_ui_from_spec`; spec generator is scratchpad `hud_spec.py`. **Spec format traps:** anchors must be snake_case (`top_left`), position/size/alignment/padding must be `{x,y}`/`{left,…}` objects — CamelCase/arrays are silently dropped with 0 warnings; Image `style.width/height` is ignored → wrap in SizeBox; ProgressBar `percent`/fill and TextBlock wrap need `set_widget_property` after build. Rebuild over a **read-only** WBP crashes the editor (appError on save) — `attrib -R` first.
- H3 DONE — hosted as child `OverworldHUD` of `/Game/Melodia/UI/BP_MelodiaExploreUI` (game-instance-owned explore UI; template hides it in battle). A BeginPlay spawner on BP_MelusinaJRPGCharacter never fired and was removed (fingerprint restored `7bec063c…`).
- PIE capture `Saved/Screenshots/WindowsEditor/ScreenShot00009.png`: layout matches Figma. Polish left: bars render as white track (fill colour not visible), skill labels overlap (widen to ~90), key badges squashed (use crop aspect), minimap empty (H6).

- **Key scheme (owner, 2026-09-26: option B):** overworld skill row is its own control set (Q/E/R/F per Figma); QWOP stays battle-only. Verified: `WBP_MelodiaRhythmHighway` lane labels already read Q/W/O/P (widget ids are legacy `LaneLabel_D/F/J/K`), bindings in `MelodiaBattleInputComponent.cpp:80-83`. Figma REST token expired (403) — owner to renew `FIGMA_API_KEY` before pulling assets from the live file.

## Steps
- **H1 Import** 14 icon PNGs → `/Game/Melodia/UI/HUD/Textures` (UI group, no mips, never stream). Gate: 14 assets saved.
- **H2 Layout** `WBP_Melodia_OverworldHUD` (1440×900 reference, DPI-scaled): minimap ring TL · quest card L · title + resonance bar TC · system row 1/2/J/Esc TR · control hints BL · reticle C · interaction prompt · name/level + Vitality/Resonance bars BC · Q/E/R/F skill buttons BR with labels. Palette: deep-water glass `#0B1628` @ ~80 %, 1 px warm edge `#C9A96E`, resonance cyan `#9EE7F7`, rose-gold `#F1B8AE`, lavender `#B9A6F0`. Gate: compile 0 errors, designer capture matches the Figma layout.
- **H3 Show it** add to viewport for the possessed player on Morning (via the existing player controller/HUD hook — find it; don't add a second spawner). Gate: PIE capture with the HUD over the world.
- **H4 Live data** Vitality/Resonance bars, level/name, quest title/motifs, skill cooldown text. Gate: values in PIE match the source authorities.
- **H5 Buttons** Esc → `WBP_MelodiaSettings`, J → `WBP_QuestJournal`. Gate: each opens in PIE.
- **H6 Minimap** top-down SceneCapture2D → render target → circular material in the ring. Gate: map turns/moves with Melusina.
- **H7 Battle handoff** hide on battle start, show on end. Gate: MelodiaIntegrationMap battle trigger.

Stop and report after each gate that fails; don't stack fixes on an unverified step.
