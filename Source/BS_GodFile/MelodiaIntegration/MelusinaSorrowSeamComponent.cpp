#include "MelusinaSorrowSeamComponent.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "MelodiaNarrativeSubsystem.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	constexpr TCHAR PaletteMPCPath[] = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette");
}

UMelusinaSorrowSeamComponent::UMelusinaSorrowSeamComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UMelusinaSorrowSeamComponent::BeginPlay()
{
	Super::BeginPlay();

	// ConstructorHelpers::FObjectFinder is constructor-only: its ctor fatals with
	// "FObjectFinders can't be used outside of constructors" when IsInConstructor is false.
	// LoadObject is the supported runtime lookup, and the veil is presentation-only so a
	// synchronous load here is bounded to one small MPC asset.
	if (!PaletteMPC)
	{
		PaletteMPC = LoadObject<UMaterialParameterCollection>(nullptr, PaletteMPCPath);
	}

	if (!PaletteMPC)
	{
		// Nothing to read: stop ticking rather than running a no-op every frame.
		UE_LOG(LogTemp, Warning,
			TEXT("MelusinaSorrowSeam: palette MPC '%s' not found; veil disabled for %s."),
			PaletteMPCPath, *GetNameSafe(GetOwner()));
		SetComponentTickEnabled(false);
	}
}

void UMelusinaSorrowSeamComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!PaletteMPC)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	float Dread = 0.f, Dissonance = 0.f, BeatPulse = 0.f, TemporalJitter = 0.f;
	if (UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(PaletteMPC))
	{
		Inst->GetScalarParameterValue(FName(TEXT("DreadPresence")), Dread);
		Inst->GetScalarParameterValue(FName(TEXT("DissonanceAmount")), Dissonance);
		Inst->GetScalarParameterValue(FName(TEXT("BeatPulse")), BeatPulse);
		Inst->GetScalarParameterValue(FName(TEXT("TemporalJitter")), TemporalJitter);
	}

	// World-healed overrides dread dim: lerp sheen to pristine 0.32 over 1.5s.
	const bool bHealed = IsWorldHealed();
	if (bHealed)
	{
		TargetSheen = HealedSheen;
	}
	CurrentSheen = FMath::FInterpTo(CurrentSheen, TargetSheen, DeltaTime, MendLerpSpeed);

	// Gate: at rest (all 0) -> no MID creation, byte-identical.
	if (FMath::IsNearlyZero(Dread) && FMath::IsNearlyZero(Dissonance) && FMath::IsNearlyZero(TemporalJitter) &&
		FMath::IsNearlyEqual(CurrentSheen, PristineSheen, 0.001f) && !bHealed)
	{
		return;
	}
	ApplyToMID();
	// Drive MID params if we have one; otherwise rely on MF_Madoka reading MPC directly (also valid).
	if (SorrowSeamMID)
	{
		SorrowSeamMID->SetScalarParameterValue(FName(TEXT("MadokaRealityWarp")), TemporalJitter);
		SorrowSeamMID->SetScalarParameterValue(FName(TEXT("DreadPresenceWarp")), Dread);
		SorrowSeamMID->SetScalarParameterValue(FName(TEXT("SheenIridescence")), CurrentSheen);
		// Breath: BeatPulse modulates emissive slightly — keep <0.08 so not flashy.
		SorrowSeamMID->SetScalarParameterValue(FName(TEXT("BeatBreath")), BeatPulse * 0.06f);
	}
}

bool UMelusinaSorrowSeamComponent::IsWorldHealed() const
{
	const UWorld* World = GetWorld();
	if (UGameInstance* GI = World ? World->GetGameInstance() : nullptr)
	{
		if (UMelodiaNarrativeSubsystem* Narr = GI->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			return Narr->IsWorldChallengeCompleted(
				FName(TEXT("challenge.first_resonance_echo")),
				FName(TEXT("challenge.first_resonance_echo.completed")));
		}
	}
	return false;
}

void UMelusinaSorrowSeamComponent::ApplyToMID()
{
	if (SorrowSeamMID || bMIDResolveAttempted)
	{
		return;
	}
	// Lazily create MID from the Sorrow Seam MI if the owner pawn has it on Trail slot.
	// This is presentation; if mesh not found, MF_Madoka still reads MPC directly so veil still warps.
	// Resolution is attempted exactly once: MI_Fabric_Melusina_SorrowSeam does not exist yet, so
	// re-scanning per tick would burn 8 GetMaterial calls and string compares every frame forever.
	bMIDResolveAttempted = true;

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	USkeletalMeshComponent* Mesh = Owner->FindComponentByClass<USkeletalMeshComponent>();
	if (!Mesh)
	{
		return;
	}

	// Try material index 0..7 for Trail; create MID from whatever is there and matches Sorrow Seam.
	const int32 SlotCount = FMath::Min(Mesh->GetNumMaterials(), 8);
	for (int32 Idx = 0; Idx < SlotCount; ++Idx)
	{
		UMaterialInterface* Mat = Mesh->GetMaterial(Idx);
		if (!Mat)
		{
			continue;
		}
		const FString MatName = Mat->GetName();
		if (MatName.Contains(TEXT("SorrowSeam")) || MatName.Contains(TEXT("Trail")))
		{
			SorrowSeamMID = Mesh->CreateDynamicMaterialInstance(Idx, Mat);
			break;
		}
	}
}
