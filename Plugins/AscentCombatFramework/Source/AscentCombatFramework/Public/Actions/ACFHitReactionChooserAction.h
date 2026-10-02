// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFChooserAction.h"
#include "Game/ACFTypes.h"
#include "AscentCombatFramework/Public/Game/ACFDamageType.h"
#include "ACFChooserAction.h"
#include "MotionWarpingComponent.h"
#include "ACFHitReactionChooserAction.generated.h"

/**
 * Maps a hit zone gameplay tag to a list of bone names
 */
USTRUCT(BlueprintType)
struct FHitZoneBoneMapping
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    FGameplayTag ZoneTag;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    TArray<FName> BoneNames;
};

/**
 * Chooser action that handles hit reactions with motion warping
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTCOMBATFRAMEWORK_API UACFHitReactionChooserAction : public UACFChooserAction
{
    GENERATED_BODY()

public:
    UACFHitReactionChooserAction();

    virtual void OnActionEnded_Implementation() override;
    virtual FTransform GetWarpTransform_Implementation() override;

    // Override to set chooser parameters
    virtual void SetChooserParams_Implementation() override;

    // Blueprint implementable function to check if this is a death hit
    UFUNCTION(BlueprintNativeEvent, Category = "ACF")
    bool IsDeathHit() const;
    virtual bool IsDeathHit_Implementation() const;

protected:
    // Get current damage event from character
    FACFDamageEvent GetCurrentDamageEvent() const;

    // Body zone that was hit (for chooser parameters)
    // Uses gameplay tags like Hit.Zone.Head, Hit.Zone.Torso, Hit.Zone.Arms, Hit.Zone.Legs
    UPROPERTY(BlueprintReadOnly, Category = "Chooser")
    FGameplayTagContainer HitZone;

    // Damage type tags (for chooser parameters)
    UPROPERTY(BlueprintReadOnly, Category = "Chooser")
    FGameplayTagContainer DamageTypeTags;

    // Hit direction (8-way directional detection for chooser)
    UPROPERTY(BlueprintReadOnly, Category = "Chooser")
    EACFDirection DamageDirection;

    // Whether this hit will kill the character (for death animations in chooser)
    UPROPERTY(BlueprintReadOnly, Category = "Chooser")
    bool bIsDead = false;

    // Maps bone names to hit zone gameplay tags (e.g., head/neck -> Hit.Zone.Head)
    // Each entry specifies a zone tag and the list of bones that belong to it
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF | Hit Zones", meta = (TitleProperty = "ZoneTag"))
    TArray<FHitZoneBoneMapping> BoneToZoneMappings;

    // Default zone tag to use when hit bone is not found in any mapping
    // Leave empty to use no zone tag for unmapped bones
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF | Hit Zones")
    FGameplayTag DefaultHitZone;

private:
    // Cache for fast bone-to-zone lookups (built from BoneToZoneMapping on first use)
    // Maps every bone in skeleton hierarchy to its zone tag
    UPROPERTY(Transient)
    TMap<FName, FGameplayTag> BoneToZoneCache;

    // Whether the cache has been built
    bool bCacheBuilt = false;

    // Builds the bone-to-zone cache by traversing hierarchy for all configured bones
    void BuildBoneToZoneCache();

protected:

    // Base distance for warping
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF | Warp Settings")
    float BaseWarpDistance = 100.f;

    // Maximum allowed warp distance
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF | Warp Settings")
    float MaxWarpDistance = 500.f;

    // Multiplier for force-based distance
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF | Warp Settings")
    float ForceDistanceMultiplier = 0.1f;

    // Whether to use damage impulse for distance calculation
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF | Warp Settings")
    bool bUseDamageImpulse = false;

    // Whether to rotate to face the attacker
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF | Warp Settings")
    bool bShouldFaceAttacker = true;
};
