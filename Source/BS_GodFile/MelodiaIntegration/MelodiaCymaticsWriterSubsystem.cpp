#include "MelodiaCymaticsWriterSubsystem.h"
#include "MelodiaWorldFieldBus.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Kismet/KismetMathLibrary.h"
#include "Containers/Ticker.h"

void UMelodiaCymaticsWriterSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Source: canonical audio palette (single writer is UMelodiaAudioReactivePresentationSubsystem)
	SourcePalette = LoadObject<UMaterialParameterCollection>(nullptr,
		TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"));

	// Driver: this subsystem is the SOLE writer
	DriverCollection = LoadObject<UMaterialParameterCollection>(nullptr,
		TEXT("/Game/Melodia/Cymatics/MPC_Cymatics_Driver.MPC_Cymatics_Driver"));

	if (!DriverCollection)
	{
		UE_LOG(LogTemp, Warning, TEXT("[CymaticsWriter] MPC_Cymatics_Driver not found — writer disabled until asset exists."));
	}

	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaCymaticsWriterSubsystem::TickWriter));
}

void UMelodiaCymaticsWriterSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	Super::Deinitialize();
}

bool UMelodiaCymaticsWriterSubsystem::TickWriter(float DeltaTime)
{
	RefreshAndPublish();
	return true;
}

void UMelodiaCymaticsWriterSubsystem::RefreshAndPublish()
{
	if (!SourcePalette || !DriverCollection)
	{
		return;
	}
	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	UMaterialParameterCollectionInstance* SrcInst = World->GetParameterCollectionInstance(SourcePalette);
	UMaterialParameterCollectionInstance* DstInst = World->GetParameterCollectionInstance(DriverCollection);
	if (!SrcInst || !DstInst)
	{
		return;
	}

	// Read canonical bands from MPC_Melodia_Palette (never own audio here)
	float BeatPulse = 0.f;
	float BassIntensity = 0.f;
	float BeatIntensity = 0.f;
	float MidIntensity = 0.f; // may be absent on palette — fallback to BeatIntensity

	SrcInst->GetScalarParameterValue(FName(TEXT("BeatPulse")), BeatPulse);
	SrcInst->GetScalarParameterValue(FName(TEXT("BassIntensity")), BassIntensity);
	SrcInst->GetScalarParameterValue(FName(TEXT("BeatIntensity")), BeatIntensity);
	if (!SrcInst->GetScalarParameterValue(FName(TEXT("MidIntensity")), MidIntensity))
	{
		MidIntensity = BeatIntensity * 0.7f + BassIntensity * 0.3f;
	}

	// Chladni modes mirrored from UMelodiaCymaticsSubsystem (read-only) so writer and sampler stay coherent
	const int32 ModeN = FMath::Clamp(2 + FMath::FloorToInt(BassIntensity * 6.0f), 1, 8);
	const int32 ModeM = FMath::Clamp(3 + FMath::FloorToInt(BeatPulse * 5.0f), 1, 8);

	// Material mappings (presentation-only)
	// IridescenceTint hue shift driven by Bass (0..0.15), EmissiveScale rides BeatPulse, UV distortion is low-freq warble
	const float EmissiveScale = 0.25f + BeatPulse * 1.2f + BassIntensity * 0.3f;
	const float IridescenceShift = FMath::Clamp(BassIntensity * 0.14f + BeatPulse * 0.06f, 0.f, 0.2f);
	const float UVDistortion = FMath::Clamp(BeatPulse * 0.08f + MidIntensity * 0.02f, 0.f, 0.12f);

	// Write to driver MPC (sole writer — no other system writes MPC_Cymatics_Driver)
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_BeatPulse")), BeatPulse);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_BassIntensity")), BassIntensity);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_MidIntensity")), MidIntensity);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_EmissiveScale")), EmissiveScale);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_IridescenceShift")), IridescenceShift);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_UVDistortion")), UVDistortion);
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_ModeN")), static_cast<float>(ModeN));
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_ModeM")), static_cast<float>(ModeM));

	// Also mirror legacy names expected by some Copernicus MIs if they sample BeatPulse/BassIntensity directly from driver
	DstInst->SetScalarParameterValue(FName(TEXT("BeatPulse")), BeatPulse);
	DstInst->SetScalarParameterValue(FName(TEXT("BassIntensity")), BassIntensity);

	// Publish to WorldField.Resonance/Tension — single bus for water + PCG + VFX.
	// Writer owns Cymatics, so its Tension is authoritative where CymaticsSubsystem has no world yet.
	const float TensionApprox = FMath::Clamp(BassIntensity * 0.85f + BeatPulse * 0.15f, 0.f, 1.f);
	UWorldFieldBus::PublishResonance(ModeN, ModeM, TensionApprox, BeatPulse);
}
