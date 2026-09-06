#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNeuralHeroMaterialSubsystem.generated.h"

/**
 * Neural Hero-Material Controller — SCAFFOLDED runtime seam (2026-09-02).
 *
 * Hosts the reusable audio-reactive HERO-MATERIAL onnx controller
 * (Tools/Audio/models/hero_material_controller.onnx, built by
 * Tools/Audio/hero_neural_material_controller.py and verified by
 * Tools/Audio/hero_neural_material_verify.py). One small network maps the
 * project's SINGLE audio writer output (MPC_Melodia_Palette: BassIntensity,
 * BeatIntensity, BeatPhase, BeatPulse, BeatTracker) to reusable hero-material
 * params (EmissiveStrength, EmissiveTint, SubsurfaceScatter, Displacement,
 * SpecularBoost) so ANY hero asset — Crystal Harp Grove crystal, FarawayMother
 * fabric, Sea Above water-glass — shares one audio->material brain.
 *
 * Guardrails (mirror UMelodiaCymaticsSubsystem): READ-ONLY consumer of the audio
 * MPC; does NOT write MPC_Melodia_Palette and does NOT own audio. It writes the
 * COMPUTED hero params to a SEPARATE, subsystem-owned material parameter
 * collection (MPC_Hero_Material) that hero materials sample. Single MPC *audio*
 * writer stays UMelodiaAudioReactivePresentationSubsystem.
 *
 * STATUS: SCAFFOLD. Requires a closed-editor Build.bat pass. The onnx + generator
 * + verifier are real and verified; the NNERuntimeORT inference call is a marked
 * TODO seam (see RunInference) pending UE 5.8 API confirmation. Without a built
 * binary, the subsystem forwards the packed MPC features as a documented fallback.
 */
UCLASS()
class BS_GODFILE_API UMelodiaNeuralHeroMaterialSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Computed hero-material parameters (0..1), refreshed on the audio tick. */
	UFUNCTION(BlueprintPure, Category = "Melodia|NeuralHero")
	void GetHeroParameters(float& OutEmissiveStrength, float& OutEmissiveTint,
						   float& OutSubsurfaceScatter, float& OutDisplacement,
						   float& OutSpecularBoost) const;

	/** Packed MPC audio feature vector feeding the network (order = controller.FEATURES). */
	UFUNCTION(BlueprintPure, Category = "Melodia|NeuralHero")
	void GetAudioFeatures(float& OutBassIntensity, float& OutBeatIntensity,
						  float& OutBeatPhase, float& OutBeatPulse,
						  float& OutBeatTracker) const;

	/** Read-only charter: never writes the audio MPC, never owns audio truth. */
	UFUNCTION(BlueprintPure, Category = "Melodia|NeuralHero")
	bool IsReadOnlyByContract() const { return true; }

private:
	bool TickInference(float DeltaTime);
	void RefreshFromMPC();
	void RunInference();          // TODO: wire NNERuntimeORT (closed-editor build) here.

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> AudioCollection;  // read-only reference

	// Packed input (order matches hero_neural_material_controller.FEATURES)
	float BassIntensity = 0.f;
	float BeatIntensity = 0.f;
	float BeatPhase = 0.f;
	float BeatPulse = 0.f;
	float BeatTracker = 0.f;

	// Network output (order matches controller.OUTPUTS)
	float EmissiveStrength = 0.f;
	float EmissiveTint = 0.f;
	float SubsurfaceScatter = 0.f;
	float Displacement = 0.f;
	float SpecularBoost = 0.f;

	FTSTicker::FDelegateHandle TickerHandle;
};