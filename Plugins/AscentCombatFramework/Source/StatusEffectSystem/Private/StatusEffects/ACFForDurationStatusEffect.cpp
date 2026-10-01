#include "StatusEffects/ACFForDurationStatusEffect.h"
#include "ARSStatisticsComponent.h"
#include "TimerManager.h"
#include <GameFramework/Character.h>
#include <Engine/World.h>

UACFForDurationStatusEffect::UACFForDurationStatusEffect()
{
}

void UACFForDurationStatusEffect::OnStatusRetriggered_Implementation()
{
	if (CharacterOwner) {
		CharacterOwner->GetWorld()->GetTimerManager().ClearTimer(ForDurationHandle);
		CharacterOwner->GetWorld()->GetTimerManager().SetTimer(ForDurationHandle, this, &UACFForDurationStatusEffect::EndEffect, Duration, false);
	}
}

void UACFForDurationStatusEffect::OnStatusEffectStarts_Implementation(ACharacter* Character)
{
	Super::OnStatusEffectStarts_Implementation(Character);

	if (CharacterOwner) {
		ownerStat = CharacterOwner->FindComponentByClass<UARSStatisticsComponent>();
	}
	OnTriggerStatusEffect();
}

void UACFForDurationStatusEffect::OnTriggerStatusEffect_Implementation()
{
	Super::OnTriggerStatusEffect_Implementation();
	if (CharacterOwner) {
		CharacterOwner->GetWorld()->GetTimerManager().SetTimer(ForDurationHandle, this, &UACFForDurationStatusEffect::EndEffect, Duration, false);
		if (ownerStat) {
			AttributeModifier.GEHandle = ownerStat->AddAttributeSetModifier(AttributeModifier);
		}
	}
}

void UACFForDurationStatusEffect::OnStatusEffectEnds_Implementation()
{
	if (CharacterOwner) {
		CharacterOwner->GetWorld()->GetTimerManager().ClearTimer(ForDurationHandle);
		if (ownerStat) {
			ownerStat->RemoveAttributeSetModifier(AttributeModifier.GEHandle);
		}
	}

	Super::OnStatusEffectEnds_Implementation();
}
