// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/ACFActionAbility.h"

#include "ACFFreeClimbJumpAction.generated.h"

class UACFClimbingComponent;

/**
 * Directions a free-climb jump can be performed in.
 * Each entry maps to a montage section in DirectionToMontageSection.
 */
UENUM(BlueprintType)
enum class EACFClimbJumpDirection : uint8 {
    Up    UMETA(DisplayName = "Up"),
    Left  UMETA(DisplayName = "Left"),
    Right UMETA(DisplayName = "Right"),
};

/**
 * Action ability that performs a Zelda-style directional jump while free-climbing a wall.
 *
 * Design contract:
 *   - The requested direction is read from the ability trigger payload (FACFAbilityPayload).
 *     VectorPayload is interpreted as a 2D directional "array": X = horizontal (right +, left -),
 *     Y = vertical (up +). It is the direction the player wants to jump toward.
 *   - The warp target is built along the wall the character is climbing (the plane defined by
 *     the climbing surface normal), so the jump follows the surface even when the wall is not
 *     perfectly vertical (slopes / overhangs).
 *   - The montage section (Up / Left / Right) is selected from the dominant component of the
 *     requested direction via DirectionToMontageSection.
 *
 * Usage: trigger via UACFAbilitySystemComponent::TriggerActionWithPayload, filling
 * Payload.VectorPayload with the current climbing move input (right, up) and Payload.bIsValid.
 *
 * Multiplayer:
 *   The direction is taken ONLY from the replicated trigger payload (carried to the server
 *   inside the gameplay event context), and the wall basis is built from the *replicated*
 *   climb surface normal (UACFClimbingComponent::CurrentClimbingNormal). No local-only input
 *   is read here, so server and owning client resolve the SAME montage section and the SAME
 *   warp target -> animation and movement stay in sync across the network.
 */
UCLASS(Blueprintable, BlueprintType)
class CHARACTERCONTROLLER_API UACFFreeClimbJumpAction : public UACFActionAbility {
    GENERATED_BODY()

public:
    UACFFreeClimbJumpAction();

    /** Resolved jump direction for the current activation. */
    UFUNCTION(BlueprintPure, Category = "ACF|ClimbJump")
    EACFClimbJumpDirection GetClimbJumpDirection() const { return FinalDirection; }

protected:
    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;

    /** Picks Up / Left / Right section based on the resolved direction. */
    virtual FName GetMontageSectionName_Implementation() override;

    /** Builds the warp target along the climbing surface in the requested direction. */
    virtual FTransform GetWarpTransform_Implementation() override;

    /** Distance, in centimeters, the jump warps the character along the wall. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|ClimbJump", meta = (ClampMin = "0.0"))
    float JumpLength = 200.f;

    /** Maps each jump direction to the montage section that should be played. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|ClimbJump")
    TMap<EACFClimbJumpDirection, FName> DirectionToMontageSection;

    /** Direction used when the payload carries no valid directional input. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|ClimbJump")
    EACFClimbJumpDirection DefaultDirection = EACFClimbJumpDirection::Up;

private:
    /** Finds the owner's free-climbing component (if any). */
    UACFClimbingComponent* GetClimbingComponent() const;

    /**
     * Builds an orthonormal basis lying on the climbed wall from its surface normal.
     * @param OutNormal    Surface normal (points away from the wall, toward the character).
     * @param OutWallRight Horizontal direction along the wall plane.
     * @param OutWallUp    Up direction along the wall plane (tilts with the wall).
     * @return false if a valid basis could not be built (e.g. no climb surface).
     */
    bool BuildWallBasis(FVector& OutNormal, FVector& OutWallRight, FVector& OutWallUp) const;

    /** Classifies a (right, up) 2D intent into a discrete jump direction. */
    static EACFClimbJumpDirection ResolveDirection(float RightAmount, float UpAmount);

    /** Requested direction in 2D wall space: X = right, Y = up. */
    FVector RequestedDirection = FVector::ZeroVector;

    /** Discrete direction resolved for this activation. */
    EACFClimbJumpDirection FinalDirection = EACFClimbJumpDirection::Up;
};
