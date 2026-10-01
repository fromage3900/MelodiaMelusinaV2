// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AttributeSet.h"
#include "AbilitySystemComponent.h"
#include "ACFGASTypes.h"
#include "ACFBaseAttributeSet.h"

#include "ACFPrimaryAttributeSet.generated.h"

/**
 * 
 */
 


UCLASS()
class ASCENTGASRUNTIME_API UACFPrimaryAttributeSet : public UACFBaseAttributeSet {
	GENERATED_BODY()

	public:
    UACFPrimaryAttributeSet();

	   UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Primary Attributes")
    FGameplayAttributeData Strength;
    ATTRIBUTE_ACCESSORS(UACFPrimaryAttributeSet, Strength);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Primary Attributes")
    FGameplayAttributeData Intelligence;
    ATTRIBUTE_ACCESSORS(UACFPrimaryAttributeSet, Intelligence);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "Primary Attributes")
    FGameplayAttributeData Endurance;
    ATTRIBUTE_ACCESSORS(UACFPrimaryAttributeSet, Endurance);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Primary Attributes")
    FGameplayAttributeData Constitution;
    ATTRIBUTE_ACCESSORS(UACFPrimaryAttributeSet, Constitution);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated,  Category = "Primary Attributes")
    FGameplayAttributeData Dexterity;
    ATTRIBUTE_ACCESSORS(UACFPrimaryAttributeSet, Dexterity);


protected:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	
};
