// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFNotifyFX.h"
#include "Components/ACFAbilitySystemComponent.h"
#include <Animation/AnimSequenceBase.h>
#include <Components/SkeletalMeshComponent.h>
#include <GameplayTagsManager.h>

void UACFNotifyFX::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
    if (MeshComp && MeshComp->GetOwner()) {
        UACFAbilitySystemComponent* amc = MeshComp->GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (amc) {
            amc->TriggerGameplayEvent(UGameplayTagsManager::Get().RequestGameplayTag(ACF::FXTag, true));
        }
    }
}
