#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaWaterGameplayTypes.generated.h"

class AActor;

/** Typed operations accepted by the authoritative water gameplay subsystem. */
UENUM(BlueprintType)
enum class EMelodiaWaterGameplayOperation : uint8
{
	Fill,
	Drain,
	Redirect,
	OpenValve,
	CloseValve,
	Pump,
	ApplyPressure,
	ResonancePulse,
	Reset
};

UENUM(BlueprintType)
enum class EMelodiaWaterPlatformMotionMode : uint8
{
	KinematicRoute,
	PhysicsBuoyant
};

/** Authored water node configuration. Runtime state is kept separately. */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterNodeConfig
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	FGameplayTag NetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	FGameplayTag NodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	FGameplayTag WaterBodyId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	float InitialLevel = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	float InitialPressure = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node", meta = (ClampMin = "0.001"))
	float Capacity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node", meta = (ClampMin = "0.0"))
	float MaxTransferPerSecond = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	FVector FlowDirection = FVector::ForwardVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node", meta = (ClampMin = "0.0"))
	float MaxFlowStrength = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Node")
	bool bPersistent = true;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterNodeState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FGameplayTag NetworkId;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FGameplayTag NodeId;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	float Level = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	float Pressure = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FVector FlowVelocity = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	bool bBlocked = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	bool bSolved = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	int32 Revision = 0;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterLinkConfig
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	FGameplayTag NetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	FGameplayTag LinkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	FGameplayTag RouteId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	FGameplayTag SourceNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	FGameplayTag DestinationNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link", meta = (ClampMin = "0.0"))
	float TransferCapacity = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link", meta = (ClampMin = "0.0"))
	float Resistance = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	bool bInitiallyOpen = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Link")
	bool bOneWay = true;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterOperationRequest
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	EMelodiaWaterGameplayOperation Operation = EMelodiaWaterGameplayOperation::ResonancePulse;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag NetworkId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag SourceNodeId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag TargetWaterNodeId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag DeviceId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag ResonanceChannel;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag RouteId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FGameplayTag PuzzleId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation", meta = (ClampMin = "0.0"))
	float Amount = 0.0f;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Strength = 0.0f;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	FVector Direction = FVector::ZeroVector;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Operation")
	TObjectPtr<AActor> SourceActor = nullptr;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterStateChange
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FGameplayTag NetworkId;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FGameplayTag NodeId;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FMelodiaWaterNodeState PreviousState;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FMelodiaWaterNodeState CurrentState;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	EMelodiaWaterGameplayOperation Operation = EMelodiaWaterGameplayOperation::ResonancePulse;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|State")
	FGameplayTag DeviceId;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterPlatformState
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	FGameplayTag PlatformId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	FGameplayTag NetworkId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	FGameplayTag RouteId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	EMelodiaWaterPlatformMotionMode MotionMode = EMelodiaWaterPlatformMotionMode::KinematicRoute;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float RouteProgress = 0.0f;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	bool bActive = false;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	bool bDocked = false;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Water|Platform")
	int32 PuzzleRevision = 0;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterSavedNodeState
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	FGameplayTag NetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	FGameplayTag NodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	FMelodiaWaterNodeState State;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterSavedRouteState
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	FGameplayTag NetworkId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	FGameplayTag RouteId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	bool bOpen = false;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterGameplaySaveData
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	int32 SchemaVersion = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	TArray<FMelodiaWaterSavedNodeState> NodeStates;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	TArray<FMelodiaWaterSavedRouteState> RouteStates;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	TArray<FMelodiaWaterPlatformState> PlatformStates;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	TSet<FGameplayTag> CompletedPuzzleIds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Melodia|Water|Save")
	int32 PuzzleRevision = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterGameplayStateChanged, FMelodiaWaterStateChange, Change);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterGameplayPuzzleSolved, FGameplayTag, PuzzleId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaWaterGameplayOperationRejected, FGameplayTag, NetworkId, FString, Reason);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterResonanceRequested, FMelodiaWaterOperationRequest, Request);
