// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "CASAnimCondition.generated.h"

/**
 *
 */
UCLASS(Blueprintable, BlueprintType, Abstract, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("CAS"))
class COMBINEDANIMATIONSSYSTEM_API UCASAnimCondition : public UObject {
    GENERATED_BODY()

protected:
    UFUNCTION(BlueprintNativeEvent, Category = CAS)
    bool VerifyCondition(const struct FCombinedAnimConfig& contextAnim, const ACharacter* animMaster);

    UFUNCTION(BlueprintPure, Category = CAS)
    class UACFCombinedAnimSlaveComponent* GetOwnerComponent() const
    {
        return ownerCompoment;
    }

    /*This Condition will apply to all the Combined Anims that has a child of this tag as Animation Tag*/
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag AnimRootTag;

    UPROPERTY()
    UACFCombinedAnimSlaveComponent* ownerCompoment;

    UWorld* GetWorld() const override;

public:
    bool Internal_VerifyCondition(class UACFCombinedAnimSlaveComponent* ownerComp, const FCombinedAnimConfig& animTag, const ACharacter* animMaster);

    friend class UACFCombinedAnimSlaveComponent;
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("CAS"))
class COMBINEDANIMATIONSSYSTEM_API UCASORCondition : public UCASAnimCondition {
    GENERATED_BODY()

protected:
    UCASORCondition() { }

    UPROPERTY(Instanced, EditDefaultsOnly, Category = "Conditions")
    TArray<UCASAnimCondition*> OrConditions;

    virtual bool VerifyCondition_Implementation(const FCombinedAnimConfig& contextAnim, const class ACharacter* animMaster) override;
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("CAS"))
class COMBINEDANIMATIONSSYSTEM_API UCASANDCondition : public UCASAnimCondition {
    GENERATED_BODY()

protected:
    UCASANDCondition() { }

    UPROPERTY(Instanced, EditDefaultsOnly, Category = "Conditions")
    TArray<UCASAnimCondition*> ANDConditions;

    virtual bool VerifyCondition_Implementation(const FCombinedAnimConfig& contextAnim, const class ACharacter* animMaster) override
    {
        for (auto& cond : ANDConditions) {
            if (!cond->Internal_VerifyCondition(ownerCompoment, contextAnim, animMaster))
                return false;
        }
        return true;
    }
};
