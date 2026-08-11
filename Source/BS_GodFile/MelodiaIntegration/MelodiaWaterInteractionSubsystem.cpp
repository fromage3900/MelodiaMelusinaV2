#include "MelodiaWaterInteractionSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "BakedShallowWaterSimulationComponent.h"
#include "MelodiaWaterRippleMaterialBridgeComponent.h"
#include "MelodiaWaterProfile.h"
#include "Materials/MaterialInterface.h"
#include "Subsystems/SubsystemCollection.h"
#include "WaterBodyActor.h"
#include "WaterBodyComponent.h"
#include "WaterBodyManager.h"
#include "WaterBodyTypes.h"
#include "WaterSubsystem.h"

void UMelodiaWaterInteractionSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	if (UWorld* World = GetWorld())
	{
		RegisteredWaterBodyManager = UWaterSubsystem::GetWaterBodyManager(World);
		if (RegisteredWaterBodyManager)
		{
			RegisteredWaterBodyManager->OnWaterBodyAdded.AddUObject(this, &ThisClass::HandleWaterBodyAdded);
			RegisteredWaterBodyManager->OnWaterBodyRemoved.AddUObject(this, &ThisClass::HandleWaterBodyRemoved);
			RegisteredWaterBodyManager->ForEachWaterBodyComponent([this](UWaterBodyComponent* WaterBodyComponent)
			{
				CacheWaterBody(WaterBodyComponent);
				return true;
			});
		}
	}
}

UMelodiaWaterInteractionSubsystem* UMelodiaWaterInteractionSubsystem::Get(const UObject* WorldContextObject)
{
	if (!WorldContextObject || !GEngine)
	{
		return nullptr;
	}

	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	return World ? World->GetSubsystem<UMelodiaWaterInteractionSubsystem>() : nullptr;
}

void UMelodiaWaterInteractionSubsystem::SubmitSample(AActor* SourceActor, const FMelodiaWaterSample& Sample)
{
	if (!IsValid(SourceActor))
	{
		return;
	}

	RemoveInvalidSamples();

	FMelodiaWaterSample NormalizedSample = Sample;
	NormalizedSample.SampleTime = GetWorld() ? GetWorld()->GetTimeSeconds() : Sample.SampleTime;
	LatestSamples.Add(TWeakObjectPtr<AActor>(SourceActor), NormalizedSample);
	OnSampleUpdated.Broadcast(NormalizedSample);
}

void UMelodiaWaterInteractionSubsystem::PublishContact(const FMelodiaWaterContactEvent& Event)
{
	// A contact without a source is valid for ambient water, so do not invent an
	// actor here. World-only events are part of the same stream as actor events.
	OnContactEvent.Broadcast(Event);

	switch (Event.EventType)
	{
	case EMelodiaWaterContactType::SurfaceEntry:
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::Ripple:
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::Footstep:
	case EMelodiaWaterContactType::WaterImpact:
	{
		FMelodiaWaterFluidImpulse FluidImpulse;
		FluidImpulse.WaterBodyId = Event.Sample.WaterBodyId;
		FluidImpulse.Location = Event.ContactLocation;
		FluidImpulse.Normal = Event.Sample.SurfaceNormal;
		FluidImpulse.Impulse = Event.ImpulseVector;
		FluidImpulse.Radius = Event.Radius;
		FluidImpulse.Strength = Event.Intensity;
		FluidImpulse.ForceMode = Event.EventType == EMelodiaWaterContactType::WaterImpact
			? EMelodiaWaterForceMode::Impulse
			: (Event.EventType == EMelodiaWaterContactType::Ripple || Event.EventType == EMelodiaWaterContactType::Footstep
				? EMelodiaWaterForceMode::Contact
				: EMelodiaWaterForceMode::Impulse);
		FluidImpulse.bRouteToNativeWater = true;
		FluidImpulse.EffectProfileId = Event.EffectProfileId;
		FluidImpulse.SourceComponentId = Event.SourceActor ? Event.SourceActor->GetFName() : NAME_None;
		FluidImpulse.Timestamp = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
		FluidImpulse.Duration = Event.Duration;
		PublishFluidImpulse(FluidImpulse);
		break;
	}
	default:
		break;
	}
}

void UMelodiaWaterInteractionSubsystem::PublishFluidImpulse(const FMelodiaWaterFluidImpulse& Impulse)
{
	FMelodiaWaterFluidImpulse NormalizedImpulse = Impulse;
	if (NormalizedImpulse.Timestamp <= 0.0f && GetWorld())
	{
		NormalizedImpulse.Timestamp = GetWorld()->GetTimeSeconds();
	}

	RecentFluidImpulses.Add(NormalizedImpulse);
	while (RecentFluidImpulses.Num() > FMath::Max(1, MaxRecentFluidImpulses))
	{
		RecentFluidImpulses.RemoveAt(0, 1, EAllowShrinking::No);
	}
	OnFluidImpulse.Broadcast(NormalizedImpulse);
}

void UMelodiaWaterInteractionSubsystem::GetRecentFluidImpulses(TArray<FMelodiaWaterFluidImpulse>& OutImpulses) const
{
	OutImpulses = RecentFluidImpulses;
}

bool UMelodiaWaterInteractionSubsystem::QueryWaterAtLocation(const FVector& WorldLocation, FMelodiaWaterSample& OutSample)
{
	return QueryWaterInternal(nullptr, WorldLocation, OutSample);
}

bool UMelodiaWaterInteractionSubsystem::QueryWaterAtLocationForActor(AActor* SourceActor, const FVector& WorldLocation, FMelodiaWaterSample& OutSample)
{
	return QueryWaterInternal(SourceActor, WorldLocation, OutSample);
}

bool UMelodiaWaterInteractionSubsystem::TryGetWaterBodyComponent(FName WaterBodyId, UWaterBodyComponent*& OutWaterBodyComponent) const
{
	OutWaterBodyComponent = nullptr;
	if (const TWeakObjectPtr<UWaterBodyComponent>* Found = WaterBodiesById.Find(WaterBodyId))
	{
		OutWaterBodyComponent = Found->Get();
	}
	return IsValid(OutWaterBodyComponent);
}

bool UMelodiaWaterInteractionSubsystem::GetNativeWaterLimits(FMelodiaWaterNativeLimits& OutLimits) const
{
	OutLimits = FMelodiaWaterNativeLimits();
	const UWorld* World = GetWorld();
	const UWaterSubsystem* WaterSubsystem = World ? UWaterSubsystem::GetWaterSubsystem(World) : nullptr;
	if (!WaterSubsystem)
	{
		return false;
	}

	OutLimits.bWaterAvailable = true;
	OutLimits.bShallowWaterSimulationEnabled = WaterSubsystem->IsShallowWaterSimulationEnabled();
	OutLimits.bUnderwaterPostProcessEnabled = WaterSubsystem->IsUnderwaterPostProcessEnabled();
	OutLimits.MaxDynamicForces = UWaterSubsystem::GetShallowWaterMaxDynamicForces();
	OutLimits.MaxImpulseForces = UWaterSubsystem::GetShallowWaterMaxImpulseForces();
	OutLimits.ShallowWaterRenderTargetSize = UWaterSubsystem::GetShallowWaterSimulationRenderTargetSize();
	return true;
}

bool UMelodiaWaterInteractionSubsystem::QueryWaterInternal(AActor* SourceActor, const FVector& WorldLocation, FMelodiaWaterSample& OutSample)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return false;
	}

	FWaterBodyManager* WaterBodyManager = RegisteredWaterBodyManager ? RegisteredWaterBodyManager : UWaterSubsystem::GetWaterBodyManager(World);
	if (!WaterBodyManager)
	{
		return false;
	}

	float BestScore = TNumericLimits<float>::Max();
	FMelodiaWaterSample BestSample;
	UWaterBodyComponent* BestWaterBodyComponent = nullptr;

	if (SourceActor)
	{
		if (const TWeakObjectPtr<UWaterBodyComponent>* Cached = ActorWaterBodies.Find(TWeakObjectPtr<AActor>(SourceActor)))
		{
			UWaterBodyComponent* CachedComponent = Cached->Get();
			if (QueryWaterBodyComponent(CachedComponent, WorldLocation, BestScore, BestSample))
			{
				BestWaterBodyComponent = CachedComponent;
			}
			else
			{
				ActorWaterBodies.Remove(TWeakObjectPtr<AActor>(SourceActor));
			}
		}
	}

	if (!BestWaterBodyComponent)
	{
		WaterBodyManager->ForEachWaterBodyComponent([&](UWaterBodyComponent* WaterBodyComponent)
		{
			float Score = TNumericLimits<float>::Max();
			FMelodiaWaterSample Candidate;
			if (QueryWaterBodyComponent(WaterBodyComponent, WorldLocation, Score, Candidate) && Score < BestScore)
			{
				BestScore = Score;
				BestSample = Candidate;
				BestWaterBodyComponent = WaterBodyComponent;
			}
			return true;
		});
	}

	if (!BestWaterBodyComponent)
	{
		return false;
	}

	if (SourceActor)
	{
		ActorWaterBodies.Add(TWeakObjectPtr<AActor>(SourceActor), BestWaterBodyComponent);
	}
	CacheWaterBody(BestWaterBodyComponent);
	EnsureSurfaceBridge(BestWaterBodyComponent->GetWaterBodyActor());
	BestSample.SampleTime = UWaterSubsystem::GetWaterSubsystem(World)
		? UWaterSubsystem::GetWaterSubsystem(World)->GetWaterTimeSeconds()
		: World->GetTimeSeconds();
	OutSample = BestSample;
	return true;
}

bool UMelodiaWaterInteractionSubsystem::QueryWaterBodyComponent(UWaterBodyComponent* WaterBodyComponent, const FVector& WorldLocation, float& OutScore, FMelodiaWaterSample& OutSample) const
{
	if (!IsValid(WaterBodyComponent))
	{
		return false;
	}

	const EWaterBodyQueryFlags QueryFlags =
		EWaterBodyQueryFlags::ComputeLocation
		| EWaterBodyQueryFlags::ComputeNormal
		| EWaterBodyQueryFlags::ComputeVelocity
		| EWaterBodyQueryFlags::ComputeDepth
		| EWaterBodyQueryFlags::ComputeImmersionDepth
		| EWaterBodyQueryFlags::IncludeWaves
		| EWaterBodyQueryFlags::SimpleWaves;
	const TValueOrError<FWaterBodyQueryResult, EWaterBodyQueryError> QueryResult =
		WaterBodyComponent->TryQueryWaterInfoClosestToWorldLocation(WorldLocation, QueryFlags);
	if (!QueryResult.HasValue() || QueryResult.GetValue().IsInExclusionVolume())
	{
		return false;
	}

	const FWaterBodyQueryResult& Query = QueryResult.GetValue();
	const FVector SurfaceLocation = Query.GetWaterSurfaceLocation();
	const bool bUnderwater = Query.IsInWater();
	OutScore = FMath::Abs(WorldLocation.Z - SurfaceLocation.Z) + (bUnderwater ? 0.0f : 100000.0f);
	OutSample = FMelodiaWaterSample();
	OutSample.bValid = true;
	OutSample.bSurfaceValid = true;
	OutSample.bUnderwater = bUnderwater;
	OutSample.SurfaceLocation = SurfaceLocation;
	OutSample.SurfaceNormal = Query.GetWaterSurfaceNormal().GetSafeNormal();
	OutSample.SurfaceVelocity = Query.GetVelocity();
	OutSample.NativeShallowWaterVelocity = Query.GetVelocity();
	OutSample.NativeShallowWaterNormal = OutSample.SurfaceNormal;
	OutSample.DistanceToSurface = WorldLocation.Z - SurfaceLocation.Z;
	OutSample.ImmersionDepth = FMath::Max(0.0f, Query.GetImmersionDepth());
	OutSample.Immersion = FMath::Clamp(OutSample.ImmersionDepth / 150.0f, 0.0f, 1.0f);
	OutSample.WaterDepth = FMath::Max(0.0f, Query.GetWaterSurfaceDepth());
	OutSample.QueryProvider = EMelodiaWaterQueryProvider::NativeWaterBody;

	if (WaterBodyComponent->UseBakedSimulationForQueriesAndPhysics())
	{
		if (UBakedShallowWaterSimulationComponent* BakedSimulation = WaterBodyComponent->GetBakedShallowWaterSimulation())
		{
			if (BakedSimulation->BakedSimulationData)
			{
				BakedSimulation->BakedSimulationData->SampleShallowWaterSimulationAtPosition(
					WorldLocation,
					OutSample.NativeShallowWaterVelocity,
					OutSample.NativeShallowWaterHeight,
					OutSample.WaterDepth);
				OutSample.SurfaceVelocity = OutSample.NativeShallowWaterVelocity;
				OutSample.QueryProvider = EMelodiaWaterQueryProvider::BakedShallowWater;
				OutSample.bUsesBakedShallowWater = true;
			}
		}
	}

	if (AWaterBody* WaterBodyActor = WaterBodyComponent->GetWaterBodyActor())
	{
		OutSample.WaterBodyId = WaterBodyActor->GetFName();
	}
	else
	{
		OutSample.WaterBodyId = FName(*FString::Printf(TEXT("WaterBody_%d"), WaterBodyComponent->GetWaterBodyIndex()));
	}
	OutSample.WaterBodyIndex = WaterBodyComponent->GetWaterBodyIndex();
	if (AWaterZone* WaterZone = WaterBodyComponent->GetWaterZone())
	{
		OutSample.WaterZoneIndex = WaterZone->GetWaterZoneIndex();
	}
	return true;
}

void UMelodiaWaterInteractionSubsystem::CacheWaterBody(UWaterBodyComponent* WaterBodyComponent)
{
	if (!IsValid(WaterBodyComponent))
	{
		return;
	}
	AWaterBody* WaterBodyActor = WaterBodyComponent->GetWaterBodyActor();
	if (IsValid(WaterBodyActor))
	{
		WaterBodiesById.Add(WaterBodyActor->GetFName(), WaterBodyComponent);
		ApplyProjectWaterDefaults(WaterBodyComponent);
	}
}

void UMelodiaWaterInteractionSubsystem::ApplyProjectWaterDefaults(UWaterBodyComponent* WaterBodyComponent)
{
	if (!IsValid(WaterBodyComponent))
	{
		return;
	}

	static const TCHAR* ProfilePath =
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default");
	UMelodiaWaterProfile* Profile = LoadObject<UMelodiaWaterProfile>(nullptr, ProfilePath);
	if (!IsValid(Profile))
	{
		return;
	}

	// This is the project-owned native default seam. Per-body identity is still
	// sourced from the UE Water Body at query time; the profile deliberately
	// does not hard-code the validation map's actor name.
	if (UMaterialInterface* SurfaceMaterial = Profile->SurfaceMaterial.LoadSynchronous())
	{
		WaterBodyComponent->SetWaterMaterial(SurfaceMaterial);
		WaterBodyComponent->SetWaterStaticMeshMaterial(SurfaceMaterial);
	}
	if (UMaterialInterface* UnderwaterMaterial = Profile->UnderwaterMaterial.LoadSynchronous())
	{
		WaterBodyComponent->SetUnderwaterPostProcessMaterial(UnderwaterMaterial);
	}

	EnsureSurfaceBridge(WaterBodyComponent->GetWaterBodyActor());
}

void UMelodiaWaterInteractionSubsystem::HandleWaterBodyAdded(UWaterBodyComponent* WaterBodyComponent)
{
	CacheWaterBody(WaterBodyComponent);
}

void UMelodiaWaterInteractionSubsystem::HandleWaterBodyRemoved(UWaterBodyComponent* WaterBodyComponent)
{
	for (auto It = WaterBodiesById.CreateIterator(); It; ++It)
	{
		if (It.Value().Get() == WaterBodyComponent)
		{
			It.RemoveCurrent();
		}
	}
	for (auto It = ActorWaterBodies.CreateIterator(); It; ++It)
	{
		if (It.Value().Get() == WaterBodyComponent)
		{
			It.RemoveCurrent();
		}
	}
}

void UMelodiaWaterInteractionSubsystem::EnsureSurfaceBridge(AActor* WaterBodyActor)
{
	if (!IsValid(WaterBodyActor) || WaterBodyActor->FindComponentByClass<UMelodiaWaterRippleMaterialBridgeComponent>())
	{
		return;
	}

	UMelodiaWaterRippleMaterialBridgeComponent* SurfaceBridge =
		NewObject<UMelodiaWaterRippleMaterialBridgeComponent>(WaterBodyActor, TEXT("MelodiaWaterRippleMaterialBridge"));
	if (SurfaceBridge)
	{
		WaterBodyActor->AddInstanceComponent(SurfaceBridge);
		SurfaceBridge->RegisterComponent();
	}
}

bool UMelodiaWaterInteractionSubsystem::GetLatestSample(AActor* SourceActor, FMelodiaWaterSample& OutSample) const
{
	if (!IsValid(SourceActor))
	{
		return false;
	}

	const FMelodiaWaterSample* Found = LatestSamples.Find(TWeakObjectPtr<AActor>(SourceActor));
	if (!Found)
	{
		return false;
	}

	OutSample = *Found;
	return true;
}

void UMelodiaWaterInteractionSubsystem::ClearActor(AActor* SourceActor)
{
	if (SourceActor)
	{
		LatestSamples.Remove(TWeakObjectPtr<AActor>(SourceActor));
		ActorWaterBodies.Remove(TWeakObjectPtr<AActor>(SourceActor));
	}
}

void UMelodiaWaterInteractionSubsystem::Deinitialize()
{
	if (RegisteredWaterBodyManager)
	{
		RegisteredWaterBodyManager->OnWaterBodyAdded.RemoveAll(this);
		RegisteredWaterBodyManager->OnWaterBodyRemoved.RemoveAll(this);
	}
	RegisteredWaterBodyManager = nullptr;
	LatestSamples.Reset();
	ActorWaterBodies.Reset();
	WaterBodiesById.Reset();
	RecentFluidImpulses.Reset();
	Super::Deinitialize();
}

void UMelodiaWaterInteractionSubsystem::RemoveInvalidSamples()
{
	for (auto It = LatestSamples.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid())
		{
			It.RemoveCurrent();
		}
	}
	for (auto It = ActorWaterBodies.CreateIterator(); It; ++It)
	{
		if (!It.Key().IsValid() || !It.Value().IsValid())
		{
			It.RemoveCurrent();
		}
	}
}
