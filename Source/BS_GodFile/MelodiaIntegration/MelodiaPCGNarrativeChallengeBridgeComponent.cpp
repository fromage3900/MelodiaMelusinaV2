#include "MelodiaPCGNarrativeChallengeBridgeComponent.h"

#include "MelodiaNarrativeSubsystem.h"
#include "Stats/Stats.h"

namespace
{
	FString EnumToString(EMelodiaContentCommitResult Value)
	{
		return StaticEnum<EMelodiaContentCommitResult>()->GetNameStringByValue(static_cast<int64>(Value));
	}

	FString EnumToString(EMelodiaContentCommitFailure Value)
	{
		return StaticEnum<EMelodiaContentCommitFailure>()->GetNameStringByValue(static_cast<int64>(Value));
	}
}

UMelodiaPCGNarrativeChallengeBridgeComponent::UMelodiaPCGNarrativeChallengeBridgeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaPCGNarrativeChallengeBridgeComponent::BeginPlay()
{
	Super::BeginPlay();
	RebindToHost();
}

void UMelodiaPCGNarrativeChallengeBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (APCGHeroMusicGraphHost* Host = BoundHost.Get())
	{
		Host->OnNoteJudged.RemoveDynamic(this, &ThisClass::HandleNoteJudged);
		Host->OnPatternCompleted.RemoveDynamic(this, &ThisClass::HandlePatternCompleted);
	}
	BoundHost.Reset();
	bBound = false;
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaPCGNarrativeChallengeBridgeComponent::RebindToHost()
{
	if (APCGHeroMusicGraphHost* ExistingHost = BoundHost.Get())
	{
		ExistingHost->OnNoteJudged.RemoveDynamic(this, &ThisClass::HandleNoteJudged);
		ExistingHost->OnPatternCompleted.RemoveDynamic(this, &ThisClass::HandlePatternCompleted);
	}

	BoundHost = Cast<APCGHeroMusicGraphHost>(GetOwner());
	APCGHeroMusicGraphHost* Host = BoundHost.Get();
	if (!Host)
	{
		bBound = false;
		UE_LOG(LogTemp, Warning,
			TEXT("MelodiaPCGNarrativeChallengeBridge: owner is not an APCGHeroMusicGraphHost; challenge '%s' will never commit."),
			*ChallengeId.ToString());
		return false;
	}

	Host->OnNoteJudged.AddUniqueDynamic(this, &ThisClass::HandleNoteJudged);
	Host->OnPatternCompleted.AddUniqueDynamic(this, &ThisClass::HandlePatternCompleted);
	bBound = true;
	bRunHadSubStandardNote = false;
	return true;
}

UMelodiaNarrativeSubsystem* UMelodiaPCGNarrativeChallengeBridgeComponent::GetNarrative() const
{
	return UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(this);
}

bool UMelodiaPCGNarrativeChallengeBridgeComponent::IsChallengeCompleted() const
{
	const UMelodiaNarrativeSubsystem* Narrative = GetNarrative();
	if (!Narrative)
	{
		// Fail closed: with no narrative authority we cannot claim completion.
		return false;
	}
	return Narrative->IsWorldChallengeCompleted(ChallengeId, CompletionFlagId);
}

void UMelodiaPCGNarrativeChallengeBridgeComponent::HandleNoteJudged(FPCGHeroMusicNoteEvent Event)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaPCGNarrativeChallengeBridge_HandleNoteJudged);
	if (!bBound || !bRequireCleanRun)
	{
		return;
	}
	if (static_cast<uint8>(Event.Grade) < static_cast<uint8>(MinimumAcceptedGrade))
	{
		bRunHadSubStandardNote = true;
	}
}

void UMelodiaPCGNarrativeChallengeBridgeComponent::HandlePatternCompleted()
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaPCGNarrativeChallengeBridge_HandlePatternCompleted);
	if (!bBound)
	{
		return;
	}

	// Consume the run-quality flag regardless of the outcome below, so a rejected
	// attempt does not carry its verdict into the player's next attempt.
	const bool bCleanRun = !bRunHadSubStandardNote;
	bRunHadSubStandardNote = false;

	if (ChallengeId.IsNone() || CompletionFlagId.IsNone() || CompletionIntentId.IsNone())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MelodiaPCGNarrativeChallengeBridge: pattern completed but ids are unset (challenge='%s' flag='%s' intent='%s'); no commit attempted."),
			*ChallengeId.ToString(), *CompletionFlagId.ToString(), *CompletionIntentId.ToString());
		return;
	}

	if (bRequireCleanRun && !bCleanRun)
	{
		UE_LOG(LogTemp, Verbose,
			TEXT("MelodiaPCGNarrativeChallengeBridge: pattern completed below the required grade; challenge '%s' not committed."),
			*ChallengeId.ToString());
		return;
	}

	UMelodiaNarrativeSubsystem* Narrative = GetNarrative();
	if (!Narrative)
	{
		LastCommitResult = EMelodiaContentCommitResult::Rejected;
		LastCommitFailure = EMelodiaContentCommitFailure::AuthorityUnavailable;
		UE_LOG(LogTemp, Warning,
			TEXT("MelodiaPCGNarrativeChallengeBridge: no narrative subsystem; challenge '%s' failed closed."),
			*ChallengeId.ToString());
		return;
	}

	// The single canonical write path. CommitWorldChallenge is one transaction:
	// completion flag, allowlisted reward and consumed intent land together or
	// not at all. Never split this into SetNarrativeFlag + GrantDialogueReward.
	EMelodiaContentCommitFailure Failure = EMelodiaContentCommitFailure::None;
	const EMelodiaContentCommitResult Result = Narrative->CommitWorldChallenge(
		ChallengeId,
		CompletionFlagId,
		RewardId,
		CompletionIntentId,
		Failure);

	LastCommitResult = Result;
	LastCommitFailure = Failure;

	switch (Result)
	{
	case EMelodiaContentCommitResult::Applied:
		UE_LOG(LogTemp, Log,
			TEXT("MelodiaPCGNarrativeChallengeBridge: music key committed challenge '%s' (flag '%s', reward '%s')."),
			*ChallengeId.ToString(), *CompletionFlagId.ToString(), *RewardId.ToString());
		break;

	case EMelodiaContentCommitResult::AlreadyApplied:
		// Expected on replay. The narrative record owns idempotency; this is a
		// no-op, not an error, and the reward is not granted twice.
		UE_LOG(LogTemp, Verbose,
			TEXT("MelodiaPCGNarrativeChallengeBridge: challenge '%s' was already complete; replay is a no-op."),
			*ChallengeId.ToString());
		break;

	default:
		UE_LOG(LogTemp, Warning,
			TEXT("MelodiaPCGNarrativeChallengeBridge: challenge '%s' commit returned %s (%s). Check the id is in WorldChallengeIds, the flag in NarrativeFlagIds and the reward in DialogueRewardIds."),
			*ChallengeId.ToString(), *EnumToString(Result), *EnumToString(Failure));
		break;
	}

	OnChallengeCommitted.Broadcast(ChallengeId, Result);
}
