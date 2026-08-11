// Copyright Monolith. All Rights Reserved.
//
// Reusable BT task: set the possessed pawn's MaxWalkSpeed (literal or Blackboard float).

#include "BehaviorTreeTasks/BTTask_SetMaxWalkSpeed.h"
#include "MonolithAIInternal.h"

#include "BehaviorTree/BehaviorTreeComponent.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "AIController.h"
#include "GameFramework/Character.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/CharacterMovementComponent.h"

UBTTask_SetMaxWalkSpeed::UBTTask_SetMaxWalkSpeed(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	NodeName = TEXT("Set Max Walk Speed");
	Speed = 200.0f;

	// Optional key: None is a valid "use the literal instead" state.
	SpeedKey.AllowNoneAsValue(true);
}

void UBTTask_SetMaxWalkSpeed::InitializeFromAsset(UBehaviorTree& Asset)
{
	Super::InitializeFromAsset(Asset);

	if (const UBlackboardData* BBAsset = GetBlackboardAsset())
	{
		SpeedKey.ResolveSelectedKey(*BBAsset);
	}
	else
	{
		SpeedKey.InvalidateResolvedKey();
	}
}

EBTNodeResult::Type UBTTask_SetMaxWalkSpeed::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* /*NodeMemory*/)
{
	const AAIController* AIOwner = OwnerComp.GetAIOwner();
	if (!AIOwner)
	{
		return EBTNodeResult::Failed;
	}

	APawn* Pawn = AIOwner->GetPawn();
	const ACharacter* Character = Cast<ACharacter>(Pawn);
	UCharacterMovementComponent* MoveComp =
		Character ? Character->GetCharacterMovement() : (Pawn ? Pawn->FindComponentByClass<UCharacterMovementComponent>() : nullptr);

	if (!MoveComp)
	{
		UE_LOG(LogMonolithAI, Verbose,
			TEXT("BTTask_SetMaxWalkSpeed[%s]: AI pawn has no CharacterMovementComponent"),
			*GetNodeName());
		return EBTNodeResult::Failed;
	}

	// Blackboard key wins when configured; otherwise use the literal.
	float NewSpeed = Speed;
	if (SpeedKey.IsSet())
	{
		if (const UBlackboardComponent* BB = OwnerComp.GetBlackboardComponent())
		{
			NewSpeed = BB->GetValueAsFloat(SpeedKey.SelectedKeyName);
		}
	}

	MoveComp->MaxWalkSpeed = NewSpeed;
	return EBTNodeResult::Succeeded;
}

FString UBTTask_SetMaxWalkSpeed::GetStaticDescription() const
{
	const FString Source = SpeedKey.IsSet()
		? FString::Printf(TEXT("BB key '%s'"), *SpeedKey.SelectedKeyName.ToString())
		: FString::Printf(TEXT("%.1f cm/s"), Speed);

	return FString::Printf(TEXT("%s\nSpeed: %s"), *Super::GetStaticDescription(), *Source);
}
