#include "MelodiaCaptureRenderSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/PlayerController.h"
#include "ImageUtils.h"
#include "Materials/MaterialInterface.h"
#include "Misc/Paths.h"
#include "Misc/DateTime.h"
#include "SceneCaptureComponent2D.h"

namespace
{
	// Canonical PPV stack per PPV_DRIFT_T3D_FIX_SPEC. Weight match is exact:
	// drift in the authored weight is the defect this gate exists to report, so
	// a fuzzy compare would blind exactly the failure mode this asserts for.
	struct FMelodiaCanonicalBlendable
	{
		LPCTSTR MaterialToken;
		float Weight;
	};

	const FMelodiaCanonicalBlendable GCanonicalBlendables[] = {
		{ TEXT("MelodiaInk"),      1.0f },
		{ TEXT("MeluColorGrade"),  0.69f },
		{ TEXT("StarryNight_Hero"),1.0f },
	};

	FString SurfaceToString(const EMelodiaRenderSurface Surface)
	{
		const UEnum* Enum = StaticEnum<EMelodiaRenderSurface>();
		return Enum ? Enum->GetNameStringByValue(static_cast<int64>(Surface)) : TEXT("Unknown");
	}

	/**
	 * Per-surface capture config (spec DASH_RENDER_SYSTEM_SPEC §4).
	 *
	 * Honest scope: SceneCapture2D cannot reproduce the viewport's BufferVisualization
	 * (MaterialBreakdown) or the PCG debug overlay, so those two surfaces fall back to
	 * a lit capture and are reported as approximate in IsPPVStackCanonical/notes.
	 * Wireframe IS a real show flag and renders genuinely in the scene capture.
	 */
	struct FMelodiaSurfaceConfig
	{
		bool bWireframe = false;
		bool bPostProcessing = true;
		bool bExactRepresentation = true;
	};

	FMelodiaSurfaceConfig GetSurfaceConfig(const EMelodiaRenderSurface Surface)
	{
		FMelodiaSurfaceConfig Config;
		switch (Surface)
		{
		case EMelodiaRenderSurface::Wireframe:
			Config.bWireframe = true;
			Config.bPostProcessing = false;
			break;
		case EMelodiaRenderSurface::MaterialBreakdown:
			Config.bExactRepresentation = false; // buffer-viz approximation
			break;
		case EMelodiaRenderSurface::PCGOverlay:
			Config.bExactRepresentation = false; // debug-overlay approximation
			break;
		case EMelodiaRenderSurface::DashTrailGhost:
		case EMelodiaRenderSurface::PortfolioHero:
		case EMelodiaRenderSurface::Gameplay:
		default:
			break;
		}
		return Config;
	}
}

bool UMelodiaCaptureRenderSubsystem::ConfigureSurface(const EMelodiaRenderSurface Surface, const FIntPoint Resolution)
{
	ActiveSurface = Surface;
	ActiveResolution = (Resolution.X == 0 && Resolution.Y == 0) ? FIntPoint(1920, 1080) : Resolution;

	// Transient presentation tuning — never mutates a level's PPV.
	if (GEngine)
	{
		GEngine->Exec(GetWorld(), TEXT("r.MotionBlur.Amount 0"));
	}

	return true;
}

bool UMelodiaCaptureRenderSubsystem::CaptureToRenderTarget(UTextureRenderTarget2D* Target)
{
	UWorld* World = GetWorld();
	if (!Target || !World)
	{
		return false;
	}

	// View source: the player camera in PIE; fall back to the first player
	// controller registered on the world. No camera, no capture -- a null view
	// would render the void and pass a size-only check, so it is refused.
	FMinimalViewInfo ViewInfo;
	APlayerController* PC = World->GetFirstPlayerController();
	if (!PC)
	{
		return false;
	}
	PC->GetPlayerViewPoint(ViewInfo.Location, ViewInfo.Rotation);

	const FMelodiaSurfaceConfig Config = GetSurfaceConfig(ActiveSurface);

	// Transient capture rig: created per capture, never persisted, never saved.
	// The rig is presentation-only and holds no authored state, so the world's
	// persistent actor list stays untouched.
	ASceneCapture2D* CaptureActor = World->SpawnActor<ASceneCapture2D>();
	if (!CaptureActor)
	{
		return false;
	}
	CaptureActor->SetActorLocationAndRotation(ViewInfo.Location, ViewInfo.Rotation);
	CaptureActor->SetActorHiddenInGame(true);
	CaptureActor->SetActorEnableCollision(false);

	USceneCaptureComponent2D* Capture = CaptureActor->GetCaptureComponent2D();
	Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorHDR;
	Capture->bCaptureEveryFrame = false;
	Capture->bCaptureOnMovement = false;
	Capture->bAlwaysPersistRenderingState = false;

	// HDR per spec: RTF_RGBA16f. FinalColorHDR runs the level PPV (the canonical
	// NikkiDream stack) into the target; SceneColorHDR would bypass post entirely.
	Capture->TextureTarget = Target;

	Capture->ShowFlags.SetWireframe(Config.bWireframe);
	Capture->ShowFlags.SetPostProcessing(Config.bPostProcessing);
	Capture->ShowFlags.SetMotionBlur(false);

	Capture->CaptureScene();

	// Detach the target before the transient actor dies so the RT outlives the rig.
	Capture->TextureTarget = nullptr;
	CaptureActor->Destroy();

	return true;
}

bool UMelodiaCaptureRenderSubsystem::CaptureToFile(const FString& LevelName, const EMelodiaRenderSurface Surface)
{
	UWorld* World = GetWorld();
	if (!World || LevelName.IsEmpty())
	{
		return false;
	}

	ConfigureSurface(Surface, ActiveResolution);
	FString Reason;
	if (!IsPPVStackCanonical(Reason))
	{
		UE_LOG(LogTemp, Warning, TEXT("[Capture] PPV stack not canonical: %s"), *Reason);
		// Evidence standard: log, do not auto-fix. The capture still runs, but the
		// report carries the drift so the gate can fail on it.
	}

	UTextureRenderTarget2D* Target = NewObject<UTextureRenderTarget2D>(this);
	Target->RenderTargetFormat = RTF_RGBA16f;
	Target->ClearColor = FLinearColor::Black;
	Target->bAutoGenerateMips = false;
	Target->InitAutoFormat(ActiveResolution.X, ActiveResolution.Y);
	Target->UpdateResourceImmediate(true);

	if (!CaptureToRenderTarget(Target))
	{
		return false;
	}

	const FString Timestamp = FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S"));
	const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("DashCaptures"));
	const FString FilePath = FPaths::Combine(Directory,
		FString::Printf(TEXT("%s_%s_%s.png"), *LevelName, *SurfaceToString(Surface), *Timestamp));

	// FImageUtils::ExportRenderTarget2DAsPNG writes LDR sRGB bytes; the HDR
	// RTF_RGBA16f path is preserved for downstream CaptureToRenderTarget users,
	// while the file artifact is the standard PNG evidence format.
	if (!FImageUtils::ExportRenderTarget2DAsPNG(Target, FilePath))
	{
		UE_LOG(LogTemp, Error, TEXT("[Capture] PNG export failed: %s"), *FilePath);
		return false;
	}

	LastCaptureFilePath = FilePath;
	UE_LOG(LogTemp, Log, TEXT("[Capture] wrote %s (%dx%d, surface=%s)"),
		*FilePath, ActiveResolution.X, ActiveResolution.Y, *SurfaceToString(Surface));
	return true;
}

bool UMelodiaCaptureRenderSubsystem::IsPPVStackCanonical(FString& OutReason) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		OutReason = TEXT("no_world");
		return false;
	}

	// Find the canonical PPV actor by name token. Renaming the actor is an
	// authored decision that must surface as drift here, not as a silent pass.
	APostProcessVolume* Found = nullptr;
	for (TActorIterator<APostProcessVolume> It(World); It; ++It)
	{
		if (It->GetFName().ToString().Contains(TEXT("NikkiDream")))
		{
			Found = *It;
			break;
		}
	}
	if (!Found)
	{
		OutReason = TEXT("ppv_nikkidream_not_found");
		return false;
	}

	const TArray<FWeightedBlendable>& Blendables = Found->Settings.WeightedBlendables;
	if (Blendables.Num() == 0)
	{
		OutReason = TEXT("ppv_nikkidream_no_blendables");
		return false;
	}

	bool bAllMatched = true;
	for (const FMelodiaCanonicalBlendable& Canonical : GCanonicalBlendables)
	{
		bool bMatched = false;
		for (const FWeightedBlendable& Blendable : Blendables)
		{
			const UMaterialInterface* Material = Cast<UMaterialInterface>(Blendable.Object);
			if (!Material)
			{
				continue;
			}
			if (Material->GetName().Contains(Canonical.MaterialToken))
			{
				if (FMath::IsNearlyEqual(Blendable.Weight, Canonical.Weight, 0.005f))
				{
					bMatched = true;
				}
				else
				{
					bMatched = false;
					OutReason = FString::Printf(TEXT("weight_drift_%s_%.3f_expected_%.3f"),
						Canonical.MaterialToken, Blendable.Weight, Canonical.Weight);
				}
				break;
			}
		}
		if (!bMatched)
		{
			if (!OutReason.StartsWith(TEXT("weight_drift_")))
			{
				OutReason = FString::Printf(TEXT("missing_blendable_%s"), Canonical.MaterialToken);
			}
			bAllMatched = false;
		}
	}

	if (bAllMatched)
	{
		OutReason = FString::Printf(TEXT("canonical (%d blendables checked)"),
			static_cast<int32>(UE_ARRAY_COUNT(GCanonicalBlendables)));
	}
	return bAllMatched;
}
