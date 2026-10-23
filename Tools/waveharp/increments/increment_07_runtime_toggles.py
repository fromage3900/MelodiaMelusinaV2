"""Increment 7 - the runtime toggles, so the new paths can be tested without editing a
Blueprint.

  * bEnableWaterChorus and bUseHeadSwap are properties on a component that lives on the
    character Blueprint, so turning them on means opening the BP. Two console commands
    make them testable in seconds instead:
        Melodia.WaveHarp.WaterChorus 0|1
        Melodia.WaveHarp.HeadSwap   0|1

  * restoring the head-swap path also restores the shipped representation's visibility,
    which the wand path had hidden.
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


header = swap(
    header,
    """ /** The stage of the form change: IDLE, PREPARE, TRANSFORM or AFTERMATH. */
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpFormStage GetFormStage() const { return FormStage; }""",
    """ /** The stage of the form change: IDLE, PREPARE, TRANSFORM or AFTERMATH. */
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpFormStage GetFormStage() const { return FormStage; }

 /** Turn the world's water chorus on or off at runtime (the surfaces have to exist). */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 void SetWaterChorusEnabled(bool bEnabled);

 /** Turn the refined wand (shaft + Carillon head) on or off at runtime, so the head
 *  swap can be A/B-ed against the shipped skeletal path without touching the Blueprint. */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 void SetHeadSwapEnabled(bool bEnabled);

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsWaterChorusEnabled() const { return bEnableWaterChorus; }

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsHeadSwapEnabled() const { return bUseHeadSwap; }""",
    "header toggles")

source = swap(
    source,
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals(const bool bBurst)""",
    """void UMelodiaWaveHarpCombatComponent::SetWaterChorusEnabled(const bool bEnabled)
{
 if (bEnableWaterChorus == bEnabled) return;
 bEnableWaterChorus = bEnabled;
 if (bEnabled)
 {
  if (GetWorld()) WaterChorus.Start(*GetWorld());
  StatusText = TEXT("CHORUS  /  The water sings with the beat.");
 }
 else
 {
  WaterChorus.Stop();
  StatusText = TEXT("CHORUS  /  Off.");
 }
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHORUS_TOGGLE enabled=%d"), bEnabled ? 1 : 0);
}

void UMelodiaWaveHarpCombatComponent::SetHeadSwapEnabled(const bool bEnabled)
{
 if (bUseHeadSwap == bEnabled) return;
 bUseHeadSwap = bEnabled;
 // The wand path hides the shipped representation; turning it off puts it back.
 if (Instrument) Instrument->SetVisibility(true);
 ApplyFormVisuals();
 StatusText = bEnabled
  ? TEXT("HEAD SWAP  /  The refined Carillon wand is live.")
  : TEXT("HEAD SWAP  /  The shipped representation is live.");
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_HEADSWAP_TOGGLE enabled=%d"), bEnabled ? 1 : 0);
}

void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals(const bool bBurst)""",
    "cpp toggles")

source = swap(
    source,
    """void UMelodiaWaveHarpCombatComponent::UpdateWandPresentation()
{
 if (!Wand) return;
 const bool bWandPath = bUseHeadSwap;
 Wand->SetVisibility(bWandPath);
 if (!bWandPath) return;""",
    """void UMelodiaWaveHarpCombatComponent::UpdateWandPresentation()
{
 if (!Wand) return;
 const bool bWandPath = bUseHeadSwap;
 Wand->SetVisibility(bWandPath);
 if (!bWandPath)
 {
  // The shipped representation is back.
  if (Instrument) Instrument->SetVisibility(true);
  return;
 }""",
    "cpp restore the shipped representation")

# the two console commands
source = swap(
    source,
    """// Print the resolved form state (the PIE receipt for the form system).""",
    """// Toggle the water chorus at runtime (the surfaces must exist in the level).
static FAutoConsoleCommandWithWorldAndArgs GMelodiaWaterChorusToggle(
 TEXT("Melodia.WaveHarp.WaterChorus"),
 TEXT("Turn the world's water chorus on or off: Melodia.WaveHarp.WaterChorus 0|1"),
 FConsoleCommandWithWorldAndArgsDelegate::CreateStatic([](const TArray<FString>& Args, UWorld* World)
 {
  if (!World || Args.Num() < 1) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
   Combat->SetWaterChorusEnabled(FCString::Atoi(*Args[0]) != 0);
 }));

// Toggle the refined wand (head swap) at runtime.
static FAutoConsoleCommandWithWorldAndArgs GMelodiaHeadSwapToggle(
 TEXT("Melodia.WaveHarp.HeadSwap"),
 TEXT("Turn the refined Carillon wand on or off: Melodia.WaveHarp.HeadSwap 0|1"),
 FConsoleCommandWithWorldAndArgsDelegate::CreateStatic([](const TArray<FString>& Args, UWorld* World)
 {
  if (!World || Args.Num() < 1) return;
  ACharacter* Char = nullptr;
  for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
  {
   if (APlayerController* PC = It->Get())
    if (PC->GetPawn()) { Char = Cast<ACharacter>(PC->GetPawn()); break; }
  }
  if (!Char) { UE_LOG(LogTemp, Warning, TEXT("MELODIA_WAVEHARP no local player pawn.")); return; }
  if (UMelodiaWaveHarpCombatComponent* Combat = Char->FindComponentByClass<UMelodiaWaveHarpCombatComponent>())
   Combat->SetHeadSwapEnabled(FCString::Atoi(*Args[0]) != 0);
 }));

// Print the resolved form state (the PIE receipt for the form system).""",
    "cpp toggle commands")

H.write_text(header, encoding="utf-8")
C.write_text(source, encoding="utf-8")
print("increment 7 applied: the runtime toggles for the water chorus and the head swap")
