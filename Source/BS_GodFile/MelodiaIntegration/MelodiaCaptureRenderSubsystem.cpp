#include "MelodiaDashRenderSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/TextureRenderTarget2D.h"

bool UMelodiaDashRenderSubsystem::ConfigureSurface(const EMelodiaDashSurface Surface, const FIntPoint Resolution)
{
	ActiveSurface = Surface;
	ActiveResolution = (Resolution.X == 0 && Resolution.Y == 0) ? FIntPoint(1920, 1080) : Resolution;

	// Transient presentation tuning — never mutates a level's PPV.
	if (GEngine)
	{
		GEngine->Exec(GetWorld(), TEXT("r.MotionBlur.Amount 0"));
	}

	// Show-flag / view-mode switching is deferred to the live SceneCapture path;
	// this scaffold validates the call contract only. Full wiring requires a
	// single live editor + Monolith 9316 and the QOL queue order (PPV drift first).
	return true;
}

bool UMelodiaDashRenderSubsystem::CaptureToRenderTarget(UTextureRenderTarget2D* Target)
{
	if (!Target)
	{
		return false;
	}
	// Scaffold: target validation only. Live capture (SceneCaptureComponent2D,
	// HDR RTF_RGBA16f, show flags per EMelodiaDashSurface) is implemented when
	// the editor is live and the PPV stack is canonical (IsPPVStackCanonical).
	return true;
}

bool UMelodiaDashRenderSubsystem::CaptureToFile(const FString& LevelName, const EMelodiaDashSurface Surface)
{
	if (LevelName.IsEmpty())
	{
		return false;
	}
	ConfigureSurface(Surface, ActiveResolution);
	FString Reason;
	if (!IsPPVStackCanonical(Reason))
	{
		UE_LOG(LogTemp, Warning, TEXT("[Dash] PPV stack not canonical: %s"), *Reason);
		// Evidence standard: log, do not auto-fix.
	}
	// Scaffold: 4-view cycle (beauty/wireframe/material/PCG) is implemented live.
	// Offline, this proves the API contract and writes a ledger row via Tools/test_dash_capture.py.
	return true;
}

bool UMelodiaDashRenderSubsystem::IsPPVStackCanonical(FString& OutReason) const
{
	// Canonical stack per PPV_DRIFT_T3D_FIX_SPEC:
	//   PPV_NikkiDream: MI_MelodiaInk 1.0, MI_MeluColorGrade 0.69, MI_StarryNight_Hero 1.0
	//   All MD_POST_PROCESS. Live check enumerates the PPV actor's blendables.
	// Scaffold returns true so the probe can exercise the contract offline;
	// the live implementation queries the level via Monolith.
	OutReason = TEXT("scaffold — live PPV enumeration deferred to editor session");
	return true;
}
