#include "MelodiaCymaticsWriterSubsystem.h"
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

float UMelodiaCymaticsWriterSubsystem::ComputeDrivenPulse(const float BeatPulse, const float EventPulse)
{
	// Additive, not max: with max() an event landing on a beat peak is invisible. The overshoot
	// (up to 1.6) reads as a flash above the beat; UVDistortion is clamped independently.
	return FMath::Clamp(BeatPulse + FMath::Clamp(EventPulse, 0.f, 1.f) * 0.6f, 0.f, 1.6f);
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

	// ── Wind lanes (2026-09-16 Muse brief P4) ─────────────────────────────────
	// The palette is the source lane for wind; OSC/TD/game write the normalized
	// XY direction plus magnitude there and never touch the driver. This writer
	// derives the driver copy, which is why the flower-field wind must not be
	// published straight to MPC_Cymatics_Driver by anything else.
	//
	// The old OSC handler reduced wind to abs(X), so -X and +X gusts were
	// identical and Y was dropped; the direction lanes carry the whole heading.
	float WindDirX = 0.f;
	float WindDirY = 0.f;
	float WindStrength = 0.f;
	const bool bHaveWindX = SrcInst->GetScalarParameterValue(FName(TEXT("WindDirX")), WindDirX);
	const bool bHaveWindY = SrcInst->GetScalarParameterValue(FName(TEXT("WindDirY")), WindDirY);
	const bool bHaveWindS = SrcInst->GetScalarParameterValue(FName(TEXT("WindStrength")), WindStrength);

	// Direction is re-orthonormalized defensively: a malformed sender can hand us
	// a non-unit vector, and a zero-length vector would poison the material's
	// normalize(). When the vector is degenerate we skip the direction writes and
	// let the driver hold its previous heading -- a hold is not a snap, and it
	// keeps NaN out of the graph. Strength still publishes 0, which is the
	// neutral state: the material multiplies its response by strength.
	const float WindDirLen = FMath::Sqrt(WindDirX * WindDirX + WindDirY * WindDirY);
	const bool bWindDirValid = bHaveWindX && bHaveWindY && WindDirLen > 1e-4f;

	// Chladni modes mirrored from UMelodiaCymaticsSubsystem (read-only) so writer and sampler stay coherent
	const int32 ModeN = FMath::Clamp(2 + FMath::FloorToInt(BassIntensity * 6.0f), 1, 8);
	const int32 ModeM = FMath::Clamp(3 + FMath::FloorToInt(BeatPulse * 5.0f), 1, 8);

	// Decaying event pulses already published on the palette ring the field like a beat:
	// GlobalSparkleIntensity (command / victory pulses from the reactivity subsystem) and
	// QuantumPulse (draws). RhythmPulse is deliberately not used: it carries command energy,
	// which is sticky until an encounter ends. Read-only here; the palette writers own these.
	float SparklePulse = 0.f;
	float QuantumPulse = 0.f;
	SrcInst->GetScalarParameterValue(FName(TEXT("GlobalSparkleIntensity")), SparklePulse);
	SrcInst->GetScalarParameterValue(FName(TEXT("QuantumPulse")), QuantumPulse);
	const float EventPulse = FMath::Clamp(FMath::Max(SparklePulse, QuantumPulse), 0.f, 1.f);
	const float DrivenPulse = ComputeDrivenPulse(BeatPulse, EventPulse);

	// Material mappings (presentation-only)
	// IridescenceTint hue shift driven by Bass (0..0.15), EmissiveScale rides the driven pulse, UV distortion is low-freq warble
	const float EmissiveScale = 0.25f + DrivenPulse * 1.2f + BassIntensity * 0.3f;
	const float IridescenceShift = FMath::Clamp(BassIntensity * 0.14f + DrivenPulse * 0.06f, 0.f, 0.2f);
	const float UVDistortion = FMath::Clamp(DrivenPulse * 0.08f + MidIntensity * 0.02f, 0.f, 0.12f);

	// Write to driver MPC (sole writer — no other system writes MPC_Cymatics_Driver)
	DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_BeatPulse")), DrivenPulse);
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

	// Derived wind lanes. Direction publishes only when the source vector is
	// usable; strength publishes whenever the lane exists, clamped so a bad
	// sender cannot drive the meadow into a runaway sweep.
	if (bWindDirValid)
	{
		DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_WindDirX")), WindDirX / WindDirLen);
		DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_WindDirY")), WindDirY / WindDirLen);
	}
	if (bHaveWindS)
	{
		DstInst->SetScalarParameterValue(FName(TEXT("Cymatic_WindStrength")),
			FMath::Clamp(WindStrength, 0.f, 10.f));
	}
}
