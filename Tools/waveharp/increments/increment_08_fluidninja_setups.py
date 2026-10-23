"""Increment 8 - the chorus SPAWNS the FluidNinja setups, so the water can be tested
without placing anything in a level by hand.

Two setups, both existing assets:
  * the CHARACTER live actor (/Game/FluidNinjaLive/NinjaLive) attached to Melusina - it
    is the sim that tracks her bones, so her hair globulates and her movement leaves a
    trail;
  * a PUDDLE live actor at her feet - the small water body that sings with the bass.

The binding then finds them (the class name contains "NinjaLive") and binds their
exposed parameters by role, exactly as it does for the surfaces the owner places.
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
    """ /** Find the world's water surfaces and bind them by role. */
 void Start(UWorld& World);""",
    """ /** Find the world's water surfaces and bind them by role. */
 void Start(UWorld& World);

 /** (Re)bind every water surface in the world, by role. */
 void BindAll();

 /** Spawn the FluidNinja setups that belong to a character: the live actor that tracks
 *  her bones (the hair globulates, the movement leaves a trail) and the small water body
 *  at her feet (the puddles sing). Returns how many were spawned. */
 int32 SpawnCharacterSetups(AActor* Owner);""",
    "chorus header")

header = swap(
    header,
    """ TArray<FSurface> Surfaces;""",
    """ TArray<FSurface> Surfaces;
 TWeakObjectPtr<AActor> CharacterLive;
 TWeakObjectPtr<AActor> PuddleLive;""",
    "chorus header members")

source = swap(
    source,
    """void FMelodiaWaterChorus::Stop()
{
 Surfaces.Reset();
 BoundParameterCount = 0;
 bStarted = false;
}""",
    """void FMelodiaWaterChorus::Stop()
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
 const auto SpawnLive = [&](AActor*& Slot, const FVector& Location, const float Scale) -> bool
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
}""",
    "chorus spawn")

source = swap(
    source,
    """void FMelodiaWaterChorus::Start(UWorld& World)
{
 Stop();
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
}""",
    """void FMelodiaWaterChorus::Start(UWorld& World)
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
}""",
    "chorus start")

# the tick spawns and re-binds once
source = swap(
    source,
    """ if (!bStarted || !Owner) return;
 UWorld* World = Owner->GetWorld();
 if (!World) return;""",
    """ if (!bStarted || !Owner) return;
 UWorld* World = Owner->GetWorld();
 if (!World) return;

 // The setups come with the character: the live actor that tracks her bones and the
 // water body at her feet. Then the binding sees them.
 if (!CharacterLive.IsValid())
 {
  if (SpawnCharacterSetups(Owner) > 0)
   BindAll();
 }""",
    "chorus tick spawn")

WC.write_text(source, encoding="utf-8")
WH.write_text(header, encoding="utf-8")
print("increment 8 applied: the chorus spawns the FluidNinja setups")
