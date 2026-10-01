// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Volumes/ACFAirCurrentVolume.h"

#include "ACFAirCurrentBoostComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAirCurrentStateChanged, bool, bInAirCurrent);

/**
 * Lightweight component automatically added to a character when it first
 * overlaps an AACFAirCurrentVolume.  Tracks how many volumes are currently
 * affecting the character and exposes a replicated flag for cosmetic use
 * (trail VFX, camera shake, UI indicator).
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFAirCurrentBoostComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UACFAirCurrentBoostComponent();

    void EnterAirCurrent(AACFAirCurrentVolume* Volume, const FACFAirCurrentConfig& Config);
    void ExitAirCurrent(AACFAirCurrentVolume* Volume);

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    bool IsInAirCurrent() const { return bInAirCurrent; }

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    FACFAirCurrentConfig GetActiveConfig() const { return ActiveConfig; }

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    bool HasActiveGlider() const;

    void NotifyGliderOpened();
    void NotifyGliderClosed();

    UPROPERTY(BlueprintAssignable, Category = "ACF|Glider|AirCurrent")
    FOnAirCurrentStateChanged OnAirCurrentStateChanged;

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(ReplicatedUsing = OnRep_bInAirCurrent)
    bool bInAirCurrent = false;

    UFUNCTION()
    void OnRep_bInAirCurrent();

    FACFAirCurrentConfig ActiveConfig;
    TWeakObjectPtr<AACFAirCurrentVolume> CurrentVolume;
    int32 ActiveVolumeCount = 0;
    bool bGliderActive = false;
};