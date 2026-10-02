// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFGASTypes.h"
#include "AttributeSet.h"
#include "CoreMinimal.h"

#include "ACFBaseAttributeSet.generated.h"

#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName)                                                                                          \
    FGameplayAttribute PropertyName##Attribute() const                                                                                        \
    {                                                                                                                                         \
        static FProperty* Property = FindFieldChecked<FProperty>(ClassName::StaticClass(), GET_MEMBER_NAME_CHECKED(ClassName, PropertyName)); \
        return FGameplayAttribute(Property);                                                                                                  \
    }                                                                                                                                         \
    FORCEINLINE float Get##PropertyName() const                                                                                               \
    {                                                                                                                                         \
        return PropertyName.GetCurrentValue();                                                                                                \
    }                                                                                                                                         \
    FORCEINLINE void Set##PropertyName(float NewVal)                                                                                          \
    {                                                                                                                                         \
        PropertyName.SetCurrentValue(NewVal);                                                                                                 \
    }                                                                                                                                         \
    FORCEINLINE void Init##PropertyName(float NewVal)                                                                                         \
    {                                                                                                                                         \
        PropertyName.SetBaseValue(NewVal);                                                                                                    \
        PropertyName.SetCurrentValue(NewVal);                                                                                                 \
    }

/**
 * Base AttributeSet class with automatic attribute clamping support.
 * Stores a list of clamp rules to apply to attributes after modification.
 */
UCLASS()
class ASCENTGASRUNTIME_API UACFBaseAttributeSet : public UAttributeSet {
    GENERATED_BODY()

protected:
    /**
     * List of clamp rules applied automatically to attributes.
     * Each entry defines min/max bounds for a specific attribute.
     */
    UPROPERTY(EditDefaultsOnly, Category = Config)
    TArray<FAttributeClamps> Clamps;

    virtual void PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue) override;
    virtual void PreAttributeBaseChange(const FGameplayAttribute& Attribute, float& NewValue) const override;
    virtual void PostAttributeChange(const FGameplayAttribute& Attribute, float OldValue, float NewValue) override;

    void ExecuteClamp(const FGameplayAttribute& Attribute, float& NewValue) const;
    void NormalizeClampedAttributesForMaxChange(const FGameplayAttribute& MaxAttribute, float OldMaxValue, float NewMaxValue) const;
};
