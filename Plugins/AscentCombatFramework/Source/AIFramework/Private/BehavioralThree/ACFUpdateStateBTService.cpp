// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "BehavioralThree/ACFUpdateStateBTService.h"
#include "ACFAIController.h"
#include "Components/ACFCommandsManagerComponent.h"
#include <BehaviorTree/BehaviorTreeComponent.h>
#include "Game/ACFFunctionLibrary.h"
#include <Logging.h>
#include <GameplayTagsManager.h>

void UACFUpdateStateBTService::TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{

    aiController = Cast<AACFAIController>(OwnerComp.GetAIOwner());
    if (aiController == nullptr) {
        UE_LOG(ACFAILog, Warning, TEXT("UACFUpdateCombatBTService get controller failed"));
        return;
    }

    CharOwner = aiController->GetPawn();
    if (CharOwner == nullptr) {
        UE_LOG(ACFAILog, Error, TEXT("GetPawn() is NULL - UACFUpdateCombatBTService"));
        aiController->Destroy();
        return;
    }

    if (aiController->IsPartOfGroup()) {
        UACFGroupAIComponent* group = aiController->GetGroup();
        const AActor* lead = aiController->GetLeadActorBK();
        if (lead) {
            const float distanceFromLeader = (CharOwner->GetActorLocation() - lead->GetActorLocation()).Size();
            aiController->SetLeadActorDistanceBK(distanceFromLeader);

            if (aiController->ShouldTeleportNearLead() && distanceFromLeader >= aiController->GetTeleportLeadDistanceTrigger()) {
                aiController->TeleportNearLead();
                aiController->SetTarget(nullptr);
                return;
            } else if (distanceFromLeader > aiController->GetMaxDistanceFromHome() && 
                aiController->GetDefaultAIState() == UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIFollowLead)) {
                aiController->SetCurrentAIState(UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIFollowLead));
                return;
            }
        } else {
            aiController->TryUpdateLeadRef();
        }
    } else {
        if (aiController->ShouldReturnHome() && aiController->GetAIState() !=  UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIReturnHome)) {
            const float distanceFromHome = (CharOwner->GetActorLocation() - aiController->GetHomeLocation()).Size();
            aiController->SetHomeDistanceBK(distanceFromHome);
            if (distanceFromHome > aiController->GetMaxDistanceFromHome()) {
                aiController->SetTarget(nullptr);
                aiController->SetCurrentAIState(UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIReturnHome));
                return;
            }
        }
    }
}
