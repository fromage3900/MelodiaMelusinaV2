#pragma once

#include "ACFComboAttackAction.h"
#include "CoreMinimal.h"

#include "ACFComboAIAttackAction.generated.h"

// Forward Declarations
class UInputAction;
class UACFComboGraph;
class UACFComboNode;
class UACFComboComponent;

/**
 * A specialized combo attack action for AI characters.
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew, meta = (DisplayName = "Combo AI Attack Action"))
class ASCENTCOMBOGRAPH_API UACFComboAIAttackAction : public UACFComboAttackAction {
    GENERATED_BODY()

public:
    UACFComboAIAttackAction();

    // AI-specific input probabilities
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI")
    TMap<FGameplayTag, float> AIInputProbabilities;

protected:
    virtual void OnActionStarted_Implementation() override;
    virtual void OnActionEnded_Implementation() override;

    // Override to prevent buffer from closing before AI can input
    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;

private:
    void SimulateAIInput();
};
