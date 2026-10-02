// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "AGSGraphNode.h"
#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Game/ACFTypes.h"
#include <Animation/AnimMontage.h>
#include "ACFBaseComboNode.h"

#include "ACFComboNode.generated.h"

class ACharacter;

/**
 *
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFComboNode : public UACFBaseComboNode {
    GENERATED_BODY()

public:
    UACFComboNode();

    virtual void ActivateNode() override;

    virtual void DeactivateNode() override;

    UFUNCTION(Blueprintpure, Category = ACF)
    UAnimMontage* GetMontage() const
    {
        return ComboMontage;
    }

    UFUNCTION(Blueprintpure, Category = ACF)
    FAttributesSetModifier GetComboNodeModifier() const
    {
        return ComboModifier;
    }

    UFUNCTION(Blueprintpure, Category = ACF)
    EDamageActivationType GetDamageToActivate() const { return DamageToActivate; }

    UFUNCTION(Blueprintpure, Category = ACF)
    TArray<FName> GetTraceChannels() const { return TraceChannels; }

protected:
    UPROPERTY(EditAnywhere, Category = ACF)
    UAnimMontage* ComboMontage;

    UPROPERTY(EditAnywhere, Category = ACF)
    FAttributesSetModifier ComboModifier;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    EDamageActivationType DamageToActivate;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TArray<FName> TraceChannels;

#if WITH_EDITOR

    virtual FText GetNodeTitle() const
    {
        if (ComboMontage) {
            return FText::FromString(ComboMontage->GetName().Left(12));
        }
        return FText::FromString("Set Montage");
    }

    virtual FText GetParagraphTitle() const
    {
        if (ComboMontage) {
            return FText::FromString(ComboMontage->GetName().Left(30));
        }
        return FText::FromString("Remember to set a Montage!");
    }

#endif

private:
    TObjectPtr<ACharacter> charOwner;
};
