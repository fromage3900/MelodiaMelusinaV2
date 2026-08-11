// Copyright Epic Games, Inc. All Rights Reserved.

#include "MelodiaIntegrationTestSink.h"

void UMelodiaIntegrationTestSink::HandleBattleRequested(FName EncounterId)
{
	bBattleRequested = true;
	BattleEncounterId = EncounterId;
}

void UMelodiaIntegrationTestSink::HandleIntentRejected(FString Intent, EMelodiaIntentFailure Failure)
{
	bBattleRejected = true;
	LastRejectionReason = Failure;
}

void UMelodiaIntegrationTestSink::HandleTravelRequested(FName LevelId)
{
	bTravelRequested = true;
	TravelLevelId = LevelId;
}

void UMelodiaIntegrationTestSink::HandleSocialStatRequested(FName InStatId, int32 Delta)
{
	StatId = InStatId;
	StatDelta = Delta;
}
