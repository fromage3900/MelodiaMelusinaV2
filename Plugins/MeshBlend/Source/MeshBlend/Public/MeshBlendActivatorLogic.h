// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ChunkedProcessingQueue.h"
#include "MeshBlendPCGHelper.h"
#include "MeshBlendPooledActors.h"
#include "MeshBlendProcessor.h"
#include "UObject/Object.h"
#include "MeshBlendActivatorLogic.generated.h"

UENUM()
enum EMeshBlendProcessStage : uint8
{
	FindDistance = 0,
	ProcessActors = 1,
};

USTRUCT()
struct FMeshBlendActorInformation
{
	GENERATED_BODY()

	UPROPERTY()
	FActorBounds Bounds;

	TWeakObjectPtr<AActor> Actor;

	UPROPERTY()
	double SkipCheckingUntil = 0.0;


	bool operator==(const FMeshBlendActorInformation& Other) const
	{
		return Actor == Other.Actor;
	}
};

FORCEINLINE uint32 GetTypeHash(const FMeshBlendActorInformation& ActorInfo)
{
	return GetTypeHash(ActorInfo.Actor);
}

USTRUCT()
struct FMeshBlendActorCheckAgainItem
{
	GENERATED_BODY()

	TWeakObjectPtr<AActor> Actor;

	UPROPERTY()
	float StopCheckingAfter = 0.0;

	UPROPERTY()
	bool HasBeenCheckedOnce = false;
};

USTRUCT()
struct FMeshBlendActorProcessingItem
{
	GENERATED_BODY()

	TWeakObjectPtr<AActor> Actor;

	UPROPERTY()
	bool bReset = false;

	UPROPERTY()
	bool bSoftReset = false;

	UPROPERTY()
	bool bRefresh = false;
};

UCLASS()
class MESHBLEND_API UMeshBlendActivatorLogic : public UObject
{
	GENERATED_BODY()

public:
	void Initialize(UWorld* InWorld);
	void Deinitialize();
	virtual void Tick(const UWorld* World);
	void ScheduleActorRefresh(AActor* Actor, bool bSoftReset);

	void RestartActivator(const UWorld* World, bool bSoftReset);
	void StopActivator();

	UPROPERTY(Transient, DuplicateTransient)
	float ProcessBudget = 0.3;

	UPROPERTY(Transient, DuplicateTransient)
	bool bDisableRestrictions = false;

	UPROPERTY(Transient, DuplicateTransient)
	bool IsBlendingEnabled = false;

	UPROPERTY(Transient, DuplicateTransient)
	TObjectPtr<UMeshBlendProcessor> MeshBlendProcessor;

private:
	bool ResetActor(AActor* Actor, bool bSoftReset);
	void TryAddActorToCheckQueue(const FMeshBlendActorProcessingItem& ActorProcessingItem);
	void OnLevelAdded(ULevel* InLevel);
	void OnActorSpawned(AActor* Actor);

	void EmptyProcessingQueues();


	void World_OnLevelAdded(ULevel* InLevel, UWorld* World);
	void World_OnLevelRemoved(ULevel* InLevel, UWorld* World);
	void Level_OnActorsAdded(const TArray<AActor*>& Actors);
	void Level_OnActorSpawned(AActor* Actor);

	bool CalculateMaxProcessingRadius(const UWorld* World, const FVector& Origin, double MaxProcessDuration);
	void ShowMissingScalarParameterWarning(const UMaterialInterface* Material);
	bool ProcessActors(const UWorld* World, const FVector& Origin, double ProcessTimeStart, double MaxProcessDuration);
	bool ProcessAddedLevels(double MaxProcessDuration);
	bool ProcessActorsToCheckQueue(double MaxProcessDuration);
	void HandleActorProcessingItem(const FMeshBlendActorProcessingItem& ActorProcessingItem);


	UPROPERTY(Transient, DuplicateTransient)
	float CurrentMaxRadius = 0;

	static constexpr int MinDistanceThreshold = 20000;
	static constexpr int MinDistanceThresholdSquared = MinDistanceThreshold * MinDistanceThreshold;

	UPROPERTY(Transient, DuplicateTransient)
	TEnumAsByte<EMeshBlendProcessStage> CurrentProcessStage = FindDistance;

	TSet<TWeakObjectPtr<ULevel>> LevelsAlreadyProcessed;
	TSet<TWeakObjectPtr<AActor>> ActorsAlreadyProcessed;
	TChunkedProcessingQueue<FMeshBlendActorInformation, 65536> ActorsProcessingQueue;
	TChunkedProcessingQueue<FMeshBlendActorProcessingItem, 65536> ActorsToCheckQueue;
	TChunkedProcessingQueue<TWeakObjectPtr<ULevel>, 2048> LevelsProcessingQueue;
	int LevelActorProcessingQueueIndex = 0;
	int ActorActivationComponentIndex = 0;

	UPROPERTY(Transient, DuplicateTransient)
	FMeshBlendPooledActors PooledActors;

	UPROPERTY(Transient, DuplicateTransient)
	FMeshBlendPCGHelper MeshBlendPCGHelper;

	void RefreshPooledActor(AActor* Actor);

	UPROPERTY(Transient, DuplicateTransient)
	TSet<FString> MaterialsMissingAutoBlendID;

	UPROPERTY(Transient, DuplicateTransient)
	bool IsInitialized = false;
};
