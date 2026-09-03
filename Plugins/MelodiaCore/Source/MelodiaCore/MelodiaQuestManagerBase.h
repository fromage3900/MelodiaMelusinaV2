#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaQuestManagerBase.generated.h"

USTRUCT(BlueprintType)
struct FMelodiaQuestDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	FName QuestId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	int32 RequiredLevel = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	int32 RewardXP = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Quest")
	int32 RewardGold = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaOnQuestAccepted, FName, QuestId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaOnQuestCompleted, FName, QuestId);

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second quest authority). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API AMelodiaQuestManagerBase : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaQuestManagerBase();

	/** First quest manager found in the world -- lets WBP_QuestJournal reach it without a manual actor reference. */
	UFUNCTION(BlueprintPure, Category="Melodia|Quest", meta=(WorldContext="WorldContextObject"))
	static AMelodiaQuestManagerBase* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category="Melodia|Quest")
	bool AcceptQuest(const FMelodiaQuestDef& Quest);

	UFUNCTION(BlueprintCallable, Category="Melodia|Quest")
	bool CompleteQuest(FName QuestId);

	UFUNCTION(BlueprintPure, Category="Melodia|Quest")
	bool IsQuestActive(FName QuestId) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Quest")
	bool IsQuestCompleted(FName QuestId) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Quest")
	TArray<FMelodiaQuestDef> GetActiveQuests() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Quest")
	TArray<FName> GetCompletedQuestIds() const;

	/** Restores quest state from a loaded save, clearing current state first. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Quest")
	void RestoreQuestState(const TArray<FMelodiaQuestDef>& InActiveQuests, const TArray<FName>& InCompletedIds);

	UPROPERTY(BlueprintAssignable, Category="Melodia|Quest")
	FMelodiaOnQuestAccepted OnQuestAccepted;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Quest")
	FMelodiaOnQuestCompleted OnQuestCompleted;

private:
	UPROPERTY()
	TMap<FName, FMelodiaQuestDef> ActiveQuests;

	UPROPERTY()
	TArray<FName> CompletedQuestIds;
};
