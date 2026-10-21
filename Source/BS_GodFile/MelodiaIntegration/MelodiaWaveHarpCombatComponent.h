#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Components/ActorComponent.h"
#include "ProceduralMeshComponent.h"
#include "MelodiaWaveHarpCombatComponent.generated.h"

class UAnimNotify_MelodiaScytheHit;

/** Fires at the scythe's forward peak. The hit is resolved on the following frame. */
UCLASS()
class BS_GODFILE_API UAnimNotify_MelodiaScytheHit : public UAnimNotify
{
 GENERATED_BODY()
public:
 virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
};

class ACharacter;
class APlayerController;
class UInputComponent;
class UStaticMeshComponent;
class UAnimMontage;
class USoundBase;
class USpringArmComponent;
class UMelodiaHybridEncounterComponent;
class UNiagaraSystem;
class UAnimSequence;
class USkeletalMesh;
class USkeletalMeshComponent;

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
 /** Magical arrow trail. Swap this asset to retune the arrow FX; the arrow only reads it at launch. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|FX") TSoftObjectPtr<UNiagaraSystem> ArrowTrailSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Weapons/WaveHarp/NS_WaveHarp_ArrowTrail.NS_WaveHarp_ArrowTrail")));
 /** Burst and ripple where a resolved note lands; an on-beat release plays them at full scale. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|FX") TSoftObjectPtr<UNiagaraSystem> HitBurstSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_ImpactBurst.NS_Melusina_ImpactBurst")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|FX") TSoftObjectPtr<UNiagaraSystem> HitRippleSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_Ripple.NS_Melusina_Ripple")));

 /** Both instruments are held in the authored hand-prop socket, so they follow the hand and arm instead of the world. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Presentation") FName InstrumentSocket = TEXT("S_Instrument_L");
 /** Offset of the bow from InstrumentSocket (rotation, location, scale). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Presentation") FTransform BowGrip = FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(.9f));
 /** Offset of the harp (astrolabe form) scale; its position is AstrolabeOffset while it floats. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Presentation") FTransform HarpGrip = FTransform(FRotator::ZeroRotator, FVector::ZeroVector, FVector(.9f));

 /** LMB is a caster basic attack; RMB owns the separate charged archery shot. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Charge", meta=(ClampMin="0.15", ClampMax="0.8")) float ChargeThresholdSeconds = .3f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Charge", meta=(ClampMin="0.1", ClampMax="0.8")) float ChargedTrailIntensity = .8f;
 /** True for the arrow just launched when it came from a charged shot. Presentation only; never scales damage. */
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Charge") bool bShotIsCharged = false;

 /** Anim slot the cast/charge clips play in (the canonical ABP slot). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") FName PoseSlot = TEXT("UpperBody");
 /** Caster stance held while aiming, and the basic-attack shot (LMB tap). */
 // Doctor chain repair retains measured arm lengths and per-frame retarget rotation.
 // Cast root-height/contact acceptance remains a separate gate; see the measured evidence receipt.
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") TSoftObjectPtr<UAnimSequence> CastStanceAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/ShinbiDoctor_20261007/A_Shin_Idle.A_Shin_Idle")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") TSoftObjectPtr<UAnimSequence> CastShootAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/ShinbiDoctor_20261007/A_Shin_Cast.A_Shin_Cast")));
 /** Charged archery shot (RMB held): draw, hold loop, fire. Canon set = arm-corrected copies (see MELUSINA_RUNTIME_CANON_2026-10-05). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") TSoftObjectPtr<UAnimSequence> ChargeDrawAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/SparrowDoctor_20261007/A_Spar_Mel_RMB_Drawback.A_Spar_Mel_RMB_Drawback")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") TSoftObjectPtr<UAnimSequence> ChargeHoldAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/SparrowDoctor_20261007/A_Spar_Mel_RMB_Loop.A_Spar_Mel_RMB_Loop")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Animation") TSoftObjectPtr<UAnimSequence> ChargeFireAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/SparrowDoctor_20261007/A_Spar_Mel_RMB_Fire.A_Spar_Mel_RMB_Fire")));

 /** Harp-to-bow-to-scythe instrument. If this skeletal mesh exists it is driven by the shape keys below; otherwise the static harp/bow blend is used. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") TSoftObjectPtr<USkeletalMesh> InstrumentMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Weapons/WaveHarp/SK_ME_WaveHarp_Scythe.SK_ME_WaveHarp_Scythe")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphBowDeployment = TEXT("Bow_Deployment");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphFlexDraw = TEXT("Flex_Draw");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphBowstringDraw = TEXT("Draw");
 /** 3rd Harmonic Form: Carillon Chime-Scythe morphs and melee trace parameters. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphScytheDeployment = TEXT("Scythe_Deployment");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphScytheChord = TEXT("Scythe_Chord_Tension");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphScytheBell = TEXT("Scythe_Bell_Swing");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee") TSoftObjectPtr<UAnimSequence> MeleeSwingAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/ShinbiDoctor_20261007/A_Shin_Cast.A_Shin_Cast")));
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee", meta=(ClampMin="100.0", ClampMax="600.0")) float MeleeReachCm = 320.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee", meta=(ClampMin="0.2", ClampMax="2.5")) float ScytheFormHoldSeconds = 1.15f;
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Melee") int32 MeleeSwings = 0;
 /** Fraction of the swing montage where the blade is farthest forward. The hit notify is placed here. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee", meta=(ClampMin="0.15", ClampMax="0.85")) float ScytheHitFraction = 0.42f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee") FName ScytheBladeStartSocket = TEXT("Scythe_BladeStart");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee") FName ScytheBladeTipSocket = TEXT("Scythe_BladeTip");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee") FName LockWarpTarget = TEXT("ScytheStep");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee") TSoftObjectPtr<UAnimSequence> LockStepAnim = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Walk_Mocap_RootX_SeamFix.A_Melusina_Walk_Mocap_RootX_SeamFix")));
 /** Scythe chain only. Arrow chords keep ComboStep. */
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Melee") int32 ScytheStep = 0;
 /** Seconds for the harp to open into the bow (and back). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument", meta=(ClampMin="0.05", ClampMax="1.0")) float TransformSeconds = .22f;
 /** How long the bow form is held after a charged release before the instrument folds back. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument", meta=(ClampMin="0.1", ClampMax="2.0")) float BowFormHoldSeconds = .7f;
 /** Floating astrolabe form: offset from the character (forward, right, up), spin and bob. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FVector AstrolabeOffset = FVector(55.f, -35.f, 25.f);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") float AstrolabeSpinDegPerSecond = 24.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") float AstrolabeBobCm = 3.f;

 // Also callable by accessibility bindings. Normal play uses the real pawn InputComponent.
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StartAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StopAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ToggleAim();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void StartDraw();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ReleaseDraw();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ToggleSequence();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void CancelPhrase();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void TriggerScytheMelee();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void ToggleLock();
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp") void RegisterLaneHit(int32 Index);
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") bool IsCombatLocked() const { return bCombatLocked; }
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") int32 GetScytheStep() const { return ScytheStep; }
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp") float GetScytheAlpha() const { return ScytheAlpha; }
 void ResolveProjectileHit(AActor* HitActor, float ReleaseBeatPhase);
 void ResolveMeleeHit(AActor* HitActor, float SwingBeatPhase);
 void CommitScytheHit();

private:
 void BindInput();
 void UnbindInput();
 void FindAimTarget();
 bool CanAct() const;
 void Lane0(); void Lane1(); void Lane2(); void Lane3();
 void Lane(int32 Index);
 void UpdateInputOwnership();
 void UpdateInstruments(float Delta);
 void UpdatePose(double Now);
 void BeginCharge(double Now);
 void PlayPose(const TSoftObjectPtr<UAnimSequence>& Clip, bool bLoop);
 void StopPose();
 void UpdateAimCamera(float Delta);
 void RestoreAimCamera();
 void UpdateSequenceFeel(float Delta);
 void UpdateLockTurn(float Delta);
 void ResolvePendingScytheHit();
 void BeginLockStep(AActor* LockActor);
 void PlayScytheMontage();
 void UpdateScytheRibbon();
 void EnsureCameraBoom();
 AActor* FindMeleeActor() const;
 float SampleBeatPhase() const;
 UAnimMontage* MakeSlotMontage(UAnimSequence* Seq, float BlendOut) const;
 void SyncLockedTarget();
 TWeakObjectPtr<ACharacter> Character;
 TWeakObjectPtr<APlayerController> Player;
 UPROPERTY(Transient) TObjectPtr<UInputComponent> BoundInput;
 TWeakObjectPtr<APlayerController> BoundPlayer;
 TWeakObjectPtr<UMelodiaHybridEncounterComponent> Target;
 TWeakObjectPtr<UMelodiaHybridEncounterComponent> PhraseTarget;
 TWeakObjectPtr<USpringArmComponent> CameraBoom;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Bow;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Harp;
 UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> Instrument;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> PoseMontage;
 enum class EPose : uint8 { None, Stance, Draw, Hold, Fire, CastShoot, ScytheSwing };
 EPose Pose = EPose::None;
 bool bCharging = false;
 double ChargeBegan = 0;
 double LastChargedRelease = -100;
 double LastMeleeSwing = -100;
 double LastScytheChain = -100;
 float FormAlpha = 0.f;
 float ScytheAlpha = 0.f;
 float ScytheMontageFraction = -1.f;
 float ScytheSwingBeatPhase = -1.f;
 float SequenceDampAlpha = 0.f;
 float SavedMaxWalkSpeed = 0.f;
 bool bHaveSavedWalkSpeed = false;
 bool bCombatLocked = false;
 bool bScytheHitArmed = false;
 bool bScytheResolveQueued = false;
 double ScytheResolveAfterTime = 0;
 int32 ScytheResolveStep = 0;
 int32 ScytheResolveSwings = 0;
 TWeakObjectPtr<AActor> ScytheResolveTarget;
 TEnumAsByte<ERootMotionMode::Type> SavedRootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;
 bool bRootMotionOverridden = false;
 UPROPERTY(Transient) TObjectPtr<UProceduralMeshComponent> ScytheRibbon;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> WarpMontage;
 bool bRibbonSection = false;
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
