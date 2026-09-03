#pragma once

#include "CoreMinimal.h"

class UWorld;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class ALight;
class ULightComponent;

/**
 * Scene capture + analytic lighting utilities for Phase 7 Lighting Analysis.
 * Tiny render targets, ReadPixels wrapper, luminance math, light inventory.
 */
namespace MonolithLightingCapture
{
	// ========================================================================
	// Luminance Result
	// ========================================================================

	/** Result of a single light sample */
	struct FLightSample
	{
		FVector Location = FVector::ZeroVector;

		// Capture-based (requires scene capture)
		float Luminance = 0.0f;         // Average luminance (cd/m^2 approximation)
		FLinearColor AverageColor = FLinearColor::Black;

		// Analytic-based (light actor iteration)
		FString DominantLightName;
		float DominantLightContribution = 0.0f;
		float ColorTemperature = 6500.0f;   // Kelvin
		bool bInShadow = false;             // True if line trace to dominant light is blocked

		// Combined
		float AnalyticLuminance = 0.0f;     // Sum of inverse-square contributions
	};

	// ========================================================================
	// Scene Capture Helpers
	// ========================================================================

	/** Create a transient render target of given size. Caller must manage lifetime. */
	UTextureRenderTarget2D* CreateTransientRT(int32 Width, int32 Height);

	/** Create a transient scene capture component configured for lighting-only capture.
	 *  Uses SCS_FinalColorHDR + show flag overrides to isolate illumination.
	 *  Registers with given world. Caller must call CleanupCapture(). */
	USceneCaptureComponent2D* CreateLightingCapture(UWorld* World, UTextureRenderTarget2D* RT);

	/** Create a transient ortho capture component for coverage maps.
	 *  @param OrthoWidth  Orthographic width in world units */
	USceneCaptureComponent2D* CreateOrthoLightingCapture(UWorld* World, UTextureRenderTarget2D* RT, float OrthoWidth);

	/** Position capture, trigger CaptureScene(), read pixels back.
	 *  @return false if capture or readback failed */
	bool CaptureAtPoint(USceneCaptureComponent2D* Capture, const FVector& Location, const FRotator& Rotation,
		TArray<FLinearColor>& OutPixels);

	/** Read pixels from an RT as FLinearColor (HDR).
	 *  Uses GameThread_GetRenderTargetResource + ReadLinearColorPixels. */
	bool ReadPixelsHDR(UTextureRenderTarget2D* RT, TArray<FLinearColor>& OutPixels);

	/** Cleanup a scene capture component (unregister + null out RT reference) */
	void CleanupCapture(USceneCaptureComponent2D* Capture);

	// ========================================================================
	// Luminance Math
	// ========================================================================

	/** Compute perceptual luminance from linear color: 0.2126R + 0.7152G + 0.0722B */
	float ComputeLuminance(const FLinearColor& Color);

	/** Compute average luminance from pixel array */
	float AverageLuminance(const TArray<FLinearColor>& Pixels);

	/** Compute average color from pixel array */
	FLinearColor AverageColor(const TArray<FLinearColor>& Pixels);

	/** Estimate color temperature from RGB (McCamy's approximation on CIE chromaticity) */
	float EstimateColorTemperature(const FLinearColor& Color);

	// ========================================================================
	// Analytic Light Sampling
	// ========================================================================

	/** Info about a single light actor */
	struct FLightInfo
	{
		FString Name;
		FString Type;           // "Point", "Spot", "Directional", "Rect"
		FVector Location = FVector::ZeroVector;
		FRotator Rotation = FRotator::ZeroRotator;
		float Intensity = 0.0f;
		FLinearColor Color = FLinearColor::White;
		float AttenuationRadius = 0.0f;
		bool bCastsShadows = false;
		float ColorTemperature = 6500.0f;
	};

	/** Gather all light actors in the world */
	TArray<FLightInfo> GatherLights(UWorld* World);

	/** Gather lights within a bounding box */
	TArray<FLightInfo> GatherLightsInRegion(UWorld* World, const FBox& Region);

	/** Compute analytic illumination at a point from all lights (inverse-square, no bounces).
	 *  Shadow traces reduce blocked light contributions to a 5% ambient fraction.
	 *  @param OutDominantLight  Index into Lights of the strongest contributor (-1 if none)
	 *  @param bTraceShadows    If true, line-trace to each light and attenuate blocked ones
	 *  @return Total analytic luminance estimate */
	float ComputeAnalyticLuminance(UWorld* World, const FVector& Point, const TArray<FLightInfo>& Lights,
		int32& OutDominantLight, bool bTraceShadows = true);

	/** Check if a point is in shadow from a light (line trace) */
	bool IsInShadow(UWorld* World, const FVector& Point, const FVector& LightLocation);

	// ========================================================================
	// Atlas Capture (for batching >10 points into one ReadPixels)
	// ========================================================================

	/** Capture multiple points into a single atlas RT. Each point gets TileSize x TileSize pixels.
	 *  @param Points       Sample locations
	 *  @param TileSize     Pixels per point (default 8)
	 *  @param MaxTilesPerRow  Tiles per row in atlas
	 *  @param OutPixels    Full atlas pixel data
	 *  @param OutAtlasWidth  Atlas width in pixels
	 *  @param OutAtlasHeight Atlas height in pixels
	 *  @return false if capture failed */
	bool CapturePointsAtlas(UWorld* World, const TArray<FVector>& Points, int32 TileSize,
		int32 MaxTilesPerRow, TArray<FLinearColor>& OutPixels, int32& OutAtlasWidth, int32& OutAtlasHeight);

	/** Extract average luminance for a single tile from atlas pixel data */
	float ExtractTileLuminance(const TArray<FLinearColor>& AtlasPixels, int32 AtlasWidth,
		int32 TileIndex, int32 TileSize, int32 TilesPerRow);

	/** Extract average color for a single tile from atlas pixel data */
	FLinearColor ExtractTileColor(const TArray<FLinearColor>& AtlasPixels, int32 AtlasWidth,
		int32 TileIndex, int32 TileSize, int32 TilesPerRow);

	// ========================================================================
	// Coverage Map
	// ========================================================================

	/** Result of a coverage analysis */
	struct FCoverageResult
	{
		float PercentLit = 0.0f;      // Luminance > bright threshold
		float PercentShadow = 0.0f;   // Between dark and bright thresholds
		float PercentDark = 0.0f;     // Below dark threshold
		TArray<float> LuminanceGrid;  // Row-major luminance values
		int32 GridWidth = 0;
		int32 GridHeight = 0;
	};

	/** Capture an orthographic coverage map of a region.
	 *  @param Center     Center of the capture area
	 *  @param Extent     Half-extent of the region (XY)
	 *  @param Resolution Grid resolution (e.g. 128)
	 *  @param DarkThreshold   Luminance below this = "dark" (default 0.05)
	 *  @param BrightThreshold Luminance above this = "lit" (default 0.2) */
	FCoverageResult CaptureCoverageMap(UWorld* World, const FVector& Center, const FVector& Extent,
		int32 Resolution, float DarkThreshold = 0.05f, float BrightThreshold = 0.2f);

	// ========================================================================
	// Dark Zone Detection (flood fill on luminance grid)
	// ========================================================================

	struct FDarkZone
	{
		FVector WorldCenter = FVector::ZeroVector;
		float AreaSqCm = 0.0f;        // Approximate area in sq cm
		int32 CellCount = 0;
		float AverageLuminance = 0.0f;
	};

	/** Flood-fill contiguous dark cells in a luminance grid.
	 *  @param Grid         Row-major luminance values
	 *  @param GridW, GridH Grid dimensions
	 *  @param Threshold    Cells below this are "dark"
	 *  @param WorldMin     World-space min of the grid region
	 *  @param CellSize     World-space size of each cell
	 *  @param MinCells     Minimum contiguous cells to qualify as a zone */
	TArray<FDarkZone> FloodFillDarkZones(const TArray<float>& Grid, int32 GridW, int32 GridH,
		float Threshold, const FVector& WorldMin, float CellSize, int32 MinCells = 4);
}
