#include "MelodiaCymaticsSubsystem.h"
#include "MelodiaWorldFieldBus.h"

#include "Engine/Engine.h"
#include "Kismet/KismetMathLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Containers/Ticker.h"

void UMelodiaCymaticsSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	// Load the shared palette published by UMelodiaAudioReactivePresentationSubsystem.
	// We READ it only — never write it (IsReadOnlyByContract).
	if (UObject* Obj = StaticLoadObject(UMaterialParameterCollection::StaticClass(), nullptr,
		TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette")))
	{
		AudioParameterCollection = Cast<UMaterialParameterCollection>(Obj);
	}
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaCymaticsSubsystem::TickCymatics));
}

void UMelodiaCymaticsSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	Super::Deinitialize();
}

bool UMelodiaCymaticsSubsystem::TickCymatics(float DeltaTime)
{
	RefreshFromMPC();
	return true;
}

void UMelodiaCymaticsSubsystem::RefreshFromMPC()
{
	if (!AudioParameterCollection)
	{
		return;
	}
	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(AudioParameterCollection);
	if (!Inst)
	{
		return;
	}
	float Pulse = 0.f;
	float Bass = 0.f;
	Inst->GetScalarParameterValue(FName(TEXT("BeatPulse")), Pulse);
	Inst->GetScalarParameterValue(FName(TEXT("BassIntensity")), Bass);
	BeatPulse = Pulse;
	BassIntensity = Bass;

	// Drive the Chladni mode from the audio bands: bass pushes radial mode, beat
	// pulse modulates the cross mode. Modes stay in [1..8] for a stable pattern.
	ModeN = FMath::Clamp(2 + FMath::FloorToInt(Bass * 6.0f), 1, 8);
	ModeM = FMath::Clamp(3 + FMath::FloorToInt(BeatPulse * 5.0f), 1, 8);

	// Publish to WorldField.Resonance/Tension — the cymatic source bus.
	// Tension here is Chladni amplitude at plate center (0.5,0.5).
	const float TensionAtCenter = FMath::Abs(SampleCymaticAmplitude(0.5f, 0.5f));
	UWorldFieldBus::PublishResonance(ModeN, ModeM, TensionAtCenter, BeatPulse);
}

float UMelodiaCymaticsSubsystem::SampleCymaticAmplitude(const float U, const float V) const
{
	// Chladni standing-wave plate: amp = cos(n·π·u)·cos(m·π·v) − cos(m·π·u)·cos(n·π·v)
	const float PiU = UE_PI * U;
	const float PiV = UE_PI * V;
	const float A = FMath::Cos(ModeN * PiU) * FMath::Cos(ModeM * PiV);
	const float B = FMath::Cos(ModeM * PiU) * FMath::Cos(ModeN * PiV);
	return (A - B) * FMath::Max(BeatPulse, 0.15f);
}

void UMelodiaCymaticsSubsystem::GetCymaticMode(int32& OutN, int32& OutM) const
{
	OutN = ModeN;
	OutM = ModeM;
}

float UMelodiaCymaticsSubsystem::GetBeatPulse() const { return BeatPulse; }
float UMelodiaCymaticsSubsystem::GetBassIntensity() const { return BassIntensity; }
