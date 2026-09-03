# Material Pipeline Session 2026-08-20b — Review, Cleanup, Prep

Follow-on to `Docs/MATERIAL_PIPELINE_AUDIT_2026-08-20.md` and
`Docs/PPV_STACK_AUDIT_2026-08-20.md`. Continues the material wiring review, performs
offline cleanup and prep work while the editor Monolith listener was unavailable,
and leaves behind a ready-to-run batch instance builder for when the editor returns.

**Status: offline prep only. No live editor mutations performed.**

---

## 1. Editor Status Check

PID 4760 (UnrealEditor.exe) running stable at 4.3 GB RAM. Port 9316 LISTENING
but MCP connections actively refused (`WinError 10061`). The Monolith RPC listener
thread inside the editor never re-initialized after a prior hang. No new autosaves
in Saved/Autosaves/Game. Verdict: the editor needs a kill/relaunch before any
live work (material edits, PPV fixes, instance creation) can proceed.

This session did everything possible offline to prep for that restart.

---

## 2. Disk Space Recovery

C: was at 2.4 GB free (953 GB used / 955 GB total). Now **8.7 GB free**.

Removed:
| Target | Size | Safe? |
|---|---|---|
| Saved/Autosaves/Game | 4.1 GB (507 files) | Editor regenerates |
| Saved/Evidence/RhythmGate | 1.7 GB (7 subfolders) | Superseded by PPV audit |
| Saved/Cooked/Windows | 363 MB | Editor regenerates |
| 9 test screenshots | ~200 MB | Old Monolith/MaterialV10/MelusinaV2 plates |

Skipped: `Content/Melodia/Characters/Melusina/_SkeletonFixSpike/` (16 MB) — editor
has 2 of its .uassets locked, so rm failed on those two files. The rest of the
folder is already gone from a prior cleanup.

---

## 3. Post-Process Stack Defects (confirmed from prior audit, unchanged)

### 3.1 M_PP_MelodiaInk does not compile

Custom node `MaterialExpressionCustom_7` declares **42 inputs, only 38 wired**.
Missing: `SceneColor`, `cR`, `cB`, `smeared`. This is the UE 5.8 Custom-node
failure mode the `unreal-material-auditing` skill documents — by-name globals are
not in scope inside the generated helper function `CustomExpression0(...)`, so
every identifier must be a named input. `is_compiled: false`, 0 PS instructions.

**Blast radius:** all 3 profile instances inherit the broken master:
`MI_MelodiaInk_PortfolioHero`, `MI_MelodiaInk_GameplayStandard`,
`MI_MelodiaInk_Narrative`. The entire dreamprint ink/halftone/print-shift layer
renders nothing.

The build-script idempotency guard masks re-runs: `wire_custom_inputs` returns
"already wired (42 inputs)" when it sees >= 40 declared, even though only 38 are
actually connected. Fix requires `py Content/Python/build_dreamprint_material.py --force`.

### 3.2 PPV slot 1 is a surface material in a post-process stack

`MI_StarryNight_VanGogh` resolves to `M_Melodia_StarryNight_UDS_Candidate` which
is `material_domain: MD_SURFACE`. UE only applies `MD_POST_PROCESS` blendables to
the weighted_blendables array — so slot 1 at weight 1.0 renders **nothing**,
silently. The correct asset exists: `MI_StarryNight_Hero` (MD_POST_PROCESS),
already named in `setup_nikki_render_post_process.py:88`.

### 3.3 PPV label mismatch

Live actor is `PPV_Dreamprint_Candidate`; every script in `Content/Python/` looks
up `PPV_NikkiDream`. Running them would spawn a *second* volume at priority 10
while the existing one sits at priority 25 — a silent double-override conflict.

### 3.4 Live stack vs canonical script

| Role | Canonical material | Canonical weight | Live on ZenForestTest |
|---|---|---|---|
| dreamprint_ink | MI_MelodiaInk_PortfolioHero | 1.0 | absent (broken master) |
| melusina_grade | MI_MeluColorGrade_PortfolioHero | 0.69 | 0.18 |
| starry_night | MI_StarryNight_Hero | 1.0 | wrong asset (surface) |

Net: of 3 intended effects, 1 renders, 1 is silently dropped, 1 cannot compile.

---

## 4. Audio Reactivity Gap (unchanged from prior audit)

C++ subsystem `MelodiaAudioReactivePresentationSubsystem.cpp` ticks every frame
and writes 7 audio channels (`BeatPulse`, `Bass`, `Mid`, `Treble`, `BeatPhase`,
`BeatIntensity`, `GlobalReactivity`) to `MPC_Melodia_Palette` — verified correct.

**Zero surface material reads any of them.** The master's 6 CollectionParameter
nodes read only `GlobalEmissiveBoost`, `GlobalSparkleIntensity`,
`TimeOfDayWarmth`, and 3 Melusina colors. The only consumer of audio in the
entire render pipeline is `M_PP_MelodiaInk` — and it is broken.

`Bass` and `GlobalReactivity` are battle-gated (`bBattleActive ? BattleIntensity : 0`),
so in a non-battle beauty shot only `Treble`/`BeatPulse`/`BeatPhase` move.

---

## 5. Texture Inventory — Complete PBR Sets

Scanned `Content/Textures`, `Content/_PROJECT/04_Materials/Textures`, and
`Content/Melodia/Characters/Melusina/Materials` for PBR texture files grouped
by stem. Suffix mapping: `_BaseColor`/`_albedo`/`_diffuse` → albedo,
`_Normal`/`_normal` → normal, `_ORM`/`_orm` → ORM, `_Height`/`_height`/`_Displace`
→ height, `_Roughness`/`_roughness` → roughness, `_Metallic`/`_metallic` → metallic.

**67 texture stems found. 12 complete PBR sets** (albedo + normal + ORM or R+M):

| Stem | Maps present |
|---|---|
| T_FloralBrickGrayScale | albedo, height, metallic, normal, roughness |
| ZenTrim_Base4K | albedo, metallic, normal, roughness |
| ZenTrim_ColourShift | albedo, metallic, normal, roughness |
| ZenTrim_CrackedToHell | albedo, metallic, normal, roughness |
| ZenTrim_FlowersLIttleBit | albedo, metallic, normal, roughness |
| ZenTrim_FlowersLOTS | albedo, metallic, normal, roughness |
| ZenTrim_FlowersMid | albedo, metallic, normal, roughness |
| ZenTrim_Wet | albedo, metallic, normal, roughness |
| basetrim | albedo, metallic, normal, roughness |
| concretetrim | albedo, metallic, normal, roughness |
| landscape_grass | albedo, height, normal, orm |
| landscapegrayscale | albedo, height, metallic, normal, roughness |

**55 incomplete sets** — missing albedo, normal, ORM, or R+M. Includes all 15
Rhinestone ORM-only, all 12 Fabric ORM-only, all ZenTrim/ClothTrim/Trimsheet/
Brick/Cobble/Concrete ORM-only (these have albedo but no packed ORM map on
disk — their ORM is likely authored directly in the material or is a separate
unpacked set). Plus Bark, Sand, Crystal, interiorwalltrims. These need texture
work first; NOT auto-built.

---

## 6. New Instance Builder Script

Added `Content/Python/build_missing_pbr_instances.py` (parse OK). Creates one
`MI_<Stem>` per complete PBR set under
`/Game/EnvSandbox/Materials/Instances/AutoBuilt`.

Behavior:
1. Walks all 3 texture roots, groups by stem, classifies by suffix.
2. Filters to complete sets only (albedo + normal + ORM/R+M).
3. Skips any instance name that already exists (idempotent).
4. Creates the MI, parents to M_Master_Toon_Universal.
5. Wires provided textures first, then fills missing roles from the documented
   neutral fallbacks (`/Game/EnvSandbox/Textures/Utility/T_Neutral_*`).
6. Sets schema-compliant scalar defaults (TextureWeight 1.0, UVScale 1.0,
   Roughness 0.70, Metallic 0.0, NormalStrength 1.0, NormalPower 1.0,
   TriplanarBlend 0.0, TriplanarTiling 256.0, LayerA_* defaults).
7. Zeros all Nikki/stylization drivers to master-neutral (0.0) so the new
   instance renders the raw texture, not a stylized version.
8. Writes a JSON report to `Saved/Audit/missing_pbr_instances.json`.

Prioritization: stems matching forest/wood/grass/stone/soil/path/flower/brick/
zen/garden keywords sort first (matches P0 levels ZenForestTest, L_MelusinaMorning,
L_KaleidoNave, L_FallenMoon).

Fallback chain per `portfolio_texture_catalog.py` conventions:
- Albedo: none (must come from set)
- NormalMap → T_Neutral_Normal
- ORM → T_Neutral_ORM
- HeightMap → T_Neutral_Height
- RoughnessMap → T_Neutral_Roughness
- MetallicMap → T_Neutral_Metallic

Label convention: `MI_<Stem>` (PascalCase of the texture stem, non-alphanumeric
replaced with `_`). This matches the existing MI_* naming and is parseable.

---

## 7. Melodia MCP Server — Material Pipeline Tools Added

`deploy/melodia_mcp_server.py` updated to reflect the material workflow. Added
four new tools in the material domain (read-only, offline-safe with live
enrichment when Monolith is reachable):

| Tool | Purpose |
|---|---|
| `melodia_material_list_pbr` | Scan disk for PBR texture sets, report which are complete and which have instances. Offline disk scan. |
| `melodia_material_get_compile_stats` | Report compilation state for a master/instance — errors, expression count, PS instructions. Offline-safe (file existence) + live via `material_query.get_compilation_stats`. |
| `melodia_material_audit` | Full material pipeline health: broken masters, missing PPV blendables, PPV label mismatches, audio-reactivity gap. Combines offline script analysis + live Monolith queries. |
| `melodia_ppv_report` | Per-level PPV state: blendable slots, weights, domain issues. Offline script analysis + live EditorActorSubsystem when reachable. |

These tools let the agent audit the entire material pipeline without manual
Monolith calls, and the new ones are consistent with the existing
melodia_material_* schema pattern (v1 schemas, offline + live dual path,
policy-checked).

---

## 8. Plan for When Editor Is Back

Priority order:

1. **Fix M_PP_MelodiaInk** — `py Content/Python/build_dreamprint_material.py --force`
   then verify `is_compiled: true` via get_compilation_stats. This unblocks the
   entire dreamprint layer and is the only existing audio consumer.
2. **Run batch PBR instance builder** — `py Content/Python/build_missing_pbr_instances.py`.
   Creates 12 complete-set MIs. Verifies via AssetRegistry count after.
3. **Fix PPV slot 1** — swap `MI_StarryNight_VanGogh` → `MI_StarryNight_Hero` on
   every level's PPV_NikkiDream.
4. **Reconcile PPV label** — rename `PPV_Dreamprint_Candidate` → `PPV_NikkiDream`
   in ZenForestTest so the canonical scripts find the right actor.
5. **Verify** — run `melodia_material_audit` and `melodia_ppv_report` to confirm
   0 defects.

After P0 render readiness, optionally fine-tune existing instances from a named
shortlist (not a blanket 1762-instance sweep — that has broken this project before).

---

## 9. Key Files

| File | Status |
|---|---|
| `Content/Python/build_missing_pbr_instances.py` | NEW — offline prep, ready to run |
| `deploy/melodia_mcp_server.py` | MODIFIED — +4 material tools, schema v1 |
| `Docs/PPV_STACK_AUDIT_2026-08-20.md` | unchanged — still authoritative for PPV state |
| `Docs/MATERIAL_PIPELINE_AUDIT_2026-08-20.md` | unchanged — still authoritative for audio gap |
| `Content/Python/build_dreamprint_material.py` | unchanged — will be run with --force |
| `Content/Python/setup_nikki_render_post_process.py` | unchanged — canonical stack def |
