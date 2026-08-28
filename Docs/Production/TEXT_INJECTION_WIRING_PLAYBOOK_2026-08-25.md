# Text-Injection Wiring Playbook (2026-08-25)

Canonical reference for repeatable material/text injection wiring in BS_GodFile (UE 5.8).
All paths relative to `C:\EnvironmentPortfolio\BS_GodFile` unless noted. No claim below is
believed without the cited file + line.

---

## 1. Injector Inventory

Three injector families exist. They are not interchangeable.

| | **Guarded manifest injector** (`Tools/water_v10_text_injector.py`) | **wire_\* family** (`Content/Python/wire_*.py`) | **T3D curve injector** (`Tools/_Archive/T3D_20260818/t3d_material_curve_injector.py`) |
|---|---|---|---|
| Entry point | `water_v10_validate()` / `water_v10_set_profile()` / `water_v10_set_material_instance()` / `water_v10_report()` (lines 125, 176, 197, 250), run via `exec(open(...).read())` inside the editor (docstring lines 8–11) | Per-feature scripts run top-to-bottom with `exec()`, e.g. `wire_audio_material_pulsation.py:main()` (line 228), `wire_fabric_type.py`, `wire_face_sdf.py`, `wire_gemstone_lane.py`, `wire_audio_water_modulation.py` | CLI: `python t3d_material_curve_injector.py --spec specs/toon_profiles/tp_melusina.json`; class API `T3DMaterialCurveInjector.apply_toon_profile_spec(spec)` (line 269) |
| Safety model | Strongest. `_assert_project_write_path` rejects non-`/Game/` or dotted paths (104–106); dry-run default, mutation requires `apply=True` (13, 176, 189–190); strict per-property allowlists + range validation for scalars/bools/colors/asset refs (31–91, 146–171); manifest existence check (94–97); save refusal raises (192–193, 238–239) | Medium. Idempotent node matching by description / parameter_name and skip-if-present (e.g. `wire_fabric_type.py:14–15`, `wire_gemstone_lane.py:7–8`); default-value-safe gates so strength=0 is visually identical to pre-wire state (`wire_fabric_type.py:10–12`, `wire_face_sdf.py:10–16`); F12/F11 scripts simulate math standalone before touching the editor (`wire_audio_material_pulsation.py:113–147`) and write an audit report to `Saved/Audit/` (line 42, 276–278). **No dry-run mode, no write-path assertion** | Weakest. Dual dispatch MI vs master/profile: `material_query:set_instance_parameter` for MIs vs `editor_query:run_python` generated code blobs for profiles (`_mi_set` 165–172, `_tp_set_*` 174–212); no path guard, no range checks, save without dirty check (130, 181); success detection by string match `"SUCCESS"` in stdout (134) |
| Best use case | Setting whitelisted scalar/vector parameters on Water v10 MIs and profile fields — any repeatable value-only polish pass | Authoring new graph topology on a Substrate master (new HLSL nodes, gates, lerps) where idempotency matters more than a spec file | Batch-applying an authored toon-profile spec (curves + scalars + colors + textures) from JSON, including reading curves back via T3D export (`read_curve_from_asset` 34–47 via `project_query export_asset_text`) |
| Authority note | Documented as "the guarded bridge" at `Docs/WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md:98–100`: validates assets, rejects unknown names, writes only project-owned instances/profiles, never mutates opaque graphs or engine content | The canonical master is `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` (`wire_fabric_type.py:22`, `wire_audio_material_pulsation.py:41`); MPC collection `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` (`wire_audio_material_pulsation.py:40`) | Lives under `Tools/_Archive/T3D_20260818/` — archived but still the only tool that parses/writes `RuntimeCurveLinearColor` keys programmatically (`_parse_color_curve` 49–103, `write_curve_to_asset` 105–134) |

---

## 2. Decision Table

One recommended tool per task type. If your task isn't here, extend an existing tool — do not
start a fourth family.

| Task type | Use | Why |
|---|---|---|
| Set a scalar/vector on an existing material instance | `water_v10_text_injector.water_v10_set_material_instance(...)` (`Tools/water_v10_text_injector.py:197–247`) | Only injector with allowlisted parameter names (67–91), numeric/range guards (218–228), `apply=True` dry-run default, and save-refusal detection (238–239). For Water v10 MIs this is also the documented contract (WATER_V10 doc line 100). For non-water MIs, copy its pattern into a sibling guarded module rather than reaching for the unguarded tools |
| Author a master-material variant curve (RuntimeCurveLinearColor on a toon profile) | `T3DMaterialCurveInjector.write_curve_to_asset` / `read_curve_from_asset` (`t3d_material_curve_injector.py:105–134`, `34–47`) | The wire_\* family does not touch curve keys; this is the only code that reconstructs RGBA channel keys from T3D text (49–103) and round-trips them. Always `--read-curve` after writing to confirm the keys landed |
| Wire an MPC collection parameter into a master graph | `wire_toon_master_material` pattern from `Content/Python/wire_audio_material_pulsation.py:153–225` | Graph topology change (new `MaterialExpressionCollectionParameter` nodes bound to `MPC_Melodia_Palette`), which the guarded injector forbids by design (docstring lines 4–6). Copy its idempotent locate-or-create loop (176–213) and recompile+save tail (215–216). Same proven shape exists in `wire_audio_water_modulation.py` for water masters |
| Apply a batch toon profile spec (curves + scalars + colors + textures from one JSON) | `T3DMaterialCurveInjector.apply_toon_profile_spec` (`t3d_material_curve_injector.py:269–297`) | Purpose-built dispatcher over the four value types with per-key ok/error reporting (275–296); demo harness `t3d_material_inject_demo.py --read/--verify/--all` (AGENTS.md core-tools table) covers read-back verification |

---

## 3. Safety Contract

Every new injector must copy all five items before merge. Reference implementation:
`Tools/water_v10_text_injector.py`.

1. **Write-path assertion.** Reject anything not starting `/Game/` and reject dotted paths
   (object suffixes): `_assert_project_write_path` (104–106). Never write engine plugin content.
2. **Dry-run default.** Every mutating entry point takes `*, apply: bool = False` and returns a
   `{"dry_run": true, ...}` payload when unset (13, 189–190, 241–247). Validation entry points
   are strictly read-only (125–143).
3. **Range/type guards before any write.** Whitelist property names and validate value ranges,
   types, RGBA arity, and asset-reference existence *before* calling `set_editor_property`
   (`_set_profile_property` 146–173; scalar pre-checks 218–228). Unknown name → hard error, never
   a silent skip (171, 213–216).
4. **Manifest/spec validation up front.** Fail fast if the driving manifest is missing
   (`_load_manifest` 94–97) and validate every referenced asset exists before mutating anything
   (`water_v10_validate` 125–143).
5. **Save verification.** Save with `only_if_is_dirty=True` and raise if the editor refuses
   (192–193, 238–239); then confirm externally via `list_dirty_packages` — AGENTS.md safe-working
   rule 9: "`save_asset` returned inconclusive at least once; confirm via `list_dirty_packages`."
   A `success: true` return means only that nothing threw.

Additional standing rules inherited from AGENTS.md that apply to every injection session:
one editor instance (rule 7); verify by re-reading after save (rule 9); never touch
`Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python (fatal enum-glue crash, see §5);
never `delete_asset` on assets you did not create.

---

## 4. Echo Pipeline Integration

Stage list per `specs/echo_pipeline.json:7–145`: author → spec_validate → monolith_static →
compile → runtime_gates → orchestra → record → promote. Runner face: `Tools/echo_run.py`
(`list`, `status`, `run static_gates`, `validate-spec <file>`, `record <gate-id> pass|fail`).

Where each injector sits:

| Stage | Injector activity |
|---|---|
| **author** | Spec authored as JSON (toon profile spec, water manifest edit, wire script constants). Producers are agents; nothing assumed until scored (echo_pipeline.json stage `author`). |
| **spec_validate** | `python Tools/echo_run.py validate-spec <file>`. For water work, `water_v10_validate()` (injector lines 125–143) doubles as asset-existence validation of every manifest-referenced path before any write. |
| **inject** | The injector runs here, dry-run first, then `apply=True`. wire_\* scripts additionally self-simulate their math offline before editor contact (`wire_audio_material_pulsation.py:113–147`) and emit audit JSON to `Saved/Audit/` as inject-stage evidence (253–278). |
| **compile** | Material side: `material_query recompile_material` + `get_compilation_stats` (`t3d_material_curve_injector.py:218–230`); wire_\* masters call `mel.recompile_material` inline (`wire_audio_material_pulsation.py:215`). Blueprint side: `blueprint_query compile_blueprint`, contract "0 errors" (echo_pipeline.json `compile` stage). |
| **fingerprint** | Quality gate `graph_fingerprint: exact_match` (echo_pipeline.json:170–177); baselines tracked at `Docs/T3D_Baseline/bp_fingerprints.json` per AGENTS.md rule 12. Any injector that touches graph topology must be followed by a fingerprint diff before record. |
| **record → promote** | Nothing is believed without a ledger row: `record_gate.py <gate-id> pass|fail` (AGENTS.md evidence standard #1; echo_pipeline.json `record` stage, 131–137). Promote updates fingerprints/catalogs (138–144). |

Gates that must pass before `record_gate.py` writes a `pass` row for an injection task:

1. Dry-run output reviewed and matches intent.
2. Asset-existence validation green (`water_v10_validate().ok == true` or equivalent).
3. Recompile stats show 0 errors (compile_and_verify, t3d injector 218–230).
4. Save confirmed via `list_dirty_packages` emptying for the target package (AGENTS.md rule 9).
5. Read-back equality: curve re-read (`read_curve_from_asset`) or instance-param re-read
   (`get_instance_parameters`, 232–242) matches the spec.
6. Fingerprint unchanged (value-only edits) or baseline updated deliberately (topology edits).

Probe-injected calls are not play evidence (AGENTS.md evidence standard #2); a Python-only green
run records as bounded evidence at best.

---

## 5. Anti-Patterns

Known failure modes. Each reached main once; none may be reintroduced.

1. **Spaced-vs-dotted node titles.** Node instance titles are spaced ("Unit Has Enough MP") while
   identifiers are dotted (`UnitHasEnoughMP`). A substring search on one form missed a live macro
   and produced a confidently wrong "this macro is never called" conclusion (AGENTS.md rule 10).
   Search both forms in every injector matcher.
2. **Pin-name mismatches causing silent no-op.** Wrong pin/parameter names fail by returning
   nothing — travel via allowlist, `StartSession` on an unregistered skill, unallowlisted Quill
   ids (AGENTS.md defect class "Silent no-op"). In material wiring the same trap is literal-chain
   semantics: `wire_face_sdf.py:12–16` documents a lerp wired per the literal spec that outputs
   black at Strength=0, violating the default-identical invariant; the fix was rewiring base ×
   gate instead. Verify by re-reading the graph after wiring, not by trusting the return value.
   Related: `manage_sublevel` takes actor names not labels, and a silent no-op and a silent
   wrong-target move look identical from the return value (AGENTS.md rule 23).
3. **Redirectors from import-over-existing-path.** FBX import into a path that already holds an
   asset creates a redirector over it; rolling back by deleting the folder leaves a dead
   redirector pointing at nothing (AGENTS.md NEVER-RUN table, row 4). Diagnose with
   `unreal.load_package`, which returns the package actually resolved to (disappearance
   checklist step 4).
4. **`delete_asset` in-session ghosts.** Deleting tells the running registry to forget an object;
   disk stays valid while `load_asset` returns False — indistinguishable from corruption
   (AGENTS.md NEVER-RUN table row 3). Recovery order: filesystem scan → forced rescan
   (`scan_paths_synchronous ... force_rescan=True`) → compare `does_asset_exist` vs `load_asset`
   → redirector check → only then backups (checklist steps 1–5). Never delete during diagnosis.
5. **Python glue crash on Skills-folder enums.** Calling `load_blueprint_class()` /
   `get_default_object()` on any Blueprint under
   `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` forces UE to generate Python glue for the
   user-defined enum `D_DamageType` → fatal `PyWrapperTypeRegistry.cpp:2641`, instant unrecoverable
   editor death taking unsaved packages (AGENTS.md "Python + skill Blueprints = instant editor
   death"). Use Monolith's C++ `blueprint_query` route (`get_cdo_properties`, `get_graph_data`,
   `export_graph`) instead. Root cause unfixed.
6. **(Bonus, same class)** Census/dump methods prove presence, never absence: a full string dump
   concluded `StockSkillRhythmIds` didn't exist while it did (AGENTS.md rule 20). Establish
   absence via reflection (`get_cdo_properties`), never a text search of the asset.

---

## Quick Recipes

Run inside the single live editor via Monolith `editor_query run_python` unless noted.
Dry-run first, always.

### R1 — Set scalars/vectors on a Water v10 material instance (guarded)

```python
exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/water_v10_text_injector.py").read())
print(water_v10_validate())                      # must be ok:true first
print(water_v10_set_material_instance(
    "/Game/MelodiaIntegration/Water/Materials/MI_Water_v10_Shallow",
    scalar_parameters={"ToonLightBands": 4.0, "SurfaceRoughness": 0.35},
    vector_parameters={"ToonHighlightTint": [1.0, 0.95, 0.85, 1.0]},
))                                                # dry-run
print(water_v10_set_material_instance(
    "/Game/MelodiaIntegration/Water/Materials/MI_Water_v10_Shallow",
    scalar_parameters={"ToonLightBands": 4.0},
    apply=True,
))
```
Then confirm `list_dirty_packages` is clean for the package (Safety Contract item 5).

### R2 — Set whitelisted profile fields

```python
print(water_v10_set_profile(
    {"ToonShadowSoftness": 0.45, "bUseSubstrateToonLayer": True, "ToonProfileId": "water_v10_default"},
))                                                # dry-run review
print(water_v10_set_profile(
    {"ToonShadowSoftness": 0.45}, apply=True,
))
```

### R3 — Apply a batch toon-profile spec from JSON (curves + scalars + colors + textures)

```powershell
# From repo root, editor live on port 9316:
python Tools/_Archive/T3D_20260818/t3d_material_curve_injector.py `
  --asset /Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default `
  --spec specs/toon_profiles/tp_melusina.json
# Read-back verification (mandatory):
python Tools/_Archive/T3D_20260818/t3d_material_curve_injector.py `
  --asset /Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default `
  --read-curve DiffuseRamp --compile
```

### R4 — Wire MPC audio-collection params into a master graph (F12 shape)

```python
# Inside the editor (Monolith run_python); idempotent — safe to rerun.
import importlib.util
spec = importlib.util.spec_from_file_location(
    "wire_f12", r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/wire_audio_material_pulsation.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# Offline math simulation prints invariants before touching the editor:
m.main()
# Graph wiring only (no full report):
result = m.wire_toon_master_material(m.TOON_MASTER_PATH)
print(result)   # expect status "wired_and_compiled", all *_present True
```
Follow with `material_query get_compilation_stats` on the master and a fingerprint diff before
recording any gate.

---

*Sources read: `Tools/water_v10_text_injector.py`; `Content/Python/wire_audio_material_pulsation.py`,
`wire_fabric_type.py`, `wire_face_sdf.py`, `wire_gemstone_lane.py`, `wire_audio_water_modulation.py`;
`Tools/_Archive/T3D_20260818/t3d_material_curve_injector.py`; `AGENTS.md` (T3D Wiring Pipeline +
defect classes); `specs/echo_pipeline.json` (+ `Tools/echo_run.py` command surface per AGENTS.md);
`Docs/WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md` §Text injection pipeline.*
