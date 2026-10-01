// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFMountComponent.h"
#include "ACFAIController.h"
#include "ACFRiderComponent.h"
#include "Actors/ACFCharacter.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "Components/ACFGroupAIComponent.h"
#include "GameFramework/Controller.h"

UACFMountComponent::UACFMountComponent()
{
}

// Sets default values for this component's properties
void UACFMountComponent::SetMounted(bool inMounted)
{
    bIsMounted = inMounted;
    if (GetPawnOwner() && rider) {
        if (bIsPlayerCompanion && bPossessMount) {
        } else {
            const AController* contr = GetPawnOwner()->GetController();
            if (contr) {
                UBehaviorTreeComponent* behavComp = GetPawnOwner()->GetController()->FindComponentByClass<UBehaviorTreeComponent>();
                if (behavComp) {
                    if (inMounted) {
                        behavComp->PauseLogic("Mounted");
                    } else {
                        behavComp->ResumeLogic("Mounted");
                    }
                }
            }
        }
    }
    Super::SetMounted(inMounted);
}
