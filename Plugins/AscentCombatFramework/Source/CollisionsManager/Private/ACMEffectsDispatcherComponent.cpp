// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACMEffectsDispatcherComponent.h"
#include "ACMImpactsFXDataAsset.h"
#include "ACMTypes.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundBase.h>
#include <Sound/SoundCue.h>
#include "Particles/ParticleSystem.h"
#include "NiagaraCommon.h"
#include "NiagaraSystem.h"
#include "Components/SkeletalMeshComponent.h"
#include <AbilitySystemComponent.h>
#include <Logging.h>
#include "ACMCollisionsFunctionLibrary.h"


// Sets default values for this component's properties
UACMEffectsDispatcherComponent::UACMEffectsDispatcherComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
}

// Called when the game starts
void UACMEffectsDispatcherComponent::BeginPlay()
{
    Super::BeginPlay();
}


void UACMEffectsDispatcherComponent::PlayReplicatedActionEffect_Implementation(const FActionEffect& effect, class ACharacter* instigator,const FComponentFX& outComps)
{
    if (instigator) {
        instigator->MakeNoise(effect.NoiseEmitted, instigator, instigator->GetActorLocation());
        ClientsPlayEffect(effect, instigator,outComps);
    }
}

void UACMEffectsDispatcherComponent::PlayActionEffectLocally(const FActionEffect& effect, class ACharacter* instigator,FComponentFX& outComps)
{
    Internal_PlayEffect(instigator, effect,outComps);
}

void UACMEffectsDispatcherComponent::PlayReplicatedImpact(const TSubclassOf<class UDamageType>& damageImpacting, const FHitResult& HitResult, AActor* instigator)
{
    if (!GetOwner()->HasAuthority()) {
        UE_LOG(ACFCollisionsLog, Error, TEXT("Trying to play a replicated GameplayCue from a client!"));
        return;
    }
    UAbilitySystemComponent* ASC = instigator->FindComponentByClass<UAbilitySystemComponent>();
    if (!ASC) {
        UE_LOG(ACFCollisionsLog, Error, TEXT("Missing Ability Comp in Instigator!! - UACMEffectsDispatcherComponent "));
        return;
    }
    FACFGameplayEffectContext* context = new FACFGameplayEffectContext();
    context->AddInstigator(instigator, instigator);
    context->DamageTypeClass = damageImpacting;
    context->AddHitResult(HitResult);

    FGameplayEffectContextHandle ContextHandle = FGameplayEffectContextHandle(context);

    FGameplayCueParameters Params;
    Params.EffectContext = ContextHandle;

    ASC->ExecuteGameplayCue(DefaultImpactCue, Params);
}


void UACMEffectsDispatcherComponent::PlayEffectLocally(const FImpactFX& effect, AActor* instigator,FComponentFX& outComps)
{
    UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAtLocation(instigator, effect,outComps );
}

bool UACMEffectsDispatcherComponent::TryGetImpactFX(const TSubclassOf<class UDamageType>& damageImpacting, class UPhysicalMaterial* materialImpacted, FBaseFX& outFXtoPlay) const
{
    if (ImpactFXs) {
        return ImpactFXs->TryGetImpactFX(damageImpacting, materialImpacted, outFXtoPlay);
    }
    return false;
}

void UACMEffectsDispatcherComponent::Internal_PlayEffect(class ACharacter* instigator, const FActionEffect& effect,const FComponentFX& outComps)
{
    if (instigator) {
        switch (effect.SpawnLocation) {
        case ESpawnFXLocation::ESpawnOnActorLocation:
        case ESpawnFXLocation::ESpawnAttachedToSocketOrBone:
            UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAttached(effect, instigator);
            break;
        case ESpawnFXLocation::ESpawnAtLocation:
            {
                FComponentFX Comps;
                Comps.ParticleSystemComponent = outComps.ParticleSystemComponent;
                Comps.AudioComponent = outComps.AudioComponent;
                Comps.NiagaraComponent = outComps.NiagaraComponent;
                UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAtLocation(instigator, FImpactFX(effect, effect.RelativeOffset),Comps);
                break;
            }
        default:
            UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAttached(effect, instigator);
            break;
        }
    }
}


//TODO DELETE
void UACMEffectsDispatcherComponent::ClientsPlayEffect_Implementation(const FActionEffect& effect, class ACharacter* instigator,const FComponentFX& outComps)
{
    Internal_PlayEffect(instigator, effect,outComps);
}

