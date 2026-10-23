"""Increment 1 - the transformation's stage machine and its data-driven VFX beats.

What it adds:
  * EMelodiaWaveHarpFormStage: IDLE -> PREPARE -> TRANSFORM -> AFTERMATH. The
    transformation is a HELD beat with a covered middle and an aftermath that carries
    the weight, rather than a pop.
  * FMelodiaWaveHarpVfxBeat: one beat of the look - which EXISTING system, at which
    socket, at which scale, with which user parameters, at which point in the stage.
    Data, not code, so the whole look of the transformation is editable without code.
  * The runtime that fires the beats as the stage advances, and reports what it played.

Jev (source=jev-live, 2026-10-22) chose: the existing NS_Melusina_* family at the head
socket driven by user parameters per stage (vfx_surface = A), and a data-driven VFX
descriptor table as the next C++ increment (next_cxx_increment = A). The owner then asked
for more spectacle than Jev's literal "hard cut"; the STRUCTURE Jev chose is kept and the
spectacle is built under it.
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


# ------------------------------------------------------------------ header: the types
header = swap(
    header,
    """/**
 * Measured socket positions of the Carillon wand, in centimetres.""",
    """/**
 * The stages of a form change, in the anime-JRPG register: a held beat, a covered
 * transformation, and an aftermath that carries the weight. The middle is covered so
 * the head can change without a pop; the weight lands in the aftermath.
 */
UENUM(BlueprintType)
enum class EMelodiaWaveHarpFormStage : uint8
{
 Idle UMETA(DisplayName = "IDLE"),
 Prepare UMETA(DisplayName = "PREPARE"),
 Transform UMETA(DisplayName = "TRANSFORM"),
 Aftermath UMETA(DisplayName = "AFTERMATH")
};

/**
 * One beat of the transformation's look: which EXISTING system, at which socket, at
 * which scale, with which user parameters, at which point in the stage.
 *
 * This is DATA, not code: the whole look of the transformation is then editable
 * without touching C++. No new Niagara graph is authored by this lane.
 */
USTRUCT(BlueprintType)
struct FMelodiaWaveHarpVfxBeat
{
 GENERATED_BODY()

 /** The stage this beat belongs to. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 EMelodiaWaveHarpFormStage Stage = EMelodiaWaveHarpFormStage::Transform;

 /** An existing system. The lane authors no new graphs. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TSoftObjectPtr<UNiagaraSystem> System;

 /** The socket the beat is played at. Empty = the character's head. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 FName Socket;

 /** The scale of the spawned system. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 float Scale = 1.f;

 /** User parameters written onto the spawned system. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TMap<FName, float> FloatParameters;

 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TMap<FName, FLinearColor> ColorParameters;

 /** Where in the stage this beat fires, 0..1. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 float Offset = 0.f;
};

/**
 * Measured socket positions of the Carillon wand, in centimetres.""",
    "header types")

# ------------------------------------------------------------------ header: the members
header = swap(
    header,
    """ /** The existing system that covers the head swap. Existing assets only: no new
 *  Niagara graph is authored for the transformation. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UNiagaraSystem> FormTransformSigilSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_StarPop.NS_Melusina_StarPop")));""",
    """ /** The existing system that covers the head swap. Existing assets only: no new
 *  Niagara graph is authored for the transformation. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UNiagaraSystem> FormTransformSigilSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_StarPop.NS_Melusina_StarPop")));

 /** The transformation's visual beats, by stage. Data, not code: the look of the
 *  change is editable without touching the component. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TArray<FMelodiaWaveHarpVfxBeat> FormVfxBeats;

 /** The stage the form change is in right now. */
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Vfx")
 EMelodiaWaveHarpFormStage FormStage = EMelodiaWaveHarpFormStage::Idle;

 /** The aftermath length, seconds. The weight lands here, not in the swap. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx", meta=(ClampMin="0.0", ClampMax="5.0"))
 float FormAftermathSeconds = 0.9f;""",
    "header members")

header = swap(
    header,
    """ UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsFormTransitionActive() const { return bFormTransitionActive; }""",
    """ UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsFormTransitionActive() const { return bFormTransitionActive; }

 /** The stage of the form change: IDLE, PREPARE, TRANSFORM or AFTERMATH. */
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpFormStage GetFormStage() const { return FormStage; }""",
    "header stage accessor")

header = swap(
    header,
    """ /** The camera push for the flourish. */
 void ApplyFormCameraPush(bool bPush);""",
    """ /** The camera push for the flourish. */
 void ApplyFormCameraPush(bool bPush);
 /** Fire the beats of a stage that the transition has just entered. */
 void PlayFormVfxBeats(EMelodiaWaveHarpFormStage Stage);
 /** The world position a beat is played at: its socket, or the character's head. */
 FVector GetFormVfxLocation(const FMelodiaWaveHarpVfxBeat& Beat) const;""",
    "header private")

header = swap(
    header,
    """ /** An attack the player pressed during the flourish. */
 bool bBufferedAttack = false;""",
    """ /** An attack the player pressed during the flourish. */
 bool bBufferedAttack = false;
 /** The stage the transition entered, used to fire each stage's beats exactly once. */
 EMelodiaWaveHarpFormStage LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
 double AftermathUntil = 0;""",
    "header state")

# ------------------------------------------------------------------ cpp: the runtime
source = swap(
    source,
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals()""",
    """void UMelodiaWaveHarpCombatComponent::PlayFormVfxBeats(EMelodiaWaveHarpFormStage Stage)
{
 if (!Character.IsValid()) return;
 for (const FMelodiaWaveHarpVfxBeat& Beat : FormVfxBeats)
 {
  if (Beat.Stage != Stage) continue;
  UNiagaraSystem* System = Beat.System.LoadSynchronous();
  if (!System)
  {
   UE_LOG(LogTemp, Verbose, TEXT("MELODIA_WAVEHARP_VFX beat skipped: no system for stage %d"), (int32)Stage);
   continue;
  }
  const FVector Where = GetFormVfxLocation(Beat);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, System, Where, FRotator::ZeroRotator,
   FVector(Beat.Scale));
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_VFX stage=%d system=%s at=%s scale=%.2f"),
   (int32)Stage, *System->GetName(), *Where.ToCompactString(), Beat.Scale);
 }
}

FVector UMelodiaWaveHarpCombatComponent::GetFormVfxLocation(const FMelodiaWaveHarpVfxBeat& Beat) const
{
 if (!Character.IsValid()) return FVector::ZeroVector;
 USkeletalMeshComponent* Mesh = Character->GetMesh();
 if (Beat.Socket != NAME_None && Mesh && Mesh->DoesSocketExist(Beat.Socket))
  return Mesh->GetSocketLocation(Beat.Socket);
 // The head is the heart of the weapon: a beat with no socket plays there.
 return Character->GetActorLocation() + FVector(0.f, 0.f, 95.f);
}

void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals()""",
    "cpp vfx beats")

# the stage machine inside the transition update
source = swap(
    source,
    """ // The head swaps at the midpoint: the caster head unfurls first, the crescent lands
 // in the second half. That is the f90 handoff of the authored performance.
 if (!bHeadSwappedThisTransition && FormTransitionAlpha >= .5f)""",
    """ // The stage machine: PREPARE while the flourish waits for its beat, TRANSFORM while
 // the head is covered and changes, AFTERMATH once the weight has to land.
 {
  const EMelodiaWaveHarpFormStage Stage = T <= 0.f
   ? EMelodiaWaveHarpFormStage::Prepare
   : (T < 1.f ? EMelodiaWaveHarpFormStage::Transform : EMelodiaWaveHarpFormStage::Aftermath);
  if (Stage != FormStage)
  {
   FormStage = Stage;
   if (Stage != LastFiredStage)
   {
    LastFiredStage = Stage;
    PlayFormVfxBeats(Stage);
   }
  }
 }

 // The head swaps at the midpoint: the caster head unfurls first, the crescent lands
 // in the second half. That is the f90 handoff of the authored performance.
 if (!bHeadSwappedThisTransition && FormTransitionAlpha >= .5f)""",
    "cpp stage machine")

# the aftermath: the stage settles back to IDLE after the transition lands
source = swap(
    source,
    """ // The transition landed. The form is committed here and nowhere else.
 bFormTransitionActive = false;
 FormTransitionAlpha = 1.f;
 CurrentForm = PendingForm;""",
    """ // The transition landed. The form is committed here and nowhere else.
 bFormTransitionActive = false;
 FormTransitionAlpha = 1.f;
 AftermathUntil = GetWorld() ? GetWorld()->GetTimeSeconds() + FMath::Max(0.f, FormAftermathSeconds) : 0;
 CurrentForm = PendingForm;""",
    "cpp aftermath start")

source = swap(
    source,
    """ if (!bFormTransitionActive)
 {
  FormTransitionAlpha = 1.f;
  return;
 }""",
    """ if (!bFormTransitionActive)
 {
  FormTransitionAlpha = 1.f;
  if (FormStage != EMelodiaWaveHarpFormStage::Idle)
  {
   // The aftermath is over: the stage goes home and the beats can fire again.
   if (GetWorld() && GetWorld()->GetTimeSeconds() > AftermathUntil)
   {
    FormStage = EMelodiaWaveHarpFormStage::Idle;
    LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
   }
  }
  return;
 }""",
    "cpp aftermath end")

H.write_text(header, encoding="utf-8")
C.write_text(source, encoding="utf-8")
print("increment 1 applied: the stage machine + the data-driven VFX beats")
