// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Graph/AQSObjectiveNode.h"

#include "AQSQuestObjective.generated.h"

class UAQSQuestManagerComponent;
class APlayerController;

UENUM(BlueprintType)
enum class ETargetReferenceType : uint8 {
	ESoftRef UMETA(DisplayName = "Soft Reference"),
	ETag UMETA(DisplayName = "Gameplay Tag"),
};

/**
 * Base class representing a quest objective in the Ascent Quest System.
 * Provides accessors for objective data, including targets, tags, descriptions,
 * completion state and repetitions. Acts as a bridge between Blueprint logic and
 * the underlying node owner.
 */
UCLASS(Blueprintable, BlueprintType, EditInlineNew)
class ASCENTQUESTSYSTEM_API UAQSQuestObjective : public UObject {
	GENERATED_BODY()

public:


	UAQSQuestObjective();

	/**
	 * Returns the list of the actors referenced by this objective as set in the graph node.
	 *
	 * @return Array of AActor pointers representing the objective targets.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	TArray<class AActor*> GetObjectiveTargetsActors() const;

	/**
	 * Returns the list of target components referenced by this objective as set in the graph node.
	 *
	 * @return Array of UAQSQuestTargetComponent pointers representing the quest targets.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE TArray<class UAQSQuestTargetComponent*> GetObjectiveTargets() const
	{
		return questTargets;
	}

	/**
	 * Returns the type of reference used by this objective to identify its targets.
	 *
	 * @return The reference type of the objective targets.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE ETargetReferenceType GetTargetRefType() const
	{
		return TargetRefType;
	}

	/**
	 * Returns the gameplay tag associated with this objective as set in the graph node.
	 *
	 * @return GameplayTag identifying the objective.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE FGameplayTag GetObjectiveTag() const
	{
		return ObjectiveTag;
	}

	/**
	 * Returns the unique identifier of this objective from its owning node.
	 *
	 * @return FGuid representing the node ID of the objective owner.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE FGuid GetObjectiveId() const
	{
		return nodeOwner->GetNodeId();
	}

	/**
	 * Returns the display name of this objective as set in the graph node.
	 *
	 * @return Localized text representing the objective name.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE FText GetObjectiveName() const
	{
		return ObjectiveName;
	}

	/**
	 * Returns the description of this objective as set in the graph node.
	 *
	 * @return Localized text describing the objective.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE FText GetDescription() const
	{
		return ObjectiveDescription;
	}

	/**
	 * Retrieves the local player controller associated with this objective.
	 *
	 * @return APlayerController pointer if valid, nullptr otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	APlayerController* GetLocalPlayerController() const;


	/**
	 * Returns the world context object associated with this objective.
	 *
	 * @return UWorld pointer of the current world context.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE class UWorld* GetWorldContextObject() const
	{
		return GetWorld();
	}

	/**
	 * Returns the current number of repetitions completed for this objective.
	 *
	 * @return Integer count of completed repetitions.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE int32 GetCurrentRepetitions() const
	{
		return nodeOwner->GetCurrentRepetitions();
	}

	/**
	 * Returns the total number of repetitions required to complete this objective.
	 *
	 * @return Integer count of required repetitions.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE int32 GetRepetitions() const
	{
		return nodeOwner->GetQuestRepetitions();
	}

	/**
	 * Checks whether this objective has been completed.
	 *
	 * @return True if completed, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool IsObjectiveCompleted() const
	{
		return nodeOwner->IsObjectiveCompleted();
	}

	/**
	 * Checks whether this objective is currently tracked by the quest system.
	 *
	 * @return True if tracked, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	FORCEINLINE bool IsTracked() const
	{
		return nodeOwner->IsTracked();
	}

	/**
	 * Marks this objective as completed and notifies the quest system.
	 */
	UFUNCTION(BlueprintCallable, Category = AQS)
	void CompleteObjective();

	/**
	 * Returns the owning node of this objective.
	 *
	 * @return UAQSObjectiveNode pointer to the owner node of this objective.
	 */
	UFUNCTION(BlueprintPure, Category = AQS)
	UAQSObjectiveNode* GetNodeOwner() const { return nodeOwner; }

	friend class UAQSObjectiveNode;

	TArray<TSoftObjectPtr<AActor>> GetObjectiveTargetsSoftRef() const;

private:
	void Internal_OnObjectiveStarted(class UAQSObjectiveNode* inNodeOwner);

	void Internal_OnObjectiveEnded(bool bInterrupted);

	void FillTargetsRef();
	UPROPERTY()
	UAQSObjectiveNode* nodeOwner;

	UPROPERTY()
	TArray<class UAQSQuestTargetComponent*> questTargets;

protected:


	/*A description for this objective, can be used for UI*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	FText ObjectiveName;

	/*A description for this objective, can be used for UI*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	FText ObjectiveDescription;

	/*Unique Tag to identify this objective*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	FGameplayTag ObjectiveTag;

	/*Define how you want to identify the targets of this objectives
	if you want tor efer directly hem thorught soft references or thorught
	their GameplayTags*/
	UPROPERTY(EditDefaultsOnly, Category = AQS)
	ETargetReferenceType TargetRefType;

	/*A list of targets that, if they have a QuestTargetComponent, will be
	updated with this objective progresses. All targets with that tag in the component
	will be alerted*/
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "TargetRefType == ETargetReferenceType::ETag"), Category = AQS)
	TArray<FGameplayTag> ReferencedTargets;

	/*A list of targets that, if they have a QuestTargetComponent, will be
	updated with this objective progresses. The provided actors need to have
	a QuestTargetComponent to work*/
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "TargetRefType == ETargetReferenceType::ESoftRef"), Category = AQS)
	TArray<TSoftObjectPtr<AActor>> ReferencedActors;

	/*Forces the load of the assets if they are not loaded (es for world partition)*/
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "TargetRefType == ETargetReferenceType::ESoftRef"), Category = AQS)
	bool bForceLoadReferencedActors = true;

	/*Called when this objective is started*/
	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void OnObjectiveStarted();
	virtual void OnObjectiveStarted_Implementation();

	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void ClientOnObjectiveStarted();
	virtual void ClientOnObjectiveStarted_Implementation();

	/*Called when this objective is completed*/
	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void OnObjectiveCompleted();
	virtual void OnObjectiveCompleted_Implementation();

	/*Called when this objective is completed*/
	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void ClientOnObjectiveCompleted();
	virtual void ClientOnObjectiveCompleted_Implementation();

	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void OnObjectiveUpdated();
	virtual void OnObjectiveUpdated_Implementation();

	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void OnObjectiveInterrupted();
	virtual void OnObjectiveInterrupted_Implementation();

	UFUNCTION(BlueprintNativeEvent, Category = AQS)
	void ClientOnObjectiveInterrupted();
	virtual void ClientOnObjectiveInterrupted_Implementation();

	UFUNCTION(BlueprintCallable, Category = AQS)
	void SetCurrentRepetitions(int32 currentRep);

	UFUNCTION(BlueprintPure, Category = AQS)
	UAQSQuestManagerComponent* GetLocalQuestManager() const;


	// UObject interface
	UWorld* GetWorld() const override { return GetLocalPlayerController() ? GetLocalPlayerController()->GetWorld() : nullptr; }
	// End of UObject interface
};
