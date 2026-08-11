// Copyright Monolith. All Rights Reserved.
//
// Generic AIController that auto-starts an assigned BehaviorTree in OnPossess().

#include "Controllers/MonolithBehaviorTreeAIController.h"
#include "MonolithAIInternal.h"

#include "BehaviorTree/BehaviorTree.h"

void AMonolithBehaviorTreeAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	if (BehaviorTreeToRun)
	{
		StartBehaviorTree();
	}
}

bool AMonolithBehaviorTreeAIController::StartBehaviorTree()
{
	if (!BehaviorTreeToRun)
	{
		UE_LOG(LogMonolithAI, Verbose,
			TEXT("MonolithBehaviorTreeAIController[%s]: no BehaviorTreeToRun assigned"),
			*GetName());
		return false;
	}

	const bool bStarted = RunBehaviorTree(BehaviorTreeToRun);
	if (!bStarted)
	{
		UE_LOG(LogMonolithAI, Warning,
			TEXT("MonolithBehaviorTreeAIController[%s]: RunBehaviorTree failed for %s"),
			*GetName(), *BehaviorTreeToRun->GetName());
	}

	return bStarted;
}
