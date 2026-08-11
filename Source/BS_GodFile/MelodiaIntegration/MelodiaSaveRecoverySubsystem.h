#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaSaveRecoverySubsystem.generated.h"

/**
 * Save/death/recovery boundary for Melodia's non-authoritative rhythm state.
 *
 * This subsystem never resolves a stock command, awards a reward, changes party
 * state, or changes a battle result.  It only invalidates a rhythm session when
 * the session owner explicitly registered its ID, and clears presentation beat
 * forwarders that cannot survive a save/load or recovery boundary.
 */
UCLASS()
class BS_GODFILE_API UMelodiaSaveRecoverySubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category="Melodia|Recovery", meta=(WorldContext="WorldContextObject"))
	static UMelodiaSaveRecoverySubsystem* Get(const UObject* WorldContextObject);

	/** Invalidates rhythm presentation/session state before canonical serialization. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void BeginSaveBoundary(const FString& Reason);

	/** Invalidates rhythm presentation/session state after canonical serialization. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void EndSaveBoundary(const FString& Reason);

	/** Invalidates rhythm presentation/session state before canonical deserialization. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void BeginLoadBoundary(const FString& Reason);

	/** Invalidates rhythm presentation/session state after canonical deserialization. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void EndLoadBoundary(const FString& Reason);

	/** Recovery hook for the stock defeat/death route; does not choose the route. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void NotifyDeathRecovery(const FString& Reason);

	/** Recovery hook for the stock retry route; does not restart or mutate combat. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void NotifyRetryRecovery(const FString& Reason);

	/**
	 * Records the ID returned by UMelodiaRhythmCombatSubsystem::StartSession.
	 * A save/death/retry boundary will invalidate only this exact session ID.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	bool TrackRhythmSession(int64 SessionId);

	/**
	 * Clears explicitly tracked rhythm state and presentation beat forwarders.
	 * If a session is active but no ID was registered, this logs and refuses to
	 * guess; the stock combat and reward authorities remain untouched.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Recovery")
	void InvalidateRhythmTransientState(const FString& Reason);

private:
	void StopPresentationBeatTrackers();

	/** Runtime-only; rhythm skill sessions are never serialized into the save. */
	int64 TrackedRhythmSessionId = 0;
};
