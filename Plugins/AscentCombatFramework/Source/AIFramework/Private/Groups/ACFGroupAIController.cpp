// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Groups/ACFGroupAIController.h"
#include "ACFAIController.h"
#include "Components/ACFGroupAIComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFTypes.h"
#include "Groups/ACFAIGroupSpawner.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Kismet/GameplayStatics.h"
#include <GameFramework/Actor.h>
#include <Perception/AIPerceptionComponent.h>
#include <UObject/Class.h>

void AACFGroupAIController::BeginPlay()
{
    Super::BeginPlay();

    if (PerceptionComponent) {
        PerceptionComponent->OnTargetPerceptionUpdated.AddDynamic(this, &AACFGroupAIController::HandlePerceptionUpdated);
    }
}

void AACFGroupAIController::EndPlay(EEndPlayReason::Type reason)
{
    Super::EndPlay(reason);

    if (PerceptionComponent) {
        PerceptionComponent->OnTargetPerceptionUpdated.RemoveDynamic(this, &AACFGroupAIController::HandlePerceptionUpdated);
    }
}

void AACFGroupAIController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);

    if (InPawn) {
        groupComp = InPawn->FindComponentByClass<UACFGroupAIComponent>();
    }
}

class UACFGroupAIComponent* AACFGroupAIController::GetOwningGroup_Implementation()
{
    return groupComp;
}

bool AACFGroupAIController::IsPartOfGroup_Implementation()
{
    return groupComp != nullptr;
}

AACFGroupAIController::AACFGroupAIController()
{
}

void AACFGroupAIController::HandlePerceptionUpdated(AActor* Actor, FAIStimulus Stimulus)
{
    if (!bUseGroupPerception)
        return;

    IACFEntityInterface* entity = Cast<IACFEntityInterface>(Actor);
    if (!entity) {
        return;
    }

    if (!Stimulus.IsActive()) {
        return;
    }

    if (!groupComp)
        return;

    if (!UACFFunctionLibrary::AreEnemyTeams(GetWorld(), groupComp->GetCombatTeam(),
            IACFEntityInterface::Execute_GetEntityCombatTeam(Actor))) {
        return;
    }

    TArray<FAIAgentsInfo> agents;
    groupComp->GetGroupAgents(agents);
    for (FAIAgentsInfo agent : agents) {
        if (agent.GetController() && agent.AICharacter) {
            int32 index = agent.GetController()->GetIndexInGroup();
            FAIAgentsInfo outAgent;
            if (groupComp->GetAgentByIndex(index, outAgent)) {
                agent.GetController()->HandlePerceptionUpdated(Actor, Stimulus);
            } else {
                AACFCharacter* adv = groupComp->GetAgentNearestTo(agent.AICharacter->GetActorLocation());
                agent.GetController()->HandlePerceptionUpdated(adv, Stimulus);
            }
        }
    }
}


