// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendActivatorLogic.h"


#include "AutoBlendUserData.h"
#include "DrawDebugHelpers.h"
#include "EngineUtils.h"
#include "MeshBlendShared.h"
#include "PrimitiveDataHelper.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/Level.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/EngineVersionComparison.h"

#if WITH_EDITOR
#include "Editor.h"
#include "EditorViewportClient.h"
#include "Engine/Selection.h"
#include "Logging/MessageLog.h"
#include "Misc/ConfigCacheIni.h"
#include "UObject/ObjectSaveContext.h"
#endif

#define LOCTEXT_NAMESPACE "UMeshBlendActivatorLogic"

void UMeshBlendActivatorLogic::Initialize(UWorld* InWorld)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	check(InWorld);

	MeshBlendProcessor = NewObject<UMeshBlendProcessor>(this);
	MeshBlendProcessor->SmallBlendCounter = StencilStartSmall;
	MeshBlendProcessor->MediumBlendCounter = StencilStartMedium;
	MeshBlendProcessor->LargeBlendCounter = StencilStartLarge;
	MeshBlendProcessor->ExtraLargeBlendCounter = StencilStartExtraLarge;

	PooledActors.OnRefreshActor.BindUObject(this, &UMeshBlendActivatorLogic::RefreshPooledActor);

	CurrentMaxRadius = TNumericLimits<float>::Max();
	CurrentProcessStage = FindDistance;

	InWorld->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UMeshBlendActivatorLogic::Level_OnActorSpawned));

	FWorldDelegates::LevelAddedToWorld.AddUObject(this, &UMeshBlendActivatorLogic::World_OnLevelAdded);
	FWorldDelegates::LevelRemovedFromWorld.AddUObject(this, &UMeshBlendActivatorLogic::World_OnLevelRemoved);

	for (ULevel* Level : InWorld->GetLevels())
	{
		World_OnLevelAdded(Level, InWorld);
	}

	IsInitialized = true;
}

void UMeshBlendActivatorLogic::Deinitialize()
{
	IsInitialized = false;
	EmptyProcessingQueues();
	MaterialsMissingAutoBlendID.Reset();

	FWorldDelegates::LevelAddedToWorld.RemoveAll(this);
	FWorldDelegates::LevelRemovedFromWorld.RemoveAll(this);
}

void UMeshBlendActivatorLogic::EmptyProcessingQueues()
{
	LevelsAlreadyProcessed.Empty();
	ActorsAlreadyProcessed.Empty();
	ActorsProcessingQueue.Empty();
	ActorsToCheckQueue.Empty();
	LevelsProcessingQueue.Empty();
	PooledActors.Empty();
	CurrentProcessStage = FindDistance;

	if (MeshBlendProcessor)
	{
		MeshBlendProcessor->Reset();
	}
}


void UMeshBlendActivatorLogic::World_OnLevelAdded(ULevel* InLevel, UWorld* World)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (World != GetWorld())
	{
		return;
	}

	if (World && IsValid(InLevel) && !LevelsAlreadyProcessed.Contains(InLevel))
	{
#if WITH_EDITOR
		InLevel->OnLoadedActorAddedToLevelPostEvent.AddUObject(this, &UMeshBlendActivatorLogic::Level_OnActorsAdded);
#endif

		LevelsProcessingQueue.Add(InLevel);
		LevelsAlreadyProcessed.Add(InLevel);
	}
}

void UMeshBlendActivatorLogic::World_OnLevelRemoved(ULevel* InLevel, UWorld* World)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (World != GetWorld())
	{
		return;
	}

	if (World && IsValid(InLevel))
	{
#if WITH_EDITOR
		InLevel->OnLoadedActorAddedToLevelPostEvent.RemoveAll(this);
#endif

		LevelsAlreadyProcessed.Remove(InLevel);
	}
}

void UMeshBlendActivatorLogic::Level_OnActorsAdded(const TArray<AActor*>& Actors)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	for (AActor* Actor : Actors)
	{
		Level_OnActorSpawned(Actor);
	}
}

void UMeshBlendActivatorLogic::Level_OnActorSpawned(AActor* Actor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (ActorsAlreadyProcessed.Contains(Actor))
	{
		TRACE_CPUPROFILER_EVENT_SCOPE_STR("ActorsAlreadyProcessed");
		return;
	}

	FMeshBlendActorProcessingItem Item;
	Item.bRefresh = true;
	Item.Actor = Actor;
	TryAddActorToCheckQueue(Item);
}

void UMeshBlendActivatorLogic::OnActorSpawned(AActor* Actor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (!IsValid(Actor))
	{
		return;
	}

	if (Actor->Tags.Contains(GName_AutoBlendHasPrimitiveData))
	{
#if WITH_EDITOR
		ResetActor(Actor, true); // Reset actor since the tags are copied to PIE while the CPD values are not
#else
		ActorsAlreadyProcessed.Remove(Actor);
		return; // Opt out early if the actor is not relevant for blending
#endif
	}

	if (FUAutoBlendHelper::DoesItBlend(Actor))
	{
		FMeshBlendActorInformation ActorInformation;
		ActorInformation.Actor = Actor;
		ActorInformation.Bounds = FMeshBlendShared::GetBounds(Actor);
		ActorsProcessingQueue.Add(ActorInformation);
	}
	else
	{
		ActorsAlreadyProcessed.Remove(Actor);
	}
}

void UMeshBlendActivatorLogic::ScheduleActorRefresh(AActor* Actor, const bool bSoftReset)
{
	if (IsValid(Actor))
	{
		ActorsAlreadyProcessed.Remove(Actor);
		FMeshBlendActorProcessingItem Item;
		Item.Actor = Actor;
		Item.bReset = true;
		Item.bRefresh = true;
		Item.bSoftReset = bSoftReset;
		TryAddActorToCheckQueue(Item);
	}
}

void UMeshBlendActivatorLogic::Tick(const UWorld* World)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (!IsInitialized)
	{
		return;
	}

	const double ProcessTimeStart = FPlatformTime::Seconds();
	double ProcessBudgetInSeconds = ProcessBudget / 1000.0;

#if WITH_EDITOR
	// Used to ensure blending is instant when rendering a movie in sequencer
	if (bDisableRestrictions)
	{
		ProcessBudgetInSeconds = 10000000;
	}

#endif

	FVector Origin;

	if (!FMeshBlendShared::GetCurrentCameraLocation(World, Origin))
	{
		return;
	}

	const double MaxProcessDuration = ProcessTimeStart + ProcessBudgetInSeconds;

	if (!ProcessAddedLevels(MaxProcessDuration))
	{
		return;
	};

	if (!PooledActors.ProcessActorQueue(MaxProcessDuration))
	{
		return;
	}

	if (!ProcessActorsToCheckQueue(MaxProcessDuration))
	{
		return;
	};

	if (CurrentProcessStage == FindDistance)
	{
		if (CalculateMaxProcessingRadius(World, Origin, MaxProcessDuration))
		{
			CurrentProcessStage = EMeshBlendProcessStage::ProcessActors;
			ActorsProcessingQueue.ResetIndexToStart();
		}
	}
	else if (CurrentProcessStage == EMeshBlendProcessStage::ProcessActors)
	{
		if (ProcessActors(World, Origin, ProcessTimeStart, MaxProcessDuration))
		{
			CurrentProcessStage = FindDistance;
			CurrentMaxRadius = TNumericLimits<float>::Max();
			ActorsProcessingQueue.ResetIndexToStart();
		}
	}
}

void UMeshBlendActivatorLogic::OnLevelAdded(ULevel* InLevel)
{
	LevelsProcessingQueue.Add(InLevel);
}

bool UMeshBlendActivatorLogic::ProcessAddedLevels(const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	TWeakObjectPtr<ULevel> LevelPointer;

	while (LevelsProcessingQueue.Next(LevelPointer))
	{
		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			LevelsProcessingQueue.KeepCurrentAsNext();
			return false;
		}

		if (!LevelPointer.IsValid())
		{
			LevelsProcessingQueue.RemoveCurrent();
			continue;
		}

		// We reset the process stage to ensure we update the CurrentMaxRadius after a level has been added
		CurrentProcessStage = FindDistance;
		CurrentMaxRadius = TNumericLimits<float>::Max();
		ActorsProcessingQueue.ResetIndexToStart();

		ULevel* Level = LevelPointer.Get();

		for (int y = LevelActorProcessingQueueIndex; y < Level->Actors.Num(); y++)
		{
			Level_OnActorSpawned(Level->Actors[y]);

			if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
			{
				LevelsProcessingQueue.KeepCurrentAsNext();
				LevelActorProcessingQueueIndex = y;
				return false;
			}
		}

		LevelActorProcessingQueueIndex = 0;
		LevelsProcessingQueue.RemoveCurrent();
	}

	return true;
}

bool UMeshBlendActivatorLogic::ProcessActorsToCheckQueue(const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	FMeshBlendActorProcessingItem ActorProcessingItem;

	while (ActorsToCheckQueue.Next(ActorProcessingItem))
	{
		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			ActorsToCheckQueue.KeepCurrentAsNext();
			return false;
		}

		if (!ActorProcessingItem.Actor.IsValid())
		{
			ActorsToCheckQueue.RemoveCurrent();
			continue;
		}

		HandleActorProcessingItem(ActorProcessingItem);
		ActorsToCheckQueue.RemoveCurrent();
	}

	return true;
}

void UMeshBlendActivatorLogic::HandleActorProcessingItem(const FMeshBlendActorProcessingItem& ActorProcessingItem)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	AActor* Actor = ActorProcessingItem.Actor.Get();

	if (!IsValid(Actor))
	{
		return;
	}

	SCOPE_CYCLE_UOBJECT(Actor, Actor);

	if (ActorProcessingItem.bReset)
	{
		ResetActor(Actor, ActorProcessingItem.bSoftReset);
	}

	if (ActorProcessingItem.bRefresh)
	{
		OnActorSpawned(Actor);
	}

	if (MeshBlendPCGHelper.ActorIsPCGActor(Actor) || Actor->Tags.Contains(GName_PooledActor))
	{
		PooledActors.AddActor(Actor);
	}
}

void UMeshBlendActivatorLogic::RefreshPooledActor(AActor* Actor)
{
	Actor->Tags.RemoveSwap(GName_AutoBlendHasPrimitiveData);

	FMeshBlendActorInformation ActorInformation;
	ActorInformation.Actor = Actor;
	ActorInformation.Bounds = FMeshBlendShared::GetBounds(Actor);
	ActorsProcessingQueue.AddUnique(ActorInformation);
}

bool UMeshBlendActivatorLogic::CalculateMaxProcessingRadius(const UWorld* World, const FVector& Origin, const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	FMeshBlendActorInformation ActorInformation;

	while (ActorsProcessingQueue.Next(ActorInformation))
	{
		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			ActorsProcessingQueue.KeepCurrentAsNext();
			return false;
		}

		if (!ActorInformation.Actor.IsValid())
		{
			ActorsProcessingQueue.RemoveCurrent();
			continue;
		}

		const AActor* Actor = ActorInformation.Actor.Get();
		FActorBounds ActorBounds = ActorInformation.Bounds;
		const float ActorDistance = FVector::DistSquared(Origin, ActorBounds.Origin) * (1.0 + FMath::Min(10.0, World->TimeSince(Actor->GetLastRenderTime())));

		if (ActorDistance < CurrentMaxRadius * CurrentMaxRadius)
		{
			CurrentMaxRadius = FMath::Sqrt(ActorDistance);

			// Abort early if we're already at the minimum distance threshold
			if (CurrentMaxRadius < MinDistanceThreshold)
			{
				CurrentMaxRadius = MinDistanceThreshold;
				ActorsProcessingQueue.ResetIndexToStart();
				return true;
			}
		}

		bool bShouldBreak = false;

		for (int x = 0; x < 50; x++)
		{
			if (!ActorsProcessingQueue.Next(ActorInformation))
			{
				bShouldBreak = true;
				break;
			}
		}

		if (bShouldBreak)
		{
			break;
		}
	}

	CurrentMaxRadius = FMath::CeilToFloat(CurrentMaxRadius / MinDistanceThreshold) * MinDistanceThreshold;
	ActorsProcessingQueue.ResetIndexToStart();
	return true;
}

void UMeshBlendActivatorLogic::ShowMissingScalarParameterWarning(const UMaterialInterface* Material)
{
	// Only show this warning once per material
	if (!MaterialsMissingAutoBlendID.Contains(*Material->GetFullName()))
	{
		MaterialsMissingAutoBlendID.Add(*Material->GetFullName());
		const FString WarningMessage = FString::Printf(
			TEXT("MeshBlend warning: Material \"%s\" is missing scalar parameter %s"),
			*Material->GetFullName(),
			*GName_AutoBlendID.ToString());
		UE_LOG(LogTemp, Warning, TEXT("%s"), *WarningMessage);
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Yellow, WarningMessage);
	}
}

bool UMeshBlendActivatorLogic::ProcessActors(const UWorld* World, const FVector& Origin, const double ProcessTimeStart, const double MaxProcessDuration)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	const double SkipCheckTime = ProcessTimeStart + 5.0;

	FMeshBlendActorInformation ActorInformation;
	while (ActorsProcessingQueue.Next(ActorInformation))
	{
		TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendActivatorLogic::ProcessActors::ActorInformation");

		if (FMeshBlendShared::IsOverProcessBudget(MaxProcessDuration))
		{
			ActorsProcessingQueue.KeepCurrentAsNext();
			return false;
		}

		if (!ActorInformation.Actor.IsValid())
		{
			MeshBlendProcessor->ActorActivationComponentIndex = 0;
			MeshBlendProcessor->ActorActivationComponentInstanceIndex = 0;
			ActorsProcessingQueue.RemoveCurrent();
			continue;
		}

		if (ActorInformation.SkipCheckingUntil > ProcessTimeStart)
		{
			continue;
		}


		AActor* Actor = ActorInformation.Actor.Get();
		FActorBounds ActorBounds = ActorInformation.Bounds;
		float ActorDistanceSquared = FVector::DistSquared(Origin, ActorBounds.Origin) * (1.0 + FMath::Min(10.0, World->TimeSince(Actor->GetLastRenderTime())));
		const float SkipCheckDistanceThreshold = CurrentMaxRadius + ActorBounds.Radius + MinDistanceThreshold * 2;

#if WITH_EDITOR
		// Used to ensure blending is instant when rendering a movie in sequencer
		if (bDisableRestrictions)
		{
			ActorDistanceSquared = 0;
		}
#endif

		if (ActorDistanceSquared > SkipCheckDistanceThreshold * SkipCheckDistanceThreshold)
		{
			ActorInformation.SkipCheckingUntil = SkipCheckTime;
			continue;
		}

		const float DistanceThreshold = CurrentMaxRadius + ActorBounds.Radius;

		if (ActorDistanceSquared < DistanceThreshold * DistanceThreshold)
		{
			if (!MeshBlendProcessor->ActivateActor(Actor, MaxProcessDuration, false))
			{
				ActorsProcessingQueue.KeepCurrentAsNext();
				return false;
			}

			ActorsProcessingQueue.RemoveCurrent();
			ActorsAlreadyProcessed.Remove(Actor);
		}
	}

	ActorsProcessingQueue.ResetIndexToStart();
	return true;
}

void UMeshBlendActivatorLogic::RestartActivator(const UWorld* World, const bool bSoftReset = false)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	IsBlendingEnabled = true;
	EmptyProcessingQueues();

	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (AActor* Actor = *It)
		{
			FMeshBlendActorProcessingItem Item;
			Item.Actor = Actor;
			Item.bReset = true;
			Item.bSoftReset = bSoftReset;
			Item.bRefresh = true;
			HandleActorProcessingItem(Item);
		}
	}
}

void UMeshBlendActivatorLogic::StopActivator()
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	IsBlendingEnabled = false;
	EmptyProcessingQueues();
}

bool UMeshBlendActivatorLogic::ResetActor(AActor* Actor, const bool bSoftReset = false)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (!Actor->Tags.Contains(GName_AutoBlendHasPrimitiveData))
	{
		return false;
	}

	Actor->Tags.RemoveSwap(GName_AutoBlendHasPrimitiveData);
	bool FoundActorsToReset = false;

	for (UActorComponent* Component : Actor->GetComponents())
	{
		if (UMeshComponent* MeshComponent = Cast<UMeshComponent>(Component))
		{
			const int BlendTagIndex = MeshComponent->ComponentTags.IndexOfByKey(GName_AutoBlendHasPrimitiveData);

			if (BlendTagIndex != INDEX_NONE)
			{
#if UE_VERSION_OLDER_THAN(5, 5, 0)
				MeshComponent->ComponentTags.RemoveAtSwap(BlendTagIndex, 1, false);
#else
				MeshComponent->ComponentTags.RemoveAtSwap(BlendTagIndex, 1, EAllowShrinking::No);
#endif

				FoundActorsToReset = true;

				if (!bSoftReset)
				{
					const int32 CustomPrimitiveDataIndex = MeshComponent->GetCustomPrimitiveDataIndexForScalarParameter(GName_AutoBlendID);

					if (CustomPrimitiveDataIndex != INDEX_NONE)
					{
						FPrimitiveDataHelper::EnsurePrimitiveDataSlot(MeshComponent, CustomPrimitiveDataIndex);

						if (UInstancedStaticMeshComponent* InstancedStaticMeshComponent = Cast<UInstancedStaticMeshComponent>(MeshComponent))
						{
							for (int32 i = 0; i < InstancedStaticMeshComponent->GetInstanceCount(); i++)
							{
								FPrimitiveDataHelper::SetCustomDataValue(InstancedStaticMeshComponent, i, CustomPrimitiveDataIndex, 0.0);
							}
							
							{
								TRACE_CPUPROFILER_EVENT_SCOPE_STR("UMeshBlendActivatorLogic::ResetActor::InstancedStaticMeshComponent->MarkRenderStateDirty");
								InstancedStaticMeshComponent->MarkRenderStateDirty();
							}
						}
						else
						{
							MeshComponent->SetCustomPrimitiveDataFloat(CustomPrimitiveDataIndex, 0.0);
						}
					}
				}
			}
		}
	}

	return FoundActorsToReset;
}

void UMeshBlendActivatorLogic::TryAddActorToCheckQueue(const FMeshBlendActorProcessingItem& ActorProcessingItem)
{
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

	if (!ActorProcessingItem.Actor.IsValid())
	{
		return;
	}

	AActor* Actor = ActorProcessingItem.Actor.Get();

	if (ActorsAlreadyProcessed.Contains(Actor))
	{
		return;
	}

	ActorsAlreadyProcessed.Add(Actor);
	ActorsToCheckQueue.Add(ActorProcessingItem);
}

#undef LOCTEXT_NAMESPACE
