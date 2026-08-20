# Material System — Next Agent Lane Prompts (2026-08-14)

**Read first:** [`MATERIAL_SYSTEM_ORGANIZATION_HANDOFF_2026-08-14.md`](MATERIAL_SYSTEM_ORGANIZATION_HANDOFF_2026-08-14.md) — verified state, inventory, traps, working contract. This file is the paste-ready lane queue. Owner direction: **organize + expand the material system to triple-AAA.**

**Repo:** `C:\EnvironmentPortfolio\BS_GodFile` · branch `feature/repo-lockin-20260813` · remote `MelodiaMelusinaV2`.

## Hard rules (every lane)

1. **One Unreal Editor. Never launch a second.** Never trust a PID — run `Get-Process UnrealEditor` + port-9316 ping yourself. `MODAL_OPEN` in the log is a dialog, not a hang — never kill the editor for it.
2. **Never** `git clean -fd/-fdx` or `git checkout -- .` (untracked `Content/` is unrecoverable). Target only exact paths.
3. **Never clobber owner-authored instance overrides** — the policy applicator's `already_overridden` skip is a hard invariant.
4. **Never `delete_asset` anything you didn't create** without owner sign-off.
5. **Done = named evidence** under `Saved/Audit/` + a ledger note. Prose "done" is not done. Verify by re-reading (rule 9).
6. After editing any `Content/Python` script, run with `importlib.reload` (sys.modules cache trap).
7. Claim ONE lane. Editor lanes serialize through the single editor; doc/offline lanes may run alongside.

---

## Lane 1 — Protection + audit closure (editor-light, do first)

**Goal:** stop the bleed. Extend git tracking to the untracked material surface and close the audit loop.

1. `git add` exact paths: all `Content/EnvSandbox/Materials/Masters/M_Water*`, `M_Master_Nikki*`, `MF_NikkiPastelGrade/StickerShade/TwinkleIris`, `MF_Triplanar_LandscapePro`, `MF_Triplanar_SubstanceStyle`, restored `_PROJECT/04_Materials/{Landscape,Cosmo,water,SDF}/Instances`, and (optionally) curated `Instances/` folders. Verify with `git status` that nothing unintended got staged; do NOT commit unless the owner asks.
2. Extend `extract_owner_instance_profiles.py` `ROOTS` with `Instances/Landscape`, `Instances/Showcase`, `Instances/Character`, `Instances/Sakura`, `Instances/NikkiHero`, `Instances/Water` → run → `Saved/Audit/owner_instance_profiles.json`.
3. Triage the 59 zero-override maskers from `Saved/Audit/mi_runtime_audit.json`: produce a list split into *intentional defaults* vs *deletable* (owner sign-off for deletions — no `delete_asset` without it).
4. Re-export stale T3D baselines (landscape master; add Nikki + water): `EditorAssetLibrary.export_asset` does NOT exist in UE 5.8 Python — try the editor's native Export or document staleness. Do not fake it.
5. Verify nothing regressed: `audit_mi_runtime.main()` → 441/439/0-no_parent before and after.

## Lane 2 — Universal master TriplanarPro parity (editor)

**Goal:** the main master gets the substance triplanar treatment landscape + Nikki already have.

1. Read `Content/Python/expand_landscape_triplanar_pro.py` and `expand_nikki_masters.py` — port the pattern onto `M_Master_Toon_Universal`.
2. Wire the **`StaticSwitchParameter`'s own `True`/`False` pins directly** — do NOT replicate `upgrade_universal_triplanar_substance.py`'s never-applied extra-`StaticSwitch` pattern (it does not compile).
3. Reuse `MF_Triplanar_LandscapePro`; param names `TriplanarPro_*` (group `03 | Triplanar`), gate `bTriplanarPro_Active` default OFF; lerp via `TriplanarPro_BlendStrength` (default 0) so Pro OFF == current look.
4. Verify: `material_query get_compilation_stats` → `is_compiled: true`; spot-check 2–3 instances read back unchanged.

## Lane 3 — Nikki master hardening + showcase (editor)

**Goal:** make the kawaii fabric master production-clean.

1. Dedupe the two `BaseTint` VectorParameters on `M_Master_Nikki` (live one = `VectorParameter_5`; verify `_0` is unreferenced before removal).
2. Review the 3 unique MFs for edge cases (mask luminance on very dark/very light albedo; `TwinkleIris` Normal input must stay world-space).
3. Give `MI_Show_NikkiDream` + `MI_Landscape_NikkiDream` tuned kawaii overrides (pastel ramps, ShadowDreamStrength ~0.2, fabric sheen) and capture cube/plane proof.
4. Verify both masters compile after every change.

## Lane 4 — Universal overhaul Stages A–C (editor, big)

**Goal:** execute `Docs/Production/UNIVERSAL_MASTER_OVERHAUL_PLAN.md` Stages A–C.

1. Stage A: optional `bShadowGarden_Active` gate (3 live instances: SakuraGarden 0.55, PondBank 0.38, CherryBlossom 0.70).
2. Stage B: unify the 5 ramp implementations onto `MF_ColorRamp3` (add advanced ColorRamp params matching the Nikki master); single sheen; `MF_VertexPaintBlend` behind `bVertexPaintBlend_Active` (default OFF); iridescence thickness option behind a gate.
3. Stage C: parameter group audit (every param in a numbered group), instance-facing defaults (drop-on-mesh baseline with all gates off), and the "Universal Master — Instance Author's Guide".
4. Every change gated default-OFF; compile + instance diff after each stage; update the plan's shipped table + `UNIVERSAL_MASTER_NODE_REVIEW.md` ledger.

## Lane 5 — AAA presentation + proof (editor, capture-heavy)

**Goal:** predictability, proof, restraint per `MATERIAL_LAYERING_PARALLAX_NIKKI_REVIEW.md`.

1. Enforce the preferred layer order; restrict parallax to hero surfaces (cliffs, stone, trims, carved ornament — NOT grass cards, petals, shoji, distant landscape).
2. Build art-direction presets (subtle/hero/magical/cinematic) for the Nikki/Magical/FairyDust families; environment assets default to *subtle*.
3. Expand the manifest/capture pipeline (`mi_preview_manifest.py`, `build_material_render_studio_grid.py`) to Landscape/Water/Trimsheet/Sakura families; produce per-family hero swatches + a full grid; write evidence under `Saved/Screenshots/Monolith/MaterialRenderStudio/`.
4. Update `Docs/Production/Materials/` docs + `Saved/Audit/` manifests so every promoted family has visual proof.

## Lane 6 — Water roadmap study (docs + editor-read-only)

**Goal:** prepare the v11 decision. NO v11 authoring yet.

1. Read `WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md` + `WATER_V10_FINALIZATION_STATUS_2026-08-09.md` promotion gates; inventory what remains (native height/velocity replay, Data Channel consumer, PIE traversal, audio, Tier 2–4 captures, WP audit).
2. Fresh audit: is `RefractionStrength` actually connected on `M_Water_Master_Grand_v10_Upgrade` (the doc's caveat)? Record findings in `Saved/Audit/water_v11_prep.json`.
3. Write the v11 spec draft: inputs from the Substrate study line, the canonical v10 surface, and the RefractionStrength verdict. No master creation.

## Lane 7 — Docs + drift (no editor)

**Goal:** docs catch up with the shipped reality.

1. Refresh `Docs/Production/UNIVERSAL_MASTER_OVERHAUL_PLAN.md` shipped table (add Nikki masters, TriplanarPro lanes, policy v2).
2. Update `Docs/Production/Materials/UNIVERSAL_WATER_FAMILY.md` inventory table (v10 canonical note already added; extend with instance counts).
3. Cross-check `project_state.py --view staleness` and refresh anything flagged against the 2026-08-14 material state.

---

## Evidence ledger (this lane file)

| Lane | Result | Evidence |
|---|---|---|
| 2026-08-14 session | 77 MIs restored, Nikki promoted+expanded, policy v2 applied (751/399/10644), audit 441/439/0, water v10 canonical + dupe resolved | `Saved/Audit/restored_mis_manifest.json`, `instance_policy_apply.json`, `mi_runtime_audit.json`, `Docs/Handoffs/MATERIAL_SYSTEM_ORGANIZATION_HANDOFF_2026-08-14.md` |
