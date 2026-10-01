#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaveHarpCombatComponent.generated.h"

class ACharacter;
class APlayerController;
class UInputComponent;
class UStaticMeshComponent;
class UAnimMontage;
class USoundBase;
class USpringArmComponent;
class UMelodiaHybridEncounterComponent;

/** Player input, weapon presentation and release timing. Stock combat resolves every hit. */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaveHarpCombatComponent final : public UActorComponent
{
 GENERATED_BODY()
public:
 UMelodiaWaveHarpCombatComponent();
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 virtual void TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Tick) override;

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") bool IsAiming() const { return bAiming; }
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") bool IsDrawing() const { return bDrawing; }
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") float GetDrawTension() const;
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") float GetHitFeedback() const;
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") float GetChordFeedback() const;
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") UMelodiaHybridEncounterComponent* GetTarget() const;
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") bool IsInSequence() const;
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") FString GetStatusText() const { return StatusText; }
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp") int32 ShotsFired = 0;
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp") int32 HitsResolved = 0;
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp") int32 ComboStep = 0;
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp") int32 ChordsCompleted = 0;
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp") float LastHitDamage = 0;

 // Authored feel variants on this same player component. None affect stock damage.
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="220", ClampMax="450")) float AimArmLength = 320.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel") FVector AimSocketOffset = FVector(0,70,30);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="0.05", ClampMax="0.3")) float AimBlendSeconds = .12f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="0.2", ClampMax="1.5")) float DrawReadySeconds = .8f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="0.15", ClampMax="0.5")) float MinimumShotInterval = .25f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="0.6", ClampMax="2")) float ChordChainWindow = 1.25f;
 /** First four semitone offsets from C4; the fifth shot closes at C5. Audio only. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Music") FVector4 ChordIntervals = FVector4(0,4,7,11);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Music") FString ChordName = TEXT("C major 7");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Feel", meta=(ClampMin="0.1", ClampMax="0.8")) float ArrowTrailIntensity = .6f;

 // Also callable by accessibility bindings. Normal play uses the real pawn InputComponent.
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StartAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StopAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ToggleAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StartDraw();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ReleaseDraw();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ToggleSequence();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void CancelPhrase();
 void ResolveProjectileHit(AActor* HitActor);

private:
 void BindInput();
 void UnbindInput();
 void FindAimTarget();
 bool CanAct() const;
 void Lane0(); void Lane1(); void Lane2(); void Lane3();
 void Lane(int32 Index);
 void UpdateInputOwnership();
 void UpdateWeaponVisibility();
 void UpdateAimCamera(float Delta);
 void RestoreAimCamera();
 TWeakObjectPtr<ACharacter> Character;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY(Transient) TObjectPtr<UInputComponent> BoundInput;
 TWeakObjectPtr<APlayerController> BoundPlayer;
 TWeakObjectPtr<UMelodiaHybridEncounterComponent> Target;
 TWeakObjectPtr<UMelodiaHybridEncounterComponent> PhraseTarget;
 TWeakObjectPtr<USpringArmComponent> CameraBoom;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Bow;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Harp;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> AttackMontage;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> DrawMontage;
 UPROPERTY(Transient) TObjectPtr<USoundBase> ShotNote;
 UPROPERTY(Transient) TArray<TObjectPtr<USoundBase>> ChordFlourishes;
 bool bAiming = false;
 bool bDrawing = false;
 bool bSuppressingMovement = false;
 bool bSavedOrientToMovement = false;
 bool bSavedControllerYaw = false;
 float SavedArmLength = 0;
 FVector SavedSocketOffset = FVector::ZeroVector;
 double DrawStarted = 0;
 double LastRelease = -100;
 double LastHit = -100;
 double LastChord = -100;
 FString StatusText;
};
