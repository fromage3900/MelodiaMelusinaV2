
#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "StatusEffects/ACFBaseStatusEffect.h"
#include "ARSTypes.h"

#include "ACFForDurationStatusEffect.generated.h"

class UARSStatisticsComponent;


UCLASS(Blueprintable, BlueprintType)
class STATUSEFFECTSYSTEM_API UACFForDurationStatusEffect : public UACFBaseStatusEffect {
    GENERATED_BODY()

public:
    UACFForDurationStatusEffect();

    FTimerHandle ForDurationHandle;

protected:
    virtual void OnStatusEffectStarts_Implementation(ACharacter* Character) override;

    virtual void OnTriggerStatusEffect_Implementation() override;

    virtual void OnStatusEffectEnds_Implementation() override;

    virtual void OnStatusRetriggered_Implementation() override;

    
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    bool bAddModifierDuringEffect = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "bAddModifierDuringEffect"), Category = ACF)
    FAttributesSetModifier AttributeModifier;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    float Duration = 5.f;

private: 

    TObjectPtr<UARSStatisticsComponent> ownerStat;

};
