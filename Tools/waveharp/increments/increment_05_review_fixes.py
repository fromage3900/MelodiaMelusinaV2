"""Increment 5 - two fixes the review found in the night's own code.

  1. The VFX beats did not re-fire when a transition entered the SAME stage twice (the
     stage guard kept the previous stage marked as fired). The marker is reset when a
     transition starts.
  2. The water burst played TWICE per form change, because ApplyFormVisuals runs both
     at the midpoint (the head swap) and at the landing. The burst belongs to the
     midpoint - the water transform covers the swap - so the landing no longer bursts.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
H = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.h"
C = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.cpp"

header = H.read_text(encoding="utf-8")
source = C.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


# the declaration takes a flag now
header = swap(
    header,
    """ /** The one writer path. Applies the committed form to the head and the morphs. */
 void ApplyFormVisuals();""",
    """ /** The one writer path. Applies the committed form to the head and the morphs.
 *  bBurst is true only at the transition's midpoint, where the water transform covers
 *  the head swap - the landing must not burst a second time. */
 void ApplyFormVisuals(bool bBurst = false);""",
    "header apply form visuals")

source = swap(
    source,
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals()
{""",
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals(const bool bBurst)
{""",
    "cpp apply form visuals")

source = swap(
    source,
    """ UpdateWandPresentation();
 // The water transform: the form change breaks the surface of the world.
 if (bEnableWaterChorus) WaterChorus.Burst(Character.Get());
}""",
    """ UpdateWandPresentation();
 // The water transform: the form change breaks the surface of the world. It belongs to
 // the midpoint, where the head actually changes.
 if (bBurst && bEnableWaterChorus) WaterChorus.Burst(Character.Get());
}""",
    "cpp burst once")

# the midpoint call bursts; the landing call does not
source = swap(
    source,
    """  bHeadSwappedThisTransition = true;
  ApplyFormVisuals();
  PlayFormTransformFlourish();""",
    """  bHeadSwappedThisTransition = true;
  ApplyFormVisuals(true);
  PlayFormTransformFlourish();""",
    "cpp midpoint burst")

# the beats fire again for every new transition
source = swap(
    source,
    """ bFormTransitionActive = true;
 bHeadSwappedThisTransition = false;
 FormTransitionAlpha = 0.f;""",
    """ bFormTransitionActive = true;
 bHeadSwappedThisTransition = false;
 // Every transition gets its beats: the fired-marker is cleared with the transition.
 LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
 FormTransitionAlpha = 0.f;""",
    "cpp reset fired stage")

H.write_text(header, encoding="utf-8")
C.write_text(source, encoding="utf-8")
print("increment 5 applied: the beats re-fire, the water bursts once")
