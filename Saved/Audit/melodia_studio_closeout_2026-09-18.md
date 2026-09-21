# Melodia Studio close-out — 2026-09-18

Scope: GN time-seam work, note-fish-school sweep, the C1 monolith-UI retire, and the
supporting audits. Every claim cites a log path.

## 1. What shipped (code)

**GN time seam (`deploy/surreal_arch/melodia_gn/`)**
- New `time.py` — the single time authority: `add_time_params` declares
  **Animated / Time Scale / Time Offset** on a Group Interface (idempotent);
  `time_seconds` = `SceneTime.Seconds * TimeScale + TimeOffset`, gated by Animated
  (Animated=False → t=0 = pre-time geometry); `add_time_to_phase` injects gated time into
  an existing sine argument (identity at t=0).
- `core.py`: `apply_universal_music_pass` now declares the time params and calls
  `add_time_to_phase`. Retrofits applied to `chimes_gn.py`, `musical_mesh_variants.py`,
  `audio_terrain.py`, `audio_reactivity.py`, `garment_audio_drape.py`, `garment_loom.py`,
  `house_dress.py`, `music_harps_real.py`, `music_terrain.py`.

**Note fish school (swept in)**
- `melodia_gn/note_school.py` registered two builders: `MEL_music_note_fish` (730 verts)
  and `MEL_music_note_school` (input-dependent — arrays fish on a spline; 0 verts at the
  default group input). `__init__.py` imports it.

**Studio package adjuncts**
- `integration.py` (+78, additive only): C1 `_retire_monolith_ui_panels` +
  `_monolith_ui_panel_names` + `_MONOLITH_UI_KEEP_IDS`.
- `branding.py`, `pie_menu.py` (main+room+window+genome pies), `bagapie_bridge.py`
  (RQ `dry_run` default), `genome_carousel.py` (Dress rail), `research_presets.py`,
  `nikki_materials.py`, `icon_loader.py`, `ui.py`.
- Tooling: `deploy/_melodia_audit_studio_ui.py` (relocated from the gitignored `Tools/`
  tree; repo-root now located by walking up to `.git`), `Tools/verify_addon.py`
  (RECORDED_EMPTIES 136→137), `Tools/registry_baseline.json` (+2 ids → 591).

## 2. Gate evidence — GREEN (6/6)

`Saved/Audit/verify_addon_2026-09-18_final.log`, run headless against the live synced
addon (Blender 5.2.1 LTS):

```
GATE A  PASS   registry=591 errors=0 []
GATE B  PASS   baseline=591 lost=0 new=0 [][]
GATE C  PASS   clusters=2 known=2 unexpected=[]
GATE D  PASS   empties=137 recorded=137
GATE E  PASS   checked=6 mismatched=[]
GATE F  PASS   offenders=none
GATE RESULT: PASS  (6/6 passed)
GATE metrics: builders=591 categories=28 dup_clusters=2
```

Sync evidence: `deploy/_sync_addon_to_blender_5_2.py` → `Live byte check: 283/283 match`,
`LIVE ADDON SYNC: OK`.

Time seam: `Saved/Audit/gn_time_seam_2026-09-18.log` → `time-seam health: 0 check(s)
failed` (wave / chime-aeolian / musical-pulse variants all show scene-time nodes driven).

## 3. GN builder WARN audit

`Saved/Audit/gn_warn_audit_2026-09-18.md` — 19 distinct (tree, class) warning pairs across
18 trees in three classes (None socket / scalar→Value / Mesh Line 'End Location'). All are
latent (the gate passes); the P0 fix is to make `core.link_sockets` fail loud.

## 4. C1 monolith-UI retire — **NOT CERTIFIED (2 of 7 checks fail)**

`Saved/Audit/health_c1_monolith_ui_2026-09-18.log`:

```
[Melodia Studio] C1 retired 1 monolith N-tab panels
[FAIL] zero monolith N-tab panels registered -- still live: ['SURREAL_ARCH_PT_plan_edit_floating']
[FAIL] legacy PROPERTIES drawer still a class -- escape hatch destroyed
[PASS] Core UI survived -- 7 panels present
[PASS] builder registry untouched -- 591 builders
[PASS] operator surreal_arch.generate still registered
[PASS] operator surreal_arch.ivy_scatter still registered
C1 health: 2 check(s) failed
```

The C1 code is **additive** (`git diff` = +78 / −0) so it cannot have regressed existing
behaviour, but it does not satisfy its own gate:

1. `SURREAL_ARCH_PT_plan_edit_floating` survives. `branding.unify_npanel_categories()`
   deliberately keeps and renames this floating plan panel ("Melodia Studio Plan"), while
   `branding.audit_monolith_ui_retired()` does **not** exempt it. Two functions disagree on
   whether it is kept — an **owner design decision**, not a mechanical fix.
2. `SURREAL_ARCH_PT_panel` (the legacy escape hatch) is `None` in this check's flow,
   because `register_overhaul` is called without `monolith.register()`, so the monolith's
   own panels are not registered. This may be a check-flow artefact rather than a code bug —
   confirmed behaviour in a normally-enabled addon is still **unverified**.

**Consequence:** C1 is recorded OPEN. The related freeze-doc hold items are NOT claimed
resolved by this record.

## 5. Hallucination corrections (this session, evidence-based)

Earlier notes in this session contained claims that did not survive re-checking. Corrected:

| Earlier claim | Reality |
|---|---|
| A music-pass fix was applied to `...\MelodiaAlexMelodiaAddon_devback\...\alextools.py` | Wrong repo (a different, non-git project). File deleted. The real fix is `melodia_gn/time.py` + `core.py`. |
| `apply_universal_music_pass` used `t.MusicPulse % 8` / `hp.value_k` | No such symbols exist. The real wiring is `add_time_to_phase` (phase-additive). The two `c7_*` memos describing it were deleted; `c7_hallucination_review_2026-09-18.md` replaces them. |
| "2 swings/second = 4 Hz" | Arithmetic error — 2 swings/second is 2 Hz. The seam is tempo-free anyway. |
| `time_seam_guard_clock_*.log` telemetry | Fabricated pseudo-telemetry; deleted. Real evidence is `gn_time_seam_2026-09-18.log`. |
| "installer scripts target Blender 5.1" | False — `_sync_addon_to_blender_5_2.py` targets 5.2 (`BLENDER_VERSION = "5.2"`). |
| "gate D grew 111→136 needs an owner decision" | Stale — the baseline was already raised to 136 on 2026-09-11 with a documented reason. |

## 6. Git

Nothing was committed before this record. The planned commit set (named files only — the
working tree carries large unrelated churn from other lanes) is:

- `deploy/surreal_arch/melodia_gn/**` (time seam + note fish school + wave) — touches
  freeze-hold `__init__.py` / `core.py`, released by owner decision.
- `deploy/surreal_arch/{integration,branding,pie_menu,bagapie_bridge,genome_carousel,
  research_presets,nikki_materials,icon_loader,ui}.py`.
- `deploy/_melodia_health_*.py`, `deploy/_melodia_audit_studio_ui.py`,
  `deploy/_probe_mesh_line.py`, `deploy/_sync_addon_to_blender_5_2.py`.
- `Tools/verify_addon.py`, `Tools/registry_baseline.json`.
- Docs: `Docs/MelodiaStudio/MELODIA_STUDIO_HOW_TO_USE_2026-09-18.md`,
  `Docs/Research/MELODIA_STUDIO_V2_WORKFLOW_2026-09-18.md`.
- Records: `Saved/Audit/c7_hallucination_review_2026-09-18.md`,
  `Saved/Audit/gn_warn_audit_2026-09-18.md`, this file.

Not touched / not committed: the frozen `nikki_decor.py` /
`nikki_musical_decorations.py` (lock `3`), and the large unrelated trees.

## 7. Open items

1. **C1 monolith-UI retire** — 2 health checks open (§4). Needs an owner decision on
   `SURREAL_ARCH_PT_plan_edit_floating` (retire vs. keep) and a check that registers the
   monolith before asserting the escape-hatch drawer.
2. **GN WARN classes** — P0 `link_sockets` fail-loud, then the per-tree fixes in
   `gn_warn_audit_2026-09-18.md`.
3. **Gate D / registry drift** — any future builder addition must update
   `Tools/registry_baseline.json` **and** `RECORDED_EMPTIES` in the same change.
4. **V2 packaging** — `blender_manifest.toml` + extension CI only if the addon ships
   publicly (`Docs/Research/MELODIA_STUDIO_V2_WORKFLOW_2026-09-18.md`).
5. **Blender process hygiene** — three Blender instances were live during this session
   (two interactive). Gate D crashed once under that load; the final run with fewer
   contenders passed. Keep the freeze rule of one writer.
