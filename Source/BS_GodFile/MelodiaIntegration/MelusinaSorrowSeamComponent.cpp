#include "MelusinaSorrowSeamComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "MelodiaNarrativeSubsystem.h"
#include "Components/SkeletalMeshComponent.h"

UMelusinaSorrowSeamComponent::UMelusinaSorrowSeamComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UMelusinaSorrowSeamComponent::BeginPlay()
{
	Super::BeginPlay();
	// PaletteMPC resolved via soft ref or subsystem locator — no hard load here to keep cooker happy.
	if (!PaletteMPC)
	{
		// Try to find /Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette if not assigned.
		static ConstructorHelpers::FObjectFinder<UMaterialParameterCollection> Finder(TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"));
		if (Finder.Succeeded()) PaletteMPC = Finder.Object;
	}
}

void UMelusinaSorrowSeamComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!PaletteMPC) return;

	float Dread = 0.f, Dissonance = 0.f, BeatPulse = 0.f, TemporalJitter = 0.f;
	if (GetWorld())
	{
		if (auto* Inst = GetWorld()->GetParameterCollectionInstance(PaletteMPC))
		{
			Inst->GetScalarParameterValue(FName(TEXT("DreadPresence")), Dread);
			Inst->GetScalarParameterValue(FName(TEXT("DissonanceAmount")), Dissonance);
			Inst->GetScalarParameterValue(FName(TEXT("BeatPulse")), BeatPulse);
			Inst->GetScalarParameterValue(FName(TEXT("TemporalJitter")), TemporalJitter);
		}
	}

	// World-healed overrides dread dim: lerp sheen to pristine 0.32 over 1.5s.
	if (IsWorldHealed())
	{
		TargetSheen = 0.32f;
	}
	CurrentSheen = FMath::FInterpTo(CurrentSheen, TargetSheen, DeltaTime, MendLerpSpeed);

	// Gate: at rest (all 0) -> no MID creation, byte-identical.
	if (FMath::IsNearlyZero(Dread) && FMath::IsNearlyZero(Dissonance) && FMath::IsNearlyZero(TemporalJitter) && FMath::IsNearlyEqual(CurrentSheen, 0.18f, 0.001f) && !IsWorldHealed())
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
	if (auto* GI = GetWorld() ? GetWorld()->GetGameInstance() : nullptr)
	{
		if (auto* Narr = GI->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			return Narr->IsWorldChallengeCompleted(FName(TEXT("challenge.first_resonance_echo")), FName(TEXT("challenge.first_resonance_echo.completed")));
		}
	}
	return false;
}

void UMelusinaSorrowSeamComponent::ApplyToMID()
{
	if (SorrowSeamMID) return;
	// Lazily create MID from the Sorrow Seam MI if the owner pawn has it on Trail slot.
	// This is presentation; if mesh not found, MF_Madoka still reads MPC directly so veil still warps.
	if (AActor* Owner = GetOwner())
	{
		if (auto* Mesh = Owner->FindComponentByClass<USkeletalMeshComponent>())
		{
			// Try material index 0..7 for Trail; create MID from whatever is there and matches Sorrow Seam.
			for (int32 Idx = 0; Idx < 8; ++Idx)
			{
				if (UMaterialInterface* Mat = Mesh->GetMaterial(Idx))
				{
					if (Mat->GetName().Contains(TEXT("SorrowSeam")) || Mat->GetName().Contains(TEXT("Trail")))
					{
						SorrowSeamMID = Mesh->CreateDynamicMaterialInstance(Idx, Mat);
						break;
					}
				}
			}
		}
	}
}
