# Cascadeur Physical-Impossibility Animation Lab — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** specialist animation R&D  
**Decision:** TEST

## Goal

Use Cascadeur for the exact class of motion where physically grounded body mechanics make Melodia's impossible situations more convincing: bracing, underwater momentum, shifted gravity, asymmetrical recovery, and rhythm-timed anticipation.

The target is not general animation replacement.

## Map and assets

```text
LV_RND_Cascadeur_PhysicalImpossibility
AN_RND_Mara_AnchorBrace_A
AN_RND_Mara_GravityShift_A
AN_RND_Mara_UnderwaterRecovery_A
AN_RND_Mara_RhythmAnticipation_A
```

## Integration reality

Treat current Live Link as one-way Cascadeur -> Unreal preview/recording, not bidirectional edit sync. Skeleton/bone-name compatibility is a first-class setup cost.

## Four micro-tests

### 1. Anchor brace

Character catches a large external force and settles into a believable loaded pose.

### 2. Gravity shift

World-down rotates 60–90 degrees over a short window; body reacts with delayed center-of-mass recovery.

### 3. Underwater momentum

Character changes direction with heavy drag and delayed limb follow-through.

### 4. Rhythm anticipation

A strong physical preparatory motion lands exactly on a known beat without feeling mechanically snapped.

## Comparator

For at least tests 1 and 4, create a fast baseline using the existing animation workflow. Measure total time to a convincing Unreal result.

## Test sequence

1. verify skeleton naming/retarget assumptions;
2. configure Live Link or export path;
3. author first pass;
4. preview in UE5.8;
5. record/import Animation Sequence;
6. make one timing change and one contact/body-mechanics change;
7. round-trip again;
8. package/cook the final Unreal animation without Cascadeur runtime dependency.

## Metrics

```text
skeleton prep minutes
first convincing blockout minutes
contact cleanup minutes
root-motion cleanup minutes
retarget steps
UE preview/record friction
second-revision minutes
final animation asset size
package result
artist confidence in physicality
```

## Hard boundaries

- Unreal animation assets remain shipping authority;
- no runtime dependency on Cascadeur;
- gameplay timing remains authored/validated in Unreal;
- Live Link convenience cannot hide a brittle skeleton naming contract;
- use Cascadeur when physical plausibility is the difficult part, not for every animation.

## Decision gates

**ADOPT specialist role** if physically difficult motions become materially faster/better and the one-way UE handoff is predictable.

**PARK** if subscription/platform/skeleton setup erases most time savings.

**REJECT broad pipeline use** if every revision requires fragile reimport/retarget repair.

## Evidence

```text
Docs/Research/Evidence/CascadeurLab/
  README.md
  skeleton_contract.md
  timing_comparison.csv
  anchor_brace_result.md
  gravity_shift_result.md
  underwater_result.md
  rhythm_result.md
  package_result.md
  decision.md
```

## Melodia-specific payoff

The strongest use is making impossible forces look physically credible enough that the surreal environment feels more real, not less.