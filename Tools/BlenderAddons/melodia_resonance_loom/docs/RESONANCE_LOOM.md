# Resonance Loom — author garments that listen to the battle beat

Melusina's wardrobe is gameplay (Infinity Nikki lens): outfits carry
presentation *and* meaning. The battle rhythm is the project's pulse —
`128BPMarpeggiomelody_beatgrid.mid` is the beat authority (tempo+bar+beat maps,
validated by `MelodiaMusicClockSubsystem`, never hand-built). Resonance Loom
joins the two: it lets an artist tailor garments whose silhouette moves **on
the actual beats the game clock plays**.

## Pipeline (all inside Blender, laptop-local, no UE editor)

```
1. Import Beatgrid   parse the project MIDI -> timeline markers (LOOM_DOWN_/LOOM_ACC_)
2. Ensure Paint      LOOM_Accent / LOOM_Hit / LOOM_Hem vertex groups
3. Bake Rhythm Keys  SK_LOOM_Accent / SK_LOOM_Hit (Tier A authored motion)
4. Validate Garment  naming + baked keys + wardrobe_draft_lint (reads C++ headers)
5. Export Garment    <Cos_id>.fbx + <Cos_id>.melodia_rhythm.json
```

## Authority boundaries (do not cross)

| Surface | Owner | Loom's role |
|---|---|---|
| Beat time | `UMelodiaMusicClockSubsystem` (Harmonix) | parses the same MIDI, never re-times |
| Rhythm input/grading | `UMelodiaRhythmCombatSubsystem` | untouched; Loom bakes presentation only |
| Wardrobe state | `UMelodiaWardrobeSubsystem` + catalog | validates drafts via `wardrobe_draft_lint`, writes nothing |
| Lanes Q/W/O/P | `BP_BattleUI::OnKeyDown` | single vocabulary in `loom_core/lanes.py` |

## The sidecar contract — `MelodiaRhythmGarment-v1`

Travels next to the garment FBX. The UE import flow reads it; the addon never
touches `.uasset`. All fields additive; unknown fields are ignored safely.

| Field | Feeds | Notes |
|---|---|---|
| `cosmetic_id` | `FMelodiaCosmeticRecord::CosmeticId` | must match the draft JSON |
| `skill_id` | `StockSkillRhythmIds` value space | one of the 8 authored ids, else silent no-op |
| `bpm`, `tempo_band` | presentation lane | parsed, never authored |
| `pattern_density` | pre-play pattern ranking | 0..1; quantum lane may rank, never time |
| `lane_hits` | highway presentation | per-lane counts Q/W/O/P |
| `accent_amplitude` / `hit_amplitude` | flourish scalar | **expressive, never a gate** (Decision 016) |
| `expressiveness_only: true` | audit marker | refuses evaluative framing |

## Decision 016 compliance (expressive, not evaluative)

`loom_core/lanes.py::assert_expressive` scans authored Loom strings for
penalty vocabulary. No "miss" exists anywhere in this addon's outputs — timing
adds flourish; a soft beat yields the normal result. The battle UI never
displays a penalty, and neither does the Loom.

## Cloth taxonomy

Loom bakes **Tier A (rigid authored motion)** from
`Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`.
Tier B (Chaos Cloth), Tier C (WPO) and Tier D (Houdini) garments should NOT
get LOOM vertex groups; their sidecars may still carry beat metadata.

## Tests

```powershell
# pure core, no Blender needed (23 tests, incl. the real beatgrid parse)
python -m unittest Tools.BlenderAddons.melodia_resonance_loom.tests.test_loom_core -v

# full bpy pipeline headless (19 checks, real Blender, real MIDI)
"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background `
  --python Tools\BlenderAddons\melodia_resonance_loom\tests\blender_smoke.py
```

## Phase 2 (built 2026-09-17)

- **`ACT_LoomSecondary`** — `melodia_loom.bake_secondary_action` keyframes the
  baked rhythm keys onto the beat grid: Hit pulses (pop, hold ~30% of a beat,
  release) on every bar line, Accent flourishes scaled by note velocity on
  loud onsets. The action is named `ACT_LoomSecondary` (naming.py SSOT) so
  UE handoff and re-runs stay deterministic.
- **Lane strategies** — `loom_core/lanes.py::LANE_STRATEGIES`: `pitch_quartile`
  (Q=lowest … P=highest), `velocity_bands` (soft→loud), `bar_position`
  (early→late in the bar). Chosen per garment in the panel; recorded in the
  sidecar as `lane_strategy` and used to compute `lane_hits`. Presentation
  only — never a gate.

## Phase 3 candidates (not built — say-so, don't fake)

- GN-based Tier B flourish previews
- per-note manual lane overrides (strategies are global per garment today)
