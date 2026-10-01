// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AQSQuestFunctionLibrary.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Graph/AQSObjectiveNode.h"
#include <GameplayTagContainer.h>

#include "AQSQuestTargetComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTrackedStatusChanged, bool, bTracked);

UCLASS(ClassGroup = (ATS), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTQUESTSYSTEM_API UAQSQuestTargetComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UAQSQuestTargetComponent();

    /** Called every time one of the referencing objectives is updated */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnObjectiveUpdated OnReferencingObjectiveUpdated;

    /** Called every time one of the referencing objectives is started */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnObjectiveStarted OnReferencingObjectiveStarted;

    /** Called every time one of the referencing objectives is completed */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnObjectiveCompleted OnReferencingObjectiveCompleted;

    /** Called every time one of the referencing objectives is interrupted */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnObjectiveCompleted OnReferencingObjectiveInterrupted;

    /** Called when the tracked status changes */
    UPROPERTY(BlueprintAssignable, Category = AQS)
    FOnTrackedStatusChanged OnTrackedStatusChanged;

    /**
     *  Completes the objective with the provided tag for all in-progress quests.
     *
     * @param objectiveToComplete The tag of the objective to complete.
     */
    UFUNCTION(BlueprintCallable, Category = AQS)
    void CompleteObjective(const FGuid& objectiveToComplete);


    /**
     *  Completes the objective with the provided tag, unlocking only the transitions
     * specified by the given names.
     *
     * @param objectiveToComplete The tag of the objective to complete.
     * @param transitionFilters The list of transition names to unlock.
     */
    UFUNCTION(BlueprintCallable, Category = AQS)
    void CompleteBranchedObjective(const FGuid& objectiveToComplete, const TArray<FName>& transitionFilters);

    /**
     *  Retrieves the target tag of this component.
     *
     * @return The target tag.
     */
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE FGameplayTag GetTargetTag() const
    {
        return TargetTag;
    }

    /**
     *  Checks if this component is tracking a target.
     *
     * @return True if the target is tracked, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE bool IsTrackedTarget() const
    {
        return bTracked;
    }

    /**
     *  Checks if this component is currently the target of an objective.
     *
     * @return True if it is currently targeted, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE bool IsCurrentlyTargetOfObjective() const
    {
        return bIsCurrentlyTargetOfObjective;
    }

    /**
     *  Retrieves the referencing objective tag currently targeting this component.
     *
     * @return The referencing objective tag.
     */
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE FGuid  GetReferencingObjective() const
    {
        return currentlyTargetingObjective;
    }

    /**
     *  Retrieves the referencing quest tag currently targeting this component.
     *
     * @return The referencing quest tag.
     */
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE FGameplayTag GetReferencingQuest() const
    {
        return currentlyTargetingQuest;
    }

    /**
     *  Called when an objective is started.
     *
     * @param objectiveId The tag of the started objective.
     * @param questTag The tag of the quest the objective belongs to.
     */
    UFUNCTION(BlueprintNativeEvent, Category = AQS)
    void OnObjectiveStarted(const FGuid& objectiveId, const FGameplayTag& questTag);

    /**
     *  Called when an objective is completed.
     *
     * @param objectiveId The tag of the completed objective.
     * @param questTag The tag of the quest the objective belongs to.
     */
    UFUNCTION(BlueprintNativeEvent, Category = AQS)
    void OnObjectiveCompleted(const FGuid& objectiveId, const FGameplayTag& questTag);

    /**
     *  Called when an objective is updated.
     *
     * @param objectiveId The tag of the updated objective.
     * @param questTag The tag of the quest the objective belongs to.
     */
    UFUNCTION(BlueprintNativeEvent, Category = AQS)
    void OnObjectiveUpdated(const FGuid& objectiveId, const FGameplayTag& questTag);

    /**
     *  Called when an objective is interrupted.
     *
     * @param objectiveId The tag of the interrupted objective.
     * @param questTag The tag of the quest the objective belongs to.
     */
    UFUNCTION(BlueprintNativeEvent, Category = AQS)
    void OnObjectiveInterrupted(const FGuid& objectiveId, const FGameplayTag& questTag);

    /**
     *  Called when the tracked status of the objective changes.
     *
     * @param bNewTracked The new tracking status.
     */
    UFUNCTION(BlueprintNativeEvent, Category = AQS)
    void OnTrackedChanged(bool bNewTracked);

    /**
     *  Dispatches an objective update.
     *
     * @param objectiveId The tag of the updated objective.
     * @param questTag The tag of the quest the objective belongs to.
     * @param objectiveUpdate The type of update.
     * @param inTracked The tracking status of the objective.
     */
    void DispatchObjectiveUpdated(const FGuid& objectiveId, const FGameplayTag& questTag, EQuestUpdateType objectiveUpdate, bool inTracked);

    /**
     *  Dispatches an objective update to the client.
     *
     * @param objectiveId The tag of the updated objective.
     * @param questTag The tag of the quest the objective belongs to.
     * @param objectiveUpdate The type of update.
     * @param inTracked The tracking status of the objective.
     */
    void ClientDispatchObjectiveUpdated(const FGuid& objectiveId, const FGameplayTag& questTag, EQuestUpdateType objectiveUpdate, bool inTracked);

    /**
     *  Sets the tracked status of the objective.
     *
     * @param inTracked The new tracking status.
     */
    void SetTracked(bool inTracked);

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /*Tag of this target. Used to call the events once a referencing objective is updated*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = AQS)
    FGameplayTag TargetTag;

private:
    UPROPERTY(SaveGame, Replicated)
    bool bIsCurrentlyTargetOfObjective = false;

    UPROPERTY(SaveGame, Replicated)
    FGuid currentlyTargetingObjective;

    UPROPERTY(SaveGame, Replicated)
    FGameplayTag currentlyTargetingQuest;

    bool bTracked;
};
