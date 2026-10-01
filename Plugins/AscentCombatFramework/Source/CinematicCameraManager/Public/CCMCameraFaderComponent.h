// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CCMTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <GameFramework/Actor.h>

#include "CCMCameraFaderComponent.generated.h"

class USpringArmComponent;
class UCameraComponent;
class AActor;
class APawn;
class UCCMFadeableActorComponent;

/**
 * UCCMCameraFaderComponent
 *
 * Actor component designed to be attached to a PlayerController.
 * Each tick it casts a line trace from the active camera to the controlled pawn and
 * temporarily fades (makes semi-transparent) any world geometry or actors that occlude the view.
 * Actors that should be fadeable must own a UCCMFadeableActorComponent, or the
 * bForceFaderComponent flag can be enabled to add that component automatically at runtime.
 *
 * At runtime the camera used for the line trace can be overridden via SetActiveCamera /
 * ClearActiveCameraOverride; when no override is set the component auto-detects the camera
 * from the currently possessed pawn.
 */
UCLASS(ClassGroup = (CCM), meta = (BlueprintSpawnableComponent))
class CINEMATICCAMERAMANAGER_API UCCMCameraFaderComponent : public UActorComponent {
    GENERATED_BODY()

public:
    UCCMCameraFaderComponent();

    // -------------------------------------------------------------------------
    //  Occlusion state
    // -------------------------------------------------------------------------

    /** Returns whether the occlusion / fading system is currently active. */
    UFUNCTION(BlueprintPure, Category = CCM)
    bool GetOcclusionEnabled() const { return bOcclusionEnabled; }

    /** Enables or disables the occlusion / fading system at runtime. */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void SetOcclusionEnabled(bool val) { bOcclusionEnabled = val; }

    // -------------------------------------------------------------------------
    //  Ignore list
    // -------------------------------------------------------------------------

    /** Adds an actor to the list of actors that are never considered as occluders. */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void AddActorToIgnore(AActor* newActor);

    /** Removes an actor from the ignore list so it can occlude again. */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void RemoveActorToIgnore(AActor* newActor);

    // -------------------------------------------------------------------------
    //  Manual fade control
    // -------------------------------------------------------------------------

    /**
     * Manually fades the given actor by applying the FadeMaterial override.
     * Returns true if the actor owns (or was given) a UCCMFadeableActorComponent.
     */
    UFUNCTION(BlueprintCallable, Category = CCM)
    bool HideActor(AActor* Actor);

    /** Restores the original materials on the given actor (removes the fade override). */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void ShowActor(AActor* Actor);

    /** Returns the list of actors that are currently faded due to occlusion. */
    UFUNCTION(BlueprintPure, Category = CCM)
    TArray<AActor*> GetOccludedActors() const { return OccludedActors; }

    // -------------------------------------------------------------------------
    //  Active camera override
    // -------------------------------------------------------------------------

    /**
     * Overrides the camera used to compute the occlusion line trace.
     * Pass a valid UCameraComponent to lock the fader to that camera.
     * Call ClearActiveCameraOverride() to revert to automatic pawn-camera detection.
     */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void SetActiveCamera(UCameraComponent* Camera);

    /**
     * Returns the camera currently used for occlusion checks.
     * This is either the manually overridden camera (set via SetActiveCamera) or the one
     * that was automatically detected from the possessed pawn.
     */
    UFUNCTION(BlueprintPure, Category = CCM)
    UCameraComponent* GetActiveCamera() const;

    /**
     * Clears any previously set camera override and reverts to automatic detection:
     * the component will look for a UCameraComponent on the currently possessed pawn.
     */
    UFUNCTION(BlueprintCallable, Category = CCM)
    void ClearActiveCameraOverride();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    // -------------------------------------------------------------------------
    //  Configuration properties
    // -------------------------------------------------------------------------

    /** Material applied to actors while they are occluding the camera. Should be a translucent / masked material. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = CCM)
    UMaterialInterface* FadeMaterial;

    /** Enables or disables the occlusion check. Disabling it also restores all currently faded actors. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    bool bOcclusionEnabled;

    /** Maximum world-unit distance from the camera at which a hit actor is considered an occluder. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    float MaxOccludingDistance = 280.f;

    /** When true, the component will also fade the player pawn when it is very close to the camera. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    bool bFadePlayer = true;

    /** Distance (in world units) between the camera and the pawn below which the pawn will be faded. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    float MaxPlayerFadeDistance = 70.f;

    /** Object types included in the occlusion line trace. Only objects of these types can become occluders. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    TArray<TEnumAsByte<EObjectTypeQuery>> CollisionObjectTypes;

    /**
     * When true, actors that do NOT already own a UCCMFadeableActorComponent will have one
     * added dynamically at runtime so they can still be faded.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    bool bForceFaderComponent = false;

    /** Class used when dynamically adding a UCCMFadeableActorComponent to actors (see bForceFaderComponent). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    TSubclassOf<UCCMFadeableActorComponent> FadeableComponentClass;

    /** Draws debug line-trace visualisation in the editor viewport every tick. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    bool bShowDebug = false;

    /** Actors that are permanently excluded from the occlusion check (editable in the Details panel). */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = CCM)
    TArray<AActor*> IgnoredActors;

public:
    // Called every frame
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    /** Spring arm detected on the currently possessed pawn (used for context; not directly queried by occlusion). */
    TObjectPtr<USpringArmComponent> ActiveSpringArm;

    /**
     * Camera used as the start point of the occlusion line trace.
     * Populated automatically from the possessed pawn unless overridden via SetActiveCamera.
     */
    TObjectPtr<UCameraComponent> ActiveCamera;

    /** The owning PlayerController (set once in BeginPlay). */
    TObjectPtr<APlayerController> ActiveController;

    /** Actors currently faded because they are occluding the camera–pawn line. */
    UPROPERTY()
    TArray<AActor*> OccludedActors;

    /** When true, ActiveCamera was set manually and HandlePawnChanges will not overwrite it. */
    bool bCameraOverridden = false;

    /** Whether the player pawn is currently being faded due to proximity. */
    bool bPlayerOccluded = false;

    /** Called whenever the controller possesses a new pawn; refreshes ActiveSpringArm and ActiveCamera. */
    UFUNCTION()
    void HandlePawnChanges(APawn* newPawn);

    /** Performs the occlusion line trace and hides / restores actors accordingly. */
    UFUNCTION()
    void CheckOcclusion();

    bool HideOccludedActor(AActor* Actor);
    void ShowOccludedActor(AActor* OccludedActor);

    /** Immediately restores all faded actors. Called when occlusion is disabled or no camera is available. */
    void ForceShowOccludedActors();

    /** Returns true if the given actor is eligible to be faded (owns or can receive a UCCMFadeableActorComponent). */
    bool CanOccludeActor(const AActor* Actor) const;
};
