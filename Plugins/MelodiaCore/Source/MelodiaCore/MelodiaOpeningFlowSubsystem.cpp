#include "MelodiaOpeningFlowSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MelodiaQuestManagerBase.h"
#include "MelodiaRulesGenerated.h"

UMelodiaOpeningFlowSubsystem* UMelodiaOpeningFlowSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	return World && World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaOpeningFlowSubsystem>()
		: nullptr;
}

bool UMelodiaOpeningFlowSubsystem::BeginMorning()
{
	return TransitionTo(EMelodiaOpeningPhase::NotStarted, EMelodiaOpeningPhase::Morning);
}

bool UMelodiaOpeningFlowSubsystem::NotifySirDeparted()
{
	return TransitionTo(EMelodiaOpeningPhase::Morning, EMelodiaOpeningPhase::SirDeparted);
}

bool UMelodiaOpeningFlowSubsystem::NotifyDreamstateEntered()
{
	return TransitionTo(EMelodiaOpeningPhase::SirDeparted, EMelodiaOpeningPhase::Dreamstate);
}

bool UMelodiaOpeningFlowSubsystem::NotifyDreamstateCompleted()
{
	const bool bTransitioned = TransitionTo(EMelodiaOpeningPhase::Dreamstate, EMelodiaOpeningPhase::ZenExploration);
	if (bTransitioned)
	{
		if (AMelodiaQuestManagerBase* QuestManager = FindQuestManager())
		{
			FMelodiaQuestDef TutorialQuest;
			TutorialQuest.QuestId = FName(MelodiaRulesGen::OpeningTutorialQuestId);
			QuestManager->AcceptQuest(TutorialQuest);
		}
	}
	return bTransitioned;
}

bool UMelodiaOpeningFlowSubsystem::NotifyZenEncounterVictory(const FName EnemyId)
{
	if (Phase != EMelodiaOpeningPhase::ZenExploration || EnemyId != FName(MelodiaRulesGen::OpeningTutorialEnemyId))
	{
		return false;
	}

	if (AMelodiaQuestManagerBase* QuestManager = FindQuestManager())
	{
		QuestManager->CompleteQuest(FName(MelodiaRulesGen::OpeningTutorialQuestId));
	}

	const EMelodiaOpeningPhase Previous = Phase;
	Phase = EMelodiaOpeningPhase::FirstDungeonUnlocked;
	bHeartMelodyTokenGranted = true;
	OnPhaseChanged.Broadcast(Phase, Previous);
	OnFirstDungeonUnlocked.Broadcast();
	return true;
}

bool UMelodiaOpeningFlowSubsystem::NotifySirRescued()
{
	return TransitionTo(EMelodiaOpeningPhase::FirstDungeonUnlocked, EMelodiaOpeningPhase::SirRescued);
}

bool UMelodiaOpeningFlowSubsystem::NotifyReturnedHome()
{
	return TransitionTo(EMelodiaOpeningPhase::SirRescued, EMelodiaOpeningPhase::ReturnedHome);
}

AMelodiaQuestManagerBase* UMelodiaOpeningFlowSubsystem::FindQuestManager() const
{
	UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	return World ? AMelodiaQuestManagerBase::Get(World) : nullptr;
}

bool UMelodiaOpeningFlowSubsystem::ApplyTravelEvent(const EMelodiaOpeningTravelEvent TravelEvent)
{
	switch (TravelEvent)
	{
	case EMelodiaOpeningTravelEvent::EnterDreamstate:
		return NotifyDreamstateEntered();
	case EMelodiaOpeningTravelEvent::CompleteDreamstate:
		return NotifyDreamstateCompleted();
	case EMelodiaOpeningTravelEvent::None:
	default:
		return true;
	}
}

void UMelodiaOpeningFlowSubsystem::ResetOpening()
{
	const EMelodiaOpeningPhase Previous = Phase;
	Phase = EMelodiaOpeningPhase::NotStarted;
	bHeartMelodyTokenGranted = false;
	VisitedExplorationPointIds.Reset();
	if (Previous != Phase)
	{
		OnPhaseChanged.Broadcast(Phase, Previous);
	}
}

bool UMelodiaOpeningFlowSubsystem::NotifyExplorationPointVisited(const FName PointId)
{
	if (Phase != EMelodiaOpeningPhase::Morning || PointId.IsNone())
	{
		return false;
	}

	bool bAlreadyVisited = false;
	VisitedExplorationPointIds.Add(PointId, &bAlreadyVisited);
	return !bAlreadyVisited;
}

void UMelodiaOpeningFlowSubsystem::RestoreFromSave(const EMelodiaOpeningPhase InPhase, const bool bInHeartMelodyTokenGranted)
{
	const EMelodiaOpeningPhase Previous = Phase;
	Phase = InPhase;
	bHeartMelodyTokenGranted = bInHeartMelodyTokenGranted;
	if (Previous != Phase)
	{
		OnPhaseChanged.Broadcast(Phase, Previous);
	}
}

bool UMelodiaOpeningFlowSubsystem::TransitionTo(const EMelodiaOpeningPhase ExpectedPhase, const EMelodiaOpeningPhase NewPhase)
{
	if (Phase != ExpectedPhase)
	{
		return false;
	}

	const EMelodiaOpeningPhase Previous = Phase;
	Phase = NewPhase;
	OnPhaseChanged.Broadcast(Phase, Previous);
	return true;
}
