# GOAL — UI as a 3D orrery that unfolds, staged in game (2026-09-26, owner: "plan with Jev, then stage it")

**Jev `jev-1.13.0` (live):** approach HYBRID 0.98 — 3D chassis/rings/petals/core unfold on the beat with MPC-driven materials; every readable text/button stays screen-space UMG. First phase ORRERY_UNFOLD_PROTOTYPE 0.83 (on the existing M/Tab toggle). Top risk STACK_CHAOS 0.61 (8 independent AddToViewport owners), then SCOPE 0.25. Owner gate 0.68.
**Sources:** Figma "Melusina Menu UI / 2" (KF-01..05, Z order chassis > petals > rings > glass core, Bayer dither) · Interface Dossier artifact 7UNUFH73… (BEAT-03 no UI materials, JUICE-01 beat-fraction motion, NAV-01 stack).
**Build on, don't duplicate:** `WBP_ComicOrrery` + `DA_OrreryRegistry` (spheres gated by story phase) · M/Tab `OrreryMenuAction` · `MPC_Melodia_Palette` BeatPulse/BeatPhase · music clock.

## Owner decisions (gate)
- D1 Canonical style: quiet-glass (Canonical gameplay HUD) vs magical-girl starfield (Redesign frame).
- D2 Motion timing: Figma ms (0/140/320/520/760) vs beat-locked at 128 BPM (0/117/234/469/703).

**Decided 2026-09-26 (owner):** D1 = magical-girl starfield · D2 = beat-locked 0/117/234/469/703 ms at 128 BPM (scale by 128/BPM when the clock differs).

## Phases
- **O1 Orrery chassis actor** — `BP_MelodiaOrreryChassis`: nested ring/petal/core static meshes (Blender or UE modeling tools; MIs off existing masters only), one Timeline driving closed→latch→unfold→ignite→settle per D2. Rendered as a UI layer: dedicated SceneCapture2D (capture-on-demand, off while closed) → RT → brush in the orrery widget. Gate: open/close in PIE, capture only ticks while open.
  - **O1 DONE 2026-09-26** — native `AMelodiaOrreryChassis` (MelodiaCore; `Open()`/`Close()`/`GetRenderTarget()`, waits ≤0.5 s for a BeatPhase wrap, logs `MELODIA_ORRERY_UNFOLD`) + Geometry-Script meshes `/Game/Melodia/UI/Orrery/Meshes/SM_Orrery{Ring,Petal,Core}`; MIs: rings `MI_Brass_FiligreeGold`, petals `MI_T_Melusina_BaroqueTiara_RoseGoldFiligree`, core/backdrop `MI_Universal_CelestialNebula`. PIE proof `Saved/Audit/hud_20260925/orrery_settled.png` (spawned via `summon`). Tune later: petals read dark; level PPV halftone leaks into the FinalColorLDR capture. Build also fixed untracked `MelodiaRhythmHitAudioComponent.cpp` (another session's; 3 API errors blocked all builds → CreateSound2D + OnAudioFinishedNative).
- **O2 Orrery widget** — `WBP_ComicOrrery` hosts the RT behind its existing sphere buttons; sphere buttons animate in on IGNITE, text on SETTLE. Gate: M/Tab opens it with the full sequence, spheres still phase-gated.
  - **O2 DONE 2026-09-26** — `AMelodiaOrreryChassis::ShowInWidget`/`CloseAll` (static, MelodiaCore); `OrreryView` Image (720², z5, HitTestInvisible) in `WBP_ComicOrrery`; `BP_MelusinaJRPGCharacter`: new **M** key → existing `ToggleOrreryMenu`, which now calls CloseAll before RemoveFromParent and ShowInWidget after AddToViewport (graphs: Toggle 11→13 nodes/12→15 links, EventGraph 89→91/100→101; backups `Saved/Audit/hud_20260925/*_before_orrery.json`). PIE: toggle opens with chassis unfolding behind the sphere buttons (`ScreenShot00010.png`), toggle again folds it and clears the widget. Seen: square hard edge on the capture, `IMG_CoreOrnament` white square covers the core, pale backdrop + teal buttons read off-style → O4/O5.
- **O3 One owner for the menu layer (risk #1)** — orrery open/close goes through a single owner that hides the overworld HUD and blocks other menu pushes while open. No 8-site CommonUI migration in this goal. Gate: open orrery, open settings, Esc — nothing stacks wrong.
- **O4 First UI-domain material** — dither + BeatPulse glow (Figma Bayer params) on the orrery glass/panels, MI off it. Gate: shimmer on the beat, text readable at 1080p.
- **O5 HUD echo** — overworld HUD panels use the O4 material; system buttons unfold (latch/settle) on hover. Gate: PIE capture.
- **O6 Stage + capture** — Morning, open orrery on a downbeat, 10 s clip.

**Not in this goal:** full CommonUI migration, calibration screen, battle UI restyle.
