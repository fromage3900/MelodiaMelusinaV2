// MelodiaNeuralHeroMaterialSubsystem.cpp — SCAFFOLDED (needs closed-editor build).
#include "MelodiaNeuralHeroMaterialSubsystem.h"

#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Engine/World.h" // UWorld::GetParameterCollectionInstance

#define LOCTEXT_NAMESPACE "MelodiaNeuralHeroMaterial"

void UMelodiaNeuralHeroMaterialSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Read-only handle to the SINGLE audio writer's MPC. Never written by us.
	AudioCollection = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Melodia/MPC_Melodia_Palette.MPC_Melodia_Palette"));

	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaNeuralHeroMaterialSubsystem::TickInference),
		0.0f);
}

void UMelodiaNeuralHeroMaterialSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
	}
	Super::Deinitialize();
}

bool UMelodiaNeuralHeroMaterialSubsystem::TickInference(float DeltaTime)
{
	RefreshFromMPC();
	RunInference();
	return true; // keep ticking
}

void UMelodiaNeuralHeroMaterialSubsystem::RefreshFromMPC()
{
	if (!AudioCollection)
	{
		return;
	}
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	UMaterialParameterCollectionInstance* Instance =
		World->GetParameterCollectionInstance(AudioCollection);
	if (!Instance)
	{
		return;
	}
	// Read-only — mirrors how UMelodiaCymaticsSubsystem consumes the palette.
	Instance->GetScalarParameterValue(TEXT("BassIntensity"), BassIntensity);
	Instance->GetScalarParameterValue(TEXT("BeatIntensity"), BeatIntensity);
	Instance->GetScalarParameterValue(TEXT("BeatPhase"), BeatPhase);
	Instance->GetScalarParameterValue(TEXT("BeatPulse"), BeatPulse);

	// BeatTracker is NOT a declared parameter on MPC_Melodia_Palette (verified against the
	// asset's 51 scalars, 2026-09-05). GetScalarParameterValue on an undeclared name leaves
	// the out-param untouched, so this field held 0 every frame and fed a permanently-zero
	// 5th element into the inference tensor documented in RunInference.
	//
	// The audio writer's own comment names the intent -- "BeatTracker ... latch = current
	// beat pulse" (MelodiaAudioReactivePresentationSubsystem.cpp) -- and it publishes that
	// latch as BeatPulse, which IS declared. So the value was always available under the
	// name that exists; only the lookup name was wrong. Sourcing it directly removes the
	// dependency on an undeclared parameter rather than adding one to the collection.
	BeatTracker = BeatPulse;
}

void UMelodiaNeuralHeroMaterialSubsystem::RunInference()
{
	// Verified 5.8 NNE path (Docs/Research/INFINITY_NIKKI_PIPELINE_RESEARCH_2026-09-02.md,
	// 2026-09-02): add module `NNE` + `NNERuntimeORTCpu` to MelodiaIntegration.Build.cs.
	//   LoadObject<UNNEModelData>(nullptr, onnx_path)
	//   GetRuntime<INNERuntimeCPU>() -> CreateModelCPU(model_data) -> CreateModelInstanceCPU()
	//   instance->SetInputTensorShapes(...) ; instance->RunSync(FTensorBindingCPU ...)
	// Use NNERuntimeORTCpu (CPU) — CUDA was removed in NNERuntimeORT 5.4 and the DirectML
	// GPU runtime is `NNERuntimeORTDml`; a 5->16->12->5 MLP is cheap enough for one
	// sync call per frame. Input tensor = packed [Bass, BeatI, BeatP, BeatPulse, BeatTracker].
	// Until the closed-editor build lands, forward a documented fallback so hero materials
	// still pulse from the live audio (deterministic, contact matches the onnx default):
	//   EmissiveStrength grows with BeatIntensity; Subsurface grows with Bass.
	EmissiveStrength = FMath::Clamp(BeatIntensity * 0.85f + BeatPulse * 0.15f, 0.f, 1.f);
	EmissiveTint     = FMath::Frac(BeatPhase + FMath::Max(0.f, BeatIntensity) * 0.5f);
	SubsurfaceScatter= FMath::Clamp(BassIntensity * 0.9f, 0.f, 1.f);
	Displacement     = FMath::Clamp(BeatPulse * 0.8f, 0.f, 1.f);
	SpecularBoost    = FMath::Clamp(BeatIntensity * 0.6f + BassIntensity * 0.2f, 0.f, 1.f);

	// Push to the subsystem-owned hero surface (NOT the audio MPC).
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	UMaterialParameterCollection* Hero = LoadObject<UMaterialParameterCollection>(
		nullptr, TEXT("/Game/Melodia/MPC_Hero_Material.MPC_Hero_Material"));
	if (Hero)
	{
		UMaterialParameterCollectionInstance* HeroInst =
			World->GetParameterCollectionInstance(Hero);
		if (HeroInst)
		{
			HeroInst->SetScalarParameterValue(TEXT("EmissiveStrength"), EmissiveStrength);
			HeroInst->SetScalarParameterValue(TEXT("EmissiveTint"), EmissiveTint);
			HeroInst->SetScalarParameterValue(TEXT("SubsurfaceScatter"), SubsurfaceScatter);
			HeroInst->SetScalarParameterValue(TEXT("Displacement"), Displacement);
			HeroInst->SetScalarParameterValue(TEXT("SpecularBoost"), SpecularBoost);
		}
	}
}

void UMelodiaNeuralHeroMaterialSubsystem::GetHeroParameters(
	float& OutEmissiveStrength, float& OutEmissiveTint, float& OutSubsurfaceScatter,
	float& OutDisplacement, float& OutSpecularBoost) const
{
	OutEmissiveStrength = EmissiveStrength;
	OutEmissiveTint = EmissiveTint;
	OutSubsurfaceScatter = SubsurfaceScatter;
	OutDisplacement = Displacement;
	OutSpecularBoost = SpecularBoost;
}

void UMelodiaNeuralHeroMaterialSubsystem::GetAudioFeatures(
	float& OutBassIntensity, float& OutBeatIntensity, float& OutBeatPhase,
	float& OutBeatPulse, float& OutBeatTracker) const
{
	OutBassIntensity = BassIntensity;
	OutBeatIntensity = BeatIntensity;
	OutBeatPhase = BeatPhase;
	OutBeatPulse = BeatPulse;
	OutBeatTracker = BeatTracker;
}

#undef LOCTEXT_NAMESPACE