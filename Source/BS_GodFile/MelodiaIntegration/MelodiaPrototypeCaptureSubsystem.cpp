#include "MelodiaPrototypeCaptureSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "HighResScreenshot.h"

void UMelodiaPrototypeCaptureSubsystem::SetCaptureSurface(const EMelodiaCaptureSurface Surface)
{
	ActiveSurface = Surface;
	// Screenshot presentation should remain crisp and readable; this is transient
	// runtime state and deliberately does not modify a level's post-process volume.
	if (GEngine)
	{
		GEngine->Exec(GetWorld(), TEXT("r.MotionBlur.Amount 0"));
	}
}

bool UMelodiaPrototypeCaptureSubsystem::CapturePrototypeScreenshot(const FString& OptionalLabel)
{
	if (!GEngine || !GEngine->GameViewport)
	{
		return false;
	}

	const FString SurfaceName = StaticEnum<EMelodiaCaptureSurface>()->GetNameStringByValue(static_cast<int64>(ActiveSurface));
	const FString Label = OptionalLabel.IsEmpty() ? SurfaceName : OptionalLabel;
	FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Melodia_%s"), *Label), true, false);
	return true;
}

FText UMelodiaPrototypeCaptureSubsystem::GetCaptureSurfaceLabel() const
{
	switch (ActiveSurface)
	{
	case EMelodiaCaptureSurface::MainMenu:
		return FText::FromString(TEXT("Main Menu Capture"));
	case EMelodiaCaptureSurface::Battle:
		return FText::FromString(TEXT("Battle Capture"));
	default:
		return FText::FromString(TEXT("Exploration Capture"));
	}
}
