// Battle arena actor ΓÇö spawns enemy mesh, owns combat state, manages camera during encounters.
// Replaces the 2.1MB BP_BattleController from the JRPG template.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaCombatStateComponent.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaEnemyDefinition.h"
#include "MelodiaBattleArena.generated.h"

class UStaticMeshComponent;
class USceneComponent;
class USpringArmComponent;
class UCameraComponent;
class UCameraShakeBase;

/** Which battle beat the camera is framing. Maps 1:1 from EMelodiaBattlePhase. */
UENUM(BlueprintType)
enum class EMelodiaArenaCameraPhase : uint8
{
	Command,
	Execution,
	EnemyTurn,
	Ult,
	Break
};

USTRUCT(BlueprintType)
struct FMelodiaCameraFraming
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	FVector Offset = FVector(-400.0f, 200.0f, 150.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	FRotator Rotation = FRotator(-15.0f, -25.0f, 0.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	float ArmLength = 450.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	float FOV = 32.0f;
};

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second battle stack). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API AMelodiaBattleArena : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaBattleArena();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena")
	TObjectPtr<USceneComponent> ArenaRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena")
	TObjectPtr<UStaticMeshComponent> EnemyMeshComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena")
	TObjectPtr<UMelodiaCombatStateComponent> CombatState;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena")
	TObjectPtr<UMelodiaRhythmExecutionComponent> RhythmExecution;

	/** Offset for the enemy mesh relative to the arena root. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	FVector EnemySpawnOffset = FVector(0.0f, 0.0f, 50.0f);

	/** Camera offset during battle (relative to arena center). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	FVector BattleCameraOffset = FVector(-400.0f, 200.0f, 150.0f);

	/** Camera rotation during battle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena")
	FRotator BattleCameraRotation = FRotator(-15.0f, -25.0f, 0.0f);

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Arena")
	FMelodiaEnemyDef ActiveEnemy;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Arena")
	bool bArenaActive = false;

	/** Set up the arena for a specific enemy definition. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena")
	void SetupArena(const FMelodiaEnemyDef& EnemyDef);

	/** Activate the arena ΓÇö show enemy, start battle camera. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena")
	void ActivateArena();

	/** Deactivate the arena ΓÇö hide enemy, restore camera. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena")
	void DeactivateArena();

	/** Get this actor as a valid battle controller for the BattleSession. */
	UFUNCTION(BlueprintPure, Category="Melodia|Arena")
	AActor* AsBattleController() { return this; }

	// --- Battle camera (SpringArm + Camera on the arena; view target while active) ---

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena|Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Arena|Camera")
	TObjectPtr<UCameraComponent> BattleCamera;

	/** Per-phase framing; missing phases fall back to Command. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena|Camera")
	TMap<EMelodiaArenaCameraPhase, FMelodiaCameraFraming> CameraFramings;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Arena|Camera")
	EMelodiaArenaCameraPhase CameraPhase = EMelodiaArenaCameraPhase::Command;

	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Camera")
	void SetCameraPhase(EMelodiaArenaCameraPhase Phase, float BlendTime = 0.6f);

	/** Short push-in used on weakness break; auto-restores on the next phase change. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Camera")
	void PlayBreakDollyIn(float Duration = 0.8f);

	// --- Feel primitives (presentation-host duties; no gameplay math) ---

	/** Global time-dilation hitstop. Strongest active request wins; re-triggers gated to 0.12s. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Feel")
	void Hitstop(float TimeScale = 0.05f, float DurationSec = 0.08f);

	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Feel")
	void PlayShake(float Scale = 1.0f);

	/** Eased global dilation toward Target over Duration (real-time), then back to 1. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Feel")
	void SetTimeDilation(float Target, float DurationSec);

	/** Radial-blur/brightness pop via the reactivity MPC ('PerfectPop' scalar). */
	UFUNCTION(BlueprintCallable, Category="Melodia|Arena|Feel")
	void PostProcessPop(float Intensity = 1.0f);

	/** Optional shake class; when unset a small rotational shake is improvised. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Arena|Feel")
	TSubclassOf<UCameraShakeBase> ShakeClass;

protected:
	virtual void BeginPlay() override;

	/** Maps battle-session phases onto camera framings while the arena is active. */
	UFUNCTION()
	void HandleBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase);

private:
	FVector SavedCameraLocation;
	FRotator SavedCameraRotation;
	bool bCameraSaved = false;

	// camera interp state
	FMelodiaCameraFraming CurrentFraming;
	FMelodiaCameraFraming TargetFraming;
	float CameraBlendSpeed = 1.6f;
	bool bDollyActive = false;
	float DollyTimeLeft = 0.0f;

	// hitstop / dilation state
	float HitstopTimeLeft = 0.0f;
	float LastHitstopRealTime = -1.0f;
	float DilationTarget = 1.0f;
	float DilationTimeLeft = 0.0f;
	float PopLevel = 0.0f;

	void ApplyFraming(const FMelodiaCameraFraming& Framing);
	FMelodiaCameraFraming FramingFor(EMelodiaArenaCameraPhase Phase) const;
};
