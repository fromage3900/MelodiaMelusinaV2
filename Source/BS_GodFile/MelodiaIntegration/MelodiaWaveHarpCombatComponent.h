#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Components/ActorComponent.h"
#include "ProceduralMeshComponent.h"
#include "MelodiaWaterChorus.h"
#include "MelodiaWaveHarpCombatComponent.generated.h"

class UAnimNotify_MelodiaScytheHit;

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
class UStaticMesh;

/** Fires at the scythe's forward peak. The hit is resolved on the following frame. */
UCLASS()
class BS_GODFILE_API UAnimNotify_MelodiaScytheHit : public UAnimNotify
{
 GENERATED_BODY()
public:
 virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
};

/**
 * The three forms of the WaveHarp.
 *
 * Form 0 HARP is the floating astrolabe of the caster, Form 1 BOW is the pinned archery
 * stance, Form 2 CARILLON is the sanctioned MELEE form (the crescent blade).
 *
 * The caster/archer hybrid stays intact: charging inside Form 0 or 1 still morphs
 * the astrolabe into the bow for the charged shot and folds it back afterwards.
 * The form is a separate axis from that automatic blend.
 */
UENUM(BlueprintType)
enum class EMelodiaWaveHarpForm : uint8
{
 Harp UMETA(DisplayName = "Form 0 - HARP"),
 Bow UMETA(DisplayName = "Form 1 - BOW"),
 CarillonMelee UMETA(DisplayName = "Form 2 - CARILLON (melee)")
};

/**
 * The stages of a form change, in the anime-JRPG register: a held beat, a covered
 * transformation, and an aftermath that carries the weight. The middle is covered so
 * the head can change without a pop; the weight lands in the aftermath.
 */
UENUM(BlueprintType)
enum class EMelodiaWaveHarpFormStage : uint8
{
 Idle UMETA(DisplayName = "IDLE"),
 Prepare UMETA(DisplayName = "PREPARE"),
 Transform UMETA(DisplayName = "TRANSFORM"),
 Aftermath UMETA(DisplayName = "AFTERMATH")
};

/** Fired on every stage change of a form change. UMelodiaMagicalTransformComponent (Wardrobe) listens, so the form change and the costume flourish are one beat, not two. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaWaveHarpFormStageChanged, EMelodiaWaveHarpFormStage, Stage, EMelodiaWaveHarpForm, TargetForm);

/**
 * One beat of the transformation's look: which EXISTING system, at which socket, at
 * which scale, with which user parameters, at which point in the stage.
 *
 * This is DATA, not code: the whole look of the transformation is then editable
 * without touching C++. No new Niagara graph is authored by this lane.
 */
USTRUCT(BlueprintType)
struct FMelodiaWaveHarpVfxBeat
{
 GENERATED_BODY()

 /** The stage this beat belongs to. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 EMelodiaWaveHarpFormStage Stage = EMelodiaWaveHarpFormStage::Transform;

 /** An existing system. The lane authors no new graphs. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TSoftObjectPtr<UNiagaraSystem> System;

 /** The socket the beat is played at. Empty = the character's head. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 FName Socket;

 /** The scale of the spawned system. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 float Scale = 1.f;

 /** User parameters written onto the spawned system. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TMap<FName, float> FloatParameters;

 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TMap<FName, FLinearColor> ColorParameters;

 /** Where in the stage this beat fires, 0..1. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 float Offset = 0.f;
};

/**
 * Measured socket positions of the Carillon wand, in centimetres.
 *
 * Source of truth: Saved/Audit/waveharp/ue_ready/waveharp_wand_bake_manifest.json
 * (the bake that produced SM_MEL_Wand_Carillon_Caster / _Melee).
 *
 * IMPORTANT - these are LOCAL OFFSETS, never skeleton sockets. the Blender FBX
 * armature export is unit-path-unsafe in UE: the exported bones land roughly
 * 90-100x too far out, which is what turned the melee trace into a 42 m sweep
 * (defect D8). The shared sockets are wand-local; the three blade sockets are
 * HEAD-LOCAL, because the crescent was modelled into the own frame of the head.
 */
USTRUCT(BlueprintType)
struct FMelodiaWaveHarpSocketOffsets
{
 GENERATED_BODY()

 /** Wand-local, cm. The grip point the hand holds. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector BowGrip = FVector(0.0, 0.0, 13.0);
 /** Wand-local, cm. Where the head is seated on the shaft. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector HeadSeat = FVector(0.0, 0.0, 105.0);
 /** Wand-local, cm. The projection point of the halo (the top of the head). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector CymaticProjection = FVector(0.0, 0.0, 121.0);
 /** Head-local, cm. The root of the crescent. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector BladeStart = FVector(21.9, 0.0, 17.0);
 /** Head-local, cm. The belly of the crescent. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector BladeMid = FVector(37.08, 0.0, -0.52);
 /** Head-local, cm. The tip of the crescent. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp") FVector BladeTip = FVector(32.77, 0.0, -22.51);

 /** Length of the crescent, start to tip, in cm (about 41 cm on the shipped bake). */
 float GetBladeLengthCm() const { return FVector::Distance(BladeStart, BladeTip); }
 /** Widest swing radius of the crescent from the shaft axis, in cm. */
 float GetBladeRadiusCm() const { return FMath::Max3(FMath::Abs(BladeStart.X), FMath::Abs(BladeMid.X), FMath::Abs(BladeTip.X)); }
};


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
 /**
  * Compose BowGrip in the character's frame so the hold follows her hand and arm.
  *
  * Default false keeps the shipped world-space behaviour: the grip offset is composed
  * with the socket's WORLD transform, so a world-fixed grip drifts as she turns and can
  * only be right at one heading. Measured against a 170 cm Melusina proxy, the shipped
  * near-horizontal grip drives the weapon 7.01 cm THROUGH the torso; a near-vertical
  * hold clears the torso by +10.5 cm and the head by +28.6..+31.7 cm with no mesh change.
  *
  * Turning this on changes the MEANING of BowGrip: write the character-space grip.
  * Solver + data writer: Content/Python/waveharp_hold_fix.py
  * (maths unit-tested by Content/Python/Tests/test_waveharp_hold_fix.py).
  */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Presentation") bool bGripFollowsCharacter = true;
 /**
  * Derive the hold offset from the live pose instead of a fixed authored rotation.
  *
  * The instrument socket lives on the hand bone, so a fixed offset can only be right at
  * one pose - and the authored near-horizontal offset drives the weapon 7.01 cm THROUGH
  * the torso (measured against a 170 cm Melusina proxy). The calibration waits for the
  * pose to settle, then solves the offset that stands the instrument up in the BODY's
  * frame: weapon +Z -> body up, weapon +Y -> body forward, so the bow's belly still
  * faces the aim direction and the scythe's blade still sweeps forward.
  *
  * Only meaningful with bGripFollowsCharacter enabled. Re-derivable at runtime with
  * CalibrateHold() or the console command Melodia.WaveHarp.RecalibrateHold.
  */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Presentation") bool bAutoCalibrateHold = true;
 /** Re-derive the hold offset from the current (settled) pose. */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Presentation") void CalibrateHold();
 /** Runtime state: the hold offset has been derived from a settled pose. */
 UPROPERTY(Transient) bool bHoldCalibrated = false;
 /** Last measured socket rotation, used to detect a settled pose. */
 UPROPERTY(Transient) FQuat LastSocketRotation = FQuat::Identity;
 /** Consecutive ticks the socket rotation has stayed still. */
 UPROPERTY(Transient) int32 PoseStabilityTicks = 0;
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

 // ---------------------------------------------------------------------------
 // THE FORM: one type, one entry point.
 //
 // SetForm is the ONLY writer of CurrentForm. Nothing else may swap the head,
 // change the form or drive the transition - the f90 FormHandoff notify confirms
 // a transition, it never starts one. This is the same single-writer rule the
 // hybrid combat canon already applies to damage, resonance and the HUD.
 // ---------------------------------------------------------------------------

 /** The committed form. Replicated: every peer must agree on which head is live. */
 UPROPERTY(ReplicatedUsing = OnRep_CurrentForm, BlueprintReadOnly, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpForm CurrentForm = EMelodiaWaveHarpForm::Harp;

 /** The form a transition is heading to. It becomes CurrentForm when the transition lands. */
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpForm PendingForm = EMelodiaWaveHarpForm::Harp;

 /** Request a form. Returns false when the request was refused (already there, locked, in a phrase). */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 bool SetForm(EMelodiaWaveHarpForm NewForm);

 /** Advance the ring: HARP -> BOW -> CARILLON -> HARP. */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 void CycleForm();

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpForm GetForm() const { return CurrentForm; }

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsFormTransitionActive() const { return bFormTransitionActive; }

 UPROPERTY(BlueprintAssignable, Category="Melodia|WaveHarp|Form")
 FMelodiaWaveHarpFormStageChanged OnFormStageChanged;

 /** The stage of the form change: IDLE, PREPARE, TRANSFORM or AFTERMATH. */
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 EMelodiaWaveHarpFormStage GetFormStage() const { return FormStage; }

 /** Turn the world's water chorus on or off at runtime (the surfaces have to exist). */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 void SetWaterChorusEnabled(bool bEnabled);

 /** Turn the refined wand (shaft + Carillon head) on or off at runtime, so the head
 *  swap can be A/B-ed against the shipped skeletal path without touching the Blueprint. */
 UFUNCTION(BlueprintCallable, Category="Melodia|WaveHarp|Form")
 void SetHeadSwapEnabled(bool bEnabled);

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsWaterChorusEnabled() const { return bEnableWaterChorus; }

 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 bool IsHeadSwapEnabled() const { return bUseHeadSwap; }

 /** 0..1 progress of the running transition, eased. 1 when no transition is running. */
 UFUNCTION(BlueprintPure, Category="Melodia|WaveHarp|Form")
 float GetFormTransitionAlpha() const { return FormTransitionAlpha; }

 /** 0..1 weight of the crescent form (1 = the melee head is live). */
 float GetMeleeFormWeight() const;

 // ---- the testable core. These are the contract C10 asserts; they carry no state
 // ---- so they can be proved without a world, in a headless automation run.

 /** The ring: the next form in HARP -> BOW -> CARILLON -> HARP. */
 static EMelodiaWaveHarpForm GetNextForm(EMelodiaWaveHarpForm Form);

 /** The eased form transition (smoothstep). The old 0.22 s linear pop is gone. */
 static float EaseFormTransition(float T);

 /** 0..1 weight of the crescent while a form change runs. */
 static float ComputeMeleeFormWeight(EMelodiaWaveHarpForm From, EMelodiaWaveHarpForm To, float Alpha);

 /** The delay that lands the transition's HANDOFF on the next downbeat. */
 static float ComputeBeatLockDelay(float SecondsToNextBeat, float TransitionSeconds);

 /** The attack gate during the flourish: the attack is refused and buffered, so the
  *  transformation never eats an input. */
 static bool AcceptAttackDuringTransition(bool bTransitionActive, bool bBufferEnabled, bool& bOutBuffered);

 /** The world start and tip of the crescent, from the measured head-local offsets.
 *  This is the geometry the melee actually sweeps: a ~41 cm blade on a ~37 cm radius. */
 bool GetBladeWorldPoints(FVector& OutStart, FVector& OutEnd) const;

 /** How long a form change takes, in seconds. The authored henshin clip is 60 eased
 *  frames; until that clip is baked this timer drives a smoothstep, so the change
 *  is never the old 0.22 s linear pop (defect D3). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form", meta=(ClampMin="0.2", ClampMax="4.0"))
 float FormTransitionSeconds = 1.0f;

 /** When set and playing, the own curves of the montage drive the transition. The authored
 *  performance is baked into a montage with FormAlpha / ScytheAlpha curves; when it
 *  lands this component reads them instead of its timer. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UAnimMontage> FormTransitionMontage;

 /** Curve read on the form transition montage. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 FName FormAlphaCurve = TEXT("FormAlpha");

 /** The crescent unfold curve on the form transition montage. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 FName ScytheAlphaCurve = TEXT("ScytheAlpha");

 /** Head-swap topology, owner-confirmed 2026-10-21: a form change swaps the HEAD.
 *  OFF by default because the Carillon art pass has not landed; the shipped
 *  skeletal path keeps working untouched until the owner flips it. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 bool bUseHeadSwap = false;

 /** The caster wand (shaft + Carillon head). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UStaticMesh> WandCasterMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Weapons/WaveHarp/SM_MEL_Wand_Carillon_Caster.SM_MEL_Wand_Carillon_Caster")));

 /** The melee wand (the same shaft, the crescent head). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UStaticMesh> WandMeleeMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Melodia/Characters/Melusina/Weapons/WaveHarp/SM_MEL_Wand_Carillon_Melee.SM_MEL_Wand_Carillon_Melee")));

 /** The idle shimmer morphs. They are driven by the MUSIC CLOCK, never by a
 *  frame-based sine: the instrument has to breathe with the music, not with the
 *  frame rate (defect D4). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerPluck = TEXT("Pluck");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerVibrate = TEXT("Vibrate_Overtone");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerSwayPos = TEXT("Sway_Pos");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerSwayNeg = TEXT("Sway_Neg");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerResonance = TEXT("Resonance_Breathe");

 /** How far the shimmer moves, 0..1. The shimmer is a living surface, not a wobble. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument", meta=(ClampMin="0.0", ClampMax="1.0"))
 float ShimmerStrength = 0.35f;

 /** The measured socket positions (wand-local and head-local, cm). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 FMelodiaWaveHarpSocketOffsets Sockets;

 /** Radius of the melee sweep, cm. The crescent is a thin blade; the old 85 cm
 *  sphere could reach a target the blade never touched. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee", meta=(ClampMin="1.0", ClampMax="60.0"))
 float MeleeSweepRadiusCm = 18.f;

 /** How far past the blade tip the sweep continues, cm. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Melee", meta=(ClampMin="0.0", ClampMax="100.0"))
 float MeleeForwardExtensionCm = 25.f;

 /** Remember the attack of the player across the form change and fire it the moment the
 *  flourish lands. The transformation must never eat an input. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 bool bBufferAttacksDuringFormChange = true;

 /** Camera push during the flourish, cm of arm length. Presentation only. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form", meta=(ClampMin="0.0", ClampMax="120.0"))
 float FormCameraPushCm = 35.f;

 /** The existing system that covers the head swap. Existing assets only: no new
 *  Niagara graph is authored for the transformation. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Form")
 TSoftObjectPtr<UNiagaraSystem> FormTransformSigilSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_StarPop.NS_Melusina_StarPop")));

 /** The transformation's visual beats, by stage. Data, not code: the look of the
 *  change is editable without touching the component. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx")
 TArray<FMelodiaWaveHarpVfxBeat> FormVfxBeats;

 /** The stage the form change is in right now. */
 UPROPERTY(BlueprintReadOnly, Category="Melodia|WaveHarp|Vfx")
 EMelodiaWaveHarpFormStage FormStage = EMelodiaWaveHarpFormStage::Idle;

 /** The water chorus: the world's water sings with the beat, and Melusina's hair
 *  globulates on it. OFF by default; the owner turns it on once the surfaces are
 *  placed in the level. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Chorus")
 bool bEnableWaterChorus = false;

 /** The aftermath length, seconds. The weight lands here, not in the swap. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Vfx", meta=(ClampMin="0.0", ClampMax="5.0"))
 float FormAftermathSeconds = 0.9f;

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

 // ---- form internals -------------------------------------------------------
 /** The one writer path. Applies the committed form to the head and the morphs.
 *  bBurst is true only at the transition's midpoint, where the water transform covers
 *  the head swap - the landing must not burst a second time. */
 void ApplyFormVisuals(bool bBurst = false);
 /** Advances the transition timer and lands the form when it completes. */
 void UpdateFormTransition(float Delta);
 /** Places the wand mesh and swaps the head at the midpoint of the transition. */
 void UpdateWandPresentation();
 /** Seconds until the next beat boundary; 0 when there is no music (act at once). */
 float SecondsUntilNextBeat() const;
 /** The idle shimmer, driven by the music clock (defect D4). */
 void UpdateIdleShimmer();
 /** Set a morph only if the mesh actually has it. */
 void SetMorphIfPresent(FName Morph, float Value);
 /** The screen-size budget: 1 close up, smaller across the lane. */
 float GetEffectScale() const;
 /** The camera push for the flourish. */
 void ApplyFormCameraPush(bool bPush);
 /** Fire the beats of a stage that the transition has just entered. */
 void PlayFormVfxBeats(EMelodiaWaveHarpFormStage Stage);
 /** The world position a beat is played at: its socket, or the character's head. */
 FVector GetFormVfxLocation(const FMelodiaWaveHarpVfxBeat& Beat) const;
 /** The existing-system flourish that covers the head swap. */
 void PlayFormTransformFlourish();
 UFUNCTION()
 void OnRep_CurrentForm();
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
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
 /** The weight of the crescent driven by the melee swing montage (the shipped path). */
 float ScytheMontageAlpha = 0.f;
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
 /** The refined wand (shaft + head) used by the head-swap topology. */
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Wand;
 bool bWandIsMelee = false;
 bool bFormTransitionActive = false;
 double FormTransitionStart = 0;
 double FormTransitionEnd = 0;
 float FormTransitionAlpha = 1.f;
 EMelodiaWaveHarpForm FormTransitionFrom = EMelodiaWaveHarpForm::Harp;
 bool bHeadSwappedThisTransition = false;
 /** An attack the player pressed during the flourish. */
 bool bBufferedAttack = false;
 /** The stage the transition entered, used to fire each stage's beats exactly once. */
 EMelodiaWaveHarpFormStage LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
 /** The world's water chorus. A plain C++ class: no reflected surface, no new owner
  *  on an existing surface - it READS the cymatics MPC and writes nothing. */
 FMelodiaWaterChorus WaterChorus;
 double AftermathUntil = 0;
 bool bBufferedMelee = false;
 float SavedFormCameraArmLength = 0.f;
 bool bHaveSavedFormCameraArm = false;
 /** The beat phase sampled at the ACTION (the start of the swing), never at impact. */
 float ScytheActionBeatPhase = -1.f;
 /** One solved hold per form: the heads sit at different points on the shaft. */
 UPROPERTY(Transient) TMap<EMelodiaWaveHarpForm, FTransform> FormGrips;
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
