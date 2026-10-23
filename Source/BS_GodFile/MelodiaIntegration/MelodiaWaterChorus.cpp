#include "MelodiaWaterChorus.h"

#include "Components/ActorComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaWorldFieldBus.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "EngineUtils.h"

namespace MelodiaWaterChorusPaths
{
// Every system here already exists in the project. This lane authors no graphs.
const TCHAR* HorizonRain = TEXT("/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_RainRipples.NS_Uni_RainRipples");
const TCHAR* SkylineBubbles = TEXT("/Game/Melodia/VFX/NS_Melusina_Globules.NS_Melusina_Globules");
const TCHAR* HairGlobules = TEXT("/Game/Melodia/VFX/NS_Melusina_Globules.NS_Melusina_Globules");
const TCHAR* FootSplash = TEXT("/Game/Melodia/VFX/NS_Melusina_Splash.NS_Melusina_Splash");
const TCHAR* SkylineMist = TEXT("/Game/Melodia/VFX/NS_Morning_PondMist.NS_Morning_PondMist");
const TCHAR* AudioPalette = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
}

void FMelodiaWaterChorus::Start(UWorld& World)
{
 Surfaces.Reset();
 BoundParameterCount = 0;
 bStarted = true;

 // The world's FluidNinja surfaces: the live actors that simulate the water.
 for (TActorIterator<AActor> It(&World); It; ++It)
 {
  AActor* Actor = *It;
  if (!Actor || Actor->IsHidden()) continue;
  const FString ClassName = Actor->GetClass()->GetName();
  const bool bLooksLive = ClassName.Contains(TEXT("NinjaLive")) || ClassName.Contains(TEXT("LiveActor"));
  if (!bLooksLive) continue;
  TInlineComponentArray<UNiagaraComponent*> NiagaraComponents(Actor);
  for (UNiagaraComponent* Niagara : NiagaraComponents)
  {
   if (!Niagara) continue;
   BindSurface(Niagara);
  }
 }

 UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS start surfaces=%d parameters=%d"),
  Surfaces.Num(), BoundParameterCount);
}

void FMelodiaWaterChorus::Stop()
{
 Surfaces.Reset();
 BoundParameterCount = 0;
 bStarted = false;
 CharacterLive.Reset();
 PuddleLive.Reset();
}

void FMelodiaWaterChorus::BindAll()
{
 Surfaces.Reset();
 BoundParameterCount = 0;
 UWorld* World = nullptr;
 for (const TWeakObjectPtr<AActor>& Candidate : { CharacterLive, PuddleLive })
 {
  if (AActor* Actor = Candidate.Get())
   if (!World) World = Actor->GetWorld();
 }
 if (!World) return;
 for (TActorIterator<AActor> It(World); It; ++It)
 {
  AActor* Actor = *It;
  if (!Actor || Actor->IsHidden()) continue;
  const FString ClassName = Actor->GetClass()->GetName();
  if (!ClassName.Contains(TEXT("NinjaLive")) && !ClassName.Contains(TEXT("LiveActor"))) continue;
  TInlineComponentArray<UNiagaraComponent*> NiagaraComponents(Actor);
  for (UNiagaraComponent* Niagara : NiagaraComponents)
   if (Niagara) BindSurface(Niagara);
 }
}

int32 FMelodiaWaterChorus::SpawnCharacterSetups(AActor* Owner)
{
 if (!Owner) return 0;
 UWorld* World = Owner->GetWorld();
 if (!World) return 0;

 UClass* LiveClass = LoadClass<AActor>(nullptr, TEXT("/Game/FluidNinjaLive/NinjaLive.NinjaLive_C"));
 if (!LiveClass)
 {
  UE_LOG(LogTemp, Warning, TEXT("MELODIA_WATER_CHORUS no FluidNinja live actor class at /Game/FluidNinjaLive/NinjaLive"));
  return 0;
 }

 int32 Spawned = 0;
 const auto SpawnLive = [&](TWeakObjectPtr<AActor>& Slot, const FVector& Location, const float Scale) -> bool
 {
  if (Slot.IsValid()) return false;
  FActorSpawnParameters Spawn;
  Spawn.Owner = Owner;
  Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  AActor* Actor = World->SpawnActor<AActor>(LiveClass, Location, FRotator::ZeroRotator, Spawn);
  if (!Actor) return false;
  Actor->SetActorScale3D(FVector(Scale));
  Slot = Actor;
  ++Spawned;
  return true;
 };

 // The character live actor: the sim that tracks her bones.
 if (SpawnLive(CharacterLive, Owner->GetActorLocation(), 1.f)
  && CharacterLive.IsValid())
 {
  CharacterLive->AttachToComponent(Owner->GetRootComponent(),
   FAttachmentTransformRules::KeepRelativeTransform);
 }
 // The puddle: a small water body at her feet.
 SpawnLive(PuddleLive, Owner->GetActorLocation() + FVector(0.f, 0.f, 4.f), 0.25f);

 UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS spawned=%d character=%s puddle=%s"),
  Spawned,
  CharacterLive.IsValid() ? *CharacterLive->GetName() : TEXT("-"),
  PuddleLive.IsValid() ? *PuddleLive->GetName() : TEXT("-"));
 return Spawned;
}

namespace
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
{
 // Role binding by name pattern: a renamed upstream parameter becomes a log line, not
 // a silent no-op. The roles are the ones the water actually needs.
 if (ParameterName.Contains(TEXT("Density"), ESearchCase::IgnoreCase)) return TEXT("Density");
 if (ParameterName.Contains(TEXT("Strength"), ESearchCase::IgnoreCase)
  || ParameterName.Contains(TEXT("Force"), ESearchCase::IgnoreCase)) return TEXT("Strength");
 if (ParameterName.Contains(TEXT("Beat"), ESearchCase::IgnoreCase)
  || ParameterName.Contains(TEXT("Pulse"), ESearchCase::IgnoreCase)) return TEXT("Beat");
 if (ParameterName.Contains(TEXT("Brush"), ESearchCase::IgnoreCase)
  || ParameterName.Contains(TEXT("Splat"), ESearchCase::IgnoreCase)
  || ParameterName.Contains(TEXT("InputPosition"), ESearchCase::IgnoreCase)) return TEXT("Input");
 if (ParameterName.Contains(TEXT("Tint"), ESearchCase::IgnoreCase)
  || ParameterName.Contains(TEXT("Colour"), ESearchCase::IgnoreCase)) return TEXT("Colour");
 return NAME_None;
}

void FMelodiaWaterChorus::BindSurface(UNiagaraComponent* Niagara)
{
 if (!Niagara) return;
 FSurface Surface;
 Surface.Niagara = Niagara;

 TArray<FNiagaraVariable> Variables;
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
 }

 Surfaces.Add(Surface);
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS bound surface=%s simspeed=%s brush=%s size=%s velocity=%s painter=%s volume=%s fog=%s"),
  *Niagara->GetName(),
  Surface.SimSpeed.IsNone() ? TEXT("-") : *Surface.SimSpeed.ToString(),
  Surface.BrushStrength.IsNone() ? TEXT("-") : *Surface.BrushStrength.ToString(),
  Surface.BrushSize.IsNone() ? TEXT("-") : *Surface.BrushSize.ToString(),
  Surface.BrushVelocity.IsNone() ? TEXT("-") : *Surface.BrushVelocity.ToString(),
  Surface.SimplePainter.IsNone() ? TEXT("-") : *Surface.SimplePainter.ToString(),
  Surface.VolumeRender.IsNone() ? TEXT("-") : *Surface.VolumeRender.ToString(),
  Surface.FogVolumeRender.IsNone() ? TEXT("-") : *Surface.FogVolumeRender.ToString());

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
 }
}

FVector FMelodiaWaterChorus::HorizonPoint(const AActor* Owner, const float Distance, const float Height) const
{
 if (!Owner) return FVector::ZeroVector;
 const FVector Base = Owner->GetActorLocation();
 const FVector Forward = Owner->GetActorForwardVector();
 return Base + Forward * Distance + FVector(0.f, 0.f, Height);
}

void FMelodiaWaterChorus::DispatchBeat(AActor* Owner)
{
 ++Beats;

 // 1. RAIN OVER THE HORIZON: the droplets disperse where the sky meets the world.
 if (UNiagaraSystem* Rain = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::HorizonRain))
 {
  const FVector Where = HorizonPoint(Owner, 4200.f, 900.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Rain, Where, FRotator::ZeroRotator, FVector(2.4f));
  ++Dispatches;
 }

 // 2. THE SKYLINE DOTS WITH BUBBLES.
 if (UNiagaraSystem* Bubbles = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::SkylineBubbles))
 {
  const FVector Where = HorizonPoint(Owner, 2600.f, 1500.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Bubbles, Where, FRotator::ZeroRotator, FVector(1.6f));
  ++Dispatches;
 }

 if (!Owner) return;

 // 3. HER HAIR GLOBULATES: the water beads in her hair on the beat.
 if (UNiagaraSystem* Globules = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::HairGlobules))
 {
  const FVector Where = Owner->GetActorLocation() + FVector(0.f, 0.f, 150.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Globules, Where, FRotator::ZeroRotator, FVector(.55f));
  ++Dispatches;
 }

 // 4. THE PUDDLES ANSWER: a splash where she stands.
 if (UNiagaraSystem* Splash = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::FootSplash))
 {
  const FVector Where = Owner->GetActorLocation() + FVector(0.f, 0.f, 6.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Splash, Where, FRotator::ZeroRotator, FVector(.8f));
  ++Dispatches;
 }
}

void FMelodiaWaterChorus::Burst(AActor* Owner, const float Scale)
{
 if (!Owner) return;
 ++Dispatches;
 const FVector Base = Owner->GetActorLocation();
 if (UNiagaraSystem* Globules = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::HairGlobules))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 140.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Globules, Where, FRotator::ZeroRotator,
   FVector(Scale * .8f));
 }
 if (UNiagaraSystem* Splash = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::FootSplash))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 8.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Splash, Where, FRotator::ZeroRotator,
   FVector(Scale));
 }
 if (UNiagaraSystem* Mist = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::SkylineMist))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 60.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Mist, Where, FRotator::ZeroRotator,
   FVector(Scale * 1.4f));
 }
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS burst scale=%.2f"), Scale);
}

void FMelodiaWaterChorus::Tick(float Delta, AActor* Owner)
{
 if (!bStarted || !Owner) return;
 UWorld* World = Owner->GetWorld();
 if (!World) return;

 // The setups come with the character: the live actor that tracks her bones and the
 // water body at her feet. Then the binding sees them.
 if (!CharacterLive.IsValid())
 {
  if (SpawnCharacterSetups(Owner) > 0)
   BindAll();
 }

 // The beat, read from the clock the project already owns. This class is a reader.
 const float Phase = UMelodiaMusicClockSubsystem::GetMusicBeatPhase(World);
 const float Pulse = UMelodiaMusicClockSubsystem::GetMusicPulse(World);

 // The bass band: the puddles sing with it. READ ONLY - the audio-reactive subsystem
 // stays the sole writer of the palette.
 float Bass = 0.f;
 if (UMaterialParameterCollection* Palette = LoadObject<UMaterialParameterCollection>(
  nullptr, MelodiaWaterChorusPaths::AudioPalette))
 {
  // The LIVE value, read the way the project's own cymatics reader reads it: through
  // the world's parameter collection instance.
  if (UMaterialParameterCollectionInstance* Instance = World->GetParameterCollectionInstance(Palette))
   Instance->GetScalarParameterValue(FName(TEXT("BassIntensity")), Bass);
 }

 // THE CHLADNI DISPERSION: the world field bus carries the standing-wave signature
 // (ModeN, ModeM) and the tension that the cymatics subsystem publishes. The water
 // disperses ALONG that figure: the fluid's input point rides the field's position and
 // its strength rides the field's tension. READ ONLY - the cymatics subsystem stays
 // the only publisher.
 const FWorldFieldSample Field =
  UWorldFieldBus::SampleResonanceTension(Owner->GetActorLocation());

 // A downbeat is a wrap of the phase.
 const bool bBeat = PreviousPhase >= 0.f && Phase < PreviousPhase;
 PreviousPhase = Phase;
 if (bBeat) DispatchBeat(Owner);

 // The water itself moves with the music: the beat and the bass drive the bound roles.
 for (const FSurface& Surface : Surfaces)
 {
  UNiagaraComponent* Niagara = Surface.Niagara.Get();
  if (!Niagara) continue;
  // FLUIDNINJA'S OWN PARAMETERS - this is where the water sings.
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

  if (!Surface.Beat.IsNone()) Niagara->SetVariableFloat(Surface.Beat, Pulse);
  if (!Surface.Strength.IsNone())
   Niagara->SetVariableFloat(Surface.Strength, 0.35f + 0.65f * FMath::Max(Bass, Field.Tension));
  if (!Surface.Density.IsNone()) Niagara->SetVariableFloat(Surface.Density, 0.4f + 0.6f * Pulse);
  // The dispersal point rides the Chladni field.
  if (!Surface.Input.IsNone())
   Niagara->SetVariablePosition(Surface.Input, Field.WorldPosition);
  if (!Surface.Colour.IsNone())
   Niagara->SetVariableLinearColor(Surface.Colour, FLinearColor(0.48f, 0.36f, 0.94f, 1.f));
 }
}
