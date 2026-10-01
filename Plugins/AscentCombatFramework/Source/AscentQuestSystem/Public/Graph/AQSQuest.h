// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraph.h"
#include "AQSQuestTargetComponent.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include <WorldPartition/DataLayer/DataLayerInstance.h>

#include "AQSQuest.generated.h"

class UAQSQuestSuccededNode;
class UAQSQuestFailedNode;
class UPrimaryDataAsset;

/**
 *
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuestStarted, const FGameplayTag&, quest);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnQuestEnded, const FGameplayTag&, quest, bool, bSuccessful);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnQuestUpdated, const FGameplayTag&, quest);

/**
 * @class UAQSQuest
 * Represents a quest in the game, managing objectives, state, and related data.
 */
UCLASS()
class ASCENTQUESTSYSTEM_API UAQSQuest : public UAGSGraph {
	GENERATED_BODY()

	friend class UAQSQuestManagerComponent;

protected:
	virtual bool ActivateNode(class UAGSGraphNode* node) override;

	/*Unique Tag for this quest, is a good practice to use a root GameplayTag for this, and
	child tags for objectives*/
	UPROPERTY(EditDefaultsOnly, Category = AQS, meta = (Categories = "Quest"))
	FGameplayTag QuestTag;

	/*Name for this quest, can be used for UI*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	FText QuestName;

	/*A description for this objective, can be used for UI*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	FText QuestDescription;

	/*An icon for this objective, can be used for UI*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	class UTexture2D* QuestIcon;

	/*A data asset you can implement in BP to expand quest properties*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	class UPrimaryDataAsset* GameSpecificData;

	/*In WP, the layer to load to have all the required actors*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	class UDataLayerAsset* LayerToLoad;

public:
	UAQSQuest();

	void CompleteQuest(bool bSucceded);
	bool GetIsStarted() const { return bIsStarted; }

	/**
	 * Gets the quest manager component.
	 * @return A pointer to the UAQSQuestManagerComponent associated with this quest.
	 */
	TObjectPtr<class UAQSQuestManagerComponent> GetQuestManager() const
	{
		return questManager;
	}

	/**
	 * Sets the completed objectives for this quest.
	 * @param inObjectives A list of gameplay tags representing completed objectives.
	 */
	void SetCompletedObjectives(const TArray<FGuid>& inObjectives)
	{

		CompletedObjectives = inObjectives;
	}

	/**
	 * Gets the Data Layer associated with this quest.
	 * @return A pointer to the UDataLayerAsset that should be loaded.
	 */
	class UDataLayerAsset* GetLayerToLoad() const { return LayerToLoad; }

	/**
	 * Sets the Data Layer that should be loaded for this quest.
	 * @param val A pointer to the UDataLayerAsset to set.
	 */
	UFUNCTION(BlueprintCallable, Category = "AQS")
	void SetLayerToLoad(class UDataLayerAsset* val) { LayerToLoad = val; }

	/**
	 * Retrieves the list of completed objectives.
	 * @return An array of FGameplayTag representing the completed objectives.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE TArray<FGuid> GetCompletedObjectives() const
	{
		return CompletedObjectives;
	}

	/**
	 * Checks if a specific objective has been completed.
	 * @param objective The objective tag to check.
	 * @return True if the objective has been completed, otherwise false.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE bool IsObjectiveCompleted(const FGuid& objective) const
	{
		return CompletedObjectives.Contains(objective);
	}

	/**
	 * Checks if this quest is currently being tracked by the player.
	 * @return True if the quest is currently tracked, otherwise false.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE bool IsCurrentTrackedQuest() const
	{
		return bIsTracked;
	}

	/**
	 * Gets the unique tag associated with this quest.
	 * @return The quest's FGameplayTag.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE FGameplayTag GetQuestTag() const
	{
		return QuestTag;
	}

	/**
	 * Gets the name of the quest.
	 * @return The quest name as an FText.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE FText GetQuestName() const
	{
		return QuestName;
	}

	/**
	 * Gets the description of the quest.
	 * @return The quest description as an FText.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE FText GetQuestDescription() const
	{
		return QuestDescription;
	}

	/**
	 * Gets the icon associated with this quest.
	 * @return A pointer to the quest's icon texture (UTexture2D).
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	FORCEINLINE UTexture2D* GetQuestIcon() const
	{
		return QuestIcon;
	}

	/**
	 * Checks if the quest has an active objective with the specified tag.
	 * @param objectiveTag The tag of the objective to check.
	 * @return True if the objective is active, otherwise false.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	bool HasActiveObjective(const FGuid& objectiveId) const;
	bool HasActiveObjectiveByTag(const FGameplayTag& objectiveTag) const;

	/**
	 * Gets the Quest Succeeded node. Every quest is supposed to only have 1 succeeded node.
	 * @return A pointer to the  UAQSQuestSuccedeedNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestSuccededNode* GetQuestSucceededNode() const;

	/**
	 * Gets the Quest Failed node. Every quest is supposed to only have 1 Failed node.
	 * @return A pointer to the  UAQSQuestFailedNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestFailedNode* GetQuestFailedNode() const;

	/**
	 * Gets the active objective node associated with a specific objective tag.
	 * @param objectiveID The Id of the objective Node.
	 * @return A pointer to the active UAQSObjectiveNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSObjectiveNode* GetActiveObjectiveNode(const FGuid& objectiveId) const;

	/**
	 * Gets the active objective associated with a specific objective tag.
	 * @param objectiveID The Id of the objective Node.
	 * @return A pointer to the active UAQSQuestObjective, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestObjective* GetActiveObjective(const FGuid& objectiveId) const;

	/**
	 * Gets an objective node by its tag.
	 * @param objectiveID The Id of the objective Node.
	 * @return A pointer to the UAQSObjectiveNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSObjectiveNode* GetObjectiveNode(const FGuid& objectiveId) const;

	/**
	 * Retrieves all currently active objectives in this quest.
	 * @return An array of UAQSQuestObjective pointers representing active objectives.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	TArray<UAQSQuestObjective*> GetAllActiveObjectives() const;

	/**
	 * Gets a specific objective by its gameplay tag.
	 * @param objectiveTag The tag of the objective.
	 * @return A pointer to the corresponding UAQSQuestObjective, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestObjective* GetObjectiveByTag(const FGameplayTag& objectiveTag) const;
	UAQSQuestObjective* GetObjectiveById(const FGuid& objectiveId) const;

	/**
	 * Gets a specific objective by its gameplay tag.
	 * @param objectiveTag The tag of the objective.
	 * @return A pointer to the corresponding UAQSQuestObjective, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UPrimaryDataAsset* GetGameSpecificData() const {
		return GameSpecificData;
	}

	/** Delegate triggered when a quest starts. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnQuestStarted OnQuestStarted;

	/** Delegate triggered when a quest ends. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnQuestEnded OnQuestEnded;

	/** Delegate triggered when an objective starts. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnObjectiveStarted OnObjectiveStarted;

	/** Delegate triggered when an objective is completed. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnObjectiveCompleted OnObjectiveCompleted;

	/** Delegate triggered every time an objective is updated. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnObjectiveUpdated OnObjectiveUpdated;

	/** Delegate triggered when an objective is interrupted. */
	UPROPERTY(BlueprintAssignable, Category = "AQS")
	FOnObjectiveInterrupted OnObjectiveInterrupted;

	FORCEINLINE bool operator==(const FGameplayTag& OtherTag) const
	{
		return this->QuestTag == OtherTag;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& OtherTag) const
	{
		return this->QuestTag != OtherTag;
	}
	FORCEINLINE bool operator==(const UAQSQuest*& Other) const
	{
		return QuestTag == Other->QuestTag;
	}

	FORCEINLINE bool operator!=(const UAQSQuest*& Other) const
	{
		return QuestTag != Other->QuestTag;
	}

private:
	bool bIsTracked;

	bool StartQuest(class APlayerController* inController, TObjectPtr<UAQSQuestManagerComponent> inQuestManager, bool bActivateChildNodes = true);

	bool StartGraph();

	void SetQuestTracked(bool inTracked);

	bool CompleteBranchedObjectiveByTag(const FGameplayTag& objectiveTag, const TArray<FName>& transitionFilters);

	bool CompleteBranchedObjective(const FGuid& objectiveID, const TArray<FName>& optionalTransitionFilters /*= TArray<FName>()*/);
	bool FromTagToID(const FGameplayTag& objectiveTag, FGuid& outID) const;
	bool CompleteObjectiveByTag(const FGameplayTag& objectiveTag);
	bool CompleteObjective(const FGuid& objectiveID);

	TObjectPtr<class UAQSQuestManagerComponent> questManager;

	void ResetQuest();

	UFUNCTION()
	void OnDataLayerStateChanged(const UDataLayerInstance* LayerInst, EDataLayerRuntimeState State);

	bool bInActivateChildrenNode;
	TArray<FGuid> CompletedObjectives;

	bool bIsStarted = false;
};
