// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ItemActors/ACFItemActor.h"
#include <AbilitySystemComponent.h>
#include <ActiveGameplayEffectHandle.h>
#include <GameplayEffect.h>
#include "Items/ACFItem.h"
#include <Net/UnrealNetwork.h>
#include <GameFramework/Pawn.h>

// Sets default values
AACFItemActor::AACFItemActor()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
}

void AACFItemActor::InitItemActor(APawn* inOwner, UACFItem* itemDefinition)
{
    check(inOwner);
    ItemOwner = inOwner;
    ItemDefinition = itemDefinition;
    InitItemFromDefinition(itemDefinition);
}

bool AACFItemActor::IsFullyInit() const
{
    return IsValid(ItemDefinition);
}

void AACFItemActor::InitItemFromDefinition_Implementation(UACFItem* itemDefinition)
{
}

// Called when the game starts or when spawned
void AACFItemActor::BeginPlay()
{
    Super::BeginPlay();
}

void AACFItemActor::OnRep_ItemOwner()
{
}

void AACFItemActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AACFItemActor, ItemOwner);
}

FActiveGameplayEffectHandle AACFItemActor::AddGASModifierToOwner(const TSubclassOf<UGameplayEffect>& gameplayModifier, const float geLevel)
{
    if (gameplayModifier) {
        UAbilitySystemComponent* AbilitySystemComponent = GetAbilityComponent();
        if (AbilitySystemComponent) {
            FGameplayEffectContextHandle EffectContext = AbilitySystemComponent->MakeEffectContext();
            UGameplayEffect* GameplayEffect = gameplayModifier->GetDefaultObject<UGameplayEffect>();
            return AbilitySystemComponent->ApplyGameplayEffectToSelf(GameplayEffect, geLevel, EffectContext);
        }
    }
    return FActiveGameplayEffectHandle();
}

void AACFItemActor::RemoveGASModifierToOwner(const FActiveGameplayEffectHandle& modifierHandle)
{
    if (modifierHandle.IsValid()) {
        UAbilitySystemComponent* AbilitySystemComponent = GetAbilityComponent();

        if (AbilitySystemComponent) {
            AbilitySystemComponent->RemoveActiveGameplayEffect(modifierHandle);
        }
    }
}

UAbilitySystemComponent* AACFItemActor::GetAbilityComponent() const
{
    if (ItemOwner) {
        return ItemOwner->FindComponentByClass<UAbilitySystemComponent>();
    }
    return nullptr;
}
