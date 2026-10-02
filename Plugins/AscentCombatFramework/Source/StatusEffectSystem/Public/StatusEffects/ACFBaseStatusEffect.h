  
#pragma once

#include "Components/ACFStatusEffectManagerComponent.h"
#include "CoreMinimal.h"
#include <GameplayEffect.h>
#include <GameplayTagContainer.h>

#include "ACFBaseStatusEffect.generated.h"

UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew, abstract)
class STATUSEFFECTSYSTEM_API UACFBaseStatusEffect : public UObject {
    GENERATED_BODY()

    friend UACFStatusEffectManagerComponent;

public:
    /** Called when this status effect starts. */
    UPROPERTY(BlueprintAssignable, BlueprintCallable)
    FOnStatusEffectChanged OnStatusEffectStarted;

    /** Called when this status effect ends. */
    UPROPERTY(BlueprintAssignable, BlueprintCallable)
    FOnStatusEffectChanged OnStatusEffectEnded;

    /**
     * Returns the character affected by this status effect.
     *
     * @return The owning character.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    class ACharacter* GetCharacterOwner() const { return CharacterOwner; }

    /**
     * Returns the actor who applied this status effect.
     *
     * @return The instigating actor.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    class AActor* GetInstigator() const { return Instigator; }

    /**
     * Returns the UI icon associated with this status effect.
     *
     * @return The icon texture.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UTexture2D* GetStatusIcon() const { return Icon; }

    /**
     * Sets the icon associated with this status effect.
     *
     * @param val The icon texture.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetStatusIcon(UTexture2D* val) { Icon = val; }

    /**
     * Returns the unique gameplay tag identifying this status effect.
     *
     * @return The status effect tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetStatusEffectTag() const { return StatusEffectTag; }

    /**
     * Sets the gameplay tag identifying this status effect.
     *
     * @param val The new tag.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetStatusEffectTag(FGameplayTag val) { StatusEffectTag = val; }

    /**
     * Ends this status effect manually. Triggers OnStatusEffectEnds and other cleanup logic.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void EndEffect();

protected:
    /**
     * Called when this status effect begins.
     *
     * @param Character The character receiving the effect.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF")
    void OnStatusEffectStarts(ACharacter* Character);
    virtual void OnStatusEffectStarts_Implementation(ACharacter* Character);

    /**
     * Called periodically or on trigger logic while the status effect is active.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF")
    void OnTriggerStatusEffect();
    virtual void OnTriggerStatusEffect_Implementation();

    /**
     * Called when this status is applied again while already active.
     * Used to handle retriggering logic.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF")
    void OnStatusRetriggered();
    virtual void OnStatusRetriggered_Implementation();

    /**
     * Called when this status effect ends.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF")
    void OnStatusEffectEnds();
    virtual void OnStatusEffectEnds_Implementation();

    /*The unique tag for this gameplay effect*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    FGameplayTag StatusEffectTag;

    
    /*The looping fx cue to be triggered together with this effect*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    FGameplayTag GameplayCueTag;

    /*Icon for UI*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    UTexture2D* Icon;

    /*If this effect can applied more than once simultaneously*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    bool bCanBeRetriggered = false;

    /** The character affected by this status effect. */
    UPROPERTY(BlueprintReadOnly, Category = "ACF")
    class ACharacter* CharacterOwner;

    /** The actor that applied this status effect. */
    UPROPERTY(BlueprintReadOnly, Category = "ACF")
    class AActor* Instigator;

    /** The component responsible for managing this status effect. */
    UPROPERTY(BlueprintReadOnly, Category = "ACF")
    class UACFStatusEffectManagerComponent* StatusComp;


private:
    void Internal_OnEffectStarted(ACharacter* Character, AActor* inInstigator);

    UWorld* GetWorld() const;

    UAbilitySystemComponent* GetAbilityComponent() const;
};
