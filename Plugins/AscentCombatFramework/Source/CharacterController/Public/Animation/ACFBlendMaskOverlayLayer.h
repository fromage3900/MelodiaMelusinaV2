// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAnimLayer.h"
#include "ACFAnimTypes.h"
#include "ACFCCTypes.h"
#include "Animation/AimOffsetBlendSpace.h"
#include "Animation/AnimNode_ACFBlendByMask.h"
#include "CoreMinimal.h"

#include "ACFBlendMaskOverlayLayer.generated.h"

class UACFBoneBlendMask;
class UAnimSequence;

/**
 * Generic overlay anim layer driven by data. One single Blueprint subclass is reused for every
 * overlay. The layer is fully self-updating: every frame it pulls the active overlay profile
 * from the owning UACFAnimInstance (GetActiveOverlayData) and resolves the current locomotion
 * stance, exposing the animation, blend mask and blend mode as Current* read-only variables for
 * the AnimGraph (ACFBlendByMask node). The main AnimInstance never pushes into it.
 *
 * Kept separate from the legacy UACFOverlayLayer (one AnimBP class per overlay) on purpose.
 */
UCLASS()
class CHARACTERCONTROLLER_API UACFBlendMaskOverlayLayer : public UACFAnimLayer {
    GENERATED_BODY()

public:
    UACFBlendMaskOverlayLayer();

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMovStance(const FGameplayTag& inOverlay);

    /** Resolved overlay animation for the current locomotion stance. */
    UPROPERTY(BlueprintReadOnly, Category = "ACF|Overlay")
    TObjectPtr<UAnimSequence> CurrentOverlayAnim;

    /** Blend mask of the current entry (idle or active stance). Null when the entry has no animation. */
    UPROPERTY(BlueprintReadOnly, Category = "ACF|Overlay")
    TObjectPtr<UACFBoneBlendMask> CurrentBlendMask;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Overlay")
    EACFMaskBlendMode CurrentBlendMode = EACFMaskBlendMode::DynamicAdditive;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|AimOffset")
    TObjectPtr<UAimOffsetBlendSpace> AimOffset;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|AimOffset")
    float AimOffsetAlpha = 1.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Overlay")
    float OverlayBlendAlfa = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FGameplayTag currentOverlayTag;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FOverlayConfig currentOverlay;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    bool bHasActiveStance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFCharacterMovementComponent> MovementComp;

    virtual void NativeInitializeAnimation() override;
    virtual void NativeThreadSafeUpdateAnimation(float DeltaSeconds) override;
    virtual void OnActivated_Implementation() override;

protected:
    void SetReferences();
    void RefreshGraphVariables();

private:
    UPROPERTY(Transient)
    FACFOverlayData RuntimeOverlayData;

    UPROPERTY(Transient)
    TObjectPtr<class UACFAnimInstance> OwnerAnimInstance;

    FGameplayTag appliedOverlayTag;
    bool bForceStanceRefresh = false;

    float DefaultSwitchTime = 0.5f;
    float targetBlendAlpha = 0.f;
};
