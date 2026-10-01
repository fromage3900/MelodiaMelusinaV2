// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFNotifyExitAction.h"
#include <Components/SkeletalMeshComponent.h>
#include "Components/ACFAbilitySystemComponent.h"
#include <GameplayTagsManager.h>

void UACFNotifyExitAction::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
    if (MeshComp && MeshComp->GetOwner() && MeshComp->GetOwner()->HasAuthority()) {
        UACFAbilitySystemComponent* actionsManager = MeshComp->GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionsManager) {
            actionsManager->TriggerGameplayEvent(UGameplayTagsManager::Get().RequestGameplayTag(ACF::ExitTag, true));
        }
    }
}
