#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaDashRenderSubsystem.generated.h"

class UTextureRenderTarget2D;

UENUM(BlueprintType)
enum class EMelodiaDashSurface : uint8
{
	Gameplay            UMETA(DisplayName="Gameplay (Beauty)"),
	Wireframe           UMETA(DisplayName="Wireframe"),
	MaterialBreakdown   UMETA(DisplayName="Material Breakdown"),
	PCGOverlay          UMETA(DisplayName="PCG Overlay"),
	DashTrailGhost      UMETA(DisplayName="Dash Trail Ghost"),
	PortfolioHero       UMETA(DisplayName="Portfolio Hero")
};

/**
 * Dash — offscreen 3D render orchestrator.
 *
 * Presentation-only. Drives the EXISTING toon spine (M_Master_Toon_Universal,
 * Substrate Toon) and the canonical PPV_NikkiDream stack; it does not create
 * new masters or write Content/_PROJECT/. Lives alongside
 * UMelodiaPrototypeCaptureSubsystem (quick viewport grab) as the controlled
 * pipeline for 4-view cycles, HDR captures, and dash-ghost composites.
 *
 * Spec: Docs/DASH_RENDER_SYSTEM_SPEC_2026-08-30.md
 * Guardrails: AGENTS.md convergence rule — no parallel masters.
 */
UCLASS()
class BS_GODFILE_API UMelodiaDashRenderSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Melodia|Dash")
	bool ConfigureSurface(EMelodiaDashSurface Surface, FIntPoint Resolution);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Dash")
	bool CaptureToRenderTarget(UTextureRenderTarget2D* Target);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Dash")
	bool CaptureToFile(const FString& LevelName, EMelodiaDashSurface Surface);

	UFUNCTION(BlueprintPure, Category = "Melodia|Dash")
	bool IsPPVStackCanonical(FString& OutReason) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Dash")
	EMelodiaDashSurface GetActiveSurface() const { return ActiveSurface; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Dash")
	FIntPoint GetActiveResolution() const { return ActiveResolution; }

private:
	EMelodiaDashSurface ActiveSurface = EMelodiaDashSurface::Gameplay;
	FIntPoint ActiveResolution = FIntPoint(1920, 1080);
};
