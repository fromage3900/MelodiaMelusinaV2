// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ATSAITargetComponent.h"
#include "ATSTargetPointComponent.h"
#include <AIController.h>
#include <Engine/TargetPoint.h>

void UATSAITargetComponent::SetCurrentTarget(class AActor* target)
{
    Super::SetCurrentTarget(target);

    AAIController* controllerOwner = Cast<AAIController>(GetOwner());
    if (target && controllerOwner) {

        UATSTargetPointComponent* pointToLookAt = target->FindComponentByClass<UATSTargetPointComponent>();

        if (pointToLookAt) {
            controllerOwner->SetFocus(pointToLookAt->GetTargetPoint(), EAIFocusPriority::Gameplay);
            SetTargetPoint(pointToLookAt);
        } else {
            controllerOwner->SetFocus(target, EAIFocusPriority::Gameplay);
        }
    } else {

        controllerOwner->ClearFocus(EAIFocusPriority::Gameplay);
    }
}
