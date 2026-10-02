// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "ACMCollisionsFunctionLibrary.generated.h"

struct FComponentFX;
struct FAttachedComponents;

/**
 * Function library for spawning and dispatching impact and action-based FX.
 * Provides helpers to trigger particle, sound, and decal effects based on physical interactions or abilities.
 */
UCLASS()
class COLLISIONSMANAGER_API UACMCollisionsFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    /**
     * Returns the global effect dispatcher component from the GameState.
     *
     * @param WorldContextObject The context object, typically from a gameplay class.
     * @return The global UACMEffectsDispatcherComponent, if found.
     */
    UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACM)
    static UACMEffectsDispatcherComponent* GetEffectDispatcher(const UObject* WorldContextObject);

    /**
     * Plays an impact effect based on the damage type and the physical material hit.
     *
     * @param damageImpacting The type of damage that caused the impact.
     * @param materialImpacted The physical material that was struck (e.g., wood, metal).
     * @param impactLocation The world-space location of the impact.
     * @param instigator The actor responsible for the impact.
     */
    UFUNCTION(BlueprintCallable, Category = ACM)
    static void PlayImpactEffect(const TSubclassOf<class UDamageType>& damageImpacting, const FHitResult& HitResult, AActor* instigator);

    /**
     * Plays an impact effect locally without replication (client-side only).
     * Does not trigger any GameplayCue or network synchronization.
     *
     * @param FXtoPlay The FX to spawn (sound, particle, decal).
     * @param instigator The actor that caused the effect.
     * @param outComps    Output container holding the spawned effect components (audio and particle),
     *                    useful for tracking lifecycle events (e.g., completion callbacks) or runtime control.
     */
    UFUNCTION(BlueprintCallable, Category = ACM)
    static void PlayEffectLocally(const FImpactFX& FXtoPlay, AActor* instigator,FComponentFX& outComps);

    /**
     * Plays a replicated action-based effect by triggering a GameplayCue across the network.
     * Typically used for skill or ability-driven FX (e.g., attacks, buffs, casts).
     *
     * @param FXtoPlay The action effect to play (defined in FActionEffect).
     * @param instigator The character triggering the effect.
     * @param WorldContextObject The object used to resolve the world context.
     */
    UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ACM)
    static void PlayReplicatedActionEffect(const FActionEffect& FXtoPlay, ACharacter* instigator, const UObject* WorldContextObject,FComponentFX& outComps);
    
    /**
     * Spawns an attached sound and particle system on a character's skeletal mesh.
     *
     * @param effect The effect definition (socket, offset, particle, sound).
     * @param instigator The character receiving the effect.
     * @return A struct containing references to the spawned components.
     */
    UFUNCTION(BlueprintCallable, Category = ACM)
    static FAttachedComponents SpawnSoundAndParticleAttached(const FActionEffect& effect, const ACharacter* instigator);

    /**
     * Spawns a sound and particle system at the target actor's location and return components
     *
     * @param Target The actor whose location will be used.
     * @param effect The effect to spawn.
     * @param outComps    Output container holding the spawned effect components (audio and particle),
 *                    useful for tracking lifecycle events (e.g., completion callbacks) or runtime control.
     */
    UFUNCTION(BlueprintCallable, Category = ACM)
    static void SpawnSoundAndParticleAtLocation(const AActor* Target, const FImpactFX& effect,FComponentFX& outComps);
    
};