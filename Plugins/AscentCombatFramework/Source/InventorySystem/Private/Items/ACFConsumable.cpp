// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Items/ACFConsumable.h"
#include "ACMEffectsDispatcherComponent.h"
#include "ARSStatisticsComponent.h"
#include "Cues/ACFItemUsedGameplayCue.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameState.h"
#include "Kismet/GameplayStatics.h"
#include "Logging.h"

UACFConsumable::UACFConsumable()
{
    ItemInfo.ItemType = EItemType::Consumable;
    ItemInfo.Name = FText::FromString("Base Consumable");
}

TArray<FGameplayEffectConfig> UACFConsumable::GetGameplayEffects() const
{
    TArray<FGameplayEffectConfig> effects;
    for (const auto& modifier : TimedAttributeSetModifier) {
        FGameplayEffectConfig effectConfig;
        effectConfig.Effect = modifier.modifier.GameplayEffectModifier;
        effectConfig.Level = modifier.modifier.GELevel;
        effects.Add(effectConfig);
    }
    return effects;
}

bool UACFConsumable::CanBeUsed_Implementation(const APawn* Pawn) const
{
    return true;
}

void UACFConsumable::Internal_UseItem(APawn* target)
{
    if (target) {

        UARSStatisticsComponent* statComp = target->FindComponentByClass<UARSStatisticsComponent>();
        if (statComp) {
            for (const auto& modifier : TimedAttributeSetModifier) {
                statComp->AddTimedAttributeSetModifier(modifier.modifier, modifier.duration);
            }
            for (const auto& statisMod : StatModifier) {
                statComp->ModifyStat(statisMod);
            }
        }

        if (GetAbilityComponent(target)) {
            FItemUseEffectContext* Context = new FItemUseEffectContext();
            Context->ConsumedItemClass = GetClass();
            Context->AddInstigator(target, target->GetController());

            FGameplayCueParameters Params;
            Params.EffectContext = FGameplayEffectContextHandle(Context);
            GetAbilityComponent(target)->ExecuteGameplayCue(OnUsedGameplayCue, Params);
        }

    } else {
        UE_LOG(ACFInventoryLog, Warning, TEXT("Invalid Item Owner - ACFConsumbale"));
    }
    OnItemUsed(target);
}

void UACFConsumable::OnItemUsed_Implementation(APawn* target)
{
    // IMPLEMENT ME!
}

UAbilitySystemComponent* UACFConsumable::GetAbilityComponent(APawn* target) const
{
    if (target) {
        return target->FindComponentByClass<UAbilitySystemComponent>();
    }
    return nullptr;
}
