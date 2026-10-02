// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ARSLevelingComponent.h"
#include "Net/UnrealNetwork.h"
#include <Curves/CurveFloat.h>
#include <GameFramework/Actor.h>

// Sets default values for this component's properties
UARSLevelingComponent::UARSLevelingComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    CharacterLevel = 1;
    SetExpToGiveOnDeath(30.f);
    SetIsReplicatedByDefault(true);
    // ...
}

void UARSLevelingComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(UARSLevelingComponent, CharacterLevel);
    DOREPLIFETIME(UARSLevelingComponent, CurrentExps);
    DOREPLIFETIME(UARSLevelingComponent, ExpToNextLevel);
    DOREPLIFETIME(UARSLevelingComponent, Perks);
}

// Called when the game starts
void UARSLevelingComponent::BeginPlay()
{
    Super::BeginPlay();

    if (GetOwner()->HasAuthority()) {

        InitilizeLevelData();
    }
}

void UARSLevelingComponent::OnLevelChanged()
{
}

void UARSLevelingComponent::AddExp_Implementation(int32 exp)
{
    Internal_AddExp(exp);

    OnCurrentExpValueChanged.Broadcast(CurrentExps, exp);
}

void UARSLevelingComponent::SetAvailablePerks_Implementation(int32 InPerks)
{
    Perks = InPerks;
}

void UARSLevelingComponent::ForceSetLevel(int32 newLevel)
{
    CharacterLevel = newLevel;
    InitilizeLevelData();
    OnLevelChanged();
}

void UARSLevelingComponent::Internal_AddExp(int32 exp)
{
    CurrentExps += exp;

    if (CurrentExps >= ExpToNextLevel && CharacterLevel < 255) {
        const int32 remainingExps = CurrentExps - ExpToNextLevel;
        CurrentExps = 0;
        CharacterLevel++;
        InitilizeLevelData();
        Perks += PerksObtainedOnLevelUp;

        OnLevelUp(CharacterLevel, remainingExps);
        OnLevelChanged();
        Internal_AddExp(remainingExps);
    }
}

void UARSLevelingComponent::OnLevelUp(int32 newlevel, int32 _remainingExp)
{
    CharacterLevel = newlevel;

    OnCharacterLevelUp.Broadcast(CharacterLevel);
}

void UARSLevelingComponent::OnRep_CurrentExp()
{
    const int32 delta = CurrentExps - LastKnownExp;
    LastKnownExp = CurrentExps;
    OnCurrentExpValueChanged.Broadcast(CurrentExps, delta);
}

void UARSLevelingComponent::OnRep_CharacterLvl()
{
    OnCharacterLevelUp.Broadcast(CharacterLevel);
}

int32 UARSLevelingComponent::GetExpOnDeath() const
{
    if (!CanLevelUp()) {
        return GetExpToGiveOnDeath();
    }

    if (GetExpToGiveOnDeathByCurrentLevel()) {
        float expToGive = GetExpToGiveOnDeathByCurrentLevel()->GetFloatValue(CharacterLevel);
        return FMath::TruncToInt(expToGive);
    }

    UE_LOG(LogTemp, Error, TEXT("Invalid ExpToGiveOnDeathByCurrentLevel Curve!"));

    return GetExpToGiveOnDeath();
}

void UARSLevelingComponent::InitilizeLevelData()
{
    ExpToNextLevel = GetTotalExpsForLevel(CharacterLevel);
}

int32 UARSLevelingComponent::GetTotalExpsForLevel(int32 level) const
{
    if (GetExpForNextLevelCurve()) {
        const float nextlevelexp = GetExpForNextLevelCurve()->GetFloatValue(level);
        return FMath::TruncToInt(nextlevelexp);
    }
    return -1;
}

int32 UARSLevelingComponent::GetTotalExpsAcquired() const
{
    return GetExpsForLevel(CharacterLevel - 1) + GetCurrentExp();
}

int32 UARSLevelingComponent::GetExpsForLevel(int32 level) const
{
    if (level > 1) {
        return GetTotalExpsForLevel(level) - GetTotalExpsForLevel(level - 1);
    }
    return GetTotalExpsForLevel(level);
}
