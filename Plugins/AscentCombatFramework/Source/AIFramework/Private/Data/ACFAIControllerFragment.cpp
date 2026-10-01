// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFAIControllerFragment.h"
#include "ACFAIController.h"
#include "BehaviorTree/BehaviorTree.h"
#include "GameFramework/Pawn.h"

void UACFAIControllerFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
    if (!pawnOwner)
    {
        return;
    }

    // AI controllers exist only on the server; clients hold a null controller reference
    // for AI-driven pawns.  Guard here so we never attempt to configure a non-existent
    // controller on a client machine and to make the intent clear at a glance.
    if (!pawnOwner->HasAuthority())
    {
        return;
    }

    AACFAIController* AICont = Cast<AACFAIController>(pawnOwner->GetController());
    if (!AICont)
    {
        return;
    }

    if (bOverrideBehaviorTree && BehaviorTree)
    {
        AICont->SetBehaviorTree(BehaviorTree);
    }

    if (bOverrideDefaultState && DefaultState.IsValid())
    {
        AICont->SetDefaultState(DefaultState);
    }

    if (bOverrideLocomotionStates)
    {
        AICont->SetLocomotionStateByAIState(LocomotionStateByAIState);
    }

    if (bOverrideHomeSettings)
    {
        AICont->SetReturnHomeCheckEnabled(bBoundToHome);
        AICont->SetMaxDistanceFromHome(MaxDistanceFromHome);
    }

    if (bOverrideTeleportSettings)
    {
        AICont->SetTeleportToLead(bTeleportToLead);
        AICont->SetTeleportTriggerDistance(TeleportToLeadTriggerDistance);
        AICont->SetTeleportNearLeadRadius(TeleportNearLeadRadius);
    }

    if (bOverrideCombatSettings)
    {
        AICont->SetLoseTargetDistance(LoseTargetDistance);
        AICont->SetIsAggressive(bIsAggressive);
        AICont->SetShouldReactOnHit(bShouldReactOnHit);
    }
}
