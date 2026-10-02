// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.
// Thanks to BontaKun

#pragma once

#include "CoreMinimal.h"
#include "StatusEffects/ACFBaseStatusEffect.h"
#include "Engine/World.h"
#include "ACFDamageOverTimeStatusEffect.generated.h"


UCLASS(Blueprintable, BlueprintType)
class STATUSEFFECTSYSTEM_API UACFDamageOverTimeStatusEffect : public UACFBaseStatusEffect
{
    GENERATED_BODY()

public:

	UACFDamageOverTimeStatusEffect(const FObjectInitializer& ObjectInitializer);

private:

	int32 CurrentTriggerIndex = 0;

	void TriggerPeriodicallyOverDuration();

protected:

	virtual void OnStatusEffectStarts_Implementation(ACharacter* Character) override;

	virtual void OnTriggerStatusEffect_Implementation() override;

	virtual void OnStatusEffectEnds_Implementation() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    float Duration = 3.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	int32 TriggerCount = 3;

	FTimerHandle PeriodicallyOverDurationHandle;
};    