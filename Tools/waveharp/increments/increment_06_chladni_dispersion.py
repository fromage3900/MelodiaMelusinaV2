"""Increment 6 - the Chladni dispersion.

The world field bus already carries the standing-wave signature (ModeN, ModeM), the
tension and the beat pulse - the cymatics subsystem publishes it and the consumers read
it. The water chorus now SAMPLES it, so the dispersion follows the Chladni figure
instead of being a generic spray: the fluid's input point rides the field's position
and its strength rides the field's tension.

The chorus only READS the bus - the cymatics subsystem remains the publisher, so there
is still exactly one writer per surface.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
C = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.cpp"

source = C.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


source = swap(
    source,
    """#include "MelodiaMusicClockSubsystem.h\"""",
    """#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaWorldFieldBus.h\"""",
    "chorus include the bus")

source = swap(
    source,
    """ // A downbeat is a wrap of the phase.""",
    """ // THE CHLADNI DISPERSION: the world field bus carries the standing-wave signature
 // (ModeN, ModeM) and the tension that the cymatics subsystem publishes. The water
 // disperses ALONG that figure: the fluid's input point rides the field's position and
 // its strength rides the field's tension. READ ONLY - the cymatics subsystem stays
 // the only publisher.
 FWorldFieldSample Field;
 if (const UWorldFieldBus* Bus = UWorldFieldBus::Get())
  Field = Bus->SampleResonanceTension(Owner->GetActorLocation());

 // A downbeat is a wrap of the phase.""",
    "chorus chladni sample")

source = swap(
    source,
    """  if (!Surface.Beat.IsNone()) Niagara->SetVariableFloat(Surface.Beat, Pulse);
  if (!Surface.Strength.IsNone()) Niagara->SetVariableFloat(Surface.Strength, 0.35f + 0.65f * Bass);
  if (!Surface.Density.IsNone()) Niagara->SetVariableFloat(Surface.Density, 0.4f + 0.6f * Pulse);""",
    """  if (!Surface.Beat.IsNone()) Niagara->SetVariableFloat(Surface.Beat, Pulse);
  if (!Surface.Strength.IsNone())
   Niagara->SetVariableFloat(Surface.Strength, 0.35f + 0.65f * FMath::Max(Bass, Field.Tension));
  if (!Surface.Density.IsNone()) Niagara->SetVariableFloat(Surface.Density, 0.4f + 0.6f * Pulse);
  // The dispersal point rides the Chladni field.
  if (!Surface.Input.IsNone())
   Niagara->SetVariablePosition(Surface.Input, Field.WorldPosition);""",
    "chorus chladni drive")

C.write_text(source, encoding="utf-8")
print("increment 6 applied: the Chladni dispersion")
