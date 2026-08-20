#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaRhythmReactivitySubsystem.generated.h"

class UPrimitiveComponent;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class USoundMix;
class USoundClass;
class FSocket;
class FInternetAddr;

USTRUCT(BlueprintType)
struct FMelodiaRhythmReactivitySignal
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float BeatPulse = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float BeatPhase = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float BPM = 128.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float ComboNormalized = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float CrescendoNormalized = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float CommandEnergy = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") EMelodiaRhythmGrade LastRhythmGrade = EMelodiaRhythmGrade::Miss;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") uint8 RhythmElement = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float CommandPulse = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float BreakPulse = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float VictoryPulse = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float EnemyTension = 0.0f;
	/**
	 * Smoothed "how dangerous right now" register: fast-attacks toward the latest
	 * graded EnemyTension, releases slowly so dread lingers (OMORI held-tension).
	 * Drives the MPC DreadPresence channel -- the cold counterpart to the cozy set.
	 * Presentation-only (Decision 033). Never feeds damage or results.
	 */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float TensionSustain = 0.0f;
	/**
	 * Continuous dissonance register derived from TensionSustain:
	 * 0 = Clear, 1 = Strain, 2 = Rupture. Maps onto the existing
	 * EMelodiaDissonanceTier vocabulary as a smooth value instead of a one-shot
	 * overlap trigger. Presentation-only.
	 */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float DissonanceAmount = 0.0f;

	// --- Cozy MPC expansion (warmth, world reactivity, ambient mood) ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float WarmthGlow = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float PetalFallIntensity = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float DreamRipple = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float EmberDance = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity") float CozyBloom = 0.0f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaRhythmReactivityChanged, const FMelodiaRhythmReactivitySignal&, Signal);

UCLASS()
class MELODIACORE_API UMelodiaRhythmReactivitySubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static const FName AudioCollectionPath;
	static const FName TensionDuckSoundMixPath;
	static const FName AmbienceSoundClassPath;

	UFUNCTION(BlueprintPure, Category="Melodia|Reactivity", meta=(WorldContext="WorldContextObject"))
	static UMelodiaRhythmReactivitySubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override { return true; }

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void NotifyBeat(float InBPM, float InBeatPhase = 0.0f);

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void NotifyCommandResolved(EMelodiaRhythmGrade Grade, float InCommandEnergy, float InComboNormalized, float InCrescendoNormalized, uint8 InRhythmElement);

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void NotifyBreak();

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void NotifyVictory();

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void NotifyEnemyIntent(float Tension = 1.0f);

	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void ResetEncounter();

	/** Direct scalar write into the reactivity MPC (e.g. 'PerfectPop' for the arena feel layer). */
	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void SetScalarOverride(const FName Parameter, const float Value) const { SetMPCScalar(Parameter, Value); }

	UFUNCTION(BlueprintPure, Category="Melodia|Reactivity")
	const FMelodiaRhythmReactivitySignal& GetSignal() const { return Signal; }

	/** Creates a dynamic material instance for every material slot on MeshComponent and registers
	 * it for beat-reactive parameter drives (DreamPulseAmp/Iridescence/TemporalStrength/
	 * ParallaxStrength on M_Master_Toon_Universal-derived instances -- a no-op on slots whose
	 * material doesn't expose those params). Scoped per-actor so only the mesh you opt in pulses
	 * with combat beat, rather than editing the shared master graph for every material project-wide. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity")
	void RegisterReactiveMeshComponent(UPrimitiveComponent* MeshComponent);

	/** Presentation-only CustomDepth/stencil bridge for outline materials. A value of 0 disables
	 * the pass; positive values enable it and select the owner's preset (typically 1/2/3).
	 * This helper does not choose interaction mappings or affect gameplay authority. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Reactivity|Stencil")
	void SetReactiveStencil(UPrimitiveComponent* MeshComponent, int32 StencilValue);

	UPROPERTY(BlueprintAssignable, Category="Melodia|Reactivity")
	FMelodiaRhythmReactivityChanged OnSignalChanged;

private:
	/** Seconds between at-rest publishes, so TouchDesigner can tell a live-but-idle
	 *  Unreal from a dead socket. 0.5s = 2 Hz: cheap, and well under any sane
	 *  receiver timeout. */
	static constexpr float HeartbeatInterval = 0.5f;
	float HeartbeatAccumulator = 0.0f;

	void Publish();
	void SetMPCScalar(const FName Parameter, float Value) const;
	void PublishToReactiveMaterials() const;
	void SendOSCFloat(const FString& Address, float Value) const;
	/** True while any pulse/decay value is still away from rest - Tick only
	 * needs to Publish() while something is actually animating. */
	bool IsSignalAtRest() const;
	/** Presentation-only ambience duck (Decision 033): as TensionSustain rises,
	 * the ambience bed (SCL_Ambience) pulls back via a SoundMix class override.
	 * Silent no-op until the SM_MelodiaTensionDuck SoundMix asset exists. */
	void UpdateTensionAmbienceDuck();

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Reactivity", meta=(AllowPrivateAccess="true"))
	FMelodiaRhythmReactivitySignal Signal;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> ReactiveDynamicMaterials;

	/** Resolved once in Initialize() instead of LoadObject-by-path on every
	 * SetMPCScalar call (was 14x/frame via the unconditional per-tick Publish). */
	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> CachedCollection = nullptr;

	/** Tension ambience duck targets, resolved lazily on first tension. Both are
	 * no-ops when the content does not exist yet (mirrors the MPC no-op policy). */
	UPROPERTY(Transient)
	TObjectPtr<USoundMix> CachedTensionDuckMix = nullptr;
	UPROPERTY(Transient)
	TObjectPtr<USoundClass> CachedAmbienceSoundClass = nullptr;
	/** Last volume written to the class override; starts at 1.0 (no duck) so the
	 * first tension spike is what triggers the first override call. */
	float LastAmbienceDuckVolume = 1.0f;

	FSocket* OscSocket = nullptr;
	TSharedPtr<FInternetAddr> OscTargetAddr;
};
