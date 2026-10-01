// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/SkeletalMesh.h"
#include "ItemActors/ACFGliderActor.h"
#include "Items/ACFItem.h"

#include "ACFGliderItem.generated.h"

/** CMC properties overridden while the glider is active. Restored automatically on EndAbility. */
USTRUCT(BlueprintType)
struct INVENTORYSYSTEM_API FGliderMovementConfig
{
    GENERATED_BODY()

    /** Gravity scale (0 = no gravity, 1 = normal). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider", meta = (ClampMin = "0.0", ClampMax = "2.0"))
    float GravityScale = 0.15f;

    /** Horizontal control while airborne (0 = none, 1 = full). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float AirControl = 0.5f;

    /** Lateral friction while falling – higher values reduce horizontal drift. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider", meta = (ClampMin = "0.0"))
    float FallingLateralFriction = 0.5f;

    /** Braking deceleration while falling (cm/s²). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider", meta = (ClampMin = "0.0"))
    float BrakingDecelerationFalling = 200.f;

    /** Max horizontal speed while gliding (cm/s). 0 = keep the character's current max speed. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glider", meta = (ClampMin = "0.0"))
    float MaxFlySpeed = 0.f;
};

/**
 * Item definition for a Zelda-style paraglider.
 * Add this to the character's inventory to enable the ACFGliderAction.
 *
 * The glider mesh, attachment socket and movement parameters are defined here
 * so that different glider items can have completely different flight feel.
 */
UCLASS(Blueprintable, BlueprintType)
class INVENTORYSYSTEM_API UACFGliderItem : public UACFItem
{
    GENERATED_BODY()

public:
    UACFGliderItem();

    /** Skeletal mesh displayed while the glider is deployed. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Glider")
    TObjectPtr<USkeletalMesh> GliderMesh;

    /** Socket on the character's SkeletalMesh to attach the glider actor to. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Glider")
    FName AttachSocketName = NAME_None;

    /**
     * Actor class to spawn when the glider is deployed.
     * Override with a Blueprint child of AACFGliderActor to customise VFX, sounds, etc.
     * Leave null to use AACFGliderActor directly.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Glider")
    TSubclassOf<AACFGliderActor> GliderActorClass;

    /** CMC overrides applied while this glider is active. Each item can feel completely different. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Glider")
    FGliderMovementConfig MovementConfig;

    virtual TSubclassOf<AACFItemActor> GetItemActorClass_Implementation() const override;
};
