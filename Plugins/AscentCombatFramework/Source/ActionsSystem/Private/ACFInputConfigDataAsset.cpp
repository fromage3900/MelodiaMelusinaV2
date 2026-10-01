// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ACFInputConfigDataAsset.h"
#include "InputMappingContext.h"
#include "ACFActionTypes.h"
#include <InputAction.h>

 UACFInputConfigDataAsset::UACFInputConfigDataAsset()
{
}


bool UACFInputConfigDataAsset::GetBindingForAbilityTag(FGameplayTag AbilityTag, FACFInputAbilityBinding& OutBinding) const
{
    for (const FACFInputAbilityBinding& Binding : InputAbilityBindings)
    {
        if (Binding.AbilityTag.MatchesTagExact(AbilityTag))
        {
            OutBinding = Binding;
            return true;
        }
    }
    
    return false;
}

bool UACFInputConfigDataAsset::GetBindingForInputAction(UInputAction* InputAction, FACFInputAbilityBinding& OutBinding) const
{
    if (!InputAction)
    {
        return false;
    }
    
    for (const FACFInputAbilityBinding& Binding : InputAbilityBindings)
    {
        if (Binding.EnhancedInputAction == InputAction)
        {
            OutBinding = Binding;
            return true;
        }
    }
    
    return false;
}