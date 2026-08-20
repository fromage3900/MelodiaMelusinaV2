# Material Pipeline Audit + Nikki Audio-Reactivity Plan (NVIDIA Showcase)

Live audit 2026-08-20. Monolith 0.20.3 · UE 5.8 CL-55116800 · editor live on :9316.
**Read-only. Nothing was modified.** Part 3 is a proposal awaiting your approval.

---

## PART 1 — PIPELINE SHAPE (measured, not estimated)

| Metric | Count | Source |
|---|---|---|
| Materials (`UMaterial`) project-wide | **892** | AssetRegistry scan |
| Material instances (`MaterialInstanceConstant`) | **3009** | AssetRegistry scan |
| Instances on `M_Master_Toon_Universal` | **1762** (58% of all) | `list_material_instances` |
| Instances with ≥1 override | 1739 | per-instance property read |
| Instances with **zero** overrides | 23 | same |
| Instances already touching Nikki params | **1228** | scalar-name match |
| MaterialParameterCollections | 22 | AssetRegistry scan |

### The spine: `M_Master_Toon_Universal`
Path: `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`

```
is_compiled              true
expression_count         1208
num_pixel_shader_instr   1162
num_vertex_shader_instr  313
num_samplers             9
estimated_ps_tex_samples 23
blend_mode               Opaque
```

Parameter surface — **365 total**:

| Kind | Count |
|---|---|
| Scalar | 255 |
| Vector | 50 |
| Texture | 31 |
| Static switch | 29 |

**Note on the "138 materials" portfolio claim:** the AssetRegistry filter for
names containing `Master`/`Toon` returns exactly **138** materials. So the claim
is defensible as "138 Toon-family materials", but the *unified spine* is more
precisely **1762 instances on one master**. The stronger, more accurate NVIDIA
line is the 1762 number — it's a bigger and more verifiable claim.

### Nikki parameter design: neutral-by-default
Of 58 Nikki/audio-adjacent scalars on the master, the intensity drivers all
default to **0**:

`PastelLift 0 · DreamSaturation 0 · DreamContrast 0 · DreamShadowLift 0 ·
RimIntensity 0 · GlowIntensity 0 · SparkleIntensity 0 · Iridescence 0 ·
FabricSheen 0 · BloomBoost 0 · TemporalStrength 0 · DreamBloomStrength 0`

Shape parameters carry real defaults (`DreamRimStrength 1.2`, `DreamRimPower 4`,
`SparkleScale 220`, `RimPower 3`, `SheenPower 6`, `NikkiHeroGradeStrength 0.35`).

This is deliberate and documented in `setup_master_universal.py:6` — "all
defaulting to neutral (0)". Per-look intensity belongs on instances. **Do not
raise these on the master**; it would shift all 1762 instances at once.

---

## PART 2 — THE AUDIO-REACTIVITY GAP (the real finding)

The audio system is **half-built**: the writer works, nothing reads it.

### Writer — exists and is correct
`Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp`
ticks every frame via `FTSTicker` and writes to
`/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`:

| MPC scalar | Driven by | Line |
|---|---|---|
| `GlobalReactivity` | `bBattleActive ? BattleIntensity : 0` | 162 |
| `Bass` | `bBattleActive ? BattleIntensity : 0` | 163 |
| `Mid` | `ImpactPulse` (decays at 3.5/s) | 164 |
| `Treble` | `cos²(BeatPhase·π)` | 165 |
| `BeatPhase` | musical time | 166 |
| `BeatPulse` | `cos²(BeatPhase·π)` | 167 |
| `BeatIntensity` | `cos²(BeatPhase·π)` | 168 |

The `cos²` (not `sin²`) choice is commented as a real past bug fix — phase 0 is
*on* the beat, so `sin²` pulsed everything on the off-beat.

### Reader — MISSING
`M_Master_Toon_Universal` contains **6 CollectionParameter nodes**, reading only:

```
GlobalEmissiveBoost · GlobalSparkleIntensity · TimeOfDayWarmth
Melusina_Lavender · Melusina_RoseGold · Melusina_SoftWhite
```

**Zero audio channels.** Verified across every candidate surface master:

| Master | CollectionParameter nodes | Audio params read | Instances |
|---|---|---|---|
| `M_Master_Toon_Universal` | 6 | **none** | 1762 |
| `M_Master_Toon_Universal_NikkiChain` | 6 | **none** | 8 |
| `M_AudioReactive_BaseMaster` | **0** | **none** | 2 |
| `M_Master_Nikki` | 0 | none | 8 |
| `M_Master_Toon_Unified` | 0 | none | 2 |
| `M_Master_Toon_Character` | 0 | none | 5 |

`M_AudioReactive_BaseMaster` is named for the job and reads nothing at all.

**Conclusion:** `Bass`, `Mid`, `Treble`, `BeatPulse`, `BeatIntensity`,
`RhythmPulse`, `ComboNormalized`, `VictoryPulse`, `BreakPulse`, `EnemyTension`
are all written every frame and consumed by **no surface material**. The only
consumer found anywhere is `M_PP_MelodiaInk` (post-process) — and that master
**does not compile** (see `PPV_STACK_AUDIT_2026-08-20.md`).

So today: **audio reactivity is not visible on any surface in any render.**

### Two more blockers for a showcase capture

1. **`Bass` is battle-gated.** Line 163: `bBattleActive ? BattleIntensity : 0`.
   In a beauty shot outside battle, `Bass` and `GlobalReactivity` are hard 0.
   Only `Treble`/`BeatPulse`/`BeatPhase` move from musical time.
2. **MPC fork.** Two collections share the name `MPC_Melodia_Palette`:

   | Path | Scalars | Vectors | Used by |
   |---|---|---|---|
   | `/Game/Melodia/_PROJECT/04_Materials/` | **47** | 17 | C++ writer ✓, master ✓ |
   | `/Game/_PROJECT/04_Materials/` | 17 | 15 | nothing found |

   The 17-scalar copy has no audio channels at all. Any script or material
   pointed at it gets silently dead values. The Melodia one is canonical.

---

## PART 3 — PROPOSAL (needs your approval before I touch anything)

Project is unstable and 1762 instances hang off one master, so this is staged
smallest-blast-radius first. **I have not executed any of it.**

### Step 1 — Wire audio into the master (1 master, additive, reversible)
Add CollectionParameter nodes to `M_Master_Toon_Universal` reading `BeatPulse`,
`Bass`, `Mid`, `Treble` from the Melodia palette MPC, then gate them behind a
**new scalar `AudioReactAmount`, default 0.0**.

Default 0 means **all 1762 instances render bit-identical** after the change.
Reactivity only appears where an instance opts in. That is the whole safety
argument, and it matches the existing neutral-default convention.

Suggested wiring (multiply into existing Nikki drivers, not new outputs):
```
SparkleIntensity_effective = SparkleIntensity + (BeatPulse * AudioSparkleGain * AudioReactAmount)
RimIntensity_effective     = RimIntensity     + (Treble    * AudioRimGain     * AudioReactAmount)
GlowIntensity_effective    = GlowIntensity    + (Mid       * AudioGlowGain    * AudioReactAmount)
DreamPulseAmp_effective    = DreamPulseAmp    + (Bass      * AudioDreamGain   * AudioReactAmount)
```
Cost estimate: ~20-30 expressions on a 1208-expression master (+2%), a handful
of PS instructions. Must re-verify with `get_compilation_stats` after.

### Step 2 — Author 3 showcase instance profiles (new assets, zero risk)
New instances, nothing existing modified:

| Profile | AudioReactAmount | Character |
|---|---|---|
| `MI_Showcase_Hero_Pulse` | 0.85 | strong on-beat sparkle + rim, for the hero plate |
| `MI_Showcase_Ambient` | 0.30 | subtle breathing, for wide environment shots |
| `MI_Showcase_Static` | 0.0 | reference/control — proves the A/B |

The Static profile matters: for NVIDIA, an A/B pair *proves* the system rather
than asserting it.

### Step 3 — Fine-tune existing instances (opt-in, batched)
Only after Steps 1-2 verify. Of the 1228 Nikki-touching instances I'd start with
a named shortlist you approve — e.g. the MelodyToken set and Melusina wardrobe —
not a blanket pass. **A project-wide sweep across 1762 instances is exactly the
kind of change that has broken this project before; I won't do it unprompted.**

### Step 4 — Make it visible in renders
Blocked on the PPV work: viewport `realtime: false` freezes time-driven effects,
and `capture_scene_preview` can't show level context. Use `HighResShot` via
`editor.run_python`, or PIE — details in `PPV_STACK_AUDIT_2026-08-20.md`.

For a *static* hero plate, reactivity is a still frame anyway — consider driving
the MPC to a chosen pose (e.g. `BeatPulse = 1.0`) via
`UKismetMaterialLibrary.SetScalarParameterValue` immediately before the shot, so
you capture the peak rather than a random phase.

### Also worth fixing while here
- `M_PP_MelodiaInk` compile failure (4 unwired Custom inputs) — it's the only
  existing audio consumer, and it's the "dreamprint" look.
- MPC fork — decide whether the 17-scalar `/Game/_PROJECT/` copy is dead and
  should be retired.

---

## Verification method

| Claim | Method |
|---|---|
| 892 / 3009 / 22 counts | `AssetRegistry.get_assets` with ARFilter |
| 1762 instances on master | `material_query.list_material_instances` |
| 1228 Nikki-touching | per-instance `scalar_parameter_values` read |
| 365 master params | `material_query.get_material_parameters` |
| Nikki defaults all 0 | same call, `value` field |
| Master reads only 6 MPC params | `export_material_graph`, CollectionParameter nodes |
| No master reads audio | same, across 6 candidate masters |
| C++ writes 7 audio scalars | `MelodiaAudioReactivePresentationSubsystem.cpp:162-168` |
| `Bass` battle-gated | same file, line 163 |
| MPC fork 47 vs 17 scalars | `run_python` over both collections |
| Compile stats | `material_query.get_compilation_stats` |
