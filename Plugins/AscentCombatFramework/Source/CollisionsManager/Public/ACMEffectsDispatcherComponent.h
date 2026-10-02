// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ACMEffectsDispatcherComponent.generated.h"

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class COLLISIONSMANAGER_API UACMEffectsDispatcherComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACMEffectsDispatcherComponent();

    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACM)
    void PlayReplicatedActionEffect(const FActionEffect& effect, class ACharacter* instigator,const FComponentFX& outComps);

    UFUNCTION(BlueprintCallable, Category = ACM)
    void PlayActionEffectLocally(const FActionEffect& effect, class ACharacter* instigator,FComponentFX& outComps);

    UFUNCTION(BlueprintCallable, Category = ACM)
    void PlayReplicatedImpact(const TSubclassOf<class UDamageType>& damageImpacting, const FHitResult& HitResult, AActor* instigator);


    UFUNCTION(BlueprintCallable, Category = ACM)
    void PlayEffectLocally(const FImpactFX& effect, AActor* instigator,FComponentFX& outComps);

    UFUNCTION(BlueprintCallable, Category = ACM)
    bool TryGetImpactFX(const TSubclassOf<class UDamageType>& damageImpacting, class UPhysicalMaterial* materialImpacted, FBaseFX& outFXtoPlay) const;

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(EditDefaultsOnly, Category = ACM)
    class UACMImpactsFXDataAsset* ImpactFXs;

    UPROPERTY(EditDefaultsOnly, Category = ACM)
    FGameplayTag DefaultImpactCue;

private:
    void Internal_PlayEffect(class ACharacter* instigator, const FActionEffect& effect,const FComponentFX& outComps);

    UFUNCTION(NetMulticast, Reliable, Category = ACM)
    void ClientsPlayEffect(const FActionEffect& effect, class ACharacter* instigator,const FComponentFX& outComps);

};
