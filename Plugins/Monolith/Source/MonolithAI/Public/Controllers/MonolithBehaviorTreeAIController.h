// Copyright Monolith. All Rights Reserved.
//
// Generic, project-agnostic AIController that auto-starts an assigned
// BehaviorTree the instant possession completes.
//
// Why this exists: a Blueprint Character/AIController BeginPlay fires BEFORE
// possession finishes, so a RunBehaviorTree call there finds no pawn and the
// tree never starts. The correct, reliable hook for autonomous BT startup is
// AAIController::OnPossess. Subclass this controller in Blueprint, assign the
// BehaviorTreeToRun, and set it as a pawn's AIControllerClass; the tree starts
// for any AI pawn with zero glue code.

#pragma once

#include "CoreMinimal.h"
#include "AIController.h"

#include "MonolithBehaviorTreeAIController.generated.h"

class UBehaviorTree;

/**
 * AIController that runs BehaviorTreeToRun automatically in OnPossess().
 *
 * Subclass this in Blueprint, set BehaviorTreeToRun, then assign the BP as a
 * pawn's AIControllerClass. The behavior tree starts the moment the controller
 * possesses the pawn -- the one hook that is guaranteed to have a valid pawn,
 * unlike BeginPlay. Use StartBehaviorTree() to (re)start it manually at runtime.
 */
UCLASS(Blueprintable, meta = (DisplayName = "Monolith Behavior Tree AI Controller"))
class MONOLITHAI_API AMonolithBehaviorTreeAIController : public AAIController
{
	GENERATED_BODY()

public:

	/** Behavior tree started automatically when this controller possesses a pawn. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
	TObjectPtr<UBehaviorTree> BehaviorTreeToRun;

	//~ Begin AAIController interface
	virtual void OnPossess(APawn* InPawn) override;
	//~ End AAIController interface

	/**
	 * Runs BehaviorTreeToRun on this controller's currently possessed pawn.
	 * Safe to call at runtime to (re)start the tree. Returns true if the tree
	 * was started.
	 */
	UFUNCTION(BlueprintCallable, Category = "AI")
	bool StartBehaviorTree();
};
