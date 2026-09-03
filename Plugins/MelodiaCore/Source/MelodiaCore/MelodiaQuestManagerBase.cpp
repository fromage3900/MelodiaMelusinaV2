#include "MelodiaQuestManagerBase.h"
#include "MelodiaProgressionComponent.h"
#include "Kismet/GameplayStatics.h"

AMelodiaQuestManagerBase::AMelodiaQuestManagerBase()
{
	PrimaryActorTick.bCanEverTick = false;
}

AMelodiaQuestManagerBase* AMelodiaQuestManagerBase::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	if (!World) return nullptr;

	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(World, AMelodiaQuestManagerBase::StaticClass(), Found);
	return Found.Num() > 0 ? Cast<AMelodiaQuestManagerBase>(Found[0]) : nullptr;
}

bool AMelodiaQuestManagerBase::AcceptQuest(const FMelodiaQuestDef& Quest)
{
	if (Quest.QuestId == NAME_None)
		return false;
	if (ActiveQuests.Contains(Quest.QuestId))
		return false;
	if (CompletedQuestIds.Contains(Quest.QuestId))
		return false;

	ActiveQuests.Add(Quest.QuestId, Quest);
	OnQuestAccepted.Broadcast(Quest.QuestId);
	return true;
}

bool AMelodiaQuestManagerBase::CompleteQuest(FName QuestId)
{
	if (!ActiveQuests.Contains(QuestId))
		return false;

	const FMelodiaQuestDef Quest = ActiveQuests[QuestId];
	ActiveQuests.Remove(QuestId);
	CompletedQuestIds.Add(QuestId);

	// Cozy: quest rewards apply directly to the player's progression component.
	if (Quest.RewardXP > 0 || Quest.RewardGold > 0)
	{
		const UWorld* World = GetWorld();
		if (APlayerController* PC = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr)
		{
			if (APawn* Pawn = PC->GetPawn())
			{
				if (UMelodiaProgressionComponent* Progression = Pawn->FindComponentByClass<UMelodiaProgressionComponent>())
				{
					if (Quest.RewardXP > 0)
					{
						Progression->AddXP(Quest.RewardXP);
					}
					if (Quest.RewardGold > 0)
					{
						Progression->AddCurrency(Quest.RewardGold);
					}
				}
			}
		}
	}

	OnQuestCompleted.Broadcast(QuestId);
	return true;
}

bool AMelodiaQuestManagerBase::IsQuestActive(FName QuestId) const
{
	return ActiveQuests.Contains(QuestId);
}

bool AMelodiaQuestManagerBase::IsQuestCompleted(FName QuestId) const
{
	return CompletedQuestIds.Contains(QuestId);
}

TArray<FMelodiaQuestDef> AMelodiaQuestManagerBase::GetActiveQuests() const
{
	TArray<FMelodiaQuestDef> Result;
	ActiveQuests.GenerateValueArray(Result);
	return Result;
}

TArray<FName> AMelodiaQuestManagerBase::GetCompletedQuestIds() const
{
	return CompletedQuestIds;
}

void AMelodiaQuestManagerBase::RestoreQuestState(const TArray<FMelodiaQuestDef>& InActiveQuests, const TArray<FName>& InCompletedIds)
{
	ActiveQuests.Empty();
	CompletedQuestIds.Empty();

	for (const FMelodiaQuestDef& Quest : InActiveQuests)
	{
		if (Quest.QuestId != NAME_None)
		{
			ActiveQuests.Add(Quest.QuestId, Quest);
		}
	}
	CompletedQuestIds = InCompletedIds;
}
