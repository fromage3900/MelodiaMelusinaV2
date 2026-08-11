// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: write a random float in [Min, Max] to a Blackboard float key.

#include "BehaviorTreeTasks/BTTask_RandomizeFloat.h"
#include "MonolithAIInternal.h"

#include "BehaviorTree/BehaviorTreeComponent.h"
#include "BehaviorTree/BlackboardComponent.h"

UBTTask_RandomizeFloat::UBTTask_RandomizeFloat(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	NodeName = TEXT("Randomize Float");
	Min = 0.0f;
	Max = 1.0f;

	// Restrict the inherited key picker to float keys.
	BlackboardKey.AddFloatFilter(this, GET_MEMBER_NAME_CHECKED(UBTTask_RandomizeFloat, BlackboardKey));
}

void UBTTask_RandomizeFloat::InitializeFromAsset(UBehaviorTree& Asset)
{
	// Base resolves BlackboardKey against the tree's blackboard asset.
	Super::InitializeFromAsset(Asset);
}

EBTNodeResult::Type UBTTask_RandomizeFloat::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* /*NodeMemory*/)
{
	UBlackboardComponent* BB = OwnerComp.GetBlackboardComponent();
	if (!BB || !BlackboardKey.IsSet())
	{
		UE_LOG(LogMonolithAI, Verbose,
			TEXT("BTTask_RandomizeFloat[%s]: no Blackboard component or unset key"),
			*GetNodeName());
		return EBTNodeResult::Failed;
	}

	const float RandomValue = FMath::FRandRange(Min, Max);
	BB->SetValueAsFloat(BlackboardKey.SelectedKeyName, RandomValue);
	return EBTNodeResult::Succeeded;
}

FString UBTTask_RandomizeFloat::GetStaticDescription() const
{
	return FString::Printf(TEXT("%s\n[%.2f, %.2f] -> %s"),
		*Super::GetStaticDescription(),
		Min, Max,
		*BlackboardKey.SelectedKeyName.ToString());
}
