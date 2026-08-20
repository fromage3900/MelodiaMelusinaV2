# MPC Unification + Fabric Instance Family — Methodical Plan

Live-verified 2026-08-20 against the running editor (Monolith 0.20.3, UE 5.8).

## CORRECTION to yesterday's audit

`MATERIAL_PIPELINE_AUDIT_2026-08-20.md` claimed "no material reads audio channels."
**That was wrong** — I matched on the JSON key `parameter_name` when
`export_material_graph` emits `ParameterName`. Corrected map:

| Material | CP nodes | Audio params read |
|---|---|---|
| `M_PP_MelodiaInk` | 14 | BeatPulse, BreakPulse, ComboNormalized, EnemyTension, InkBass, InkMid, InkReact, InkSyncVision, InkTreble, VictoryPulse |
| `M_PP_MeluColorGrade` | 7 | BeatIntensity, BeatPulse, InkSyncVision, RhythmPulse, VictoryPulse |
| `M_PP_StorybookOutline_Premium_Candidate` | 1 | RhythmPulse |
| `M_Master_Toon_Universal` | 6 | **none** |
| `M_Master_Toon_Universal_NikkiChain` | 6 | **none** |
| `M_Master_Toon_Cosmic` | 6 | **none** |
| `M_PP_StarryNightOverlay_Candidate` | 12 | none (reads UDS weather instead) |

**Accurate statement:** audio reactivity is fully wired in the **post-process**
layer and absent from the **surface** layer. That's a coherent architecture, not a
bug — but it means audio reactivity dies with the PPV, and `M_PP_MelodiaInk`
(the richest consumer, 10 channels) **does not compile**. So today audio
reactivity is still invisible, just for a different reason than I first said.

## MPC system status — verified claim by claim

| Claim | Status | Evidence |
|---|---|---|
| One canonical audio MPC | **TRUE** | all 5 C++ writers load `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` |
| `MPC_Portfolio_Audio` is dead | **TRUE, already handled** | `MelodiaRhythmReactivitySubsystem.cpp:17-22` documents the migration off it; only 2 scalars, no readers |
| Beat writer owns beat namespace | **TRUE** | `MelodiaAudioReactivePresentationSubsystem.cpp:155-161` asserts sole ownership; `cos²` fix documented |
| PP materials consume audio | **TRUE** | 3 PP materials, 16 distinct channels |
| Surface materials consume audio | **FALSE** | 0 of 6 masters checked |
| `MPC_Melodia_Palette` is forked | **TRUE — unresolved** | `/Game/Melodia/_PROJECT/` 47 scalars (canonical) vs `/Game/_PROJECT/` 17 scalars (no audio, no known reader) |
| `Bass` usable outside battle | **FALSE** | line 163 gates on `bBattleActive` |

### Remaining MPC defects
1. **Fork:** the 17-scalar `/Game/_PROJECT/04_Materials/MPC_Melodia_Palette` has no
   audio channels and no identified reader. Retire or document — leaving two
   assets with one name guarantees a future silent-dead-value bug.
2. **`M_PP_MelodiaInk` won't compile** (4 unwired Custom inputs: `SceneColor`,
   `cR`, `cB`, `smeared`). Its 10 audio channels are dead until fixed.
3. **`Bass`/`GlobalReactivity` are 0 outside battle** — beauty shots get no bass
   response. Either capture in battle or drive the MPC manually pre-shot.

---

## THE TEXTURE FINDING — real PBR on disk, stubs in project

`/Game/Textures/Fabrics` holds **50 textures, all 32×32** — placeholders.
The real source is on disk at `C:\EnvironmentPortfolio\wix\textures\pbr\`:
**56 PNGs, 90 MB, 12 complete sets.**

| Set | Maps | Res |
|---|---|---|
| `T_Fabric_BaroqueFiligreeLace` | BC, H, Mask, N, ORM | 2048² |
| `T_Fabric_BaroqueLace` | BC, H, Mask, N, ORM | 2048² |
| `T_Fabric_CelestialWeave` | BC, H, N, ORM, Sparkle | 2048² |
| `T_Fabric_IridescentCelestialWeave` | BC, H, N, ORM, Sparkle | 2048² |
| `T_Fabric_RoyalVelvet` | BC, H, N, ORM, Sheen | 2048² |
| `T_Fabric_SheerSilk` | BC, H, N, ORM, Sheen | 2048² |
| `T_Fabric_GildedBrocade` | BC, DetailN, H, N, ORM | 2048² |
| `T_Fabric_GildedJacquard` | BC, DetailN, H, N, ORM | 2048² |
| `T_Fabric_GoldEmbroidery` | BC, DetailN, H, N, ORM | 2048² |
| `T_Fabric_GoldThreadedEmbroidery` | BC, DetailN, H, N, ORM | 2048² |
| `T_Melusina_FrontPanel` | BC, N, ORM | **4096²** |
| `T_Melusina_Shirt` | BC, N, ORM | **4096²** |

Zero material instances reference any of them.

### Second defect: sRGB flags are wrong on the stubs
Every `_ORM`, `_H`, `_Mask`, `_Sheen`, `_Sparkle` in-project has `sRGB: true`.
Those carry **linear data**, not colour. sRGB-decoding them skews roughness,
metallic, AO, height and mask values. Normals are correctly `sRGB: false` /
`TC_NORMALMAP`, so whoever imported them got normals right and data maps wrong.

Correct settings:
| Suffix | sRGB | Compression |
|---|---|---|
| `_BC` | **true** | TC_DEFAULT |
| `_N`, `_DetailN` | false | TC_NORMALMAP |
| `_ORM`, `_H`, `_Mask`, `_Sheen`, `_Sparkle` | **false** | TC_MASKS |

### Wider scope (not for today)
256 PBR-suffixed texture sets project-wide have no instance. Notable clusters:
Violin (5 sets), SirMelodious (4), Tileables (4), EnchantedForest crystals.
7506 of 9878 textures are unreferenced, but most are UI atlases (1440 Kenney
input prompts, 339 Figma UI) — not material candidates.

---

## PLAN — staged, smallest blast radius first

### Phase 1 — Fix texture settings (10 assets, reversible)
Set sRGB=false + TC_MASKS on the data maps of the 10 fabric sets already in
project. Pure import-setting change; no graph edits. Verify by re-reading flags.

### Phase 2 — Reimport real source over the stubs (12 sets)
Reimport 2048²/4096² PNGs from `wix/textures/pbr/` onto the existing 32×32
assets so **all existing references survive** (same asset paths, same GUIDs).
Re-apply Phase 1 settings after (reimport can reset them). Verify resolutions.

### Phase 3 — Fabric instance family (NEW assets, zero risk)
Create instances on `M_Master_Toon_Universal` under
`/Game/Melodia/_PROJECT/04_Materials/Instances/Fabrics/`. Nothing existing is
modified. Per-set tuning uses the Nikki params that already exist:

| Set | FabricSheen | Iridescence | SparkleIntensity | Notes |
|---|---|---|---|---|
| RoyalVelvet | 0.65 | 0.05 | 0.0 | sheen map drives velvet falloff |
| SheerSilk | 0.45 | 0.12 | 0.05 | light, high sheen |
| CelestialWeave | 0.25 | 0.35 | 0.55 | sparkle map |
| IridescentCelestialWeave | 0.30 | **0.75** | 0.65 | hero iridescent |
| GildedBrocade | 0.15 | 0.10 | 0.20 | gold, DetailN |
| GildedJacquard | 0.15 | 0.10 | 0.18 | gold, DetailN |
| GoldEmbroidery | 0.10 | 0.08 | 0.30 | gold thread |
| GoldThreadedEmbroidery | 0.10 | 0.08 | 0.32 | gold thread |
| BaroqueLace | 0.35 | 0.15 | 0.10 | Mask for opacity |
| BaroqueFiligreeLace | 0.35 | 0.18 | 0.12 | Mask for opacity |

Values are starting points chosen against the master's existing defaults
(`FabricSheen 0`, `SheenPower 6`, `IridescencePower 1`, `SparkleScale 220`) —
expect to tune after the first look-dev render.

### Phase 4 — Audio reactivity (needs your decision)
Two options, both additive:
- **A (safer):** fix `M_PP_MelodiaInk`'s 4 Custom inputs. Restores 10 audio
  channels through the existing PP architecture. No surface changes.
- **B (new capability):** add gated audio CP nodes to `M_Master_Toon_Universal`
  behind `AudioReactAmount` default 0.0, so surfaces can pulse too. All 1762
  instances render identical until an instance opts in.

Recommend **A first** — it repairs a designed system rather than adding a
parallel one. B is the bigger showcase story, but it's the riskier edit.

### Phase 5 — Proof render
`HighResShot` via `run_python` with viewport realtime ON, capturing the fabric
family on a lookdev mesh. A/B: `AudioReactAmount` 0 vs 0.85, or MPC `BeatPulse`
pinned 0 vs 1.

## Guardrails
- Nothing in Phases 1-3 touches `M_Master_Toon_Universal` or any of its 1762
  instances.
- Phase 4 is opt-in-by-default and gated.
- No project-wide instance sweep. Batches only, from an approved list.
- Verify with `get_compilation_stats` after every phase that touches a graph.
