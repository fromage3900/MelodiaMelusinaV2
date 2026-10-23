"""Increment 10 - bind FluidNinja BY ITS EXACT API, learned from the live surface.

The live diagnostic dumped all 220 exposed user parameters of the NinjaLiveComponent.
The ones that matter for a beat-reactive, surreal water world are:

    User.SimSpeed                       float   the sim's speed - the beat
    User.Painter.BrushStrength          float   how hard the brush paints - the bass
    User.Painter.BrushSize              float   the radius of the dispersal
    User.Painter.ParticleBrushVelocity  vector  the direction of the dispersal
    User.SimplePainterMode              bool    the simple painter: tracks objects and
                                                    draws their trajectories (the trails)
    User.VolumeRender                   bool    the water volume
    User.FogVolumeRender                bool    the mist over the water
    User.FogVolumeMaterial              object  the mist's material
    User.VolumeMaterial                 object  the water surface's material

So the chorus now binds these BY NAME (exact, with the right setter for the type), and
falls back to the pattern matcher only when a surface does not expose them.

The tracked bones (User.TrackedBones) are an array of bone names - setting them needs the
character's hair bone names, so that stays an editor-pass item and is written down.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
WH = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.h"
WC = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.cpp"

header = WH.read_text(encoding="utf-8")
source = WC.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


header = swap(
    header,
    """ struct FSurface
 {
  TWeakObjectPtr<UNiagaraComponent> Niagara;
  FName Density;
  FName Strength;
  FName Beat;
  FName Input;
  FName Colour;
 };""",
    """ struct FSurface
 {
  TWeakObjectPtr<UNiagaraComponent> Niagara;
  FName Density;
  FName Strength;
  FName Beat;
  FName Input;
  FName Colour;
  /** FluidNinja's own API, bound by exact name (learned from the live surface). */
  FName SimSpeed;
  FName BrushStrength;
  FName BrushSize;
  FName BrushVelocity;
  FName SimplePainter;
  FName VolumeRender;
  FName FogVolumeRender;
 };""",
    "chorus header surface")

source = swap(
    source,
    """ // The beat has no parameter of its own on this surface: fall back to the density, so
 // the pulse still modulates something real.
 if (Surface.Beat.IsNone() && !Surface.Density.IsNone())
  Surface.Beat = Surface.Density;""",
    """ // The beat has no parameter of its own on this surface: fall back to the density, so
 // the pulse still modulates something real.
 if (Surface.Beat.IsNone() && !Surface.Density.IsNone())
  Surface.Beat = Surface.Density;

 // FluidNinja's OWN names, bound exactly. These are the parameters that make the water
 // sing: the sim's speed is the beat, the brush strength is the bass, the brush size
 // and velocity are the Chladni figure, and the simple painter draws the trails.
 {
  const auto Exact = [&](const TCHAR* Name) -> FName
  {
   for (const FNiagaraVariable& Variable : Variables)
    if (Variable.GetName() == FName(Name)) return Variable.GetName();
   return NAME_None;
  };
  Surface.SimSpeed = Exact(TEXT("User.SimSpeed"));
  Surface.BrushStrength = Exact(TEXT("User.Painter.BrushStrength"));
  Surface.BrushSize = Exact(TEXT("User.Painter.BrushSize"));
  Surface.BrushVelocity = Exact(TEXT("User.Painter.ParticleBrushVelocity"));
  Surface.SimplePainter = Exact(TEXT("User.SimplePainterMode"));
  Surface.VolumeRender = Exact(TEXT("User.VolumeRender"));
  Surface.FogVolumeRender = Exact(TEXT("User.FogVolumeRender"));
 }""",
    "chorus exact binding")

source = swap(
    source,
    """ UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS bound surface=%s density=%s strength=%s beat=%s input=%s"),
  *Niagara->GetName(),
  Surface.Density.IsNone() ? TEXT("-") : *Surface.Density.ToString(),
  Surface.Strength.IsNone() ? TEXT("-") : *Surface.Strength.ToString(),
  Surface.Beat.IsNone() ? TEXT("-") : *Surface.Beat.ToString(),
  Surface.Input.IsNone() ? TEXT("-") : *Surface.Input.ToString());""",
    """ UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS bound surface=%s simspeed=%s brush=%s size=%s velocity=%s painter=%s volume=%s fog=%s"),
  *Niagara->GetName(),
  Surface.SimSpeed.IsNone() ? TEXT("-") : *Surface.SimSpeed.ToString(),
  Surface.BrushStrength.IsNone() ? TEXT("-") : *Surface.BrushStrength.ToString(),
  Surface.BrushSize.IsNone() ? TEXT("-") : *Surface.BrushSize.ToString(),
  Surface.BrushVelocity.IsNone() ? TEXT("-") : *Surface.BrushVelocity.ToString(),
  Surface.SimplePainter.IsNone() ? TEXT("-") : *Surface.SimplePainter.ToString(),
  Surface.VolumeRender.IsNone() ? TEXT("-") : *Surface.VolumeRender.ToString(),
  Surface.FogVolumeRender.IsNone() ? TEXT("-") : *Surface.FogVolumeRender.ToString());""",
    "chorus receipt exact")

# the tick drives FluidNinja's own parameters
source = swap(
    source,
    """  if (!Surface.Beat.IsNone()) Niagara->SetVariableFloat(Surface.Beat, Pulse);""",
    """  // FLUIDNINJA'S OWN PARAMETERS - this is where the water sings.
  // The sim speeds up with the beat; the brush paints harder with the bass; the brush
  // radius and direction follow the Chladni figure; the simple painter draws the trails.
  if (!Surface.SimSpeed.IsNone())
   Niagara->SetVariableFloat(Surface.SimSpeed, 1.f + 1.5f * Pulse);
  if (!Surface.BrushStrength.IsNone())
   Niagara->SetVariableFloat(Surface.BrushStrength, 0.6f + 2.4f * FMath::Max(Bass, Field.Tension));
  if (!Surface.BrushSize.IsNone())
   Niagara->SetVariableFloat(Surface.BrushSize, 60.f + 90.f * Field.Tension);
  if (!Surface.BrushVelocity.IsNone())
   Niagara->SetVariableVec3(Surface.BrushVelocity, FVector(0.f, 0.f, 40.f + 120.f * Pulse));
  if (!Surface.SimplePainter.IsNone())
   Niagara->SetVariableBool(Surface.SimplePainter, true);
  if (!Surface.VolumeRender.IsNone()) Niagara->SetVariableBool(Surface.VolumeRender, true);
  if (!Surface.FogVolumeRender.IsNone()) Niagara->SetVariableBool(Surface.FogVolumeRender, true);

  if (!Surface.Beat.IsNone()) Niagara->SetVariableFloat(Surface.Beat, Pulse);""",
    "chorus tick fluidninja")

WC.write_text(source, encoding="utf-8")
WH.write_text(header, encoding="utf-8")
print("increment 10 applied: FluidNinja is bound by its exact API")
