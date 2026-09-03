#include "MelodiaSaveRecoverySubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "RhythmBeatTracker.h"

UMelodiaSaveRecoverySubsystem* UMelodiaSaveRecoverySubsystem::Get(const UObject* WorldContextObject)
{
	if (!IsValid(WorldContextObject))
	{
		return nullptr;
	}

	const UWorld* World = GEngine
		? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull)
		: nullptr;
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaSaveRecoverySubsystem>() : nullptr;
}

void UMelodiaSaveRecoverySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	TrackedRhythmSessionId = 0;
}

void UMelodiaSaveRecoverySubsystem::Deinitialize()
{
	InvalidateRhythmTransientState(TEXT("save/recovery subsystem deinitialize"));
	Super::Deinitialize();
}

void UMelodiaSaveRecoverySubsystem::BeginSaveBoundary(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("before save: %s"), *Reason));
}

void UMelodiaSaveRecoverySubsystem::EndSaveBoundary(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("after save: %s"), *Reason));
}

void UMelodiaSaveRecoverySubsystem::BeginLoadBoundary(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("before load: %s"), *Reason));
}

void UMelodiaSaveRecoverySubsystem::EndLoadBoundary(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("after load: %s"), *Reason));
}

void UMelodiaSaveRecoverySubsystem::NotifyDeathRecovery(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("death recovery: %s"), *Reason));
}

void UMelodiaSaveRecoverySubsystem::NotifyRetryRecovery(const FString& Reason)
{
	InvalidateRhythmTransientState(FString::Printf(TEXT("retry recovery: %s"), *Reason));
}

bool UMelodiaSaveRecoverySubsystem::TrackRhythmSession(const int64 SessionId)
{
	if (SessionId <= 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_RECOVERY rejected rhythm session registration: invalid session id %lld."), SessionId);
		return false;
	}

	if (TrackedRhythmSessionId != 0 && TrackedRhythmSessionId != SessionId)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_RECOVERY rejected rhythm session registration: session %lld is already tracked; refusing to replace it with %lld."),
			TrackedRhythmSessionId, SessionId);
		return false;
	}

	TrackedRhythmSessionId = SessionId;
	return true;
}

void UMelodiaSaveRecoverySubsystem::InvalidateRhythmTransientState(const FString& Reason)
{
	bool bSessionInvalidated = false;
	UMelodiaRhythmCombatSubsystem* RhythmSubsystem = UMelodiaRhythmCombatSubsystem::Get(this);

	if (TrackedRhythmSessionId != 0)
	{
		const int64 SessionId = TrackedRhythmSessionId;
		bSessionInvalidated = RhythmSubsystem && RhythmSubsystem->GetActiveSessionId() != 0;
		if (bSessionInvalidated)
		{
			RhythmSubsystem->InvalidateSession();
		}
		else
		{
			UE_LOG(LogTemp, Log,
				TEXT("MELODIA_RECOVERY tracked rhythm session %lld was already inactive at %s."),
				SessionId, *Reason);
		}
		TrackedRhythmSessionId = 0;
	}
	else if (RhythmSubsystem && RhythmSubsystem->GetActiveSessionId() != 0)
	{
		// The subsystem intentionally exposes no guessed "invalidate all" operation.
		// Refusing to fabricate a session ID is safer than touching an unrelated
		// combat transaction or completing it on behalf of stock combat.
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_RECOVERY found an active rhythm session at %s but no registered session ID; leaving it untouched."),
			*Reason);
	}

	StopPresentationBeatTrackers();
	UE_LOG(LogTemp, Log,
		TEXT("MELODIA_RHYTHM_TRANSIENT_INVALIDATED reason=%s session_invalidated=%d"),
		*Reason, bSessionInvalidated ? 1 : 0);
}

void UMelodiaSaveRecoverySubsystem::StopPresentationBeatTrackers()
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (!World)
	{
		return;
	}

	int32 StoppedTrackers = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		TArray<UActorComponent*> Components;
		It->GetComponents(Components);
		for (UActorComponent* Component : Components)
		{
			URhythmBeatTracker* Tracker = Cast<URhythmBeatTracker>(Component);
			if (Tracker && Tracker->IsTracking())
			{
				Tracker->StopTracking();
				++StoppedTrackers;
			}
		}
	}

	if (StoppedTrackers > 0)
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_RECOVERY stopped %d presentation beat tracker(s)."), StoppedTrackers);
	}
}
