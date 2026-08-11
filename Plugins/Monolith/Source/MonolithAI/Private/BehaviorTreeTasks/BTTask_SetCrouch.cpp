// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: crouch / uncrouch the possessed ACharacter pawn.

#include "BehaviorTreeTasks/BTTask_SetCrouch.h"
#include "MonolithAIInternal.h"

#include "BehaviorTree/BehaviorTreeComponent.h"
#include "AIController.h"
#include "GameFramework/Character.h"

UBTTask_SetCrouch::UBTTask_SetCrouch(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	NodeName = TEXT("Set Crouch");
	bCrouch = true;
}

EBTNodeResult::Type UBTTask_SetCrouch::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* /*NodeMemory*/)
{
	const AAIController* AIOwner = OwnerComp.GetAIOwner();
	if (!AIOwner)
	{
		return EBTNodeResult::Failed;
	}

	ACharacter* Character = Cast<ACharacter>(AIOwner->GetPawn());
	if (!Character)
	{
		UE_LOG(LogMonolithAI, Verbose,
			TEXT("BTTask_SetCrouch[%s]: AI pawn is not an ACharacter"),
			*GetNodeName());
		return EBTNodeResult::Failed;
	}

	if (bCrouch)
	{
		Character->Crouch();
	}
	else
	{
		Character->UnCrouch();
	}

	return EBTNodeResult::Succeeded;
}

FString UBTTask_SetCrouch::GetStaticDescription() const
{
	return FString::Printf(TEXT("%s\n%s"),
		*Super::GetStaticDescription(),
		bCrouch ? TEXT("Crouch") : TEXT("UnCrouch"));
}
