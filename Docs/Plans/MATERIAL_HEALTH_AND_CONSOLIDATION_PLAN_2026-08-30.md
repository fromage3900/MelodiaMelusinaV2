# Material Health + Project-Wide Organize/Label/Consolidate Plan

> **Status:** PLANNING — Monolith live bridge verified DOWN at audit time.
> **Date:** 2026-08-30
> **Companion skill:** `melodia-lookdev-audit` (harness inventory), `melodia-p0-orchestration` (editor serialization rules)
> **Author:** Melusina

---

## 1. Verified ground truth (read-only, done with editor open)

| Fact | Finding | Evidence |
|---|---|---|
| Editor | OPEN — `UnrealEditor.exe` PID 38996, ~7.6 GB | `tasklist` |
| Monolith plugin | `Enabled: true` in `BS_GodFile.uproject` | uproject grep |
| Monolith HTTP | **DOWN** — `/mcp` and `/health` both return HTTP 000 (connection refused) on `127.0.0.1:9316` and `localhost:9316` | curl |
| Ghost listener | PID 51260 (netstat LISTENING) is dead — no live process | `Get-Process` |
| Monolith engine-side | ALIVE and indexing (`LogMonolithIndex` processing 235→1 changes) | `Saved/Logs/BS_GodFile.log` |
| Modal-blocked | Repeated `MODAL_OPEN` warnings (`Saving packages... | 50%`, `This asset editor has no docked tabs.`) — these block the game thread and silence MCP | editor log |
| Audit tools | All `melodia_*` audits return `source: offline` / cached; `system_health` reports `monolith.reachable: false` — CORRECT, not a false negative | MCP tool output |

**Conclusion:** The editor is open and healthy; Monolith's MCP server is unreachable because it is (or was) blocked behind editor modal dialogs. Every audit below is CACHED HYPOTHESIS until Monolith answers live.

**To unblock (owner action):** dismiss any open modal in the editor (the "asset editor has no docked tabs" / "Saving packages" dialogs), confirm `GET http://localhost:9316/health` returns 200 + version. Do NOT kill the editor — that risks unsaved packages (AGENTS.md rule #8, #7).

---

## 2. Material health findings (CACHED — re-verify live)

### 2.1 Broken compile — `M_PP_MelodiaInk`
- 42 declared inputs, only 38 wired. Missing: `SceneColor`, `cR`, `cB`, `smeared` (all SceneTexture `PostProcessInput0` samples).
- UE 5.8 by-name failure mode: one unwired pin silences the whole Custom node → the material compiles but contributes nothing.
- Zero `SceneTexture` expressions exist in the graph.
- **Known fix:** `Content/Python/build_dreamprint_material.py:wire_custom_inputs(force=True)` (creates the 4 SceneTexture nodes + dynamic-UV offset chains from scratch).
- **Trap:** `_fix_ink_wiring.py` assumes SceneTextures exist → IndexErrors. Use `wire_custom_inputs(force=True)`.

### 2.2 Surface-domain blendable silently dropped
- `MI_StarryNight_VanGogh` resolves to `MD_SURFACE`; post-process blendables must be `MD_POST_PROCESS` or UE silently drops them.
- Canonical is `MI_StarryNight_Hero` (correct post-process variant).

### 2.3 Audio-reactivity gap
- `UMelodiaAudioReactivePresentationSubsystem` writes BeatPulse/Bass/Mid/Treble/BeatPhase/BeatIntensity/GlobalReactivity to `MPC_Melodia_Palette` every frame.
- No surface material reads them; only `M_PP_MelodiaInk` consumes audio and it does not compile.
- Fixing the ink compile closes the gap.

### 2.4 PPV stack drift (ZenForestTest live capture, cached)
- Actor label: `PPV_Dreamprint_Candidate` in level vs `PPV_NikkiDream` in scripts → **label mismatch**.
- Slot weights off-canonical: grade `0.18` vs canonical `0.69`; outline `0.57` vs `1.0`.
- Canonical stack (3 blendables): `MI_MelodiaInk_PortfolioHero` (1.0), `MI_MeluColorGrade_PortfolioHero` (0.69), `MI_StarryNight_Hero` (1.0).

### 2.5 PBR / texture sets (cached)
- **12 complete** sets (albedo+normal+ORM/roughness+metallic) — **NONE has a built material instance** (complete textures, nothing consuming them — a real gap).
- **93 incomplete** stems.
- Notable families: `T_Bling_Rhinestone01–15`, `T_Cathedral_*`, `T_Fabric_*`, `T_FarawayMother_*`, `T_Houdini_*`, `T_Melusina_*`, `T_Terrace_*`, `T_Trimsheet_*`, `T_ClothTrim_*`.
- Suspected duplicates / leftovers to consolidate:
  - `Melusina_sUpdatedShirt` vs `T_Melusina_UpdatedShirt` (casing/dup?)
  - `T_ClothTrim_Base4K` vs `T_Trimsheet_*`
  - `__op9p__o90`, `crystal1`, `concretetrim1` (junk stems)

---

## 3. The four workstreams, mapped to existing harnesses

### A. Organize
Build a texture/material catalog keyed by set (12 complete + 93 incomplete), group thematic families, flag junk stems.
Harnesses: `melodia_material_list_pbr`, `Tools/duplicate_assets_audit.py`, `Tools/audit_project_hygiene.py`.

### B. Label
Unify PPV actor label (`PPV_NikkiDream` everywhere), fix surface-domain blendable, standardize asset naming.
Harnesses: `Content/Python/finalize_ppv_hero_stack.py` (idempotent), `Content/Python/build_ppv_nikkidream.py`, `Content/Python/strip_ppv_color_overrides.py`, `Content/Python/finalize_ppv_for_shipping.py`.

### C. Consolidate
Dedupe material instances: `T_ClothTrim_*` vs `T_Trimsheet_*`, Rhinestone family, casing duplicates.
Harnesses: `Tools/duplicate_assets_audit.py`, `melodia_material_get_compile_stats` per candidate.

### D. Remove stubs
Empty-bodied events, dead exec islands, unreachable assets, duplicate short names.
Harnesses: `Tools/bp_sweep.py` (5 defect classes), `Tools/graph_reachability.py`, `melodia_material_get_compile_stats` for dead material branches.

### E. Material health project-wide
Per-master compile stats, the ink fix, the audio gap, the surface-domain blendable.
Harnesses: `melodia_material_get_compile_stats`, `melodia_material_audit`, `build_dreamprint_material.py`.

---

## 3.5 Offline consolidation findings (verified read-only, 2026-08-30)

Ran `Tools/duplicate_assets_audit.py` + `Tools/audit_project_hygiene.py` (both read-only, no editor).

| Metric | Value | Interpretation |
|---|---|---|
| EnvSandbox `.uasset` on disk | 9,026 | — |
| EnvSandbox `.uasset` tracked | 1,226 | ~7,800 are gitignored |
| Duplicate short names | 1,124 | Mostly `Alphas_Melodia` ↔ `Textures/Source/MelodiaGameUI` mirror + `Greybox_Kit` per-mesh `_fbm` copies |
| Byte-identical `.uasset` groups | 42 (84 rows) | **0 tracked in git** — all in ignored `_Archive`/`Candidates`/untracked territory |
| Junk folders (`_Scratch`/`_Archive`/`Candidates`) | 0 (under counted roots) | clean |
| Empty dirs / large dirs / generated | 1569 / 42 / 86 | hygiene report written |

**KEY CONTEXT:** `Content/EnvSandbox/*` is gitignored wholesale (`.gitignore:183`). So the 1,124 dup names and 42 byte-identical groups are **disk-space / workspace cleanliness issues in ignored content — NOT repo bloat.** The only tracked live duplicate found is `Purple_Nebula_7` under `Content/Melodia/_PROJECT/04_Materials/Textures/sbs_-_.../`.

**Consolidation actions (require owner decision — none executed):**
- Byte-identical archive mirrors (`_Archive`/`Candidates` ≈ 58+5 files, ~4 MB): safe to delete for disk, but they are the safety net. Reclaim only if the live copy is verified referenced.
- `Alphas_Melodia` (13) vs `Textures/Source/MelodiaGameUI` (32) mirror family: consolidate to one location.
- `Greybox_Kit` per-mesh `_fbm` texture copies: the base textures already exist at the kit root — the per-mesh copies are redundant.
- `Purple_Nebula_7` tracked dupe: dedupe to one tracked path.

Ledger: `Saved/Audit/duplicate_assets_consolidation_ledger.json`.

---

## 4. Safety rules (binding, AGENTS.md + skill)

1. One editor instance; serialise all editor mutations through Monolith.
2. Do NOT kill the editor or dismiss modals blindly — unsaved-package hazard.
3. Never hand-edit `.uasset`; all material/PPV mutation via editor Python/Monolith.
4. Never call `load_blueprint_class()`/`get_default_object()` on skill Blueprints (`D_DamageType` fatal crash) — use Monolith reflection.
5. `delete_asset` only on assets you created; never on anything you didn't.
6. Existing harnesses win over new scripts — search before writing.
7. Do not add new GN builders/presets without explicit direction — organize/document existing only.

---

## 5. Execution sequence

### Phase 0 — Unblock live Monolith (owner)
1. Dismiss any open modal in the editor.
2. Confirm `GET http://localhost:9316/health` → 200 + `version`.
3. Re-run `melodia_system_health` → expect `monolith.reachable: true`.

### Phase 1 — Live audit sweep (read-only, safe)
Run, in one batch, all pointing at live Monolith:
- `melodia_material_audit` (live)
- `melodia_material_list_pbr` (disk)
- `melodia_ppv_report` (live)
- `melodia_material_get_compile_stats` on the 4 masters + ink
- `Tools/bp_sweep.py`, `Tools/duplicate_assets_audit.py`, `Tools/graph_reachability.py`
Produce one consolidated JSON report → `Saved/Audit/material_health_live_2026-08-30.json`.

### Phase 2 — Report & prioritize (owner review)
Ranked list: broken compile > silent PP drop > audio gap > PPV label/weight > dedup > stubs.
Owner picks what to touch. Nothing fixed without sign-off.

### Phase 3 — Fix pass (after owner picks)
- Wire ink: `wire_custom_inputs(force=True)`.
- Swap `MI_StarryNight_VanGogh` → `MI_StarryNight_Hero`.
- Apply canonical PPV stack + fix label: `finalize_ppv_hero_stack.py`.
- Consolidate confirmed duplicates; remove confirmed stubs.

### Phase 4 — Verify
Re-run the live audit sweep; confirm all compile stats green and PPV state matches canonical.

---

## 6. Deliverables
- Consolidated live health report (JSON + markdown summary).
- PBR/texture catalog (sets, families, dupes, junk).
- PPV canonical-state audit + fix log.
- Stub/duplicate removal list with `bp_live_path`/reachability proof.
- Updated docs + ledger rows for any gate touched.

---

## 7. One thing to do first
**Phase 0.** Every item above is a hypothesis until `GET http://localhost:9316/health` returns live. Dismiss the modal, confirm health, then re-run the audit sweep. Do not plan fixes on the cached data as if it were truth.
