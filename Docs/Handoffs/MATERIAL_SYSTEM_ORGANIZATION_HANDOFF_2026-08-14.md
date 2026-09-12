# Material System Organization — Handoff (2026-08-14)

**Scope: material system cohesion, expansion, and AAA readiness.** The owner wants the
material library organized, expanded, and pushed to triple-AAA presentation quality.
Trust this file over older material docs where they conflict — see §2 "verified state".

**Pick up:** `Saved/Audit/mi_runtime_audit.json` · `Saved/Audit/instance_policy_apply.json` ·
`Saved/Audit/restored_mis_manifest.json` · `specs/instance_parameter_policy.json` ·
`Docs/Production/UNIVERSAL_MASTER_OVERHAUL_PLAN.md` ·
`Docs/Production/Materials/MATERIAL_LAYERING_PARALLAX_NIKKI_REVIEW.md` ·
`Docs/Production/Materials/UNIVERSAL_WATER_FAMILY.md`.

---

## 1. What landed 2026-08-14 (this session)

| Item | State |
|---|---|
| Missing MIs restored | **77/77** from git history + local LFS store (`Tools/restore_missing_instances.py` — LFS-aware). All registered, parent-verified, saved. Manifest: `Saved/Audit/restored_mis_manifest.json`. |
| Parent repair | 8 restored SDF MIs → `M_Master_Toon_Universal`; `MI_SakuraLandscape` → landscape master. |
| **Nikki masters promoted + expanded** | `M_Master_Nikki` + `M_Master_Nikki_Landscape` promoted `_Scratch` → `Masters/`. 3 **unique** functions: `MF_NikkiPastelGrade` (ON), `MF_NikkiStickerShade` (OFF), `MF_NikkiTwinkleIris` (ON). Substance triplanar Pro lane (reuses `MF_Triplanar_LandscapePro`), ShadowDream family, `bKawaiiSquish_Active` WPO, kawaii defaults (BaseTint cream, EmissiveFloor 0.18). Both compile clean (153/173 exprs). Instances: `MI_Show_NikkiDream`, `MI_Landscape_NikkiDream`. |
| Landscape Triplanar Pro (earlier) | `M_Master_Toon_Landscape_HeightBlend` has the substance-style lane: `bTriplanarPro_Active` + 9 `TriplanarPro_*` params, group `03 | Triplanar`, compiled. |
| Policy v2 + cute sweep | `specs/instance_parameter_policy.json` v2 (MPC_Melodia_Palette-sourced palettes: Melusina_Lavender/Aqua/RoseGold/SoftWhite + MeluPrimary/Secondary/Accent). Applicator upgraded: first-match-wins + static-switch rules. Applied: **751 scanned / 399 changed / 10,644 params**; owner overrides never clobbered; grounded against parent's live param list. |
| Audit state | **441 instances, 439 ok, 0 no_parent, 59 zero-override, 24 "dups"** (all false positives: package-vs-object same path). `MI_WaterV10_NativeDefault` allowlisted as `ok_intentional_mi_parent`. |
| Water canonical | **`M_Water_Master_Grand_v10_Upgrade`** = canonical v10 (additive V9 upgrade, compile-verified). `v10_Substrate` = study line (gates open). `MI_Water_v10_BiolumGrotto` reparented → v10_Upgrade. Duplicate `MI_IridescentRock` resolved (single copy at `Masters/`, loser removed — zero referencers). Docs updated. |
| Editor | Restarted mid-session (old process died; new one healthy). **Never trust a PID — verify with `Get-Process UnrealEditor` + port 9316 ping before editor work.** |

---

## 2. Material system inventory (current)

**Masters (production `EnvSandbox/Materials/Masters/`):**
- `M_Master_Toon_Universal` — the big generalist (~105+ MIs), tracked in git.
- `M_Master_Toon_Landscape_HeightBlend` — painted-layer landscape master + TriplanarPro lane, tracked.
- `M_Master_Nikki` / `M_Master_Nikki_Landscape` — the kawaii fabric masters, **untracked** (promoted today).
- Water: `M_Water_Master_Grand_v6/v7/v9/v10_Upgrade/v10_Substrate` + post/underwater variants, **untracked**.
- SDF family: `M_SDF_*`, `M_Master_SDF_Toon`, `M_Toon_SDF*` — SDF MIs parent mostly to `M_Master_Toon_Universal`.

**Functions (`EnvSandbox/Materials/Functions/`):** `MF_Triplanar_LandscapePro` (substance projection, shared by landscape + Nikki), `MF_NikkiPastelGrade/StickerShade/TwinkleIris` (Nikki-only), `MF_ColorRamp3`, `MF_IridescenceSheen`, `MF_NikkiDreamGrade/RimGlow/Sparkle/IridescenceSheen` (shared), `MF_LandscapeHeightCompete`, `MF_NormalAdjust`.

**Instances (~441 curated):** `Instances/` (Environment+families, Landscape, Showcase, Character, Sakura, NikkiHero, NikkiIntegrated, MelodyTokens, Water, Melusina, Grotto…), `SDF/Instances/` (124), `Impressionist/Instances`, `_PROJECT/04_Materials/` (restored Cosmo/water/Landscape-Instances/SDF), `VFX/Materials`.

**Git tracking status (critical):** only the "toon spine" (121 masters + 18 profiles, `68521ae3`) is tracked. **All instances, all water masters, and the new Nikki assets are UNTRACKED.** A `git clean`-class accident destroys them irrecoverably (restore tool helps only for the 77 that were ever tracked).

---

## 3. Remaining work — recommended order

### P0 — Protect + finish the audit loop
1. **Extend git tracking**: water masters (`M_Water*`), curated instance folders, new Nikki masters + 3 functions, restored `_PROJECT` instances. Prefer additive `git add` of exact paths (never `git clean` / `git checkout -- .`).
2. **Run `extract_owner_instance_profiles.py`** (extend `ROOTS` with recently-edited folders first) → produces `Saved/Audit/owner_instance_profiles.json`, the policy-v2 specimen that was never generated.
3. **Zero-override maskers (59)**: audit each — intentional defaults vs deletable; owner sign-off before deletion.
4. **Re-export stale T3D baselines** (landscape master is stale; Nikki + water have none). `EditorAssetLibrary.export_asset` does NOT exist in UE 5.8 Python — use the editor's native export or document staleness (docs are "UNVERIFIED, not wrong" until refreshed).

### P1 — Parity + expansion
5. **Universal master TriplanarPro parity**: the main master lacks the substance lane (landscape + Nikki have it). Port the pattern from `expand_nikki_masters.py` / `expand_landscape_triplanar_pro.py`: `bTriplanarPro_Active` (default OFF) + `TriplanarPro_*` params reusing `MF_Triplanar_LandscapePro`, spliced at the BaseColor tail. **Trap:** `upgrade_universal_triplanar_substance.py` was NEVER applied live — its gate pattern (extra `StaticSwitch` node driving `StaticSwitchParameter.Value`) does not compile; wire the `StaticSwitchParameter`'s own `True`/`False` pins directly.
6. **Universal master overhaul Stages A–E** (`UNIVERSAL_MASTER_OVERHAUL_PLAN.md`):
   - Stage A: optional `bShadowGarden_Active` gate (3 live instances).
   - Stage B: unify the 5 ramp implementations onto `MF_ColorRamp3`; single sheen (consolidate); `MF_VertexPaintBlend` behind a gate; iridescence thickness option.
   - Stage C: param-group stragglers; "Universal Master — Instance Author's Guide" doc.
   - Stage D: out-of-range override sweep (mostly done by policy v2 — verify via audit report).
   - Stage E: Melodia art-style integration (ink/impasto/SDF-layer options) — only if owner requests.
7. **Melodia SDF conversion track**: `VinylGroove`, `Facade_Baroque`, `CelestialStarMap` substrate ports + `M_SDF_ParallaxPulse` fix (from the overhaul plan §Missed tasks).
8. **Nikki master follow-ups**: dedupe the two `BaseTint` VectorParameters on `M_Master_Nikki` (tintmul uses `VectorParameter_5`; `_0` is dead weight — verify before removing).

### P2 — AAA presentation
9. Follow `MATERIAL_LAYERING_PARALLAX_NIKKI_REVIEW.md`: **predictability, proof, restraint**. Enforce the preferred layer order (base → normal/height → macro/triplanar → wear/wetness → style grade → emissive → distance fade). Restrict parallax to hero surfaces. Nikki/Magical/FairyDust as art-direction presets (subtle/hero/magical/cinematic), **default subtle for environment assets**.
10. **Visual proof**: capture material grids + per-family hero swatches (the existing capture tooling: `build_material_render_studio_grid.py`, `mi_preview_manifest.py`) before claiming portfolio-ready; expand manifest coverage to Landscape/Water/Trimsheet/Sakura families.

### P3 — Water roadmap (owner: "UE water on the roadmap")
11. v11 = next-gen water master, **only after** the native-integration promotion gates close (`WATER_V10_FINALIZATION_STATUS_2026-08-09.md` §Remaining promotion gates: native height/velocity replay, Data Channel consumer, PIE traversal, audio activation, Tier 2–4 captures, packaged WP audit; plus the `RefractionStrength` fresh-connection audit flagged in `UNIVERSAL_WATER_FAMILY.md`). The `v10_Substrate` study line + `WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md` are the starting point.

---

## 4. Working contract (must-read before editor work)

- **One editor instance, always.** `Get-Process UnrealEditor` → exactly one; port 9316 listening. `MODAL_OPEN` in the log = dialog blocking the game thread, NOT a hang — never kill the editor for it (it costs every unsaved package).
- **Run scripts in the editor** via Monolith `run_python` with `{"action":"run_python","command":<code>}` (HTTP JSON-RPC at `http://127.0.0.1:9316/mcp`; client: `Content/Python/monolith_mcp_client.py`). Plain `Tools/` scripts run shell-side, no `unreal` import.
- **Module cache trap:** the editor caches imported modules in `sys.modules`. After editing a `Content/Python` script, run with `import importlib, <mod> as m; importlib.reload(m); m.main()` — otherwise you execute stale code (hit twice this session).
- **Verify by re-reading** (AGENTS.md rule 9): `success:true` ≠ done; re-read values via reflection; check `list_dirty_packages` after saves; only save the assets you own.
- **Never clobber owner overrides** — the policy applicator skips `already_overridden`; keep that invariant in any new instance pass.
- **Grounding rule:** never set an instance param that doesn't provably exist on the parent master — match substrings against the parent's live parameter list.

## 5. Traps learned this session

1. **`StaticSwitchParameter` (and `StaticBoolParameter`) need their own `True`/`False` pins wired** — the old "drive a separate `StaticSwitch` node's Value" pattern does NOT compile ("Missing A/B input"). `StaticBoolParameter` has no selectable pins at all — use `StaticSwitchParameter` for gates.
2. **UE Python wrappers are not `is`-equal** for the same native node — compare by `get_name()` or by a node's input's `parameter_name`, never `is`.
3. **Duplicate parameter names exist on masters** (two `BaseTint` on Nikki; the audit lists `bUsePaintedLayers` ×4) — locate nodes by their role/wiring, not by "the" parameter with a name.
4. **LFS restore:** tracked `.uasset` blobs may be 130-byte LFS pointers; real content lives in `.git/lfs/objects/<oid-shard>/<oid>` (all 77 were present locally — `Tools/restore_missing_instances.py` handles this now).
5. **Dead duplicate MF calls** exist on promoted masters (two `MF_IridescenceSheen` calls on `M_Master_Nikki_Landscape`, one unwired) — pick the live call by "has wired `BaseColorIn`", and re-check compiles after any surgery (`material_query get_compilation_stats`).
6. **`EditorAssetLibrary.export_asset` and `AssetTools.rename_asset` don't exist / don't persist redirectors** in this UE 5.8 Python binding — use `EditorAssetLibrary.rename_asset` and verify the redirector on disk; plan around it.
7. **Never** `git clean -fd/-fdx`, `git checkout -- .`, or `delete_asset` on anything you didn't create — the project has no recoverable copy of untracked `Content/` (AGENTS.md).

## 6. Key commands

```
# editor health
Get-Process UnrealEditor ; Test-NetConnection 127.0.0.1 -Port 9316

# run an editor script (reload-aware)
python -c "import sys; sys.path.insert(0, r'C:\EnvironmentPortfolio\BS_GodFile\Content\Python'); \
import monolith_mcp_client as m; \
print(m.call_tool('editor_query', {'action':'run_python','command':'import importlib, <mod> as x; importlib.reload(x); x.main()'})['content'][0]['text'])"

# audits / passes (editor-side)
import audit_mi_runtime ; import apply_instance_parameter_policy ; import extract_owner_instance_profiles
import expand_nikki_masters ; import expand_landscape_triplanar_pro   # (idempotent, tag-cleaning)

# compile check
material_query {action: get_compilation_stats, asset_path: <path>}   # is_compiled + compile_errors

# restore (shell-side)
python Tools/restore_missing_instances.py
```
