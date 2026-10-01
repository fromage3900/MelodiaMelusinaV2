// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBaseAttributeSet.h"
#include "ACFGASTypes.h"
#include "AbilitySystemComponent.h"
#include "AttributeSet.h"
#include "CoreMinimal.h"

#include "ACFAttributeSet.generated.h"

/**
 *
 */

UCLASS()
class ASCENTGASRUNTIME_API UACFAttributeSet : public UACFBaseAttributeSet {
    GENERATED_BODY()

public:
    UACFAttributeSet();

    /* SECONDARY ATT */

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData MeleeDamage;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, MeleeDamage);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData RangedDamage;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, RangedDamage);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData SpellDamage;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, SpellDamage);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData PhysicalDefense;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, PhysicalDefense);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData SpellDefense;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, SpellDefense);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData CritChance;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, CritChance);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Secondary Attributes")
    FGameplayAttributeData BlockDefense;
    ATTRIBUTE_ACCESSORS(UACFAttributeSet, BlockDefense);

protected:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
