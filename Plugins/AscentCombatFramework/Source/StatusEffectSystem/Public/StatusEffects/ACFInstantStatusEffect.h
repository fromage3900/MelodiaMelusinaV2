
#pragma once

#include "CoreMinimal.h"
#include "StatusEffects/ACFBaseStatusEffect.h"
#include "ACFInstantStatusEffect.generated.h"


UCLASS(Category = ACF, Blueprintable, BlueprintType)
class STATUSEFFECTSYSTEM_API UACFInstantStatusEffect : public UACFBaseStatusEffect
{
    GENERATED_BODY()

public:	


	UACFInstantStatusEffect(const FObjectInitializer& ObjectInitializer);

protected:

	virtual void OnStatusEffectStarts_Implementation(ACharacter* Character) override;

	virtual void OnTriggerStatusEffect_Implementation() override;

	virtual void OnStatusEffectEnds_Implementation() override;

};    