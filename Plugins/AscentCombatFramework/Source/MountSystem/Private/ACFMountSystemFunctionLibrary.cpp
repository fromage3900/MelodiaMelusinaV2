// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFMountSystemFunctionLibrary.h"
#include "ACFMountableComponent.h"
#include "Components/ACFInteractionComponent.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Actors/ACFCharacter.h"

class AACFCharacter* UACFMountSystemFunctionLibrary::GetLocalRiderPlayerCharacter(const UObject* WorldContextObject)
{
    APawn* charOwner = UGameplayStatics::GetPlayerPawn(WorldContextObject, 0);

    if (charOwner) {
        const UACFMountableComponent* mountComp = charOwner->FindComponentByClass<UACFMountableComponent>();
        if (mountComp) {
            if (mountComp->IsMounted() && mountComp->NeedsPossession()) {
                return Cast<AACFCharacter>(mountComp->GetRider());
            }
        } 
        return Cast<AACFCharacter>(charOwner);     
    }
    return nullptr;
}

class AActor* UACFMountSystemFunctionLibrary::GetLocalBestInteractable(const UObject* WorldContextObject)
{
    const AACFCharacter* LocalRiderPlayer = GetLocalRiderPlayerCharacter(WorldContextObject);
    if (!LocalRiderPlayer)
    {
        return nullptr;
    }

    const UACFInteractionComponent* InteractionComponent = LocalRiderPlayer->FindComponentByClass<UACFInteractionComponent>();
    return InteractionComponent ? InteractionComponent->GetCurrentBestInteractableActor() : nullptr;
}

class AActor* UACFMountSystemFunctionLibrary::GetLocalCurrentInteractingActor(const UObject* WorldContextObject)
{
    const AACFCharacter* LocalRiderPlayer = GetLocalRiderPlayerCharacter(WorldContextObject);
    if (!LocalRiderPlayer)
    {
        return nullptr;
    }

    const UACFInteractionComponent* InteractionComponent = LocalRiderPlayer->FindComponentByClass<UACFInteractionComponent>();
    return InteractionComponent ? InteractionComponent->GetCurrentInteractingActor() : nullptr;
}


bool UACFMountSystemFunctionLibrary::DoesDamageInvolveLocalPlayer(const FACFDamageEvent& damageEvent, bool& bIsVictim)
{
//     if (!damageEvent.DamageDealer || !damageEvent.DamageReceiver) {
//         return false;
//     }
    AACFCharacter* localChar = GetLocalRiderPlayerCharacter(damageEvent.DamageDealer);
    if (damageEvent.DamageDealer == localChar || damageEvent.DamageReceiver == localChar) {
        if (damageEvent.DamageDealer == localChar) {
            bIsVictim = false;
        } else {
        
             bIsVictim = true;
        }
        return true;
    }
    return false;
}
