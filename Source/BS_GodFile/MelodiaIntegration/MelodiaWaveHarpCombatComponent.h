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
