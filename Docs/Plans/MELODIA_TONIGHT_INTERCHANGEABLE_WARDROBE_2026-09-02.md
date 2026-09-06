# Melodia Tonight — Interchangeable Wardrobe + Shorenwake Shader Plan (2026-09-02)

**Time:** 21:59 EDT · **Editor:** `UnrealEditor-Cmd.exe` up (PID 52520), **Monolith 9316 NOT listening** → editor-bound work stays STAGED tonight.
**Painter:** down (clean, last bake done). **Blender 5.2.1** present.
**Scope (as you asked):** Houdini/Shorenwake-garment research already read; vision board built; CLO/MD reality audited; interchangeable wardrobe pipeline docs + intake sources written. This doc is the updated, thorough execution plan for tonight + first-live-window.

---

## 0. Ground truth tonight (verified)

| Asset / capability | State |
|---|---|
| `Plugins/MelodiaWardrobe/` (7 slots, 38 drafts) | **compiled/live** — the interchange engine exists |
| Universal garment master spec S0–S6 | **S0/S1/S3 DONE**, S4/S5/S6 `EDITOR-GATED`, S2 partial |
| Canonical Substance stage `CanonicalOutfit.spp` | **DONE** — 28 open sets, 93 resources, `saved: true` |
| Shorenwake/Tidepool Chladni variant | **DONE** — 2048, 9 maps + 8-frame flipbook, eigenmode lane |
| Shader vision board | **DONE** — `Saved/Audit/wardrobe_pipeline/VISION_BOARD_CanonicalShorewake.png` |
| Interchange intake candidate (Fab Dresses-for-MetaHumans) | **VERIFIED live**, not downloaded (needs Fab login/license) |
| CLO store download API | **NONE** — interactive only |
| MD drape | **GUI-only** — no script API (verified 0 .pyd/.py, empty PythonLib) |
| Monolith 9316 | **DOWN** — editor-bound materialize/ground-snap blocked tonight |

---

## 1. Execution lanes (ordered by what actually unblocks)

### Lane A — CLOSE the documented garment gates (editor-gated; drives everything)
Open when either (a) a real interactive editor opens OR (b) the `UnrealEditor-Cmd` commandlet
finishes. These are the master-spec S4/S5/S6 gates:
1. **S4 — Materialize the 14 MIs** (`10 garment layers + 4 water zones`) on the verified small
   family only. Import via Interchange / `unreal` python. **Query parent texture-param names
   first** (Toon master exposes `Albedo`, not `BaseColor`). Dry-run first. Save after each.
   Gate: `universal_garment_s4_per_garment_mi`.
2. **S5 — Live ground-snap:** fix `TraceChannel` int-vs-enum raycast bug; place Faraway Mother
   + Sea Above garments on CanonicalLandscape (raycast 50000→-50000 + 15cm re-trace + floating_check),
   never a new landscape. `universal_garment_s5_per_level_pcg_placement`.
3. **S6 — MD/Vellum drape seam:** record Vellum node presence; bind tier-B Chaos to Skirt_Full
   hero sheet; VAT bake for km terrain. `universal_garment_s6_md_drape_integration_seam`.
4. **Vocabulary gate** stays PASS (`universal_garment_vocab_check.py` must not regress).

### Lane B — INTERCHANGE PROOF (2nd-citizen intake; offline-capable once a file exists)
1. Get one downloadable dress piece onto disk: you log into Fab (or drop an FBX/OBJ into
   `Imports/`). I can drive the Fab UI if you're signed in.
2. **Blender 5.2.1 prep** (I script it): import FBX (Static Mesh) → strip/rename per
   `Cos_<Slot>_Melusina<Descriptor>` → cluster into the **10-garment-layer cadence** → export
   OBJ (Substance) + FBX (UE). Re-rig to `SK_Melusina_Skeleton` OR keep UE5 Manny/Quinn.
3. **Substance stage** (proven startup-module path): create the interchange `.spp` with the
   piece's sets OPEN + Chladni variant + AO resources. `all_saved=true` + self-deleting builder.
4. **Register** in `DA_MelodiaCosmeticCatalog` + a `Cos_` draft → runtime-swappable.
   → This is the *end-to-end interchange proof* (market → Blender → Substance → catalog → swap).

### Lane C — SHADER LOOKDEV CONTINUATION (offline-capable now)
1. **Shorenwake/Tidepool flipbook** is done (5/8 distinct frames verified). Optional: cook a
   **4K single-frame** for the hero surface (hero-gem family precedent is 2048; keep coherent).
2. **AO bake staging** is in the canonical stage; if you want a *proper* high→low geometry AO
   bake for the canonical (not just the imported bake-of-record), that is a Painter bake
   operation I drive next session — flag it.
3. **Seasonal lace** gap (P2): per-season `_Opacity.png` for Collar / Shoulder_Trim / Ornament
   on `M_Master_Toon_Universal_Alpha` — author if you want the winter lace cutout tonight.

### Lane D — HERMES SKILLS (done tonight)
Updated `melodia-universal-garment` (interchange intake + canonical staging + eigenmode variant +
vision-board builder, tools/helper refs) and `melodia-copernicus-parallax` (ShorenwakeTidepool
eigenmode lane + flipbook phase-crawl + distinct-frame verification).

---

## 2. The honest blockers tonight

| # | Blocker | Why | Unblock |
|---|---|---|---|
| 1 | **Monolith 9316 down** (only SYN_SENT, no listener) | editor is a commandlet, not interactive+MCP | Reopen a real editor with Monolith; verify `curl :9316 initialize` returns |
| 2 | **Fab download** | needs logged-in ownership/license | You sign in + claim, or drop a file in `Imports/` |
| 3 | **MD/CLO drape** | no script API | Interactive only — you drag in MD; pipeline ingests the export |
| 4 | **Vision Read** of the board | this model has no image endpoint | Human/vision LookDev pass owed (state as such) |

---

## 3. What I do next (no input needed)
- Keep Lane C offline work ready (4K variant, seasonal opacity authoring) if you want.
- When the editor's Monolith comes up, I run Lane A gates with before/after Monolith
  evidence + a `record_gate.py` row per the echo contract — prose is not a row.
- When a piece file lands in `Imports/` (or you sign into Fab), I run Lane B end-to-end.

## 4. Reference map
| Doc | Path |
|---|---|
| Interchange wardrobe pipeline | `Docs/Art/UNIVERSAL_GARMENT_INTERCHANGEABLE_WARDROBE_2026-09-02.md` |
| Canonical staging + schema | `Docs/Production/CANONICAL_SHOREWAKE_SUBSTANCE_STAGING_PIPELINE_2026-09-02.md` |
| Universal garment master spec | `Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md` |
| Wardrobe ontology | `Docs/Art/UNIVERSAL_GARMENT_WARDROBE_ONTOLOGY_2026-09-02.md` |
| Intake sources manifest | `Saved/Audit/wardrobe_pipeline/intake_sources_2026-09-02.json` |
| Vision board | `Saved/Audit/wardrobe_pipeline/VISION_BOARD_CanonicalShorewake.png` + `.json` |
| Canonical staged project | `substance_staging/CanonicalOutfit/spp/CanonicalOutfit.spp` |
| Shorenwake/Tidepool maps | `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/` |

*Generated 2026-09-02 21:59. Editor-gated items carry their echo gate ids; nothing below is prose-shipped.*