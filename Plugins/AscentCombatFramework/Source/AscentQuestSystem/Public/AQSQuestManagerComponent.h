// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AQSQuestTargetComponent.h"
#include "AQSTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Graph/AQSQuest.h"
#include <Containers/Map.h>
#include <GameplayTagContainer.h>

#include "AQSQuestManagerComponent.generated.h"

class UAQSQuestObjective;
class UAQSQuestTargetComponent;
class UAQSQuest;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInProgressQuestsUpdate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCompletedQuestsUpdate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnFailedQuestsUpdate);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTrackedQuestUpdate);

UCLASS(Blueprintable, ClassGroup = (ATS), meta = (BlueprintSpawnableComponent))
class ASCENTQUESTSYSTEM_API UAQSQuestManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UAQSQuestManagerComponent();

public:
	//** REPLICATION **//
	/**
	 * Completes an objective on the server.
	 * @param objectiveToComplete The id of the objective to be completed.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = AQS)
	void ServerCompleteObjective(const FGuid& objectiveToComplete);

	/**
	 * Completes an objective on the server.
	 * @param objectiveToComplete The id of the objective to be completed.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = AQS)
	void ServerCompleteObjectiveByTag(const FGameplayTag& objectiveToComplete);

	/**
	 * Completes a branched objective on the server.
	 * @param objectiveToComplete The tag of the objective to be completed.
	 * @param optionalTransitionFilters A list of transition filters to unlock specific paths.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = AQS)
	void ServerCompleteBranchedObjective(const FGuid& objectiveToComplete, const TArray<FName>& optionalTransitionFilters);

	/**
	 * Starts a quest on the server.
	 * Starts a quest on the server.
	 * @param questTag The tag of the quest to start.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = AQS, meta = (GameplayTagFilter = "Quest"))
	void ServerStartQuest(const FGameplayTag& questTag);

	/**
	 * Removes an in-progress quest on the server.
	 * @param questTag The tag of the quest to remove.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = AQS)
	void ServerRemoveInProgressQuest(const FGameplayTag& questTag);



	/**
	 * Starts a quest.
	 * @param questTag The tag of the quest to start.
	 * @return True if the quest started successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS, meta = (GameplayTagFilter = "Quest"))
	bool StartQuest(const FGameplayTag& questTag);

	/**
	 * Stops a quest, resetting its state.
	 * @param questTag The tag of the quest to stop.
	 * @return True if the quest was successfully stopped.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS, meta = (GameplayTagFilter = "Quest"))
	bool StopQuest(const FGameplayTag& questTag);

	/**
	 * Attempts to complete an objective in all in-progress quests.
	 * @param objectiveToComplete The tag of the objective to complete.
	 * @return True if the objective was completed.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool CompleteObjective(FGameplayTag objectiveToComplete);

	/**
   * Attempts to complete an objective in all in-progress quests.
   * @param objectiveID The ID of the objective to complete.
   * @return True if the objective was completed.
	*/
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool CompleteObjectiveByNodeID(const FGuid& objectiveID);


	/**
	 * Completes a branched objective by unlocking only the specified transitions.
	 * @param objectiveToComplete The tag of the objective to complete.
	 * @param optionalTransitionFilters The transition filters that determine the unlocking paths.
	 * @return True if the objective was completed.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool CompleteBranchedObjective(const FGuid& objectiveToComplete, TArray<FName> optionalTransitionFilters);

	/**
	 * Tracks an in-progress quest using its tag.
	 * @param questTag The tag of the quest to track.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void TrackInProgressQuestByTag(const FGameplayTag& questTag);

	/**
	 * Tracks an in-progress quest.
	 * @param questToTrack The quest object to track.
	 * @return True if the quest was successfully tracked.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool TrackInProgressQuest(class UAQSQuest* questToTrack);

	/**
	 * Removes an in-progress quest.
	 * @param quest The quest object to remove.
	 * @return True if the quest was successfully removed.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool RemoveInProgressQuest(UAQSQuest* quest);

	/**
	 * Untracks the currently tracked quest.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void UntrackCurrentQuest();

	//** SERVER ONLY GETTERS **//

	/**
	 * Checks if a quest is currently in progress.
	 * @param quest The quest to check.
	 * @return True if the quest is in progress.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	FORCEINLINE bool IsQuestInProgress(class UAQSQuest* quest) const { return InProgressQuests.Contains(quest); }

	/**
	 * Retrieves the list of in-progress quests.
	 * @return An array of currently in-progress quests.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	FORCEINLINE TArray<class UAQSQuest*> GetInProgressQuests() const { return InProgressQuests; }

	/**
	 * Retrieves the list of completed quests.
	 * @return An array containing all completed quests.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	FORCEINLINE TArray<class UAQSQuest*> GetCompletedQuests() const
	{
		return CompletedQuests;
	}

	/**
	 * Retrieves the list of failed quests.
	 * @return An array containing all failed quests.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	FORCEINLINE TArray<class UAQSQuest*> GetFailedQuests() const
	{
		return FailedQuests;
	}

	/**
	 * Retrieves the currently tracked quest.
	 * @return A pointer to the currently tracked quest, or nullptr if none is being tracked.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	FORCEINLINE class UAQSQuest* GetCurrentlyTrackedQuest() const
	{
		return TrackedQuest;
	}

	/**
	 * Retrieves the objectives of the currently tracked quest.
	 * @return An array of quest objectives associated with the currently tracked quest.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	TArray<UAQSQuestObjective*> GetCurrentlyTrackedQuestObjectives() const;

	/**
	 * Retrieves the quest target components of the currently tracked quest.
	 * @return An array of quest target components related to the currently tracked quest.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	TArray<UAQSQuestTargetComponent*> GetCurrentlyTrackedQuestObjectivesTargets() const;

	/**
	 * Retrieves the actors that are targets of the currently tracked quest objectives.
	 * @return An array of actors that serve as quest objective targets.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS| Server")
	TArray<AActor*> GetCurrentlyTrackedQuestObjectivesTargetActors() const;

	//** END  **//

	//** SERVER & CLIENT GETTERS **//

	/**
	 * Checks if an objective is in progress.
	 * @param objectiveTag The Id of the objective.
	 * @return True if the objective is in progress.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	bool IsObjectiveInProgress(const FGuid& objectiveTag) const;

	/**
   * Checks if an objective is in progress.
   * @param objectiveTag The tag of the objective.
   * @return True if the objective is in progress.
   */
	UFUNCTION(BlueprintPure, Category = AQS)
	bool IsObjectiveInProgressByTag(const FGameplayTag& objectiveTag) const;
	/**
	 * Retrieves a quest from the database using its tag.
	 * @param questTag The tag of the quest.
	 * @return A pointer to the quest if found.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	class UAQSQuest* GetQuestFromDB(const FGameplayTag& questTag);

	/**
	 * Retrieves a quest from the ACTIVE QUESTS ONLY
	 * @param questTag The tag of the quest.
	 * @return A pointer to the quest if found.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	class UAQSQuest* GetQuest(const FGameplayTag& questTag) const;

	/**
	 * Retrieves a quest objective from the database.
	 * @param objectiveTag The tag of the objective to retrieve.
	 * @param questTag The tag of the quest associated with the objective.
	 * @return A pointer to the quest objective if found, otherwise nullptr.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	class UAQSQuestObjective* GetQuestObjectiveFromDB(const FGuid& objectiveId, const FGameplayTag& questTag) const;

	/**
	 * Attempts to retrieve information about an in-progress objective.
	 * @param questTag The tag of the quest containing the objective.
	 * @param objectiveTag The tag of the objective.
	 * @param outObjectiveInfo Output parameter to store the retrieved objective info.
	 * @return True if the objective info was successfully retrieved.
	*/
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool TryGetInProgressObjectiveInfo(const FGameplayTag& questTag, const FGuid& objectiveId, FAQSObjectiveInfo& outObjectiveInfo) const;

	/**
	 * Attempts to retrieve information about an in-progress quest.
	 * @param questTag The tag of the quest.
	 * @param outQuestInfo Output parameter to store the retrieved quest info.
	 * @return True if the quest info was successfully retrieved.
	*/
	UFUNCTION(BlueprintPure, Category = AQS)
	bool TryGetInProgressQuestInfo(const FGameplayTag& questTag, FAQSQuestInfo& outQuestInfo);

	/**
	 * Attempts to get the target actors associated with an in-progress objective.
	 * @param objectiveTag The tag of the objective.
	 * @param questTag The tag of the quest.
	 * @param outTargets Output array of target actors.
	 * @return True if the target actors were successfully retrieved.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	bool TryGetTargetActorsForInProgressObjective(const FGuid& objectiveId, const FGameplayTag& questTag, TArray<class AActor*>& outTargets);

	/**
	 * Checks if a quest contains an in-progress objective.
	 * @param quest The quest record to check.
	 * @param questTag The tag of the objective to look for.
	 * @return True if the objective exists within the quest.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool DoesQuestHaveInProgressObjective(const FAQSQuestRecord& quest, const FGuid& objectiveId) const
	{
		return quest.Objectives.Contains(objectiveId);
	}

	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool DoesQuestHaveInProgressObjectiveByTag(const FAQSQuestRecord& quest, const FGameplayTag& objectiveTag) const
	{
		return quest.Objectives.Contains(objectiveTag);
	}

	/**
	 * Checks if a quest is currently in progress using its tag.
	 * @param questTag The tag of the quest.
	 * @return True if the quest is in progress.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool IsQuestInProgressByTag(const FGameplayTag& questTag) const
	{
		return InProgressQuestsRecords.Contains(questTag);
	}

	/**
	 * Checks if a quest has been completed using its tag.
	 * @param questTag The tag of the quest.
	 * @return True if the quest has been completed.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool IsQuestCompletedByTag(const FGameplayTag& questTag) const
	{
		return CompletedQuestsTags.Contains(questTag);
	}

	/**
	 * Checks if a specific objective within a quest has been completed.
	 * @param questTag The tag of the quest.
	 * @param objectiveTag The tag of the objective.
	 * @return True if the objective has been completed.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	bool IsObjectiveCompletedByTag(const FGameplayTag& questTag, const FGameplayTag& objectiveTag) const;

	/**
	 * Checks if a quest has failed using its tag.
	 * @param questTag The tag of the quest.
	 * @return True if the quest has failed.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool IsQuestFailedByTag(const FGameplayTag& questTag) const
	{
		return FailedQuestsTags.Contains(questTag);
	}

	/**
	 * Retrieves all information about the in-progress quests.
	 * @param outInfo The array to store the retrieved quest information.

	UFUNCTION(BlueprintPure, Category = AQS)
	void GetInProgressQuestsInfo(TArray<FAQSQuestInfo>& outInfo) const; */

	/**
	 * Gets the Quest Succeeded node. Every quest is supposed to only have 1 succeeded node.
	 * @param the quest to check for the succeed node
	 * @return A pointer to the  UAQSQuestSuccedeedNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestSuccededNode* GetQuestSucceededNode(const FGameplayTag& questTag);

	/**
	 * Gets the Quest Failed node. Every quest is supposed to only have 1 Failed node.
	 * @param the quest to check for the failed node
	 * @return A pointer to the  UAQSQuestFailedNode, or nullptr if not found.
	 */
	UFUNCTION(BlueprintPure, Category = "AQS")
	UAQSQuestFailedNode* GetQuestFailedNode(const FGameplayTag& questTag);

	/*Returns the base info of the in progress quests*/
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE TArray<FAQSQuestRecord> GetInProgressQuestsRecords() const
	{
		return InProgressQuestsRecords.Quests;
	}

	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE TArray<FGameplayTag> GetCompletedQuestsTag() const
	{
		return CompletedQuestsTags;
	}

	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE TArray<FGameplayTag> GetFailedQuestsTag() const
	{
		return FailedQuestsTags;
	}

	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE FGameplayTag GetCurrentlyTrackedQuestTag() const
	{
		return TrackedQuestTag;
	}
	//** END  **//

	/*GET TARGETS*/
	/*Retrieves all targets with the provided tag*/
	UFUNCTION(BlueprintCallable, Category = AQS)
	TArray<class UAQSQuestTargetComponent*> GetAllTargetsWithTag(const FGameplayTag& targetTag) const;

	/*Retrieves all targets with the provided tags*/
	UFUNCTION(BlueprintCallable, Category = AQS)
	TArray<class UAQSQuestTargetComponent*> GetAllTargetsWithTags(const TArray<FGameplayTag>& targetTags) const;

	//** EVENT DISPATCHERS **//

	/** Triggered when a quest starts. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnQuestStarted OnQuestStarted;

	/** Triggered when a quest ends. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnQuestEnded OnQuestEnded;

	/** Triggered when an objective starts. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnObjectiveStarted OnObjectiveStarted;

	/** Triggered when an objective is completed. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnObjectiveCompleted OnObjectiveCompleted;

	/** Triggered when an objective is updated. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnObjectiveUpdated OnObjectiveUpdated;

	/** Triggered when an objective is interrupted. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnObjectiveInterrupted OnObjectiveInterrupted;

	/** Triggered when the currently tracked quest is updated. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnInProgressQuestsUpdate OnTrackedQuestUpdated;

	/** Triggered when in-progress quests are updated. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnInProgressQuestsUpdate OnInProgressQuestsUpdate;

	/** Triggered when completed quests are updated. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnCompletedQuestsUpdate OnCompletedQuestsUpdate;

	/** Triggered when failed quests are updated. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnFailedQuestsUpdate OnFailedQuestsUpdate;

	/** Triggered when the currently tracked quest changes. */
	UPROPERTY(BlueprintAssignable, Category = AQS)
	FOnTrackedQuestUpdate OnTrackedQuestChanged;

	void RegisterTarget(class UAQSQuestTargetComponent* targetComp);

	void UnregisterTarget(class UAQSQuestTargetComponent* targetComp);

	void DispatchObjectiveUpdate(const FGuid& objectiveId, const FGameplayTag& questTag, EQuestUpdateType updateType);
	void UpdateInProgressQuestRecords(UAQSQuest* quest);
	
	UFUNCTION(BlueprintPure, Category = AQS)
	FGameplayTag GetDefaultQuestTag() const { return DefaultQuestTag; }

	UFUNCTION(BlueprintCallable, Category = AQS)
	void SetDefaultQuestTag(FGameplayTag val) { DefaultQuestTag = val; }

	UFUNCTION(Client, Reliable, Category = AQS)
	void ClientDispatchQuestStarted(const FGameplayTag& questTag);

	UFUNCTION(Client, Reliable, Category = AQS)
	void ClientDispatchQuestCompleted(const FGameplayTag& questTag, bool bSucceded);


	//** DEBUG FUNCTIONS **//

	/**
	 * Proceeds the given quest for debugging purposes.
	 * @param inProgressQuest The tag of the quest to proceed.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void DEBUG_ProceedQuest(const FGameplayTag& inProgressQuest);

	/**
	 * Proceeds the currently tracked quest for debugging purposes.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void DEBUG_ProceedTrackedQuest();

	/**
	 * Removes an in-progress quest for debugging purposes.
	 * @param inProgressQuest The tag of the quest to remove.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void DEBUG_RemoveInProgressQuest(const FGameplayTag& inProgressQuest);

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	/*When a quest starts, if no quests are tracked, automatically
	sets the new quest as the tracked one*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	bool bAutoTrackQuest = true;

	/*The Database of quests*/
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = AQS, meta = (RequiredAssetDataTags = "RowStructure=/Script/AscentQuestSystem.AQSQuestData"))
	class UDataTable* QuestsDB;

	/*The default quest to be started */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (Categories = "Quest"), Category = AQS)
	FGameplayTag DefaultQuestTag;

	/*to be called before saving the quests*/
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = AQS)
	void OnComponentSaved();

	/*to be called after loading the quests*/
	UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category = AQS)
	void OnComponentLoaded();

private:
	bool Internal_StartQuest(UAQSQuest* questToStart, const bool bStartChildNodes, bool autoTrack = true);

	void BindQuestEvents(UAQSQuest* questToStart);

	UPROPERTY()
	TArray<TObjectPtr<UAQSQuest>> CompletedQuests;

	UPROPERTY()
	TArray<TObjectPtr<UAQSQuest>> FailedQuests;

	UPROPERTY()
	TArray<TObjectPtr<UAQSQuest>> InProgressQuests;

	UPROPERTY()
	TObjectPtr<UAQSQuest> TrackedQuest;

	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_CompletedQuestsTags)
	TArray<FGameplayTag> CompletedQuestsTags;

	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_FailedQuestsTags)
	TArray<FGameplayTag> FailedQuestsTags;

	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_InProgressQuestsRecords)
	FAQSQuestList InProgressQuestsRecords;

	UPROPERTY(SaveGame, ReplicatedUsing = OnRep_TrackedQuest)
	FGameplayTag TrackedQuestTag;

	UFUNCTION()
	void OnRep_TrackedQuest();

	UFUNCTION()
	void OnRep_InProgressQuestsRecords();

	UFUNCTION()
	void OnRep_FailedQuestsTags();

	UFUNCTION()
	void OnRep_CompletedQuestsTags();

	TMultiMap<FGameplayTag, UAQSQuestTargetComponent*> QuestTargets;

	UFUNCTION()
	void HandleQuestCompleted(const FGameplayTag& questToComplete, bool bSuccesful);

	void UnbindQuestEvents(UAQSQuest* quest);

	UFUNCTION()
	void HandleObjectiveStarted(const FGuid& objective, const FGameplayTag& quest);

	UFUNCTION()
	void HandleObjectiveCompleted(const FGuid& objective, const FGameplayTag& quest);

	UFUNCTION()
	void HandleObjectiveUpdated(const FGuid& objective, const FGameplayTag& quest);

	void SyncGraphs();

	void SynchInProgressQuest();

	void SynchFailedQuests();

	void SynchCompletedQuests();

	UPROPERTY()
	TMap<FGameplayTag, UAQSQuest*> loadedQuests;


};
