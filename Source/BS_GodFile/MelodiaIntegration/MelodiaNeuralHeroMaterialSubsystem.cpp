// MelodiaNeuralHeroMaterialSubsystem.cpp — SCAFFOLDED (needs closed-editor build).
#include "MelodiaNeuralHeroMaterialSubsystem.h"

#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "ParamCollectionEngineSubsystem.h" // UMaterialParameterCollection::GetInstance / material param writes

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
	BassIntensity  = Instance->GetScalarParameterValue(TEXT("BassIntensity"));
	BeatIntensity  = Instance->GetScalarParameterValue(TEXT("BeatIntensity"));
	BeatPhase      = Instance->GetScalarParameterValue(TEXT("BeatPhase"));
	BeatPulse      = Instance->GetScalarParameterValue(TEXT("BeatPulse"));
	BeatTracker    = Instance->GetScalarParameterValue(TEXT("BeatTracker"));
}

void UMelodiaNeuralHeroMaterialSubsystem::RunInference()
{
	// TODO(closed-editor build): NNERuntimeORT inference of
	//   Tools/Audio/models/hero_material_controller.onnx over the packed features.
	// Project carries NNERuntimeORT enabled in .uproject; onnxruntime verified in
	// .venv-guardrails. Until the C++ binary is rebuilt, forward a documented
	// fallback so hero materials still pulse from the live audio (deterministic,
	// audio-responsive — matches the onnx default controller intent):
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