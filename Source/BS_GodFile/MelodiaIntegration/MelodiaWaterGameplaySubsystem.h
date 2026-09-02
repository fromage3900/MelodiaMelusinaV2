#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaWaterGameplaySubsystem.generated.h"

class FSubsystemCollectionBase;

/**
 * Persistent, deterministic water-gameplay authority. It owns logical network
 * state; the world water subsystem remains the native surface/query authority.
 */
UCLASS()
class BS_GODFILE_API UMelodiaWaterGameplaySubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaWaterGameplaySubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool RegisterNode(const FMelodiaWaterNodeConfig& Config);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool RegisterLink(const FMelodiaWaterLinkConfig& Config);

	/** Removes world bindings while retaining logical node/route state for save/load. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool UnregisterNetworkBindings(FGameplayTag NetworkId);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool ApplyOperation(const FMelodiaWaterOperationRequest& Request);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool ApplyResonance(FGameplayTag NetworkId, FGameplayTag TargetWaterNodeId, FGameplayTag ResonanceChannel, float Strength, FGameplayTag PuzzleId, FGameplayTag RouteId, AActor* SourceActor);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetNodeState(FGameplayTag NetworkId, FGameplayTag NodeId, FMelodiaWaterNodeState& OutState) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	float GetWaterLevelForNode(FGameplayTag NetworkId, FGameplayTag NodeId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	float GetPressureForNode(FGameplayTag NetworkId, FGameplayTag NodeId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetResolvedWaterFlow(FGameplayTag WaterBodyId, FVector& OutFlow) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool IsWaterRouteOpen(FGameplayTag NetworkId, FGameplayTag RouteId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetPlatformMotionState(FName PlatformId, FMelodiaWaterPlatformState& OutState) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool RegisterPlatform(const FMelodiaWaterPlatformState& State);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool UpdatePlatformState(const FMelodiaWaterPlatformState& State);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool IsPuzzleSolved(FGameplayTag PuzzleId) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Save")
	void CaptureSaveState(UPARAM(ref) FMelodiaWaterGameplaySaveData& OutData) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Save")
	void RestoreSaveState(const FMelodiaWaterGameplaySaveData& Data);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	void ResetWaterGameplayState();

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|Gameplay")
	FMelodiaWaterGameplayStateChanged OnStateChanged;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|Gameplay")
	FMelodiaWaterGameplayPuzzleSolved OnPuzzleSolved;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|Gameplay")
	FMelodiaWaterGameplayOperationRejected OnOperationRejected;

private:
	struct FNetworkRuntime
	{
		TMap<FGameplayTag, FMelodiaWaterNodeConfig> NodeConfigs;
		TMap<FGameplayTag, FMelodiaWaterNodeState> NodeStates;
		TMap<FGameplayTag, FMelodiaWaterLinkConfig> LinkConfigs;
		TMap<FGameplayTag, bool> OpenRoutes;
	};

	void RecomputeFlow(FGameplayTag NetworkId);
	void Reject(const FMelodiaWaterOperationRequest& Request, const FString& Reason);
	bool FindNode(FGameplayTag NetworkId, FGameplayTag NodeId, FNetworkRuntime*& OutNetwork, FMelodiaWaterNodeConfig*& OutConfig, FMelodiaWaterNodeState*& OutState);
	const FNetworkRuntime* FindNetwork(FGameplayTag NetworkId) const;
	FNetworkRuntime* FindNetwork(FGameplayTag NetworkId);
	bool IsRouteOpen(const FNetworkRuntime& Network, FGameplayTag RouteId) const;
	FGameplayTag RouteKey(const FMelodiaWaterLinkConfig& Link) const;
	void ApplyPendingNodeState(FGameplayTag NetworkId, FGameplayTag NodeId, FMelodiaWaterNodeState& State);

	TMap<FGameplayTag, FNetworkRuntime> Networks;
        TMap<FName, FMelodiaWaterPlatformState> PlatformStates;
	TSet<FGameplayTag> CompletedPuzzleIds;
	int32 PuzzleRevision = 0;
	FMelodiaWaterGameplaySaveData PendingSaveState;
	bool bHasPendingSaveState = false;
};
