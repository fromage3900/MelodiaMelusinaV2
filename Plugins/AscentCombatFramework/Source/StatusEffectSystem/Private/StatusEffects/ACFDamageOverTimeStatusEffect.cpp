#include "StatusEffects/ACFDamageOverTimeStatusEffect.h"
#include "TimerManager.h"
#include <GameFramework/Character.h>


UACFDamageOverTimeStatusEffect::UACFDamageOverTimeStatusEffect(const FObjectInitializer& ObjectInitializer)
{

}	

void UACFDamageOverTimeStatusEffect::TriggerPeriodicallyOverDuration() 
{
	if (!PeriodicallyOverDurationHandle.IsValid()) {
		const float time = TriggerCount == 0 ? 0 : Duration / TriggerCount;

		GetOuter()->GetWorld()->GetTimerManager().SetTimer(PeriodicallyOverDurationHandle, this, &UACFDamageOverTimeStatusEffect::TriggerPeriodicallyOverDuration, time, true);

		//GetWorldTimerManager().SetTimer(PeriodicallyOverDurationHandle, this, &UACFDamageOverTimeStatusEffect::TriggerPeriodicallyOverDuration, time, true);
	}

	OnTriggerStatusEffect();
	
	if (TriggerCount <= CurrentTriggerIndex++) {
		CurrentTriggerIndex = 0;
		EndEffect();
	}
}


void UACFDamageOverTimeStatusEffect::OnStatusEffectStarts_Implementation(ACharacter* Character)
{
	Super::OnStatusEffectStarts_Implementation(Character);

	TriggerPeriodicallyOverDuration();
}

void UACFDamageOverTimeStatusEffect::OnTriggerStatusEffect_Implementation()
{
	Super::OnTriggerStatusEffect_Implementation();
}

void UACFDamageOverTimeStatusEffect::OnStatusEffectEnds_Implementation()
{
	GetOuter()->GetWorld()->GetTimerManager().ClearTimer(PeriodicallyOverDurationHandle);   


	Super::OnStatusEffectEnds_Implementation();
}