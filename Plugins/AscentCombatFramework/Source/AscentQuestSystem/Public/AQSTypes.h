// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AQSQuestObjective.h"
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Graph/AQSQuest.h"
#include <Net/Serialization/FastArraySerializer.h>
#include "AGSGraphNode.h"

#include "AQSTypes.generated.h"

class UAQSQuest;

/**
 *
 */
USTRUCT(BlueprintType)
struct FAQSQuestData : public FTableRowBase {
	GENERATED_BODY()

	FAQSQuestData()
	{
		Quest = nullptr;
	}

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = AQS)
	class UAQSQuest* Quest;
};

USTRUCT(BlueprintType)
struct FAQSObjectiveRecord {
	GENERATED_BODY()

public:
	FAQSObjectiveRecord()
	{
		CurrentRepetitions = 0;
	};

	FAQSObjectiveRecord(const UAQSQuestObjective* objective)
	{
		Objective = objective->GetObjectiveTag();
		CurrentRepetitions = objective->GetCurrentRepetitions();
		ObjectiveId = objective->GetNodeOwner()->GetNodeId();
	}

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	FGameplayTag Objective;

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	FGuid ObjectiveId;

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	int32 CurrentRepetitions;

	FORCEINLINE bool operator==(const FAQSObjectiveRecord& Other) const
	{
		return this->ObjectiveId == Other.ObjectiveId;
	}

	FORCEINLINE bool operator!=(const FAQSObjectiveRecord& Other) const
	{
		return this->Objective != Other.Objective;
	}

	FORCEINLINE bool operator==(const FGuid& Other) const
	{
		return this->ObjectiveId == Other;
	}

	FORCEINLINE bool operator!=(const FGuid& Other) const
	{
		return this->ObjectiveId != Other;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return this->Objective == Other;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return this->Objective != Other;
	}
};

USTRUCT(BlueprintType)
struct FAQSQuestRecord : public FFastArraySerializerItem {
	GENERATED_BODY()

public:
	FAQSQuestRecord(const class UAQSQuest* quest);

	FAQSQuestRecord() {};

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	FGameplayTag Quest;

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	TArray<FAQSObjectiveRecord> Objectives;

	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	TArray<FGuid> CompletedObjectives;

	FORCEINLINE bool operator==(const FAQSQuestRecord& Other) const
	{
		return this->Quest == Other.Quest;
	}

	FORCEINLINE bool operator!=(const FAQSQuestRecord& Other) const
	{
		return this->Quest != Other.Quest;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return this->Quest == Other;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return this->Quest != Other;
	}
};

USTRUCT(BlueprintType, meta = (HasNativeNetSerialize))
struct FAQSQuestList : public FFastArraySerializer {
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
	TArray<FAQSQuestRecord> Quests;

	bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
	{
		return FFastArraySerializer::FastArrayDeltaSerialize<FAQSQuestRecord, FAQSQuestList>(Quests, DeltaParms, *this);
	}

	void AddQuest(const FAQSQuestRecord& Record)
	{
		const int32 Index = Quests.IndexOfByKey(Record);

		if (Index != INDEX_NONE) {
			Quests[Index] = Record;
			MarkItemDirty(Quests[Index]);
		}
		else {
			const int32 NewIndex = Quests.Add(Record);
			MarkItemDirty(Quests[NewIndex]);
		}
	}

	bool Contains(const FGameplayTag& QuestTag) const
	{
		return Quests.Contains(QuestTag);
	}

	void RemoveQuest(const FGameplayTag& QuestTag)
	{
		const int32 Index = Quests.IndexOfByPredicate([&](const FAQSQuestRecord& R) {
			return R.Quest == QuestTag;
			});
		if (Index != INDEX_NONE) {
			Quests.RemoveAt(Index);
			MarkArrayDirty();
		}
	}
	void Remove(const FAQSQuestRecord& Record)
	{
		const int32 Index = Quests.IndexOfByKey(Record);
		if (Index != INDEX_NONE) {
			Quests.RemoveAt(Index);
			MarkArrayDirty();
		}
	}

	const FAQSQuestRecord* GetQuest(const FGameplayTag& QuestTag) const
	{
		return Quests.FindByPredicate([&](const FAQSQuestRecord& R) {
			return R.Quest == QuestTag;
			});
	}
};

template <>
struct TStructOpsTypeTraits<FAQSQuestList> : public TStructOpsTypeTraitsBase2<FAQSQuestList> {
	enum { WithNetDeltaSerializer = true };
};

USTRUCT(BlueprintType)
struct FAQSObjectiveInfo {
	GENERATED_BODY()

public:
	FAQSObjectiveInfo()
	{
		CurrentRepetitions = 0;
		TotalRepetitions = 1;
	};

	FAQSObjectiveInfo(const UAQSQuestObjective* objective, const FAQSObjectiveRecord& objectiveRecord)
	{
		ObjectiveTag = objectiveRecord.Objective;
		CurrentRepetitions = objectiveRecord.CurrentRepetitions;
		ObjectiveName = objective->GetObjectiveName();
		ObjectiveDescription = objective->GetDescription();
		TotalRepetitions = objective->GetRepetitions();
	};

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FGameplayTag ObjectiveTag;

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FText ObjectiveName;

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FText ObjectiveDescription;

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	int32 CurrentRepetitions;

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	int32 TotalRepetitions;
};

USTRUCT(BlueprintType)
struct FAQSQuestInfo {
	GENERATED_BODY()

public:
	FAQSQuestInfo()
	{

		QuestIcon = nullptr;
	};

	FAQSQuestInfo(const UAQSQuest* quest, const FAQSQuestRecord& questRecord)
	{
		QuestTag = quest->GetQuestTag();
		QuestName = quest->GetQuestName();
		QuestDescription = quest->GetQuestDescription();
		QuestIcon = quest->GetQuestIcon();
		Objectives = questRecord.Objectives;
	};

	/*Unique Tag for this quest, is a good practice to use a root GameplayTag for this, and
	child tags for objectives*/
	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FGameplayTag QuestTag;

	/*Name for this quest, can be used for UI*/
	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FText QuestName;

	/*A description for this objective, can be used for UI*/
	UPROPERTY(BlueprintReadOnly, Category = AQS)
	FText QuestDescription;

	/*An icon for this objective, can be used for UI*/
	UPROPERTY(BlueprintReadOnly, Category = AQS)
	class UTexture2D* QuestIcon;

	UPROPERTY(BlueprintReadOnly, Category = AQS)
	TArray<FAQSObjectiveRecord> Objectives;
};

UCLASS()
class ASCENTQUESTSYSTEM_API UAQSTypes : public UObject {
	GENERATED_BODY()
};
