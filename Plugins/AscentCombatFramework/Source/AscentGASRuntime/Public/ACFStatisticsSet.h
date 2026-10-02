// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "AttributeSet.h"
#include "AbilitySystemComponent.h"
#include "ACFGASTypes.h"
#include "ACFBaseAttributeSet.h"

#include "ACFStatisticsSet.generated.h"

/**
 * 
 */
 


UCLASS()
class ASCENTGASRUNTIME_API UACFStatisticsSet : public UACFBaseAttributeSet {
	GENERATED_BODY()

	public:
    UACFStatisticsSet();


    /* STATISTICS */

    // Health Attributes
    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData MaxHealth;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, MaxHealth);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData Health;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, Health);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData HealthRegen;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, HealthRegen);

    // Stamina Attributes
    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData MaxStamina;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, MaxStamina);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData Stamina;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, Stamina);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData StaminaRegen;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, StaminaRegen);

    // Mana Attributes
    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData MaxMana;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, MaxMana);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData Mana;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, Mana);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData ManaRegen;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, ManaRegen);

    // Equilibrium Attributes
    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData MaxEquilibrium;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, MaxEquilibrium);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData Equilibrium;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, Equilibrium);

    UPROPERTY(EditAnywhere, BlueprintReadWrite,  Replicated, Category = "Statistics")
    FGameplayAttributeData EquilibriumRegen;
    ATTRIBUTE_ACCESSORS(UACFStatisticsSet, EquilibriumRegen);



protected:
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	
};
