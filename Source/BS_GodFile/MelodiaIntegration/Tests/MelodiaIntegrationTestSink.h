// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "../MelodiaNarrativeSubsystem.h"
#include "MelodiaIntegrationTestSink.generated.h"

/**
 * UObject sink for binding to dynamic multicast delegates in automation
 * tests (dynamic delegates cannot bind lambdas; they need UFUNCTION targets).
 */
UCLASS(Transient)
class BS_GODFILE_API UMelodiaIntegrationTestSink final : public UObject
{
	GENERATED_BODY()

public:
	bool bBattleRequested = false;
	FName BattleEncounterId;
	bool bBattleRejected = false;
	/** Reason carried by the most recent rejection, so tests can assert WHY, not just that. */
	EMelodiaIntentFailure LastRejectionReason = EMelodiaIntentFailure::UnknownIntent;
	bool bTravelRequested = false;
	FName TravelLevelId;
	int32 StatDelta = 0;
	FName StatId;

	UFUNCTION()
	void HandleBattleRequested(FName EncounterId);

	UFUNCTION()
	void HandleIntentRejected(FString Intent, EMelodiaIntentFailure Failure);

	UFUNCTION()
	void HandleTravelRequested(FName LevelId);

	UFUNCTION()
	void HandleSocialStatRequested(FName InStatId, int32 Delta);
};
