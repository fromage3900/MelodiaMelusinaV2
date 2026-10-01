// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBaseComboNode.h"
#include "AGSGraph.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"

#include <GameFramework/Character.h>
#include <GameplayTagContainer.h>

#include "ACFComboGraph.generated.h"

class UInputAction;
class UACFComboNode;
class UACFActionAbility;
class UACFTransition;
class ACharacter;
class UACFComboComponent;

/**
 *
 */
UENUM()
enum class EComboState : uint8 {
    /** Node is enabled. */
    Started,
    /** Node is disabled. */
    NotStarted,

};

/**
 * ACF Combo Graph System
 *
 * Manages combo chains using a graph-based structure.
 * This class handles transitions, animations, and state management
 * for player or AI-controlled combo executions.
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFComboGraph : public UAGSGraph {
    GENERATED_BODY()

public:
    UACFComboGraph();

    /**
     * Starts a combo sequence from a specified entry action.
     * @param inStartAction The gameplay tag representing the starting combo action.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StartCombo(const FGameplayTag& inStartAction);

    /**
     * Stops the currently active combo sequence and resets the graph state.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StopCombo();

    /**
     * Returns the current animation montage associated with the combo node being executed.
     * @return Pointer to the active UAnimMontage or nullptr if no montage is active.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UAnimMontage* GetCurrentComboMontage() const;

    /**
     * Retrieves the current attribute modifier applied by the combo.
     * @param outModifier Reference to the struct that will hold the modifier.
     * @return True if a valid modifier is found, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetCurrentComboModifier(FAttributesSetModifier& outModifier) const;

    /**
     * Attempts to transition to the next combo node based on the provided input.
     * @param currentInput The gameplay tag identifying the current input action.
     * @param Character The character attempting the transition.
     * @return True if the transition is successful, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool PerformTransition(const FGameplayTag& currentInput, const ACharacter* Character);

    /**
     * Gets the tag that triggered the current combo sequence.
     * @return The gameplay tag that initiated the combo.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetTriggeringAction() const;

    /**
     * Returns the current node being executed in the combo graph.
     * @return Pointer to the current UACFComboNode, or nullptr if none is active.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UACFComboNode* GetCurrentComboNode() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsActive() const
    {
        return Enabled == EComboState::Started;
    }

    ACharacter* GetCharacterOwner() const
    {
        return characterOwner;
    }

    void SetCharacterOwner(ACharacter* inOwner)
    {
        characterOwner = inOwner;
    }

    UACFComboComponent* GetOwningComponent() const;


    // They can be different instances, but they are the same combo
    FORCEINLINE bool operator==(const UACFComboGraph* Other) const { return this->GetClass() == Other->GetClass(); }

    FORCEINLINE bool operator!=(const UACFComboGraph* Other) const { return this->GetClass() != Other->GetClass(); }

    UWorld* GetWorld() const override { return characterOwner ? characterOwner->GetWorld() : nullptr; }

    TArray<FGameplayTag> GetValidInputsForCurrentNode() const;
    // AI/Player State Management
    void SetIsAI(bool bInIsAI);
    bool IsAI() const;

private:
    EComboState Enabled = EComboState::NotStarted;

    TObjectPtr<ACharacter> characterOwner;

    FGameplayTag triggeringAction;

protected:
    virtual bool ActivateNode(class UAGSGraphNode* node) override;
    // New Methods
    bool HandleRerouteNode(UACFBaseComboNode* comboNode);
    TArray<TPair<UAGSGraphNode*, UACFTransition*>> GetSortedTransitions(UACFBaseComboNode* comboNode);
    bool HandleAITransitions(const TArray<TPair<UAGSGraphNode*, UACFTransition*>>& Transitions, const FGameplayTag& currentInput, const ACharacter* Character, UACFBaseComboNode* CurrentNode);
    bool HandlePlayerTransitions(const TArray<TPair<UAGSGraphNode*, UACFTransition*>>& Transitions, const FGameplayTag& currentInput, const ACharacter* Character, UACFBaseComboNode* CurrentNode);
    // AI-specific state
    UPROPERTY()
    bool bIsAI;
};
