// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFPlayImpactFXNotify.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "GameFramework/Character.h"
#include <Components/SkeletalMeshComponent.h>

void UACFPlayImpactFXNotify::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
    Super::Notify(MeshComp, Animation, EventReference);

    if (MeshComp) {
        ACharacter* CharacterOwner = Cast<ACharacter>(MeshComp->GetOwner());
        if (CharacterOwner) {
            UACFEffectsManagerComponent* effectsComp = CharacterOwner->FindComponentByClass<UACFEffectsManagerComponent>();
            if (effectsComp) {
                FBaseFX outFX;
                effectsComp->TryGetDamageFX(HitReaction, DamageReceivedType, outFX);
                FActionEffect outEffect = FActionEffect(outFX, SpawnLocation, SocketOrBoneLocation);
                FComponentFX compFX;
                UACFFunctionLibrary::PlayActionEffectLocally(outEffect, CharacterOwner, CharacterOwner,compFX);
            }
        }
    }
}
