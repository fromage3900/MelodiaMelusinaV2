// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACMCollisionsFunctionLibrary.h"
#include "ACMEffectsDispatcherComponent.h"
#include "GameFramework/GameState.h"
#include "Kismet/GameplayStatics.h"
#include <GameFramework/Character.h>
#include <NiagaraFunctionLibrary.h>
#include <Kismet/GameplayStatics.h>
#include "ACMTypes.h"
#include <NiagaraComponent.h>
#include <GameFramework/GameStateBase.h>
#include <Components/SkeletalMeshComponent.h>

UACMEffectsDispatcherComponent* UACMCollisionsFunctionLibrary::GetEffectDispatcher(const UObject* WorldContextObject)
{
    const AGameStateBase* gameState = UGameplayStatics::GetGameState(WorldContextObject);

    if (gameState) {
        UACMEffectsDispatcherComponent* effectManag = gameState->FindComponentByClass<class UACMEffectsDispatcherComponent>();
        if (effectManag) {
            return effectManag;
        }
    }

    UE_LOG(LogTemp, Error, TEXT("Missing  Effects Dispatcher Component in GAME STATE! - UACMCollisionsFunctionLibrary::GetEffectDispatcher "));

    return nullptr;
}

void UACMCollisionsFunctionLibrary::PlayImpactEffect(const TSubclassOf<class UDamageType>& damageImpacting, const FHitResult& HitResult, AActor* instigator)
{

    UACMEffectsDispatcherComponent* effectDips = UACMCollisionsFunctionLibrary::GetEffectDispatcher(instigator);
    if (effectDips) {
        effectDips->PlayReplicatedImpact(damageImpacting, HitResult, instigator);
        return;
    }
    UE_LOG(LogTemp, Error, TEXT("Missing  Effects Dispatcher Component in GAME STATE! - UACMCollisionsFunctionLibrary "));
}

void UACMCollisionsFunctionLibrary::PlayEffectLocally(const FImpactFX& FXtoPlay, AActor* instigator,FComponentFX& outComps)
{
    UACMEffectsDispatcherComponent* effectDips = UACMCollisionsFunctionLibrary::GetEffectDispatcher(instigator);
    if (effectDips) {
        effectDips->PlayEffectLocally(FXtoPlay, instigator,outComps);
        return;
    }
    UE_LOG(LogTemp, Error, TEXT("Missing  Effects Dispatcher Component in GAME STATE! - UACMCollisionsFunctionLibrary "));
}

void UACMCollisionsFunctionLibrary::PlayReplicatedActionEffect(const FActionEffect& FXtoPlay, ACharacter* instigator, const UObject* WorldContextObject,FComponentFX& outComps)
{
    UACMEffectsDispatcherComponent* effectDips = UACMCollisionsFunctionLibrary::GetEffectDispatcher(WorldContextObject);
    if (effectDips) {
        effectDips->PlayReplicatedActionEffect(FXtoPlay, instigator,outComps);
        return;
    }
    UE_LOG(LogTemp, Error, TEXT("Missing  Effects Dispatcher Component in GAME STATE! - UACMCollisionsFunctionLibrary "));
}

FAttachedComponents UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAttached(const FActionEffect& effect, const ACharacter* instigator)
{
    FAttachedComponents comps;
    if (effect.ActionParticle) {
        comps.CascadeComp = UGameplayStatics::SpawnEmitterAttached(effect.ActionParticle, instigator->GetMesh(), effect.SocketOrBoneName,
            effect.RelativeOffset.GetLocation(), effect.RelativeOffset.GetRotation().Rotator(), effect.RelativeOffset.GetScale3D());
    }
    
    if (effect.ActionSound) {
        comps.AudioComp = UGameplayStatics::SpawnSoundAttached(effect.ActionSound, instigator->GetMesh(), effect.SocketOrBoneName);
    }
    
    if (effect.NiagaraParticle) {
        comps.NiagaraComp = UNiagaraFunctionLibrary::SpawnSystemAttached(effect.NiagaraParticle, instigator->GetMesh(), effect.SocketOrBoneName,
            effect.RelativeOffset.GetLocation(), effect.RelativeOffset.GetRotation().Rotator(), effect.RelativeOffset.GetScale3D(),
            EAttachLocation::SnapToTarget, true, ENCPoolMethod::AutoRelease);
    }
    return comps;
}

void UACMCollisionsFunctionLibrary::SpawnSoundAndParticleAtLocation(const AActor* Target, const FImpactFX& effect,FComponentFX& outComps)
{
    if (effect.ActionParticle) {
        outComps.ParticleSystemComponent = UGameplayStatics::SpawnEmitterAtLocation(Target, effect.ActionParticle, effect.SpawnLocation.GetLocation(),
            effect.SpawnLocation.GetRotation().Rotator(), effect.SpawnLocation.GetScale3D());
    }

    if (effect.ActionSound) {
        outComps.AudioComponent =
        UGameplayStatics::SpawnSoundAtLocation(Target, effect.ActionSound, effect.SpawnLocation.GetLocation());
    }

    if (effect.NiagaraParticle) {
        outComps.NiagaraComponent =
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(Target, effect.NiagaraParticle, effect.SpawnLocation.GetLocation(),
            effect.SpawnLocation.GetRotation().Rotator(), effect.SpawnLocation.GetScale3D());
    }
}
