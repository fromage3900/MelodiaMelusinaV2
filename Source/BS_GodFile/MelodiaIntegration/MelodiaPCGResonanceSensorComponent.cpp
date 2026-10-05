#include "MelodiaPCGResonanceSensorComponent.h"
#include "MelodiaHarmonicStateSubsystem.h"
#include "MelodiaWorldFieldBus.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"

UMelodiaPCGResonanceSensorComponent::UMelodiaPCGResonanceSensorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = 0.1f;
	SetIsReplicatedByDefault(false);
}

void UMelodiaPCGResonanceSensorComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		HarmonicState = World->GetSubsystem<UMelodiaHarmonicStateSubsystem>();
	}
	Rescan(); // publish the first field source immediately so SampleAt is not empty
}

void UMelodiaPCGResonanceSensorComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (FieldSourceId != 0)
	{
		UWorldFieldBus::RemoveFieldSource(FieldSourceId);
		FieldSourceId = 0;
	}
	Super::EndPlay(EndPlayReason);
}

void UMelodiaPCGResonanceSensorComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	RescanTimer += DeltaTime;
	if (RescanTimer >= RescanIntervalSec)
	{
		RescanTimer = 0.0f;
		Rescan();
	}

	// The eased density is what the harmonic spine (and therefore the MPC lane and the
	// field source) carries. Push it every tick; the subsystem publishes it unchanged.
	if (HarmonicState.IsValid())
	{
		HarmonicState->SetPCGResonanceDensity(Density);
	}
}

void UMelodiaPCGResonanceSensorComponent::Rescan()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	FVector SamplePoint = LastSamplePoint;
	if (bSamplePlayer)
	{
		if (const APlayerController* PC = World->GetFirstPlayerController())
		{
			if (const APawn* Pawn = PC->GetPawn())
			{
				SamplePoint = Pawn->GetActorLocation();
			}
		}
	}
	if (SamplePoint.IsNearlyZero())
	{
		if (const AActor* Owner = GetOwner())
		{
			SamplePoint = Owner->GetActorLocation();
		}
	}
	LastSamplePoint = SamplePoint;

	// Slow scan: count resonant-tagged instances within the radius. One pass over the
	// level's actors (same TActorIterator + GetComponents pattern the cymatic field uses),
	// O(instances) but only every RescanIntervalSec.
	int32 NearCount = 0;
	const float RadiusSq = DensityRadiusCm * DensityRadiusCm;
	for (TActorIterator<AActor> It(World); It && NearCount < DensityFullCount; ++It)
	{
		AActor* Actor = *It;
		if (!Actor)
		{
			continue;
		}
		const bool bActorTagged = Actor->ActorHasTag(ResonantTag);

		TInlineComponentArray<UInstancedStaticMeshComponent*> Comps;
		Actor->GetComponents(Comps);
		for (UInstancedStaticMeshComponent* Comp : Comps)
		{
			if (!Comp || Comp->GetInstanceCount() == 0)
			{
				continue;
			}
			if (!bActorTagged && !Comp->ComponentHasTag(ResonantTag))
			{
				continue;
			}
			for (int32 i = 0; i < Comp->GetInstanceCount(); ++i)
			{
				FTransform T;
				if (!Comp->GetInstanceTransform(i, T, /*bWorldSpace*/ true))
				{
					continue;
				}
				if (FVector::DistSquared(T.GetLocation(), SamplePoint) <= RadiusSq)
				{
					++NearCount;
				}
				if (NearCount >= DensityFullCount)
				{
					break;
				}
			}
		}
	}

	const float Target = FMath::Clamp(static_cast<float>(NearCount) / static_cast<float>(DensityFullCount), 0.0f, 1.0f);
	Density = FMath::FInterpTo(Density, Target, RescanIntervalSec, 0.8f);

	UpdateFieldSource();
}

void UMelodiaPCGResonanceSensorComponent::UpdateFieldSource()
{
	if (FieldSourceId != 0)
	{
		UWorldFieldBus::RemoveFieldSource(FieldSourceId);
		FieldSourceId = 0;
	}

	// Register this volume's PCG cluster as a local spatial field source so
	// UWorldFieldBus::SampleAt() is genuinely PCG-aware around it. The signature
	// rides the current harmonic mode (N = 1 + mode), tension rides the local density.
	uint8 Mode = 0;
	float Tension = 0.0f;
	float Consonance = 0.5f;
	float BeatPulse = 0.0f;
	if (const UMelodiaHarmonicStateSubsystem* H = HarmonicState.Get())
	{
		Mode = static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(H->GetMode()), 0, 4));
		Tension = H->GetTension();
		Consonance = H->GetConsonance();
		BeatPulse = H->GetResolution();
	}
	FieldSourceId = UWorldFieldBus::PublishFieldSource(
		LastSamplePoint, DensityRadiusCm,
		1 + static_cast<int32>(Mode), 2,
		Tension * Density, BeatPulse, Mode, Consonance, 1.0f);
}
