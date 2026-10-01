// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"

#include "ACFAirCurrentVolume.generated.h"

class ACharacter;
class UBoxComponent;
class UArrowComponent;
class UAbilitySystemComponent;
class UACFAirCurrentBoostComponent;

// ---------------------------------------------------------------------------

/** Configuration for a single air-current volume. */
USTRUCT(BlueprintType)
struct FACFAirCurrentConfig
{
    GENERATED_BODY()

    /** World-space direction of the air current (normalised at runtime). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    FVector Direction = FVector::UpVector;

    /** Impulse magnitude in cm/s (single-shot) or cm/s^2 (continuous). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent", meta = (ClampMin = "0.0"))
    float Strength = 1200.f;

    /** Hard cap on velocity the current can add along its direction. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent", meta = (ClampMin = "0.0"))
    float MaxAddedSpeed = 800.f;

    /** true = force every tick; false = single impulse on overlap begin. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    bool bContinuous = true;

    /** If > 0 and bContinuous, force is applied in discrete pulses instead of every frame. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent", meta = (ClampMin = "0.0", EditCondition = "bContinuous"))
    float PulseIntervalSec = 0.f;

    /** When true only characters with an active UACFGliderAction receive the boost. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    bool bOnlyAffectsGliders = true;

    /** When true, strength scales 0->1 from volume edge to centre (soft falloff). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    bool bScaleWithOverlapDepth = false;
};

// ---------------------------------------------------------------------------

/** Tracked data per overlapping character. */
USTRUCT()
struct FACFAirCurrentOverlapEntry
{
    GENERATED_BODY()

    UPROPERTY()
    TWeakObjectPtr<ACharacter> Character;

    UPROPERTY()
    TWeakObjectPtr<UACFAirCurrentBoostComponent> BoostComponent;

    /** Accumulated time since last pulse (only used when PulseIntervalSec > 0). */
    float PulseAccumulator = 0.f;
};

// ---------------------------------------------------------------------------

/**
 * Level-placed volume that applies a directional velocity boost to characters
 * gliding through it (or any falling character if bOnlyAffectsGliders is false).
 *
 * All cosmetic effects (VFX, audio) are driven via Gameplay Cues so that they
 * replicate automatically through the Ability System.  Assign cue tags in the
 * Blueprint child or per-instance in the details panel.
 *
 * Setup:
 *   1. Drop an AACFAirCurrentVolume into the level.
 *   2. Scale the CollisionVolume box to the desired region.
 *   3. Set AirCurrentConfig.Direction (the arrow component previews it).
 *   4. Tune Strength, MaxAddedSpeed, bContinuous to taste.
 *   5. Optionally set AirCurrentCueTag to a looping GameplayCue (e.g. GameplayCue.Glider.AirCurrent).
 *   6. Create a GC_Notify_Actor Blueprint for that tag to handle Niagara, audio, etc.
 */
UCLASS(Blueprintable, BlueprintType, ClassGroup = (ACF))
class ASCENTCOMBATFRAMEWORK_API AACFAirCurrentVolume : public AActor
{
    GENERATED_BODY()

public:
    AACFAirCurrentVolume();

    // -- Queries --------------------------------------------------------------

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    FVector GetCurrentDirection() const;

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    float GetCurrentStrength() const;

    UFUNCTION(BlueprintPure, Category = "ACF|Glider|AirCurrent")
    bool IsActive() const { return bIsActive; }

    // -- Activation -----------------------------------------------------------

    /** Toggle the volume on or off at runtime (e.g. quest gate). */
    UFUNCTION(BlueprintCallable, Category = "ACF|Glider|AirCurrent")
    void SetActive(bool bNewActive);

    // -- Replication ----------------------------------------------------------

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    // -- Components -----------------------------------------------------------

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Glider|AirCurrent")
    TObjectPtr<UBoxComponent> CollisionVolume;

    /** Editor-only arrow that previews the wind direction. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Glider|AirCurrent")
    TObjectPtr<UArrowComponent> DirectionArrow;

    // -- Configuration --------------------------------------------------------

    /** Per-instance air current settings. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    FACFAirCurrentConfig AirCurrentConfig;

    /**
     * Looping Gameplay Cue added to characters while they are inside the air current.
     * The cue Blueprint handles all cosmetics (Niagara, audio, camera shake, etc.)
     * and replicates automatically via the character's AbilitySystemComponent.
     * Leave empty for no cosmetic effects.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent", meta = (Categories = "GameplayCue"))
    FGameplayTag AirCurrentCueTag;

    /** Should the volume start active? */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Glider|AirCurrent")
    bool bStartActive = true;

    // -- Events ---------------------------------------------------------------

    /** Called on the server when a character first receives the air current boost. */
    UFUNCTION(BlueprintNativeEvent, Category = "ACF|Glider|AirCurrent")
    void OnCharacterEnteredCurrent(ACharacter* Character);
    virtual void OnCharacterEnteredCurrent_Implementation(ACharacter* Character) {}

    /** Called on the server when a character leaves the air current. */
    UFUNCTION(BlueprintNativeEvent, Category = "ACF|Glider|AirCurrent")
    void OnCharacterExitedCurrent(ACharacter* Character);
    virtual void OnCharacterExitedCurrent_Implementation(ACharacter* Character) {}

    // -- Internals ------------------------------------------------------------

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

#if WITH_EDITOR
    virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

private:
    /** Syncs the arrow component rotation to AirCurrentConfig.Direction. */
    void UpdateDirectionArrow();

    UPROPERTY(ReplicatedUsing = OnRep_bIsActive)
    bool bIsActive = true;

    UFUNCTION()
    void OnRep_bIsActive();

    UPROPERTY()
    TArray<FACFAirCurrentOverlapEntry> OverlappingEntries;

    UFUNCTION()
    void HandleBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
        bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void HandleEndOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

    bool IsCharacterEligible(const ACharacter* Character) const;
    void ApplyBoostToCharacter(ACharacter* Character, float DeltaTime, float DepthScale);
    float ComputeDepthScale(const ACharacter* Character) const;
    UACFAirCurrentBoostComponent* EnsureBoostComponent(ACharacter* Character);

    void AddAirCurrentCue(ACharacter* Character);
    void RemoveAirCurrentCue(ACharacter* Character);

    void ClearAllOverlaps();
    int32 FindOverlapEntry(const ACharacter* Character) const;
};