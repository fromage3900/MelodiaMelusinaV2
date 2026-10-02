// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Graph/ACFTransition.h"
#include "ACFActionCondition.h"
#include "Actors/ACFCharacter.h"
#include "Logging.h"


bool UACFTransition::AreConditionsMet(const ACharacter* Character) const
{
    // If no conditions are set, the transition is automatically valid
    UE_LOG(ACFLog, Warning, TEXT("No of Conditions: %d"), Conditions.Num());
    if (Conditions.Num() == 0) {
        return true;
    }
    if (!Character) {
        UE_LOG(ACFLog, Error, TEXT("Character is null!"));
        return false;
    }

    // Attempt to cast ACharacter to AACFCharacter
    const AACFCharacter* ACFCharacter = Cast<AACFCharacter>(Character);
    if (!ACFCharacter) {
        UE_LOG(ACFLog, Error, TEXT("Failed to cast character to AACFCharacter! Transition conditions cannot be evaluated."));
        return false; // Conditions cannot be met without AACFCharacter
    }

    // Log the successful casting
    UE_LOG(ACFLog, Warning, TEXT("Successfully cast character to AACFCharacter: %s"), *ACFCharacter->GetName());

    // Evaluate each condition
    for (UACFActionCondition* Condition : Conditions) {
        if (!Condition) {
            UE_LOG(ACFLog, Error, TEXT("Condition is null! Skipping."));
            continue;
        }

        const bool bConditionMet = Condition->IsConditionMet(ACFCharacter);

        // Log the result of the condition
        UE_LOG(ACFLog, Warning, TEXT("Condition %s evaluated to: %s"),
            *Condition->GetName(), bConditionMet ? TEXT("True") : TEXT("False"));

        if (!bConditionMet) {
            UE_LOG(ACFLog, Warning, TEXT("Condition %s failed!"), *Condition->GetName());
            return false; // Fail if any condition is not met
        }
    }

    UE_LOG(ACFLog, Warning, TEXT("All conditions passed for transition"));
    return true; // All conditions passed
}

