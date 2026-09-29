#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Containers/Ticker.h"
#include "MelodiaAiriBridgeSubsystem.generated.h"

class FJsonObject;

/**
 * Development-only, observation-first doorway to an external AIRI relay.
 *
 * This subsystem is created only when the editor/game is launched with
 * -MelodiaAiriBridge. It sends allowlisted semantic context asynchronously
 * and accepts only a validated emote into its debug state.
 */
UCLASS()
class BS_GODFILE_API UMelodiaAiriBridgeSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	bool bRelayConnected = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	FString LastTransmittedType;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	FString LastReceivedType;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	FString LastAcceptedDebugIntent;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	int32 RejectedIntentCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|AIRI Bridge")
	float LastRoundTripMs = 0.0f;

private:
	bool bIntentPollInFlight = false;
	FDelegateHandle IntentPollTicker;
	TArray<double> RecentIntentTimes;

	void PublishWorldLocation(const UWorld& World);
	bool PollIntents(float DeltaSeconds);
	void HandlePollResponse(const FString& ResponseBody);
	bool ApplyDebugIntent(const TSharedPtr<FJsonObject>& Intent);
	void RejectIntent(const FString& Reason);
};
