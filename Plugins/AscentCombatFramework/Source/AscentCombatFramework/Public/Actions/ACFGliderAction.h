// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFSustainedAction.h"
#include "CoreMinimal.h"
#include "Items/ACFGliderItem.h"

#include "ACFGliderAction.generated.h"

class AACFGliderActor;
class UACFAirCurrentBoostComponent;

/**
 * Zelda-style paraglider action.
 *
 * Requires a UACFGliderItem (or subclass) to be present in the character's inventory.
 * The item provides the skeletal mesh and attach socket; this action spawns a replicated
 * AACFGliderActor server-side and overrides CMC properties to slow the descent.
 *
 * Setup checklist:
 *   1. Create a UACFGliderItem Blueprint and set GliderMesh + AttachSocketName.
 *   2. Add the item to the character's inventory.
 *   3. Set GliderItemClass in this ability's Blueprint child to match your item class.
 *   4. Fill GliderMovementConfig to taste.
 *   5. Assign a loopable AnimMontage to animMontage.
 *   6. Set TriggeringTag (e.g. "Actions.Glider") and add to ACFAbilitySystemComponent.
 *   7. Bind trigger input to TriggerAction / ReleaseAction.
 */
UCLASS(Blueprintable, BlueprintType)
class ASCENTCOMBATFRAMEWORK_API UACFGliderAction : public UACFSustainedAction
{
    GENERATED_BODY()

public:
    UACFGliderAction();

    UFUNCTION(BlueprintPure, Category = "ACF|Glider")
    AACFGliderActor* GetGliderActor() const { return SpawnedGliderActor; }

    /** Returns true if the character is currently inside an air current volume. */
    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    bool IsInAirCurrent() const;

protected:
    /**
     * If true the ability requires a UACFGliderItem (or subclass) in the character's inventory.
     * The item supplies the mesh, attach socket and movement parameters.
     * If false the ability activates without any inventory check and uses the
     * movement settings defined directly on this ability (GliderMovementConfig below).
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Glider")
    bool bNeedsItem = false;

    /** Item class to search for in the inventory. Only used when bNeedsItem is true. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Glider", meta = (EditCondition = "bNeedsItem"))
    TSubclassOf<UACFGliderItem> GliderItemClass;

    /**
     * Movement overrides applied while gliding.
     * Only used when bNeedsItem is false.
     * When bNeedsItem is true these values come from the UACFGliderItem instead.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "ACF|Glider", meta = (EditCondition = "!bNeedsItem"))
    FGliderMovementConfig GliderMovementConfig;

    /** Called on the server after the glider opens (actor spawned, CMC overrides applied). */
    UFUNCTION(BlueprintNativeEvent, DisplayName = "OnGliderOpened", Category = "ACF|Glider")
    void OnGliderOpened();
    virtual void OnGliderOpened_Implementation() {}

    /** Called on the server before the glider closes (actor still alive, CMC not yet restored). */
    UFUNCTION(BlueprintNativeEvent, DisplayName = "OnGliderClosed", Category = "ACF|Glider")
    void OnGliderClosed(bool bWasCancelled);
    virtual void OnGliderClosed_Implementation(bool bWasCancelled) {}

    /** Called on the server when the glider enters an air current volume. */
    UFUNCTION(BlueprintNativeEvent, DisplayName = "OnAirCurrentEntered", Category = "ACF|Glider|AirCurrent")
    void OnAirCurrentEntered();
    virtual void OnAirCurrentEntered_Implementation() {}

    /** Called on the server when the glider exits all air current volumes. */
    UFUNCTION(BlueprintNativeEvent, DisplayName = "OnAirCurrentExited", Category = "ACF|Glider|AirCurrent")
    void OnAirCurrentExited();
    virtual void OnAirCurrentExited_Implementation() {}

    virtual void OnMontageFinished_Implementation(bool bInterrupted) override
    {
        ReleaseAction();
    }

    /** Spawns the glider actor when the NotablePoint anim notify fires. */
    virtual void OnNotablePointReached_Implementation() override;

    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags = nullptr,
        const FGameplayTagContainer* TargetTags = nullptr,
        OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const override;

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        const FGameplayEventData* TriggerEventData) override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        bool bReplicateEndAbility,
        bool bWasCancelled) override;

private:
    struct FOriginalMovementConfig
    {
        float GravityScale               = 1.f;
        float AirControl                 = 0.05f;
        float FallingLateralFriction     = 0.f;
        float BrakingDecelerationFalling = 0.f;
        float MaxWalkSpeed               = 600.f;
    } OriginalMovement;

    UPROPERTY()
    TObjectPtr<AACFGliderActor> SpawnedGliderActor;

    /** Glider item resolved on activation, kept alive until the NotablePoint fires. */
    UPROPERTY()
    TObjectPtr<UACFGliderItem> CachedGliderItem;

    /** Cached reference to the air current boost component (may be null). */
    UPROPERTY()
    TObjectPtr<UACFAirCurrentBoostComponent> AirCurrentComp;

    void SpawnGliderActor(ACharacter* Char, UACFGliderItem* GliderItem);
    void DestroyGliderActor();
    void RestoreHandIK(ACharacter* Char);
    void ApplyMovementConfig(UCharacterMovementComponent* MovComp, const FGliderMovementConfig& Config);
    void RestoreMovementConfig(UCharacterMovementComponent* MovComp);

    UFUNCTION()
    void HandleLanded(const FHitResult& Hit);

    UFUNCTION()
    void HandleAirCurrentStateChanged(bool bNowInAirCurrent);

    UFUNCTION()
    void HandleMovementModeChanged(ACharacter* Character, EMovementMode PrevMovementMode, uint8 PrevCustomMode);
};
