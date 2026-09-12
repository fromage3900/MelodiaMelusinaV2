# Handoff — Material Surface Git Protection + Audit Closure (2026-08-15)

**Pick up:** `.gitignore` (staged) · `Content/Python/extract_owner_instance_profiles.py` (ROOTS extended) ·
`Saved/Audit/owner_instance_profiles.json` (new) ·
`Saved/Portfolio/Materials/material_family_manifest.json` + `Saved/Portfolio/MaterialPreviews/previews_manifest.json` (regenerated).

**Branch note:** HEAD moved under this session — another agent committed the previously
pre-staged MelodiaIntegration BP kit (`df311872`, 13:32) plus docs/scripts/quarantine
batches (`65813cd5`…`3a3f16a5`, 13:35–13:36). The work below is staged **on top of** that
new HEAD; nothing was committed by this session (owner rule: no commit unless asked).

---

## What landed

### 1. Git protection — the untracked material surface is now staged (825 files)

**Root cause found:** the 08-14 "untracked surface" warning was only half-true — all 112
Masters + 18 ToonProfiles were already tracked via `.gitignore` negations (lines 175–180).
The real gap was **everything else**: Functions (78), Instances (507), SDF/Instances (173),
Impressionist (6), VFX/Materials (29), Textures/Utility neutral maps (5), restored
`_PROJECT/04_Materials/{Cosmo,Landscape,water}` (24), and the two restored `MI_ToonLayer`
copies — all silently ignored by `Content/*` + `Content/EnvSandbox/Materials/*`.

**Fix:** extended `.gitignore` with a "Curated material surface" negation block (lines
182–235). Each directory level is re-included before its children (`Content/*` excludes the
parents; git will not descend into an excluded dir). Scope decisions:

| Protected | Count | Size |
|---|---|---|
| `Materials/Functions/` | 78 | 2.3 MB |
| `Materials/Instances/` | 507 | 11.4 MB |
| `Materials/SDF/Instances/` | 173 | 1.9 MB |
| `Materials/Impressionist/` | 6 | 0.16 MB |
| `VFX/Materials/` | 29 | ~0.1 MB |
| `Textures/Utility/` (T_Neutral_*) | 5 | 0.05 MB |
| `_PROJECT/04_Materials/{Cosmo,Landscape,water}` | 24 | ~0.5 MB |
| `MI_ToonLayer` (Materials + Art) | 2 | ~0.3 KB |

**Stays ignored (verified):** `SDF/Textures` (36 MB), `_Scratch/` (quarantines), `_Archive/`,
`_PROJECT/04_Materials/Textures` (651 MB), `Space/` (75 MB), `Textures/Shared`. A `git clean`
-class accident now destroys the protected surface only if it is also unstaged + uncommitted —
**commit the staged set when the owner approves** (exact-path staging; never `git clean`/`checkout -- .`).

`git check-ignore -v` verified: protected paths resolve to `!` negations; bulk folders
still resolve to ignore rules.

### 2. Owner instance profiles — the missing policy specimen now exists

- `extract_owner_instance_profiles.py` `ROOTS` extended (Landscape, Showcase, Character,
  Sakura, Water full tree, Rhythm, MelodyTokens, Grotto added; Water narrowed root→tree).
- Ran via Monolith `run_python` (with `__file__` set manually — stdin-execution trap).
- **575 instances scanned / 574 with overrides** → `Saved/Audit/owner_instance_profiles.json`
  (1.25 MB). Top scalars: TextureWeight (374), ShadowDreamStrength (364), Roughness (360),
  RampStrength (353). Top vectors: ShadowDreamTint (395), Ramp{Low,Mid,High} (351).
  Parent histogram: Universal 377, FBX legacy (characters) 91, Landscape 15, Water 9+7+7, Nikki 8.

### 3. AAA Phase 6 capture — first run of `material_family_manifest_full.py`

- Disk-only script (no `unreal` import) — ran shell-side, no editor risk.
- `material_family_manifest.json` regenerated: **30 materials** (Showcase 11, Zen 15,
  Baroque 4), fresh timestamps; `previews_manifest.json` regenerated alongside.
- **Gap for the next lane:** the manifest covers only the three spec modules
  (starter/zen/theme). Landscape/Water/Trimsheet/Sakura families still have **no entries** —
  extend the spec-module list or make the manifest disk-scan the instance folders to close
  the "AAA presentation proof" item for good.

---

## Still open (unchanged, from 08-15 core sweep handoff)

- 24 runtime duplicate short names (incl. real 2-location `MI_SakuraLandscape`, `MI_IridescentRock`
  at Masters root); 59 zero-override MIs; ~773 `Textures_Shared` copies; 12 `_Scratch` zero-ref assets.
- Universal master TriplanarPro parity + overhaul Stages A–E; SDF conversion track
  (VinylGroove/Facade_Baroque/CelestialStarMap + `M_SDF_ParallaxPulse` fix); Nikki BaseTint dedupe.
- Water: 9 native-integration promotion gates + `RefractionStrength` audit block v11.
- Visual proof: per-family hero swatches / render-studio grid still not captured (capture
  tooling exists: `build_material_render_studio_grid.py`, `mi_preview_manifest.py`).

## Session traps (add to AGENTS.md if recurring)

1. **Multi-agent repo: HEAD moves under you.** `git log` at session start ≠ log at session
   end; another agent committed mid-session. Stage-on-top is safe (additive), but never
   build on an assumption that the index is yours alone.
2. **`git add` on gitignored paths silently succeeds with zero files** unless the directory
   chain is re-included first — `git check-ignore -v` per target is the only honest proof.
