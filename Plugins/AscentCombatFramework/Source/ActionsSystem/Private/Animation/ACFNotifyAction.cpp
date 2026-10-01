// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFNotifyAction.h"
#include "Components/ACFAbilitySystemComponent.h"
#include <Components/SkeletalMeshComponent.h>
#include <Kismet/KismetSystemLibrary.h>
#include <GameplayTagsManager.h>

void UACFNotifyAction::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
    if (MeshComp && MeshComp->GetOwner()) {

        UACFAbilitySystemComponent* amc = MeshComp->GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (amc) {
            amc->TriggerGameplayEvent(UGameplayTagsManager::Get().RequestGameplayTag(ACF::NotableTag, true));
        }
    }
}
