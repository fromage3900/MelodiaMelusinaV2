// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFVaultComponent.h"
#include "GameFramework/Character.h"
#include "Components/SkeletalMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include <Animation/AnimInstance.h>

 UACFVaultComponent::UACFVaultComponent()
{
    bVaultChecksEnabled = false;
    bAutoEnable = true;
    SetIsReplicatedByDefault(true);
}

void UACFVaultComponent::SetActorToVault(AActor* val)
{
    actorToVault = val;
}

bool UACFVaultComponent::CanVault() const
{
    bool defaultAnsw = true;
    if (charOwner) {
        const UAnimInstance* animInstance = charOwner->GetMesh()->GetAnimInstance();
        if (animInstance) {
            defaultAnsw = !animInstance->IsAnyMontagePlaying();
        }
    }
    return defaultAnsw && bVaultChecksEnabled && IsValid(actorToVault);
}

void UACFVaultComponent::SetVaultingEnabled(bool inEnabled)
{
    bVaultChecksEnabled = inEnabled;
 
    if (!bVaultChecksEnabled) {
        actorToVault = nullptr;
    }
    OnEnabledStateChanged(bVaultChecksEnabled);
    OnActivationChanged.Broadcast(bVaultChecksEnabled);
}

void UACFVaultComponent::BeginPlay()
{
    Super::BeginPlay();
    charOwner = Cast<ACharacter>(GetOwner());
    if (charOwner && charOwner->HasAuthority() && bAutoEnable) {
        SetVaultingEnabled(true);
    }
}

void UACFVaultComponent::OnEnabledStateChanged_Implementation(const bool bEnabled)
{
}

void UACFVaultComponent::OnRep_Activated()
{
    OnActivationChanged.Broadcast(bVaultChecksEnabled);
}

void UACFVaultComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFVaultComponent, bVaultChecksEnabled);
}
