# Melodia Studio — Finalize, Organize & Snapshot Plan

**Date:** 2026-09-07
**Precondition met:** S0 sync DONE — live AppData addon byte-identical 249/249 to P: checkout, stamped main @ 025ae175. All work below runs against a synced ecosystem.
**Law:** GIT PIPELINE LAW — no commits/branches/pushes without explicit owner approval per operation. Edits land on P: SSOT, three-copy sync, then collab/laptop/longterm PR on approval.
**Read with:** LAPTOP_SEMESTER_CAPESTONE_PLAN_2026-09-07.md, deploy/surreal_arch/Docs/ADDON_AUTHORITY_2026-09-03.md

---

## Verified state (2026-09-07, headless census against LIVE install)

- Registry: **466 builders, 22 categories, 0 no-category, 0 metadata/map mismatches.**
- Music family: **69 builders** (instruments, notation, them_* set pieces, waveform/harmonic systems).
- Monolith: `surreal_architecture_gen.py` byte-identical P:↔C:; P2 absorption at 210/276; remainder = greybox(41) + prototype/array trio(3) + 4 notation duplicates + misc.
- Snapshot machinery exists: `Tools/registry_baseline.json` (both repos).

### Defect census (found today)

| # | Defect | Evidence |
|---|---|---|
| D1 | **5 duplicate v1/v2 builder pairs**: MEL_material_crosswalk(+v2), MEL_music_harp(+v2), MEL_music_waveform_wall(+v2), MEL_pcg_music_tags(+v2), MEL_pcg_water_tags(+v2) | normalized-name census, Saved/Audit/_census_dups.py |
| D2 | **Duplicate helper defs inside core_forms_kit.py** — `_higg_load` defined at lines 19 AND 58; `_higg_node` at 79 AND 378 (P2 absorption copy-paste artifact; second def shadows first) | grep ^def |
| D3 | **Higgsas library unreachable on this laptop** — default path `G:\programs\BlenderPlugins\Higgsas...v1.3 vfxMed\...` (G: does not exist; folder name also lacks the ` vfxMed` suffix). Real library: `C:\Users\brenn\Downloads\Higgsas_Geometry_Nodes_Toolset_v1.3\Higgsas Geo Nodes Blender 5.0\Blender 5.0 Higgsas Geo Node Groups v13.blend`. Result: all 15 `_higg_node` call sites (pillar NTSpin/NTTaper, brick wall NTBricks Grid/NTSolidify, etc.) **silently fall back to primitive geometry** — the trees build but are NOT the intended Higgsas-enhanced versions. Prefs override `higgsas_library_path` exists but is unset. | capabilities.py:8, core_forms_kit.py:39, walls_kit.py |
| D4 | **6 categories missing panel labels** (`<no-meta>` in CATEGORY_META): asian, civic, experimental, melusina_house, zen_kit, + one more — they render as raw ids in the N-panel | _census_panel.py |
| D5 | Verify runner broken: smoke queue references 6 scripts that exist in no tree (carried from semester plan S0.6) | blender_smoke_queue.json |
| D6 | Higgsas library lives in Downloads — not durable, not versioned, wrong machine-locality (G: default suggests it was authored on another PC) | find |
| D7 | **9 real-error builders** (not input-dependent empties): socket-name drift — MEL_auto_bevel / MEL_curvature_bevel / MEL_weighted_bevel (`KeyError 'Angle'`), MEL_biolum_vein / MEL_fracture_seam (`KeyError 'Mesh'`), MEL_mother_hair_cascade / MEL_white_seam_spline (`KeyError 'Resolution'`), MEL_mother_moonlight_rig / MEL_shell_thorax (`NoneType has no attribute inputs` — node creation returned None, i.e. wrong node type name). 105 further "empty geometry" builders are input-dependent (known class, 43 proven by family gates). Monolith: 208/209 ok, **ZEN_PAGODA fails**. | registry_baseline.json diff, Saved/Audit/_baseline_diff.py |
| D8 | **Registry vs baseline: 0 lost / 0 new** — 466 live == 466 snapshot. No missing builders from sync drift; "missing" = the 9 broken + ungraduated workshop patterns (F-plan S2.1) + monolith remainder (greybox 41, trio 3). | _baseline_diff.py |
| D9 | **Pie-menu defects** (pie_menu.py, 358 lines): (a) room pie exposes 8 of 11 shapes — ELLIPSE/SUPERELLIPSE/FREEFORM unreachable, acknowledged dead-end comment; (b) `set_room_shape` silently falls back to `obj["melodia_room_shape"]` custom property when the enum rejects — a parallel state authority outside surreal_arch_props; (c) window pie has dead `if has_props: pass` block; (d) genome pie crams 6 axes × ± into 7 wedges (8-wedge cap — fragile, cramped); (e) context menu hard-references `surreal_arch.pie_score` owned by music_ui.py — cross-module coupling, breaks the menu if music registration fails; (f) **score pie hardcodes MEL_music_waveform_wall (the v1 of dup pair D1)** — F2 resolution to v2 silently stales the pie. | pie_menu.py:43,166,194-196,207-226,280; music_ui.py:548 |
| D10 | **Two catalog UIs, no declared owner**: ui.py Architecture Picker draws the MONOLITH's 209 arch_type ids (style groups → categories → grid); the melodia_gn package has its own N-panel catalog for the 466 builders. Same "Melodia Studio" tab, two enumeration paths, neither lists the other's inventory. Music (69) lives in the package catalog; the picker's monolith list also carries music-adjacent ids. This is the "sync builders to UI panel" root problem — it is a surface-ownership question, not a draw-loop bug. | ui.py:97-155, integration.py:497-515 |

---

## F1 — Higgsas repair (do first; unblocks honest tree inspection)

1. **Relocate the library to a durable, repo-adjacent home:** copy `Blender 5.0 Higgsas Geo Node Groups v13.blend` → `P:\MelodiaMelusinaV2-Laptop\RawArt\BlenderLibraries\Higgsas\` (RawArt is the promoted-binary area; large .blend stays OUT of git tracking — verify .gitignore or add the dir to it; LFS only if owner wants it cross-machine).
2. **Fix the path resolution in capabilities.py:** replace the single hardcoded G: default with an ordered candidate list (prefs override → P:\RawArt\BlenderLibraries\Higgsas → G:\ legacy → Downloads), first-existing wins. One-file change, no behavior change for machines where G: exists.
3. **Kill D2 in the same edit window:** delete the duplicate `_higg_load`/`_higg_node` defs in core_forms_kit.py (keep the later, more complete versions at 58/79+; verify call sites resolve identically).
4. **Gate:** headless harness that (a) asserts `higgsas_bridge.is_available()` True, (b) loads each of the 33 HIGGSAS_ARCH_NODES names from the library, (c) builds MEL_pillar + MEL_brick_wall and asserts a real `GeometryNodeGroup` node (not fallback primitive) exists in each tree. Evidence → Saved/Audit/higgsas/.
5. Three-copy sync (P: → C: → AppData), md5 3-hash.

## F2 — Duplicate & dead-tree cleanup (D1 + deeper census)

1. For each of the 5 v1/v2 pairs: diff the two builder functions, declare ONE authority (v2 unless v1 has params v2 lost), demote the loser behind the established convergence pattern (bool gate / alias) — never silent delete. Owner picks if the diff is ambiguous.
2. Extend the census beyond name-normalization: **functional duplicates** — builders whose realized output bbox+vert count match within tolerance on identical param sets (catches renamed copies the string census misses). One headless pass over all 466, JSON evidence in Saved/Audit/dup_census/.
3. Cross-check the 4 monolith music-notation originals already routed via melodia_gn_route (per P2 notes) — confirm they are demotion candidates for P5, record in ADDON_AUTHORITY.
4. Cross-check the 16 known dead builders / 8 passthrough stubs from the 2026-09-04 audit — mark role='research'/hidden rather than delete (M5 rule: deletion only in a clean owner session).

## F2b — Broken-builder repair (D7: the actual "missing builders")

Nothing was lost to sync (0 lost / 0 new vs baseline). The real gaps are 10 failures:

1. **Socket-name drift (7)** — MEL_auto_bevel / MEL_curvature_bevel / MEL_weighted_bevel ask for input `'Angle'` (Bevel node socket was renamed in 5.x — enumerate `node.inputs` and match by identifier or current name); MEL_biolum_vein / MEL_fracture_seam ask `'Mesh'`; MEL_mother_hair_cascade / MEL_white_seam_spline ask `'Resolution'` (CurvePrimitive sockets). Fix pattern: one helper `set_input_by_candidates(node, [names...], value)` in core, then 7 one-line call-site fixes.
2. **Node-type None (2)** — MEL_mother_moonlight_rig / MEL_shell_thorax: `nodes.new()` returned None → wrong bl_idname for 5.2. Identify correct type, fix, gate.
3. **Monolith ZEN_PAGODA (1)** — single failing dispatch id; diagnose via the M0 harness, fix or record as research-role.
4. Gate: re-run the full 466-builder harness; target **0 real errors** (empty-geometry input-dependent class recorded separately, not counted as fail), regenerate registry_baseline.json, diff must show only these 10 flipped ok:false→true.

## F3 — UI panel sync: music + all updated builders (D4)

1. **Add CATEGORY_META labels for the 6 `<no-meta>` categories** (Asian Kit, Civic Kit, Experimental, Melusina House, Zen Kit, + sixth) so the N-panel shows human names.
2. **Audit the 69 music builders' panel placement:** the `MEL_music_them_*` set pieces sit in set_dressing while their siblings are in music — confirm that split is intentional (structure vs notation) and record the decision in ADDON_AUTHORITY; move only what the owner says is misplaced.
3. **Panel enumeration proof:** headless-instantiate the panel draw path (or the catalog list the panel reads) and assert every one of the 466 ids appears exactly once under exactly one category — no orphans, no double-listing, no P2-kit omissions. This is the "synced to UI panel" gate.
4. GUI screenshot verification of the Melodia Studio N-panel: Music category expanded showing the full 69; one spawn click on a P2-kit builder (zen/scifi/filigree) proving the previously-missing kits are live.

## F3b — Pie menu + UI cleanup (D9, D10)

Pie review findings (pie_menu.py 358 lines + music_ui.py score pie):

Setup is sound in skeleton: Shift+Q main pie, Alt+Q room, Ctrl+Shift+Q window, Shift+Alt+Q genome, Shift+M score; keymaps idempotent-guarded; context-menu append/remove tracked; Q-alone deliberately avoided (MACHIN3tools conflict). Defects to fix:

1. **(D9a) Room pie dead-end** — ELLIPSE/SUPERELLIPSE/FREEFORM unreachable (8-wedge cap). Fix: wedge "More Shapes…" opening a sub-menu (regular menu, not pie) with the 3 advanced shapes; pies stay 8-max, sub-menus don't.
2. **(D9b) Parallel state authority** — `set_room_shape` fallback writes `obj["melodia_room_shape"]` when the enum rejects: invisible second authority, generator never reads it. Kill per working agreement: extend gb_room_shape enum to cover all 11 shapes (it was "patched in Phase B" — verify) and make the fallback report an error, not silently stash.
3. **(D9c) Dead code** — window pie `if has_props: pass` block; remove or implement the intended toggle/count row (as sub-menu per #1 pattern).
4. **(D9d) Genome pie cramp** — 6 axes × ±12 buttons in 7 wedges. Restructure: 6 wedges = one axis each (column with +/−), wedge 7 = "Presets…" sub-menu (Zen Shrine, Gothic Cloister, …), wedge 8 = Reset Genome.
5. **(D9e) Cross-module coupling** — context menu hard-references `surreal_arch.pie_score` owned by music_ui.py. Guard with `hasattr(bpy.ops.surreal_arch, "pie_score")` (or a registry check) so the object context menu can't break when music_ui registration fails.
6. **(D9f) Hardcoded dup victim** — score pie pins MEL_music_waveform_wall (v1). Repoint to the F2-declared authority; add a lint rule: pie/menu tree_name references must exist in GROUP_BUILDERS and must not be a demoted alias (assert in the F3 enumeration gate).
7. **(D10) Catalog surface ownership** — declare in ADDON_AUTHORITY: Architecture Picker (ui.py) = MONOLITH arch_type workflow surface (209 scene ids); package N-panel catalog = GN builder surface (466 ids). Then wire the seam: picker search (`search_index`) extended to include package builder ids routed through mel_gn.stack_add, so ONE search box finds both inventories — music included. No merged mega-list, no second picker.
8. Polish pass: consistent icons, "Melodia Studio" header label everywhere (branding.py product_label), no raw enum ids visible to the user (D4 labels feed this).
9. Gate: headless poll test — every operator referenced by every pie/menu exists and is registered; enumeration gate (#F3.3) extended to pie tree_names; GUI screenshot of main pie + room pie + score pie.

## F4 — Monolith organization (the remaining strangler work)

Sequenced after F1–F3 so cleanup happens on a verified, panel-synced package:

1. **M0 baseline re-run:** regenerate the 209-id dispatch baseline JSON against the now-synced trees; this is the regression floor for everything below.
2. **Greybox family (41)** — the big remainder; rides the shell convergence ladder (C2 city cell rewire → C3 music shell fold → C4 monolith routing). Desktop-side ladder decisions consume laptop-built proof; laptop does not re-implement.
3. **Prototype/array trio (3)** — belongs to the P3 dispatch rework; park with a note, don't absorb early.
4. **Opportunistic kit extraction (M4 rule):** monolith functions move into package modules only when touched by F1/F2 fixes — no bulk cuts.
5. **ADDON_AUTHORITY refresh:** every ownership decision from F1–F4 gets a row (roof roles, shell authority, Higgsas bridge ownership, dup resolutions).

## F5 — Finalize & snapshot (the long-term anchor)

1. **Registry snapshot:** regenerate `Tools/registry_baseline.json` from the live install post-F1–F4; commit via approved collab/laptop/longterm PR. Future sessions diff against it — any builder-count change without a matching approved commit = drift alarm.
2. **Version stamp:** bump addon bl_info version (branding.py reads it) to mark the finalized state, e.g. 3.0.0 "converged".
3. **Repair the verify runner (D5):** author the 6 missing smoke scripts OR (preferred, smaller) trim blender_smoke_queue.json to real scripts + add the three new gates from F1/F2/F3 as queue jobs. `verify_melodia_studio.ps1` exits 0 = snapshot certified.
4. **Nightly census cron (semester plan S4):** headless registry count + `-CheckOnly` provenance + baseline diff → Saved/Audit/ + telegram alert on drift.
5. **Snapshot record:** one dated section appended to this file — builder count, category count, gate results, HEAD, live-install stamp. That row is the "finalized Melodia Studio v3.0.0" reference for the semester and capstone.

---

## Order & effort

```
F1  Higgsas repair           ~1 session   (blocking: trees are silently degraded without it)
F2  duplicate cleanup        ~1 session   (5 pairs + functional census)
F2b broken-builder repair    ~1 session   (10 real failures → 0-error harness)
F3  panel sync + proof       ~half session (labels + enumeration gate + screenshots)
F3b pie menu + UI cleanup    ~1 session   (6 pie defects + catalog ownership seam)
F4  monolith remainder       ongoing, opportunity-driven (greybox rides C-ladder)
F5  snapshot + verify runner ~half session (after F1–F3b green)
```

## Ledger

| Gate | Status | Evidence |
|---|---|---|
| S0 live install byte-clean | **DONE 2026-09-07** | 249/249 match, stamp main@025ae175 |
| F1 Higgsas available + no silent fallback | OPEN | — |
| F1b core_forms_kit duplicate defs removed | OPEN | — |
| F2 5 dup pairs resolved + functional census | OPEN | Saved/Audit/_census_dups.py (string census done) |
| F2b 10 broken builders → 0 real errors | OPEN | registry_baseline.json (114 fail: 9 real + 105 input-dependent empties) |
| F3 466/466 panel enumeration + labels | OPEN | _census_panel.py (22 cats, 6 no-meta) |
| F3b pie defects fixed + poll gate | OPEN | pie_menu.py review 2026-09-07 |
| F3b catalog ownership declared + search seam | OPEN | — |
| F4 M0 baseline re-run | OPEN | — |
| F5 registry snapshot + verify runner 0-exit | OPEN | baseline diff 0-lost/0-new vs 466 snapshot |

---

## Snapshot record — 2026-09-07 (semester anchor)

**Melodia Studio state, certified for Fall 2026 semester start:**

- Live install: byte-identical 249/249 to P: checkout, stamped branch=main HEAD=025ae175.
- Registry: **466 builders / 22 categories / 0 uncategorized**, 0 lost vs Tools/registry_baseline.json, 0 new.
- Monolith dispatch baseline: 208/209 ok (ZEN_PAGODA open, F4).
- Known-open defect classes at snapshot time (all ledgered above, none block asset prep):
  9 real-error builders (F2b), 5 dup pairs (F2), Higgsas path unreachable on laptop (F1),
  6 no-label categories + pie/UI defects (F3/F3b), verify-runner smoke gap (F5).
- Durable census tool: `Tools/melodia_studio_census.py` — run headless any session;
  PASS = registry matches baseline (no drift). JSON evidence: `Saved/Audit/melodia_studio_census.json`.
- Music family: 69 builders registered and enumerated (see _census output in F-plan recon).

Session ritual for the semester (from LAPTOP_SEMESTER_CAPESTONE_PLAN S1):
`sync_workstation.ps1` + `install_melodia_studio.ps1 -CheckOnly` on open;
`melodia_studio_census.py` weekly or after any addon edit; three-copy sync after every edit.

**This row is the v-snapshot reference. F1–F5 execute against it; the next snapshot
record supersedes it only with a fresh census PASS + owner approval.**

