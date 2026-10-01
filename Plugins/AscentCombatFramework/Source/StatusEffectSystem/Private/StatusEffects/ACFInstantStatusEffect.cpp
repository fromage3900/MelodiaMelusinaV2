#include "StatusEffects/ACFInstantStatusEffect.h"
#include "StatusEffects/ACFBaseStatusEffect.h"
#include <GameFramework/Character.h>

UACFInstantStatusEffect::UACFInstantStatusEffect(const FObjectInitializer& ObjectInitializer)
{

}	

void UACFInstantStatusEffect::OnStatusEffectStarts_Implementation(ACharacter* Character)
{
	Super::OnStatusEffectStarts_Implementation(Character);
	OnTriggerStatusEffect();
/*	EndEffect();*/
}

void UACFInstantStatusEffect::OnTriggerStatusEffect_Implementation()
{
	Super::OnTriggerStatusEffect_Implementation();
}

void UACFInstantStatusEffect::OnStatusEffectEnds_Implementation()
{
	Super::OnStatusEffectEnds_Implementation();
}