#pragma once

#include "CoreMinimal.h"
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
	bool UnregisterNetworkBindings(FName NetworkId);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool ApplyOperation(const FMelodiaWaterOperationRequest& Request);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool ApplyResonance(FName NetworkId, FName TargetWaterNodeId, FName ResonanceChannel, float Strength, FName PuzzleId, FName RouteId, AActor* SourceActor);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetNodeState(FName NetworkId, FName NodeId, FMelodiaWaterNodeState& OutState) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	float GetWaterLevelForNode(FName NetworkId, FName NodeId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	float GetPressureForNode(FName NetworkId, FName NodeId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetResolvedWaterFlow(FName WaterBodyId, FVector& OutFlow) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool IsWaterRouteOpen(FName NetworkId, FName RouteId) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool GetPlatformMotionState(FName PlatformId, FMelodiaWaterPlatformState& OutState) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool RegisterPlatform(const FMelodiaWaterPlatformState& State);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Gameplay")
	bool UpdatePlatformState(const FMelodiaWaterPlatformState& State);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Gameplay")
	bool IsPuzzleSolved(FName PuzzleId) const;

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
		TMap<FName, FMelodiaWaterNodeConfig> NodeConfigs;
		TMap<FName, FMelodiaWaterNodeState> NodeStates;
		TMap<FName, FMelodiaWaterLinkConfig> LinkConfigs;
		TMap<FName, bool> OpenRoutes;
	};

	void RecomputeFlow(FName NetworkId);
	void Reject(const FMelodiaWaterOperationRequest& Request, const FString& Reason);
	bool FindNode(FName NetworkId, FName NodeId, FNetworkRuntime*& OutNetwork, FMelodiaWaterNodeConfig*& OutConfig, FMelodiaWaterNodeState*& OutState);
	const FNetworkRuntime* FindNetwork(FName NetworkId) const;
	FNetworkRuntime* FindNetwork(FName NetworkId);
	bool IsRouteOpen(const FNetworkRuntime& Network, FName RouteId) const;
	FName RouteKey(const FMelodiaWaterLinkConfig& Link) const;
	void ApplyPendingNodeState(FName NetworkId, FName NodeId, FMelodiaWaterNodeState& State);

	TMap<FName, FNetworkRuntime> Networks;
	TMap<FName, FMelodiaWaterPlatformState> PlatformStates;
	TSet<FName> CompletedPuzzleIds;
	int32 PuzzleRevision = 0;
	FMelodiaWaterGameplaySaveData PendingSaveState;
	bool bHasPendingSaveState = false;
};
