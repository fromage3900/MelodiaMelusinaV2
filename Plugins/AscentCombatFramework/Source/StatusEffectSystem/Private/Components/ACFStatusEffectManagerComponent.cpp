
#include "Components/ACFStatusEffectManagerComponent.h"
#include "ACFStatusTypes.h"
#include "ARSStatisticsComponent.h"
#include "StatusEffects/ACFBaseStatusEffect.h"
#include <GameFramework/Character.h>
#include <Net/UnrealNetwork.h>

UACFStatusEffectManagerComponent::UACFStatusEffectManagerComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    SetComponentTickEnabled(false);
}

void UACFStatusEffectManagerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFStatusEffectManagerComponent, StatusEffects);
}

void UACFStatusEffectManagerComponent::BeginPlay()
{
    Super::BeginPlay();

    CharacterOwner = Cast<ACharacter>(GetOwner());
}

void UACFStatusEffectManagerComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

bool UACFStatusEffectManagerComponent::IsAffectedByStatusEffect(FGameplayTag StatusEffectTag)
{
    return StatusEffects.Contains(StatusEffectTag);
}

void UACFStatusEffectManagerComponent::CreateAndApplyStatusEffect_Implementation(TSubclassOf<UACFBaseStatusEffect> StatusEffectToConstruct, AActor* instigator)
{
    if (!StatusEffectToConstruct) {
        UE_LOG(LogTemp, Warning, TEXT("StatusEffectToConstructnot set or invalid! - ACFStatusEffectManagerComponent"));
        return;
    }

    UACFBaseStatusEffect* statusEffect = NewObject<UACFBaseStatusEffect>(this, StatusEffectToConstruct);
    if (statusEffect) {
        AddStatusEffect(statusEffect, instigator);
    }
}

void UACFStatusEffectManagerComponent::AddStatusEffect(UACFBaseStatusEffect* StatusEffect, AActor* instigator)
{
    if (StatusEffects.Contains(StatusEffect->StatusEffectTag)) {
        FStatusEffect* effect = StatusEffects.FindByKey(StatusEffect->StatusEffectTag);

        if (effect->effectInstance && effect->effectInstance->bCanBeRetriggered) {
            effect->effectInstance->OnStatusRetriggered();
            OnStatusRetriggered.Broadcast(StatusEffect->StatusEffectTag);
            OnAnyStatusChanged.Broadcast();
        }
    } else {
        StatusEffects.Add(FStatusEffect(StatusEffect));
        StatusEffect->OnStatusEffectEnded.AddDynamic(this, &UACFStatusEffectManagerComponent::Internal_RemoveStatusEffect);
        StatusEffect->Internal_OnEffectStarted(Cast<ACharacter>(GetOwner()), instigator);
        OnStatusStarted.Broadcast(StatusEffect->StatusEffectTag);
        OnAnyStatusChanged.Broadcast();
    }
}

void UACFStatusEffectManagerComponent::RemoveStatusEffect_Implementation(FGameplayTag StatusEffectTag)
{
    if (StatusEffects.Contains(StatusEffectTag)) {
        FStatusEffect* effect = StatusEffects.FindByKey(StatusEffectTag);
        if (effect && effect->effectInstance) {
            effect->effectInstance->EndEffect();
            OnStatusRemoved.Broadcast(StatusEffectTag);
        }
    }
}

void UACFStatusEffectManagerComponent::OnRep_StatusEffects()
{
    OnAnyStatusChanged.Broadcast();
}

void UACFStatusEffectManagerComponent::Internal_RemoveStatusEffect(FGameplayTag StatusEffectTag)
{
    if (StatusEffects.Contains(StatusEffectTag)) {
        const FStatusEffect* effect = StatusEffects.FindByKey(StatusEffectTag);
        const FStatusEffect newEff = *effect;
        StatusEffects.Remove(newEff);
        OnAnyStatusChanged.Broadcast();
    }
}
