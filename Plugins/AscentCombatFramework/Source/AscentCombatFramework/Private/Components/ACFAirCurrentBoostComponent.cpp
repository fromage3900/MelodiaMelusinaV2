// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFAirCurrentBoostComponent.h"

#include "Net/UnrealNetwork.h"

// ---------------------------------------------------------------------------

UACFAirCurrentBoostComponent::UACFAirCurrentBoostComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UACFAirCurrentBoostComponent::BeginPlay()
{
    Super::BeginPlay();
}

// ---------------------------------------------------------------------------
// Replication
// ---------------------------------------------------------------------------

void UACFAirCurrentBoostComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFAirCurrentBoostComponent, bInAirCurrent);
}

void UACFAirCurrentBoostComponent::OnRep_bInAirCurrent()
{
    OnAirCurrentStateChanged.Broadcast(bInAirCurrent);
}

// ---------------------------------------------------------------------------
// Enter / Exit
// ---------------------------------------------------------------------------

void UACFAirCurrentBoostComponent::EnterAirCurrent(AACFAirCurrentVolume* Volume, const FACFAirCurrentConfig& Config)
{
    ++ActiveVolumeCount;
    ActiveConfig  = Config;
    CurrentVolume = Volume;

    if (!bInAirCurrent)
    {
        bInAirCurrent = true;
        OnAirCurrentStateChanged.Broadcast(true);
    }
}

void UACFAirCurrentBoostComponent::ExitAirCurrent(AACFAirCurrentVolume* Volume)
{
    ActiveVolumeCount = FMath::Max(ActiveVolumeCount - 1, 0);

    if (CurrentVolume == Volume)
    {
        CurrentVolume = nullptr;
    }

    if (ActiveVolumeCount == 0 && bInAirCurrent)
    {
        bInAirCurrent = false;
        ActiveConfig  = FACFAirCurrentConfig();
        OnAirCurrentStateChanged.Broadcast(false);
    }
}

// ---------------------------------------------------------------------------
// Glider state helpers
// ---------------------------------------------------------------------------

bool UACFAirCurrentBoostComponent::HasActiveGlider() const
{
    return bGliderActive;
}

void UACFAirCurrentBoostComponent::NotifyGliderOpened()
{
    bGliderActive = true;
}

void UACFAirCurrentBoostComponent::NotifyGliderClosed()
{
    bGliderActive = false;
}