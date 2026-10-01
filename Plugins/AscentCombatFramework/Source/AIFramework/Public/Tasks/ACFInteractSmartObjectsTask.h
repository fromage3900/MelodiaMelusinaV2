// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2025.
// All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFTask.h"
#include "GameplayTagContainer.h"
#include "SmartObjectRuntime.h"
#include "SmartObjectTypes.h"
#include "ACFInteractSmartObjectsTask.generated.h"

class UContextualAnimSceneAsset;
class USmartObjectBehaviorDefinition;
struct FSmartObjectClaimHandle;

/**
 * Task that searches for a suitable Smart Object around the controlled pawn
 * and triggers the interaction (e.g., via Gameplay Behaviors / Contextual Anim).
 *
 * Filters exposed to designers:
 * - UserTags: tags describing the user requesting a slot (used by SmartObject filtering).
 * - ClaimPriority: priority used when claiming a slot (can include already-claimed slots at lower priority).
 * - ActivityRequirements: tag query that must match the SmartObject activity.
 * - QueryBoxDimension: half-extents of the AABB (in cm) used for the spatial search around the pawn.
 * - BehaviorDefinitionClasses: restrict results to SmartObjects using specific Behavior Definitions.
 */
UCLASS(BlueprintType, Blueprintable)
class AIFRAMEWORK_API UACFInteractSmartObjectsTask : public UACFTask
{
	GENERATED_BODY()

public:
	/** Gameplay tags describing the user/actor that is requesting a Smart Object slot. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Routine|SmartObject")
	FGameplayTagContainer UserTags;

	/** Claim priority used by the user; search may include lower-priority already-claimed slots. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Routine|SmartObject")
	ESmartObjectClaimPriority ClaimPriority = ESmartObjectClaimPriority::Normal;

	/** Only return slots whose activity tags satisfy this query. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Routine|SmartObject")
	FGameplayTagQuery ActivityRequirements;

	UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="Routine|SmartObject")
	UContextualAnimSceneAsset* EnterLoopContextualAnimSceneAsset;

	UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="Routine|SmartObject")
	UContextualAnimSceneAsset* ExitContextualAnimSceneAsset;
	
	/** Half-extents (X/Y/Z in cm) of the search box centered on the pawn location. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Routine|SmartObject", meta=(ClampMin="0.0", UIMin="0.0"))
	FVector QueryBoxDimension = FVector(2000.f, 2000.f, 2000.f);

	/** Optional restriction: only SmartObjects whose Behavior Definition is one of these classes will be returned. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Routine|SmartObject")
	TArray<TSubclassOf<USmartObjectBehaviorDefinition>> BehaviorDefinitionClasses;

	/** Called by the routine service when this task starts. */
	virtual void OnTaskStarted_Implementation(const APawn* ControlledPawn) override;

	/** Called when this task is ended/stopped by the routine. */
	virtual void OnTaskEnded_Implementation() override;
protected:
	
	UPROPERTY(Transient)
	FSmartObjectClaimHandle TaskClaimHandle = FSmartObjectClaimHandle();

	// Keep the AI task and the claim here (not in the routine component)
	UPROPERTY(Transient)
	TObjectPtr<class UAITask_UseGameplayBehaviorSmartObject> ActiveSOAITask = nullptr;
	
private:
	/**
	 * Perform the Smart Object search using the configured filters and area around the pawn.
	 * @param ControlledPawn The pawn that is requesting/using the Smart Object.
	 */
	void FindSmartObject(const APawn* ControlledPawn);

	/**
	 * Move to and use the claimed Smart Object slot (e.g., via Gameplay Behavior or Contextual Anim).
	 * @param ControlledPawn The pawn that will interact.
	 * @param ClaimHandle The valid claim handle for the selected slot.
	 */
	void InteractSmartObject(const APawn* ControlledPawn,FSmartObjectClaimHandle& ClaimHandle);

	UFUNCTION()
	void OnSOAITaskFinished();
};
