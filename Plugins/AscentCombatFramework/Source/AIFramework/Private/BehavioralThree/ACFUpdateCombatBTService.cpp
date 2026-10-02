// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "BehavioralThree/ACFUpdateCombatBTService.h"
#include "ACFAIController.h"
#include "Components/ACFCombatBehaviourComponent.h"
#include "Components/ACFThreatManagerComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Interfaces/ACFEntityInterface.h"
#include <AI/NavigationSystemBase.h>
#include <BehaviorTree/BehaviorTreeComponent.h>
#include <BehaviorTree/Blackboard/BlackboardKeyType_Float.h>
#include <BehaviorTree/Blackboard/BlackboardKeyType_Object.h>
#include <BehaviorTree/BlackboardComponent.h>
#include <GameFramework/Actor.h>
#include <Navigation/PathFollowingComponent.h>
#include <NavigationSystem.h>
#include <Logging.h>

void UACFUpdateCombatBTService::TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
    EvaluateAndUpdateCombat(OwnerComp);
    Super::TickNode(OwnerComp, NodeMemory, DeltaSeconds);
}

void UACFUpdateCombatBTService::OnSearchStart(FBehaviorTreeSearchData& SearchData)
{
    EvaluateAndUpdateCombat(SearchData.OwnerComp);

    Super::OnSearchStart(SearchData);
}

void UACFUpdateCombatBTService::EvaluateAndUpdateCombat(UBehaviorTreeComponent& OwnerComp)
{
    const UBlackboardComponent* bbc = OwnerComp.GetBlackboardComponent();

    aiController = Cast<AACFAIController>(OwnerComp.GetAIOwner());

    if (!aiController) {
        UE_LOG(ACFAILog, Warning, TEXT("UACFUpdateCombatBTService get controller failed"));
        return;
    }

    targetActor = aiController->GetTargetActorBK();
    IACFEntityInterface* entity = Cast<IACFEntityInterface>(targetActor.Get());


    if (!entity || !targetActor || !IACFEntityInterface::Execute_IsEntityAlive(targetActor)) {
        if (!aiController->RequestAnotherTarget()) {
            aiController->SetTarget(nullptr);
        }
        return;
    }

    CharOwner = Cast<AACFCharacter>(aiController->GetPawn());

    if (!CharOwner) {
        UE_LOG(ACFAILog, Error, TEXT("GetPawn() is NULL - UACFUpdateCombatBTService"));
        return;
    }

    if (targetActor->GetDistanceTo(CharOwner) > aiController->GetLoseTargetDistance()) {
        if (!aiController->RequestAnotherTarget()) {
            aiController->SetTarget(nullptr);
        }
        return;
    }
    UpdateCombat();
}

void UACFUpdateCombatBTService::UpdateCombat()
{
    float distanceToTarget;
    ACharacter* targetChar = Cast<ACharacter>(targetActor);
    if (targetChar) {
        distanceToTarget = UACFFunctionLibrary::CalculateDistanceBetweenCharactersExtents(CharOwner, targetChar);
    } else {
        distanceToTarget = CharOwner->GetDistanceTo(targetActor);
    }

    aiController->SetTargetActorDistanceBK(distanceToTarget);

    if (distanceToTarget > aiController->GetLoseTargetDistance()) {
        aiController->SetTarget(nullptr);
    }

    combatBehav = aiController->GetCombatBehavior();

    if (combatBehav) {
        EAICombatState combatState = combatBehav->GetBestCombatStateByTargetDistance(distanceToTarget); // aiController->GetCombatStateBK();

        if (combatState != aiController->GetCombatStateBK()) {
            aiController->SetCombatStateBK(combatState);

        }
         aiController->UpdateCombatLocomotion();
    }
}
