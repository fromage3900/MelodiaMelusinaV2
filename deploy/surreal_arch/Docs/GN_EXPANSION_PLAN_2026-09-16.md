# Melodia GN expansion plan — 2026-09-16 (final revision of the semester)

**STATUS (2026-09-16 evening):** W0+W1 executed — the tree was restored (25 files), the
Sep-14 wave was found unwired and wired (registry 568 → **589**), the tessellation id
collision was renamed (`MEL_escher_tessellation`), the baseline was re-cut, the live
install synced — **gate 6/6 PASS, census PASS**. Evidence:
`Saved/Audit/gate_2026-09-16_final.log`, `Saved/Audit/census_2026-09-16_final.json`,
`Saved/Audit/SESSION_CLOSEOUT_2026-09-16.md`. The §1 text below is the as-found record.

**Supersedes:** [`GN_EXPANSION_PLAN_2026-08-17.md`](GN_EXPANSION_PLAN_2026-08-17.md) (keep both as history).
**Regime:** under the 2026-09-11 semester freeze — tag `melodia-studio-freeze-2026-09-11`;
gate `Tools/verify_addon.py`; baseline `Tools/registry_baseline.json`.
**Deep-review note:** every number in this revision was measured on 2026-09-16 or is
cited to the log that measured it. Where the tree could not be measured directly, the
measuring base is stated. Prose is not a row.

---

## 0. Executive summary

- The registry itself is healthy: **568 builders / 25 categories / 0 build errors /
  0 lost vs baseline** (measured today on the reconstructed checkout, `§2`).
- **One blocker: the P: checkout cannot import.** 22 tracked source files (19 in
  `melodia_gn/`, plus `convergence_mode.py`, `trim_sheet_lab.py`, `trimsheet_magic.py`),
  the gate tool `Tools/verify_addon.py`, the census tool `Tools/melodia_studio_census.py`
  and the freeze doc are **deleted in the working tree while present at HEAD**. Nothing is
  lost; the repair is one `git restore` command and it needs owner sign-off (pipeline law).
  Until then neither the addon, nor the gate, nor the census can run from P:.
- After the restore: baseline re-cut v2 (only 2 ids of drift), the duplicate-cluster
  decision, and one warning-sweep batch. That is the whole remaining distance to green.

## 1. State of the tree — measured 2026-09-16 (BLOCKING)

| Fact | Value | Evidence |
|---|---|---|
| `import surreal_arch.melodia_gn` from P: | **FAILS** — `ImportError` at `melodia_gn/__init__.py:38` (`musical_mesh_variants`) | reproduced headless, Blender 5.2.1, `Saved/Audit/import_chain_probe.py` |
| Deleted-but-tracked under `deploy/surreal_arch/` | **22 files** — 19 `melodia_gn/*.py` (incl. the 09-11 recovered set: `barrel_vault_kit`, `curved_wall`, `dreamy_gothic_arch`, `garment_material_id/smart_bevel/trim_uv/vertex_ao`, `gold_light_strip`, `music_euro_remainder`, `musical_mesh_variants`, `ornament_strip`, `rose_window`, `ue_proxy_kit`, …), plus `eyewear.py`, `core_forms_port.py`, `greybox_port.py`, `music_port.py`, `nikki_decor.py`, and `convergence_mode.py`, `trim_sheet_lab.py`, `trimsheet_magic.py` | `git status --porcelain deploy/surreal_arch/` |
| Gate + census tools | `Tools/verify_addon.py` **ABSENT** (` D`), `Tools/melodia_studio_census.py` **ABSENT** (` D`) | `git status`, `ls` |
| Freeze doc | `Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md` **ABSENT** (` D`); readable at HEAD | `git status` |
| Worktree deletions overall | **715 tracked paths** (` D`): Content/Melodia 211 · `__ExternalActors__` 60 · Saved/Audit 46 · Docs/References 37 · melodia-design-system 70 · Tools/wave_violin 29 · Tools/eyewear_verify 28 · Content/EnvSandbox 25 · deploy/surreal_arch 22 · … | `git status --porcelain | grep -c '^ D'` |
| Local source deviations under the addon | exactly **2 modified files**: `melodia_gn/melodia_house.py` (+245, opening-family work, uncommitted), `melodia_gn/presets.py` | `git status`, `git diff --stat` |
| Live install | `surreal_arch` **not installed** — AppData holds `surreal_arch_bak/` (complete 106-file `melodia_gn` snapshot). Never author there. | `ls %APPDATA%/…/addons/` |

**Nothing is lost.** All 22 files plus both tools and the freeze doc exist at HEAD
(`git show HEAD:<path>` verified per file during the 09-16 review, and the full set was
restored into a throwaway overlay at `%LOCALAPPDATA%/Temp/melodia_overlay` for the census).

**Repair (owner sign-off required — working-tree mutation on the SSOT tree).** Restore
**deleted files only** — a bare `git restore deploy/surreal_arch` would DISCARD the two
uncommitted modifications (`melodia_house.py` opening-family work, `presets.py`). Use:

```
git ls-files -d -z -- deploy/surreal_arch Tools/verify_addon.py Tools/melodia_studio_census.py \
    Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md | xargs -0 -r git restore --
```

(`git ls-files -d` lists exactly the deleted-but-tracked files; the two modified files are
untouched. Verify after: `git status --porcelain deploy/surreal_arch/` shows only the two
` M` lines.)

Then, in order: gate → census → reinstall live (Blender closed) → record the session.
Do **not** proceed to any wave below before this.

**Not affected:** the brooch lab (`Saved/Accessories/brooch_lab` — standalone `bpy`
scripts, no addon dependency), the Sverchok fabrication lane, the UE project.

## 2. Registry today (reconstructed checkout: repo + 22 HEAD-restored files)

Measured 2026-09-16, `Saved/Audit/gn_census_2026-09-16_overlay.json`:

| Metric | Value |
|---|---|
| Builders | **568** |
| Roles | sku 450 · modifier 88 · factory 24 · pcg_alias 3 · pcg_keep 3 |
| Hidden (not in GN Stack) | 30 |
| Categories | 25 (1 without a `CATEGORY_META` label: **Garment**) |
| Duplicate-id clusters (normalized) | **7** — see F2 |
| Baseline (`Tools/registry_baseline.json`, 566 ids) | **lost 0 · new 2**: `MEL_eyewear_hero`, `MEL_mh_opening_family` |
| Monolith `build_*` functions | 276 |

**Method note (carry this forward):** the freeze doc records *three* registries that did
not agree on 09-11 (checkout 530 / live 494 / baseline 473); the gate later recorded
`registry=561 · baseline=561`. Counts are only meaningful with their base. State the base
or the number is decoration.

## 3. What landed since the 08-17 plan

- **Wave D (09-04 → 09-07)** — house + ecosystem convergence: `MEL_mh6_room_shell`
  genome authority (`melusina_house_v6.py`), ONE-ECOSYSTEM absorption, monolith overhaul
  plan, Convergence Mode (`convergence_mode.py`), registry snapshot plan
  (`MELODIA_STUDIO_FINALIZE_SNAPSHOT_PLAN_2026-09-07.md`), bbox audit (`BoundBox` realize
  gate — gate F class, still 6/6).
- **Wave E (09-11) — the freeze.** 17 live-only module sources recovered into the tracked
  tree; `ADDON_AUTHORITY_2026-09-03.md` rescued from the gitignored AppData copy;
  baseline re-cut; `SNAPSHOT_FREEZE_20260911.blend`; six hold rules; gate A–F run
  (`Saved/Audit/gate_2026-09-11.log` — A/B/C PASS lines recorded).
- **Wave F (09-12)** — garment curvature-AO fix promoted; Chladni foundry promoted
  (#184); **Trim Sheet Lab** module (`trim_sheet_lab.py` + `trimsheet_magic.py` + hybrid
  manifest pipeline, #197); **eyewear builders** (`melodia_gn/eyewear.py`; census run
  `Saved/Audit/census_eyewear.log` → 562, PASS).
- **Wave G (09-14, committed)** — audio-reactive study decor + Escher math builders:
  `audio_architecture.py` (`MEL_audio_facade`, `MEL_audio_landscape`), shared
  `add_audio_reactivity()` helper, `cute_decor.py` (14 builders), `escher_decor.py`
  (4 builders), `study_ground.py` — 26 builders, all Sound-Evaluation reactive
  (commit `2d0552c2`).
- **Adjacent, not in the addon registry** — the brooch lab: genome-driven GN v5 stack
  (5 silhouettes), materials/animation, SDF cast bake, SV fabrication cards. Its own
  authority: `Saved/Accessories/brooch_lab/BROOCH_SYSTEM_PLAN.md`.

## 4. Standing rules (the hold, restated for the next session)

The six freeze rules stand (one writer / one-way install / frozen ids update the baseline
in the same change / no duplicate-id ownership / no parallel builder for an existing
concern / every gate falsifiable and ledgered). Plus the boundaries settled since:

1. **GN owns presentation geometry.** The registry is the single builder authority — the
   discovery checklist in `ADDON_AUTHORITY_2026-09-03.md` runs before any new geometry.
2. **The lab lanes do not graduate by accident.** The brooch lab (and eyewear, while it
   lives in the registry) stays genome-driven; a lab builder graduates into
   `register_builder` only when a second consumer exists.
3. **Fabrication documents are the Sverchok lane** (`SVERCHOK_STAGE_LOG.md`). SV cards
   never leave geometry in the scene; GN is not used for DXF/nesting/SVG/G-code and SV is
   not used for presentation geometry. The brooch cast bake (SDF) is the current proof
   that this split works.
4. **Docs live in the tracked tree or they do not exist.** The 09-03 doc "was correct and
   prevented nothing" because it sat in a gitignored path. Anything future-relevant is
   written to P: in the session that learns it.

## 5. Open defect ledger

- **F0 — the tree regression (§1).** Blocking; repair with sign-off.
- **F1 — gate/census tools deleted from the worktree.** Restored with F0; then the gate
  runs again and the log path is recorded.
- **F2 — duplicate-id clusters (7 normalized).** Five v1/v2 alias pairs
  (`material_crosswalk`, `music_harp`, `music_waveform_wall`, `pcg_music_tags`,
  `pcg_water_tags` — pre-existing, listed in `verify_addon.py:KNOWN_DUPLICATES`) plus two
  new: `MEL_escher_belvedere` vs `MEL_gb_escher_belvedere`, `MEL_escher_waterfall` vs
  `MEL_gb_escher_waterfall`. Owner decision: alias (hide one, keep the id) or rename. Rule
  4 forbids leaving import order as the decider.
- **F3 — baseline drift.** 566 → 568 (two ids). Re-cut with sign-off as part of W1; the
  freeze rule says ids update the baseline in the same change — make that true again.
- **F4 — build-warning classes in the gate log** (non-fatal, but dead links are silent
  no-ops): 5.2 `Mesh Line` socket rename (`'End Location'` not found), `link_sockets`
  None-pairs in `MEL_gb_escher_*`, `MEL_garment_vertex_ao`, `MEL_legacy_*`; float-vs-
  socket link-type errors in `MEL_*_variant`/`MEL_*_siku`/`MEL_roll_walkable`. One sweep
  batch, gate re-run after.
- **F5 — leftovers from 08-17:** `FILIGREE_*` monolith rewrites · B3 v22 ornament eyeball
  (needs `MELODIA_ALLOW_STAGE_SAVE=1`) · L4 Figma icons (`icon_loader.py` no-op) ·
  PCG/LiveLink 9876 conflict · greybox snap/composer placement · AppData sync + GUI draw.
- **F6 — known-lost sources:** `castle_kit_kit.py`, `zen_kit_kit.py` exist nowhere as
  source (freeze record). Decide: recover from `__pycache__` bytecode, or formally retire
  the ids.
- **F7 — live install state:** `surreal_arch_bak` only. Reinstall after F0/F1, Blender
  closed, one-way P: → live.

## 6. Next waves (ordered, smallest safe increments)

| Wave | Content | Exit condition |
|---|---|---|
| **W0** | F0 restore → gate run → census run → F7 reinstall | gate log path recorded; census PASS vs baseline |
| **W1** | F3 baseline re-cut v2 (absorb the 2 ids + anything W0 census adds) | gate B PASS with the new baseline |
| **W2** | F2 duplicate-cluster decisions executed (alias or rename, recorded in metadata) | gate C unexpected=[] |
| **W3** | F4 warning sweep (the four classes), one batch | gate re-run, warnings counted before/after |
| **W4** | Capability decision: **SDF composite kit** — the brooch cast bake proved the 5.2 chain (`MeshToSDFGrid → SDFGridBoolean → SDFGridFillet → GridToMesh` + crumb filter). Lab-only, or `MEL_sdf_*` in the registry? | written decision; if registry, second consumer named first |
| **W5** | Graduation reviews: brooch genome → `surreal_os`-style package; eyewear module docs/wiring | written decision, no code before it |
| **W6** | F5 leftovers as one batch (FILIGREE rewrites first) | per-item gate notes |

Explicitly **not** in this plan: UE-side work, world/sky shader work, Sverchok fab-lane
changes (each has its own authority doc), and any new Set-Dressing volume (frozen).

## 7. Evidence index

- Freeze + gate: `Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md` (at HEAD),
  `Saved/Audit/gate_2026-09-11.log`, `Tools/verify_addon.py` (at HEAD).
- Authority: `deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md`.
- Today's measurements: `Saved/Audit/gn_census_2026-09-16_overlay.json` (overlay census),
  `Saved/Audit/import_chain_probe.py` (the import repro), `git status` distributions.
- Prior registries: `Saved/Audit/census_2026-09-11.log`, `census_eyewear.log`,
  `Saved/Audit/melodia_studio_census.json` (09-12), `Tools/registry_baseline.json`.
- Snapshot: `Saved/MelusinasHouse/SNAPSHOT_FREEZE_20260911.blend`
  (md5 `9d527dd96078b1534a8409250e221511`).
- Neighbour lanes: `Saved/Accessories/brooch_lab/BROOCH_SYSTEM_PLAN.md` (brooch),
  `Saved/Accessories/brooch_lab/SVERCHOK_STAGE_LOG.md` (fabrication).

*Written 2026-09-16 by the Melodia agent after a full re-read of the freeze, authority,
census and git state. Untracked — commit decision is the owner's.*
