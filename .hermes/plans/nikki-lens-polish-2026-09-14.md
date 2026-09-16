# Melodia Polish Plan — Through an Infinity Nikki Developer's Lens (2026-09-14)

How Nikki wins: the outfit IS the gameplay verb, the wardrobe screen is a core loop,
fabric holds up at macro distance, photo mode is a progression pillar, and every
ability reads at silhouette distance. This plan maps those principles onto Melodia's
systems with exact assets and acceptance checks. No new frameworks; converge and prove.

All states below verified firsthand tonight (live editor reads, disk scans, test runs).
Stale offline tool payloads (ppv_report's PortfolioHero canon, the audit's ink note)
are explicitly overruled by live reads where they conflict.

## 0. Standing (last 24h, verified)

- main @ fe4dcc04 = merged #213 (68 files: tokenized rhythm HUD, 2 Quill widgets,
  qsc allowlist test update, zero-neutral skiff hull dials, Sea Above prototype
  actors + 2 PCG styles). No docs/Saved in the merge.
- PR #214 @ ccd2224c, Echo Static Gates GREEN, MERGEABLE, awaiting owner's merge
  command (never push to main from an agent lane):
  guard_collapsed_paths + regression (2/2 green, re-run tonight),
  BRANCH_LEDGER_2026-09-13 (61 refs: 22 merged-equivalent / 36 unique-work /
  3 stale cached), chapter scaffold + 4-beat 03_tide_listening,
  UI inventory 144 widgets / 955 styled in CURRENT_STATE §3,
  53 LFS packages (7 frozen PPV + MPC_Ink/Palette + ET_CharacterFX +
  3 WaveHarp_R07 + exact recursive deps + ENV_StorybookAmbientVFX),
  source-owned PPV canon (MelodiaIntegrationConfig.cpp): StorybookOutline 1.0,
  StarryNight 1.0, MeluColorGrade 1.0, MelodiaInk 0.31.
- Live editor proofs tonight: outline + starry + ink parents and MIs all compile
  clean (outline 72 expr / 329 PS instr; starry 64 / 347; ink 75 / 226).
  Owner-corrected: unfrozen M_PP_MelodiaInk compiles fine — audit note was stale.
- L_MelusinaMorning saved state: PPV_NikkiDream external actor holds all four
  frozen MIs. Weights live in binary; read from the Details panel in-session.
- Frozen outline parent carries the Aug-2026 corrections in HLSL (buffer-space
  taps, view-rect clamp with half-texel inset, normalized normals, smoothstep,
  V7.1 raw-stencil read) — found via UTF-16 scan; UE FStrings are wide, so
  ASCII scans miss shader code. Screen proof still owed (see §3.1).
- Retained red (fenced, honest): QSC contract 3/4 — quest.shorewake.passage,
  flag.shorewake.passage, reward.skiff_passage absent from the DA (test re-run
  tonight names exactly these three). Owner choice: bless in DA or retire beat.
- Busy main tree holds dirty sheep/hair/wardrobe/player work
  (cleanup/pbr-twin-landing-2026-09-10) — preserve in place, never touch.

Top risks: (1) dirty sheep tree diverging from stabilization branch — rebase
only in isolated worktrees, DU conflicts take upstream deletion + re-home;
(2) broad dir-level .gitignore un-ignores permit future accidental adds —
exact-file list is the control, review it on every assets PR;
(3) stale offline payloads vs live truth — cite live reads (compile_stats,
disk scans, test runs), never the offline scripts, until those scripts are fixed.

## 1. Nikki-Lens Polish Backlog (player-visible impact order)

1. Ability-outfit readability. Nikki principle: traversal outfits telegraph
   their verb at silhouette distance. Melodia: wardrobe traversal (Glide via
   UMelodiaWardrobeSubsystem) + Melusina meshes + ET_Melodia_CharacterFX.
   Acceptance: each traversal outfit has a distinct silhouette accent and an
   equip VFX beat; a first-time viewer names the granted ability correctly.
2. Macro fabric fidelity. Nikki: cloth holds up nose-close. Melodia: perceptual
   LOD tiers (32/16/0-step POM, Toksvig, dithered crossfade) + Chladni weaves.
   Acceptance: LOD0 macro capture vs LOD3 vista, no shimmer/popping; the 25
   optical-LOD contract suites stay green (Tools/run_contract_tests.py).
3. Wardrobe screen as core loop. Nikki: styling UI is gameplay. Melodia: P0
   widgets from the §3 inventory (BP_MelodiaBattleUI grade/song labels, stock
   KeyboardLegend #F2D69E, WBP_MainMenu text, WBP_MenuButton label) tokenized
   against the rhythm-HUD reference. Acceptance: ui_style_audit shows zero
   hardcoded P0-visible colors; rest remain listed rows, not drive-bys.
4. Photo/capture pillar. Nikki: photo mode retains players. Melodia:
   MelodiaCaptureRenderSubsystem + AutomationLibrary.take_high_res_screenshot
   (call and RETURN — never sleep the game thread; HighResShot via Monolith
   does not reach the viewport). Acceptance: a committed capture set (pinned
   sky, recorded params) reproducible by a second operator.
5. Hero–companion cohesion. Nikki: companions share the style genome.
   Melodia: ChoralSheep (ABP locomotion + DA done; deformation proven
   numerically) vs Melusina. Acceptance: lit-level beauty capture of sheep
   trailing at 180 cm beside Melusina; follow/transition PIE proof.
6. Line-work identity. Nikki: clean readable ink. Melodia: frozen outline,
   first in stack at 1.0. Acceptance: mismatched-resolution capture proof
   (clean full-frame outline at off-viewport size) — §3.1.
7. Per-chapter color cohesion. Nikki: regions have palettes. Melodia: frozen
   grade + MPC_Melodia_Palette (+ MPC_MelodiaInk). Acceptance: one global
   stack stays default; per-level overrides only with a before/after pair
   proving need. Never fork materials per level.
8. Signature sky. Nikki: vista moments anchor memory. Melodia: StarryNight
   (parent still M_PP_StarryNightOverlay_Candidate). Acceptance: candidate
   re-frozen under Frozen/ after tuning; no Canon asset references a
   Candidate path afterward (grep gate).
9. Hero signaling language. Nikki: visual grammar for interactivity. Melodia:
   stencil table 0–3 (placeholder warm/cool/gold) + undefined hero stencil 4.
   Acceptance: stencil-4 behavior defined, preset colors finalized, and the
   mesh→stencil assignments listed (quest target, hover, selection).
10. Beauty within budget. Nikki: gorgeous AND smooth. Melodia: known PS costs
    (outline 329, starry 347, ink 226). Acceptance: Unreal Insights trace on
    the tuning level stays inside the agreed ms budget with all four
    blendables live; any new blendable ships with its instruction count noted.

## 2. LookDev Proof Sequence (editor session order)

1. Mismatch-capture proof: viewport size noted, AutomationLibrary capture at a
   different resolution, full-frame outline asserted + JSON report beside the
   PNG (frames without a report are not evidence). Artifact: PNG + JSON in
   Saved/Audit/<date>/.
2. Morning reconciliation: PPV_NikkiDream blendables vs canon order/weights;
   record the four live weights; tune outline + starry under a PINNED sky
   (Ultra Dynamic Sky time-of-day unpinned invalidated past A/B per
   CURRENT_STATE §7.4 — pin first, every session).
3. Starry freeze: duplicate candidate values into a Frozen parent, repoint
   MI_StarryNight_Frozen, recompile, re-run proof 1. Artifact: compile-clean
   stats + capture pair.
4. Stencil-4 + presets: owner art direction; implement as MI params + mesh
   stencil assignments only (no new systems). Artifact: assignment list.
5. Sakura/Template stale volumes (owner red decision): delete or disable the
   unlabeled priority-0 volumes carrying quarantined M_PP_ToonOutline +
   M_PP_StorybookVines_Inst. Never touch Sakura art direction itself.

## 3. Execution Rules (unchanged)

Worktrees only; never checkout/reset/stash the busy tree. Protected files need
explicit sign-off per change (SKIP_PROTECTION=1 with approval cited). No pushes
to main — owner merges. One editor, one MCP surface. C++ via closed-editor
Build.bat. Gameplay proof via PIE in MelodiaIntegrationMap, additive fixtures
only. Done per item = merged PR with CI green or a signed owner-decision list,
plus one CURRENT_STATE.md row. Report three lines per item.
