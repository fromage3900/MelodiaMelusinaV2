"""Increment 9 - the role binding learns from the live data.

The first live run bound:
    density  -> User.VelocityDensityInputTexture   (a TEXTURE)
    strength -> User.Painter.ForceAdditiveStrokeBlending (a BOOL)
    beat     -> nothing
    input    -> User.Painter.ParticleBrushVelocity  (a VECTOR)

So the matcher was binding by NAME only, and happily picked a texture for a float role.

Two fixes, both learned from the live run:
  1. a type heuristic: a parameter whose name says it is a texture or a flag is NOT a
     float role, and the most specific (shortest) name wins;
  2. the receipt now dumps EVERY exposed user parameter of the surface, once per bind, so
     the next iteration of the loop can pick the exact names instead of guessing.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
WC = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.cpp"

source = WC.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


# the role matcher gains a type heuristic
source = swap(
    source,
    """FName FMelodiaWaterChorus::RoleForParameter(const FString& ParameterName)
{""",
    """namespace
{
/** The name says it is not a float: a texture, a flag, a curve or a mesh. */
bool MelodiaIsNotAFloat(const FString& Name)
{
 return Name.Contains(TEXT("Texture")) || Name.Contains(TEXT("Blending"))
  || Name.Contains(TEXT("Enable")) || Name.Contains(TEXT("Toggle"))
  || Name.Contains(TEXT("Curve")) || Name.Contains(TEXT("Mesh"))
  || Name.Contains(TEXT("Material")) || Name.Contains(TEXT("Array"));
}
}

FName FMelodiaWaterChorus::RoleForParameter(const FString& ParameterName)
{""",
    "chorus type heuristic")

# the binding: skip the non-floats for the float roles, prefer the shortest name
source = swap(
    source,
    """ TArray<FNiagaraVariable> Variables;
 Niagara->GetOverrideParameters().GetParameters(Variables);
 for (const FNiagaraVariable& Variable : Variables)
 {
  const FString Name = Variable.GetName().ToString();
  const FName Role = RoleForParameter(Name);
  if (Role.IsNone()) continue;
  ++BoundParameterCount;
  if (Role == TEXT("Density")) Surface.Density = Variable.GetName();
  else if (Role == TEXT("Strength")) Surface.Strength = Variable.GetName();
  else if (Role == TEXT("Beat")) Surface.Beat = Variable.GetName();
  else if (Role == TEXT("Input")) Surface.Input = Variable.GetName();
  else if (Role == TEXT("Colour")) Surface.Colour = Variable.GetName();
 }""",
    """ TArray<FNiagaraVariable> Variables;
 Niagara->GetOverrideParameters().GetParameters(Variables);
 for (const FNiagaraVariable& Variable : Variables)
 {
  const FString Name = Variable.GetName().ToString();
  const FName Role = RoleForParameter(Name);
  if (Role.IsNone()) continue;
  // The float roles need a FLOAT. A texture or a flag named "Density" is not one.
  if (Role == TEXT("Density") || Role == TEXT("Strength") || Role == TEXT("Beat"))
  {
   if (MelodiaIsNotAFloat(Name)) continue;
  }
  ++BoundParameterCount;

  // The most specific name wins: the shortest match for a role.
  const auto IsBetter = [](const FName& Current, const FString& Candidate)
  {
   return Current.IsNone() || Candidate.Len() < Current.ToString().Len();
  };
  if (Role == TEXT("Density"))
  {
   if (IsBetter(Surface.Density, Name)) Surface.Density = Variable.GetName();
  }
  else if (Role == TEXT("Strength"))
  {
   if (IsBetter(Surface.Strength, Name)) Surface.Strength = Variable.GetName();
  }
  else if (Role == TEXT("Beat"))
  {
   if (IsBetter(Surface.Beat, Name)) Surface.Beat = Variable.GetName();
  }
  else if (Role == TEXT("Input"))
  {
   if (IsBetter(Surface.Input, Name)) Surface.Input = Variable.GetName();
  }
  else if (Role == TEXT("Colour"))
  {
   if (IsBetter(Surface.Colour, Name)) Surface.Colour = Variable.GetName();
  }
 }

 // The beat has no parameter of its own on this surface: fall back to the density, so
 // the pulse still modulates something real.
 if (Surface.Beat.IsNone() && !Surface.Density.IsNone())
  Surface.Beat = Surface.Density;""",
    "chorus binding")

# the receipt dumps the exposed parameters, once, so the next iteration picks exactly
source = swap(
    source,
    """ UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS bound surface=%s density=%s strength=%s beat=%s input=%s"),
  *Niagara->GetName(),
  Surface.Density.IsNone() ? TEXT("-") : *Surface.Density.ToString(),
  Surface.Strength.IsNone() ? TEXT("-") : *Surface.Strength.ToString(),
  Surface.Beat.IsNone() ? TEXT("-") : *Surface.Beat.ToString(),
  Surface.Input.IsNone() ? TEXT("-") : *Surface.Input.ToString());""",
    """ UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS bound surface=%s density=%s strength=%s beat=%s input=%s"),
  *Niagara->GetName(),
  Surface.Density.IsNone() ? TEXT("-") : *Surface.Density.ToString(),
  Surface.Strength.IsNone() ? TEXT("-") : *Surface.Strength.ToString(),
  Surface.Beat.IsNone() ? TEXT("-") : *Surface.Beat.ToString(),
  Surface.Input.IsNone() ? TEXT("-") : *Surface.Input.ToString());

 // The diagnostic: every exposed user parameter, once per surface, so the next loop
 // iteration binds by EXACT name instead of by pattern.
 {
  static TSet<FString> Dumped;
  const FString Key = Niagara->GetName();
  if (!Dumped.Contains(Key))
  {
   Dumped.Add(Key);
   FString Exposed;
   for (const FNiagaraVariable& Variable : Variables)
    Exposed += FString::Printf(TEXT("%s | "), *Variable.GetName().ToString());
   UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS_EXPOSED %s (%d): %s"),
    *Key, Variables.Num(), *Exposed);
  }
 }""",
    "chorus diagnostic dump")

WC.write_text(source, encoding="utf-8")
print("increment 9 applied: the role binding is type-aware and the receipt dumps the exposed parameters")
