#include "MonolithMeshLightingActions.h"
#include "MonolithMeshLightingCapture.h"
#include "MonolithMeshUtils.h"
#include "MonolithMeshAnalysis.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/BlockingVolume.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshLightingActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. sample_light_levels
	Registry.RegisterAction(TEXT("mesh"), TEXT("sample_light_levels"),
		TEXT("Sample light levels at specified points. Modes: capture (scene capture w/ Lumen GI), analytic (inverse-square from light actors), both. Returns luminance, dominant light, color temperature, shadow state per point. Hard cap 50 points."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshLightingActions::SampleLightLevels),
		FParamSchemaBuilder()
			.Required(TEXT("points"), TEXT("array"), TEXT("Array of sample positions [[x,y,z], ...]"))
			.Optional(TEXT("mode"), TEXT("string"), TEXT("Sampling mode: capture, analytic, or both"), TEXT("both"))
			.Build());

	// 2. find_dark_corners
	Registry.RegisterAction(TEXT("mesh"), TEXT("find_dark_corners"),
		TEXT("Find contiguous dark regions in a volume. Uses orthographic scene capture + flood-fill. Returns dark zones with area and average luminance."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshLightingActions::FindDarkCorners),
		FParamSchemaBuilder()
			.Optional(TEXT("volume_name"), TEXT("string"), TEXT("Name of blocking volume to analyze"), TEXT(""))
			.Optional(TEXT("region_min"), TEXT("array"), TEXT("Min corner [x, y, z] (alternative to volume_name)"), TEXT(""))
			.Optional(TEXT("region_max"), TEXT("array"), TEXT("Max corner [x, y, z] (alternative to volume_name)"), TEXT(""))
			.Optional(TEXT("threshold"), TEXT("number"), TEXT("Luminance threshold for 'dark' (0-1)"), TEXT("0.05"))
			.Optional(TEXT("resolution"), TEXT("integer"), TEXT("Capture resolution (16-256)"), TEXT("128"))
			.Build());

	// 3. analyze_light_transitions
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_light_transitions"),
		TEXT("Sample light levels along a path and flag harsh bright-to-dark transitions (>4:1 ratio over <200cm). Critical for hospice: harsh transitions cause discomfort for light-sensitive patients."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshLightingActions::AnalyzeLightTransitions),
		FParamSchemaBuilder()
			.Required(TEXT("path_points"), TEXT("array"), TEXT("Array of path positions [[x,y,z], ...]"))
			.Optional(TEXT("sample_interval"), TEXT("number"), TEXT("Distance between samples in cm"), TEXT("200"))
			.Optional(TEXT("harsh_ratio"), TEXT("number"), TEXT("Luminance ratio threshold for harsh transition"), TEXT("4.0"))
			.Optional(TEXT("harsh_distance"), TEXT("number"), TEXT("Max distance in cm for transition to be considered harsh"), TEXT("200"))
			.Build());

	// 4. get_light_coverage
	Registry.RegisterAction(TEXT("mesh"), TEXT("get_light_coverage"),
		TEXT("Room-level lighting audit. Orthographic capture for floor coverage percentages (lit/shadow/dark). Light inventory with type, intensity, color, shadow-casting flag."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshLightingActions::GetLightCoverage),
		FParamSchemaBuilder()
			.Required(TEXT("volume_name"), TEXT("string"), TEXT("Name of blocking volume to audit"))
			.Optional(TEXT("resolution"), TEXT("integer"), TEXT("Coverage map resolution"), TEXT("128"))
			.Optional(TEXT("dark_threshold"), TEXT("number"), TEXT("Luminance below this = dark"), TEXT("0.05"))
			.Optional(TEXT("bright_threshold"), TEXT("number"), TEXT("Luminance above this = lit"), TEXT("0.2"))
			.Build());

	// 5. suggest_light_placement
	Registry.RegisterAction(TEXT("mesh"), TEXT("suggest_light_placement"),
		TEXT("Suggest light placements for a mood. Analytic only: target luminance per mood, inverse-square backward-solve, avoids existing light overlap. Moods: horror_dim, safe_room, clinical, ambient."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshLightingActions::SuggestLightPlacement),
		FParamSchemaBuilder()
			.Required(TEXT("volume_name"), TEXT("string"), TEXT("Volume to light"))
			.Required(TEXT("mood"), TEXT("string"), TEXT("Target mood: horror_dim, safe_room, clinical, or ambient"))
			.Optional(TEXT("max_lights"), TEXT("integer"), TEXT("Maximum number of lights to suggest"), TEXT("8"))
			.Build());
}

// ============================================================================
// Helpers
// ============================================================================

namespace
{
	TArray<TSharedPtr<FJsonValue>> MLight_VecToArr(const FVector& V)
	{
		return MonolithMeshAnalysis::VectorToJsonArray(V);
	}

	bool MLight_ParseVectorArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FVector>& Out)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr;
		if (!Params->TryGetArrayField(Key, Arr) || Arr->Num() == 0)
		{
			return false;
		}

		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			const TArray<TSharedPtr<FJsonValue>>* Inner;
			if (Val->TryGetArray(Inner) && Inner->Num() >= 3)
			{
				FVector V;
				V.X = (*Inner)[0]->AsNumber();
				V.Y = (*Inner)[1]->AsNumber();
				V.Z = (*Inner)[2]->AsNumber();
				Out.Add(V);
			}
		}

		return Out.Num() > 0;
	}

	/** Find a blocking volume by name and return its world-space bounds */
	bool FindVolumeBounds(const TSharedPtr<FJsonObject>& Params, FVector& OutCenter, FVector& OutExtent, FString& OutError)
	{
		FString VolumeName;
		if (Params->TryGetStringField(TEXT("volume_name"), VolumeName) && !VolumeName.IsEmpty())
		{
			AActor* Volume = MonolithMeshUtils::FindActorByName(VolumeName, OutError);
			if (!Volume)
			{
				return false;
			}
			Volume->GetActorBounds(false, OutCenter, OutExtent);
			return true;
		}

		// Fallback: region_min/max
		FVector RegionMin, RegionMax;
		if (MonolithMeshUtils::ParseVector(Params, TEXT("region_min"), RegionMin) &&
			MonolithMeshUtils::ParseVector(Params, TEXT("region_max"), RegionMax))
		{
			OutCenter = (RegionMin + RegionMax) * 0.5f;
			OutExtent = (RegionMax - RegionMin) * 0.5f;
			OutExtent = OutExtent.GetAbs(); // Ensure positive
			return true;
		}

		OutError = TEXT("Either volume_name or region_min+region_max required");
		return false;
	}

	TSharedPtr<FJsonObject> LightInfoToJson(const MonolithLightingCapture::FLightInfo& L)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("name"), L.Name);
		Obj->SetStringField(TEXT("type"), L.Type);
		Obj->SetArrayField(TEXT("location"), MLight_VecToArr(L.Location));
		Obj->SetNumberField(TEXT("intensity"), L.Intensity);
		Obj->SetNumberField(TEXT("attenuation_radius"), L.AttenuationRadius);
		Obj->SetBoolField(TEXT("casts_shadows"), L.bCastsShadows);
		Obj->SetNumberField(TEXT("color_temperature"), L.ColorTemperature);

		TSharedPtr<FJsonObject> ColorObj = MakeShared<FJsonObject>();
		ColorObj->SetNumberField(TEXT("r"), L.Color.R);
		ColorObj->SetNumberField(TEXT("g"), L.Color.G);
		ColorObj->SetNumberField(TEXT("b"), L.Color.B);
		Obj->SetObjectField(TEXT("color"), ColorObj);

		return Obj;
	}

	/** Mood configuration */
	struct FMoodConfig
	{
		float TargetLuminance = 0.0f;    // Target average floor luminance
		float MinLuminance = 0.0f;       // Minimum acceptable at any point
		float MaxLuminance = 0.0f;       // Maximum acceptable at any point
		float PreferredColorTemp = 0.0f; // Kelvin
		FString LightType;               // Preferred light type
		FString Description;
	};

	FMoodConfig GetMoodConfig(const FString& Mood)
	{
		FMoodConfig Config;

		if (Mood == TEXT("horror_dim"))
		{
			Config.TargetLuminance = 0.03f;
			Config.MinLuminance = 0.005f;
			Config.MaxLuminance = 0.15f;
			Config.PreferredColorTemp = 3200.0f;
			Config.LightType = TEXT("Point");
			Config.Description = TEXT("Dim, warm pools of light with large dark areas. Shadows are features, not bugs.");
		}
		else if (Mood == TEXT("safe_room"))
		{
			Config.TargetLuminance = 0.25f;
			Config.MinLuminance = 0.08f;
			Config.MaxLuminance = 0.6f;
			Config.PreferredColorTemp = 4000.0f;
			Config.LightType = TEXT("Point");
			Config.Description = TEXT("Warm, even lighting. Visible corners, no hidden threats. Hospice-friendly — no harsh transitions.");
		}
		else if (Mood == TEXT("clinical"))
		{
			Config.TargetLuminance = 0.5f;
			Config.MinLuminance = 0.2f;
			Config.MaxLuminance = 0.8f;
			Config.PreferredColorTemp = 5500.0f;
			Config.LightType = TEXT("Rect");
			Config.Description = TEXT("Bright, even, cool-white lighting. Flat shadows. Sterile feel.");
		}
		else // ambient
		{
			Config.TargetLuminance = 0.15f;
			Config.MinLuminance = 0.05f;
			Config.MaxLuminance = 0.4f;
			Config.PreferredColorTemp = 4500.0f;
			Config.LightType = TEXT("Point");
			Config.Description = TEXT("Moderate, balanced ambient illumination. Gentle shadows.");
		}

		return Config;
	}
}

// ============================================================================
// 1. sample_light_levels
// ============================================================================

FMonolithActionResult FMonolithMeshLightingActions::SampleLightLevels(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FVector> Points;
	if (!MLight_ParseVectorArray(Params, TEXT("points"), Points))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: points (array of [x,y,z] arrays)"));
	}

	// Hard cap
	if (Points.Num() > 50)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Too many sample points (%d). Maximum is 50 per call."), Points.Num()));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString Mode = TEXT("both");
	Params->TryGetStringField(TEXT("mode"), Mode);
	Mode = Mode.ToLower();

	const bool bDoCapture = (Mode == TEXT("capture") || Mode == TEXT("both"));
	const bool bDoAnalytic = (Mode == TEXT("analytic") || Mode == TEXT("both"));

	// Gather lights for analytic mode
	TArray<MonolithLightingCapture::FLightInfo> Lights;
	if (bDoAnalytic)
	{
		Lights = MonolithLightingCapture::GatherLights(World);
	}

	// Scene capture sampling
	TArray<float> CaptureLuminances;
	TArray<FLinearColor> CaptureColors;
	CaptureLuminances.SetNumZeroed(Points.Num());
	CaptureColors.SetNum(Points.Num());
	for (auto& C : CaptureColors) C = FLinearColor::Black;

	if (bDoCapture)
	{
		// Use atlas approach for >10 points, individual for fewer
		if (Points.Num() > 10)
		{
			TArray<FLinearColor> AtlasPixels;
			int32 AtlasW, AtlasH;
			const int32 TileSize = 8;
			const int32 TilesPerRow = FMath::Min(10, Points.Num());

			if (MonolithLightingCapture::CapturePointsAtlas(World, Points, TileSize, TilesPerRow,
				AtlasPixels, AtlasW, AtlasH))
			{
				for (int32 i = 0; i < Points.Num(); ++i)
				{
					CaptureLuminances[i] = MonolithLightingCapture::ExtractTileLuminance(
						AtlasPixels, AtlasW, i, TileSize, TilesPerRow);
					CaptureColors[i] = MonolithLightingCapture::ExtractTileColor(
						AtlasPixels, AtlasW, i, TileSize, TilesPerRow);
				}
			}
		}
		else
		{
			// Individual captures
			UTextureRenderTarget2D* RT = MonolithLightingCapture::CreateTransientRT(8, 8);
			USceneCaptureComponent2D* Capture = MonolithLightingCapture::CreateLightingCapture(World, RT);

			for (int32 i = 0; i < Points.Num(); ++i)
			{
				TArray<FLinearColor> Pixels;
				if (MonolithLightingCapture::CaptureAtPoint(Capture, Points[i], FRotator(-90.0f, 0.0f, 0.0f), Pixels))
				{
					CaptureLuminances[i] = MonolithLightingCapture::AverageLuminance(Pixels);
					CaptureColors[i] = MonolithLightingCapture::AverageColor(Pixels);
				}
			}

			MonolithLightingCapture::CleanupCapture(Capture);
		}
	}

	// Build results
	TArray<TSharedPtr<FJsonValue>> ResultArray;
	for (int32 i = 0; i < Points.Num(); ++i)
	{
		TSharedPtr<FJsonObject> Sample = MakeShared<FJsonObject>();
		Sample->SetArrayField(TEXT("location"), MLight_VecToArr(Points[i]));

		if (bDoCapture)
		{
			Sample->SetNumberField(TEXT("capture_luminance"), CaptureLuminances[i]);
			TSharedPtr<FJsonObject> ColorObj = MakeShared<FJsonObject>();
			ColorObj->SetNumberField(TEXT("r"), CaptureColors[i].R);
			ColorObj->SetNumberField(TEXT("g"), CaptureColors[i].G);
			ColorObj->SetNumberField(TEXT("b"), CaptureColors[i].B);
			Sample->SetObjectField(TEXT("capture_color"), ColorObj);
			Sample->SetNumberField(TEXT("color_temperature"),
				MonolithLightingCapture::EstimateColorTemperature(CaptureColors[i]));
		}

		if (bDoAnalytic)
		{
			int32 DominantIdx = -1;
			float AnalyticLum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Points[i], Lights, DominantIdx);
			Sample->SetNumberField(TEXT("analytic_luminance"), AnalyticLum);

			if (DominantIdx >= 0 && DominantIdx < Lights.Num())
			{
				Sample->SetStringField(TEXT("dominant_light"), Lights[DominantIdx].Name);
				int32 DomDummy;
				Sample->SetNumberField(TEXT("dominant_light_contribution"),
					MonolithLightingCapture::ComputeAnalyticLuminance(World, Points[i],
						TArray<MonolithLightingCapture::FLightInfo>{Lights[DominantIdx]}, DomDummy));

				// Derive in_shadow from whether majority of light is blocked:
				// compare shadowed luminance to unshadowed luminance
				int32 UnshadowedDummy;
				float UnshadowedLum = MonolithLightingCapture::ComputeAnalyticLuminance(
					World, Points[i], Lights, UnshadowedDummy, /*bTraceShadows=*/ false);
				bool bInShadow = (UnshadowedLum > 0.0f) && (AnalyticLum < UnshadowedLum * 0.5f);
				Sample->SetBoolField(TEXT("in_shadow"), bInShadow);

				Sample->SetNumberField(TEXT("dominant_color_temperature"), Lights[DominantIdx].ColorTemperature);
			}
			else
			{
				Sample->SetStringField(TEXT("dominant_light"), TEXT("none"));
				Sample->SetBoolField(TEXT("in_shadow"), true);
			}
		}

		// Combined luminance (prefer capture when available)
		float FinalLum = bDoCapture ? CaptureLuminances[i] : 0.0f;
		if (!bDoCapture && bDoAnalytic)
		{
			int32 Dummy;
			FinalLum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Points[i], Lights, Dummy);
		}
		Sample->SetNumberField(TEXT("luminance"), FinalLum);

		ResultArray.Add(MakeShared<FJsonValueObject>(Sample));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetArrayField(TEXT("samples"), ResultArray);
	Root->SetNumberField(TEXT("point_count"), Points.Num());
	Root->SetStringField(TEXT("mode"), Mode);

	return FMonolithActionResult::Success(Root);
}

// ============================================================================
// 2. find_dark_corners
// ============================================================================

FMonolithActionResult FMonolithMeshLightingActions::FindDarkCorners(const TSharedPtr<FJsonObject>& Params)
{
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FVector Center, Extent;
	FString Error;
	if (!FindVolumeBounds(Params, Center, Extent, Error))
	{
		return FMonolithActionResult::Error(Error);
	}

	double Threshold = 0.05;
	Params->TryGetNumberField(TEXT("threshold"), Threshold);
	Threshold = FMath::Clamp(Threshold, 0.001, 1.0);

	double ResolutionD = 128.0;
	Params->TryGetNumberField(TEXT("resolution"), ResolutionD);
	int32 Resolution = FMath::Clamp(static_cast<int32>(ResolutionD), 16, 256);

	// Capture coverage map
	MonolithLightingCapture::FCoverageResult Coverage =
		MonolithLightingCapture::CaptureCoverageMap(World, Center, Extent, Resolution,
			static_cast<float>(Threshold), 0.2f);

	if (Coverage.LuminanceGrid.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Scene capture failed — ensure editor viewport is rendering"));
	}

	// Flood fill dark zones
	const FVector WorldMin = Center - Extent;
	const float CellSize = (Extent.X * 2.0f) / Resolution;

	TArray<MonolithLightingCapture::FDarkZone> DarkZones =
		MonolithLightingCapture::FloodFillDarkZones(Coverage.LuminanceGrid, Coverage.GridWidth, Coverage.GridHeight,
			static_cast<float>(Threshold), WorldMin, CellSize, 4);

	// Sort by area descending
	DarkZones.Sort([](const MonolithLightingCapture::FDarkZone& A, const MonolithLightingCapture::FDarkZone& B)
	{
		return A.AreaSqCm > B.AreaSqCm;
	});

	// Build results
	TArray<TSharedPtr<FJsonValue>> ZonesArray;
	for (const MonolithLightingCapture::FDarkZone& Zone : DarkZones)
	{
		TSharedPtr<FJsonObject> ZoneObj = MakeShared<FJsonObject>();
		ZoneObj->SetArrayField(TEXT("center"), MLight_VecToArr(Zone.WorldCenter));
		ZoneObj->SetNumberField(TEXT("area_sq_cm"), Zone.AreaSqCm);
		ZoneObj->SetNumberField(TEXT("area_sq_m"), Zone.AreaSqCm / 10000.0f);
		ZoneObj->SetNumberField(TEXT("cell_count"), Zone.CellCount);
		ZoneObj->SetNumberField(TEXT("average_luminance"), Zone.AverageLuminance);

		// Could a monster hide here? Rough heuristic: area > 1 sq meter
		ZoneObj->SetBoolField(TEXT("monster_hideable"), Zone.AreaSqCm > 10000.0f);

		ZonesArray.Add(MakeShared<FJsonValueObject>(ZoneObj));
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetArrayField(TEXT("dark_zones"), ZonesArray);
	Root->SetNumberField(TEXT("zone_count"), DarkZones.Num());
	Root->SetNumberField(TEXT("threshold"), Threshold);
	Root->SetNumberField(TEXT("capture_resolution"), Resolution);

	// Summary coverage percentages
	Root->SetNumberField(TEXT("percent_dark"), Coverage.PercentDark);
	Root->SetNumberField(TEXT("percent_shadow"), Coverage.PercentShadow);
	Root->SetNumberField(TEXT("percent_lit"), Coverage.PercentLit);

	return FMonolithActionResult::Success(Root);
}

// ============================================================================
// 3. analyze_light_transitions
// ============================================================================

FMonolithActionResult FMonolithMeshLightingActions::AnalyzeLightTransitions(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FVector> PathPoints;
	if (!MLight_ParseVectorArray(Params, TEXT("path_points"), PathPoints) || PathPoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: path_points (need at least 2 points)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	double SampleInterval = 200.0;
	Params->TryGetNumberField(TEXT("sample_interval"), SampleInterval);
	SampleInterval = FMath::Clamp(SampleInterval, 50.0, 2000.0);

	double HarshRatio = 4.0;
	Params->TryGetNumberField(TEXT("harsh_ratio"), HarshRatio);

	double HarshDistance = 200.0;
	Params->TryGetNumberField(TEXT("harsh_distance"), HarshDistance);

	// Generate sample points along path at intervals
	TArray<FVector> SamplePoints;
	TArray<float> CumulativeDistances;
	float TotalDist = 0.0f;

	SamplePoints.Add(PathPoints[0]);
	CumulativeDistances.Add(0.0f);

	for (int32 i = 1; i < PathPoints.Num(); ++i)
	{
		const FVector& From = PathPoints[i - 1];
		const FVector& To = PathPoints[i];
		const float SegLength = FVector::Dist(From, To);

		if (SegLength < 1.0f)
		{
			continue;
		}

		const FVector Dir = (To - From) / SegLength;
		float Walked = static_cast<float>(SampleInterval);

		while (Walked < SegLength)
		{
			SamplePoints.Add(From + Dir * Walked);
			TotalDist += static_cast<float>(SampleInterval);
			CumulativeDistances.Add(TotalDist);
			Walked += static_cast<float>(SampleInterval);
		}

		TotalDist += SegLength - (Walked - static_cast<float>(SampleInterval));
	}

	// Add final point
	if (SamplePoints.Num() > 0 && !SamplePoints.Last().Equals(PathPoints.Last(), 1.0f))
	{
		SamplePoints.Add(PathPoints.Last());
		CumulativeDistances.Add(TotalDist);
	}

	// Hard cap
	if (SamplePoints.Num() > 50)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Path generates %d sample points (max 50). Increase sample_interval or shorten path."),
			SamplePoints.Num()));
	}

	// Sample light levels using capture
	TArray<float> Luminances;
	Luminances.SetNumZeroed(SamplePoints.Num());

	{
		UTextureRenderTarget2D* RT = MonolithLightingCapture::CreateTransientRT(8, 8);
		USceneCaptureComponent2D* Capture = MonolithLightingCapture::CreateLightingCapture(World, RT);

		for (int32 i = 0; i < SamplePoints.Num(); ++i)
		{
			TArray<FLinearColor> Pixels;
			if (MonolithLightingCapture::CaptureAtPoint(Capture, SamplePoints[i], FRotator(-90.0f, 0.0f, 0.0f), Pixels))
			{
				Luminances[i] = MonolithLightingCapture::AverageLuminance(Pixels);
			}
		}

		MonolithLightingCapture::CleanupCapture(Capture);
	}

	// Build sample array and detect harsh transitions
	TArray<TSharedPtr<FJsonValue>> SamplesArr;
	TArray<TSharedPtr<FJsonValue>> TransitionsArr;

	float MinLum = FLT_MAX, MaxLum = 0.0f;

	for (int32 i = 0; i < SamplePoints.Num(); ++i)
	{
		TSharedPtr<FJsonObject> S = MakeShared<FJsonObject>();
		S->SetArrayField(TEXT("location"), MLight_VecToArr(SamplePoints[i]));
		S->SetNumberField(TEXT("distance_along_path"), CumulativeDistances[i]);
		S->SetNumberField(TEXT("luminance"), Luminances[i]);
		SamplesArr.Add(MakeShared<FJsonValueObject>(S));

		MinLum = FMath::Min(MinLum, Luminances[i]);
		MaxLum = FMath::Max(MaxLum, Luminances[i]);

		// Check transition from previous sample
		if (i > 0)
		{
			const float Prev = FMath::Max(Luminances[i - 1], 0.001f);
			const float Curr = FMath::Max(Luminances[i], 0.001f);
			const float Ratio = FMath::Max(Prev / Curr, Curr / Prev);
			const float Dist = CumulativeDistances[i] - CumulativeDistances[i - 1];

			if (Ratio >= HarshRatio && Dist <= HarshDistance)
			{
				TSharedPtr<FJsonObject> T = MakeShared<FJsonObject>();
				T->SetArrayField(TEXT("from"), MLight_VecToArr(SamplePoints[i - 1]));
				T->SetArrayField(TEXT("to"), MLight_VecToArr(SamplePoints[i]));
				T->SetNumberField(TEXT("from_luminance"), Luminances[i - 1]);
				T->SetNumberField(TEXT("to_luminance"), Luminances[i]);
				T->SetNumberField(TEXT("ratio"), Ratio);
				T->SetNumberField(TEXT("distance_cm"), Dist);
				T->SetStringField(TEXT("direction"), Luminances[i] > Luminances[i - 1] ? TEXT("dark_to_bright") : TEXT("bright_to_dark"));
				T->SetStringField(TEXT("severity"), Ratio >= HarshRatio * 2.0 ? TEXT("severe") : TEXT("harsh"));
				T->SetStringField(TEXT("hospice_note"),
					TEXT("Harsh light transitions can cause discomfort for patients with light sensitivity, migraines, or photophobia."));
				TransitionsArr.Add(MakeShared<FJsonValueObject>(T));
			}
		}
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetArrayField(TEXT("samples"), SamplesArr);
	Root->SetArrayField(TEXT("harsh_transitions"), TransitionsArr);
	Root->SetNumberField(TEXT("sample_count"), SamplePoints.Num());
	Root->SetNumberField(TEXT("harsh_transition_count"), TransitionsArr.Num());
	Root->SetNumberField(TEXT("path_length_cm"), TotalDist);
	Root->SetNumberField(TEXT("min_luminance"), MinLum);
	Root->SetNumberField(TEXT("max_luminance"), MaxLum);
	Root->SetNumberField(TEXT("luminance_range_ratio"),
		MinLum > 0.001f ? MaxLum / MinLum : (MaxLum > 0.0f ? 9999.0f : 1.0f));

	if (TransitionsArr.Num() > 0)
	{
		Root->SetStringField(TEXT("assessment"), TEXT("HARSH TRANSITIONS DETECTED — review for hospice accessibility"));
	}
	else
	{
		Root->SetStringField(TEXT("assessment"), TEXT("No harsh transitions — path lighting is gradual"));
	}

	return FMonolithActionResult::Success(Root);
}

// ============================================================================
// 4. get_light_coverage
// ============================================================================

FMonolithActionResult FMonolithMeshLightingActions::GetLightCoverage(const TSharedPtr<FJsonObject>& Params)
{
	FString VolumeName;
	if (!Params->TryGetStringField(TEXT("volume_name"), VolumeName) || VolumeName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: volume_name"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString Error;
	AActor* Volume = MonolithMeshUtils::FindActorByName(VolumeName, Error);
	if (!Volume)
	{
		return FMonolithActionResult::Error(Error);
	}

	FVector Center, Extent;
	Volume->GetActorBounds(false, Center, Extent);

	double ResolutionD = 128.0;
	Params->TryGetNumberField(TEXT("resolution"), ResolutionD);
	int32 Resolution = FMath::Clamp(static_cast<int32>(ResolutionD), 16, 256);

	double DarkThreshold = 0.05;
	Params->TryGetNumberField(TEXT("dark_threshold"), DarkThreshold);

	double BrightThreshold = 0.2;
	Params->TryGetNumberField(TEXT("bright_threshold"), BrightThreshold);

	// Capture coverage
	MonolithLightingCapture::FCoverageResult Coverage =
		MonolithLightingCapture::CaptureCoverageMap(World, Center, Extent, Resolution,
			static_cast<float>(DarkThreshold), static_cast<float>(BrightThreshold));

	if (Coverage.LuminanceGrid.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Scene capture failed"));
	}

	// Luminance histogram (10 buckets)
	TArray<int32> Histogram;
	Histogram.SetNumZeroed(10);
	for (float Lum : Coverage.LuminanceGrid)
	{
		int32 Bucket = FMath::Clamp(static_cast<int32>(Lum * 10.0f), 0, 9);
		++Histogram[Bucket];
	}

	TArray<TSharedPtr<FJsonValue>> HistArr;
	const TArray<FString> BucketLabels = {
		TEXT("0.0-0.1"), TEXT("0.1-0.2"), TEXT("0.2-0.3"), TEXT("0.3-0.4"), TEXT("0.4-0.5"),
		TEXT("0.5-0.6"), TEXT("0.6-0.7"), TEXT("0.7-0.8"), TEXT("0.8-0.9"), TEXT("0.9-1.0+")
	};
	for (int32 i = 0; i < 10; ++i)
	{
		TSharedPtr<FJsonObject> Bucket = MakeShared<FJsonObject>();
		Bucket->SetStringField(TEXT("range"), BucketLabels[i]);
		Bucket->SetNumberField(TEXT("count"), Histogram[i]);
		Bucket->SetNumberField(TEXT("percent"),
			Coverage.GridWidth * Coverage.GridHeight > 0
			? 100.0f * Histogram[i] / (Coverage.GridWidth * Coverage.GridHeight)
			: 0.0f);
		HistArr.Add(MakeShared<FJsonValueObject>(Bucket));
	}

	// Light inventory
	FBox Region(Center - Extent, Center + Extent);
	TArray<MonolithLightingCapture::FLightInfo> Lights =
		MonolithLightingCapture::GatherLightsInRegion(World, Region);

	TArray<TSharedPtr<FJsonValue>> LightArr;
	int32 ShadowCasterCount = 0;
	for (const MonolithLightingCapture::FLightInfo& L : Lights)
	{
		LightArr.Add(MakeShared<FJsonValueObject>(LightInfoToJson(L)));
		if (L.bCastsShadows)
		{
			++ShadowCasterCount;
		}
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("volume"), VolumeName);
	Root->SetNumberField(TEXT("percent_lit"), Coverage.PercentLit);
	Root->SetNumberField(TEXT("percent_shadow"), Coverage.PercentShadow);
	Root->SetNumberField(TEXT("percent_dark"), Coverage.PercentDark);
	Root->SetArrayField(TEXT("luminance_histogram"), HistArr);
	Root->SetArrayField(TEXT("lights"), LightArr);
	Root->SetNumberField(TEXT("light_count"), Lights.Num());
	Root->SetNumberField(TEXT("shadow_caster_count"), ShadowCasterCount);
	Root->SetNumberField(TEXT("capture_resolution"), Resolution);

	return FMonolithActionResult::Success(Root);
}

// ============================================================================
// 5. suggest_light_placement
// ============================================================================

FMonolithActionResult FMonolithMeshLightingActions::SuggestLightPlacement(const TSharedPtr<FJsonObject>& Params)
{
	FString VolumeName;
	if (!Params->TryGetStringField(TEXT("volume_name"), VolumeName) || VolumeName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: volume_name"));
	}

	FString Mood;
	if (!Params->TryGetStringField(TEXT("mood"), Mood) || Mood.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: mood (horror_dim, safe_room, clinical, ambient)"));
	}
	Mood = Mood.ToLower();

	if (Mood != TEXT("horror_dim") && Mood != TEXT("safe_room") && Mood != TEXT("clinical") && Mood != TEXT("ambient"))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Invalid mood '%s'. Valid: horror_dim, safe_room, clinical, ambient"), *Mood));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString Error;
	AActor* Volume = MonolithMeshUtils::FindActorByName(VolumeName, Error);
	if (!Volume)
	{
		return FMonolithActionResult::Error(Error);
	}

	FVector Center, Extent;
	Volume->GetActorBounds(false, Center, Extent);

	double MaxLightsD = 8.0;
	Params->TryGetNumberField(TEXT("max_lights"), MaxLightsD);
	int32 MaxLights = FMath::Clamp(static_cast<int32>(MaxLightsD), 1, 20);

	FMoodConfig Config = GetMoodConfig(Mood);

	// Gather existing lights
	FBox Region(Center - Extent, Center + Extent);
	TArray<MonolithLightingCapture::FLightInfo> ExistingLights =
		MonolithLightingCapture::GatherLightsInRegion(World, Region);

	// Sample current lighting on a grid
	const int32 GridSize = 4; // 4x4 sample grid on the floor
	const float StepX = (Extent.X * 2.0f) / (GridSize + 1);
	const float StepY = (Extent.Y * 2.0f) / (GridSize + 1);

	struct FGridSample
	{
		FVector Location;
		float AnalyticLuminance;
		bool bNeedsLight;
	};

	TArray<FGridSample> GridSamples;
	const float FloorZ = Center.Z - Extent.Z + 10.0f; // Slightly above floor

	for (int32 gy = 1; gy <= GridSize; ++gy)
	{
		for (int32 gx = 1; gx <= GridSize; ++gx)
		{
			FGridSample S;
			S.Location = FVector(
				Center.X - Extent.X + StepX * gx,
				Center.Y - Extent.Y + StepY * gy,
				FloorZ);

			int32 Dummy;
			S.AnalyticLuminance = MonolithLightingCapture::ComputeAnalyticLuminance(
				World, S.Location, ExistingLights, Dummy);
			S.bNeedsLight = S.AnalyticLuminance < Config.TargetLuminance * 0.5f;

			GridSamples.Add(S);
		}
	}

	// Sort grid cells by luminance (darkest first — those need lights most)
	GridSamples.Sort([](const FGridSample& A, const FGridSample& B)
	{
		return A.AnalyticLuminance < B.AnalyticLuminance;
	});

	// Suggest lights at dark positions
	// Inverse-square backward-solve: I = TargetLuminance * d^2
	// Place light at ceiling height above the dark point
	const float CeilingZ = Center.Z + Extent.Z - 30.0f; // Near ceiling
	const float LightHeight = CeilingZ - FloorZ;

	TArray<TSharedPtr<FJsonValue>> Suggestions;
	TArray<FVector> PlacedPositions; // Track to avoid overlap

	for (const FGridSample& S : GridSamples)
	{
		if (Suggestions.Num() >= MaxLights)
		{
			break;
		}

		if (!S.bNeedsLight)
		{
			continue;
		}

		// Check overlap with existing lights and already-suggested lights
		FVector ProposedPos(S.Location.X, S.Location.Y, CeilingZ);
		bool bTooClose = false;

		for (const MonolithLightingCapture::FLightInfo& L : ExistingLights)
		{
			if (L.Type != TEXT("Directional") && FVector::Dist(L.Location, ProposedPos) < 200.0f)
			{
				bTooClose = true;
				break;
			}
		}

		for (const FVector& P : PlacedPositions)
		{
			if (FVector::Dist(P, ProposedPos) < 200.0f)
			{
				bTooClose = true;
				break;
			}
		}

		if (bTooClose)
		{
			continue;
		}

		// Backward-solve intensity: I = TargetLuminance * d^2
		const float DistSq = LightHeight * LightHeight;
		const float SuggestedIntensity = Config.TargetLuminance * DistSq;

		// Attenuation radius: enough to cover from ceiling to floor + some spread
		const float SuggestedRadius = LightHeight * 1.5f;

		TSharedPtr<FJsonObject> Suggestion = MakeShared<FJsonObject>();
		Suggestion->SetStringField(TEXT("type"), Config.LightType);
		Suggestion->SetArrayField(TEXT("position"), MLight_VecToArr(ProposedPos));
		Suggestion->SetNumberField(TEXT("intensity"), SuggestedIntensity);
		Suggestion->SetNumberField(TEXT("attenuation_radius"), SuggestedRadius);
		Suggestion->SetNumberField(TEXT("color_temperature"), Config.PreferredColorTemp);
		Suggestion->SetBoolField(TEXT("cast_shadows"), Mood != TEXT("clinical")); // Clinical = flat
		Suggestion->SetNumberField(TEXT("floor_luminance_at_point"), S.AnalyticLuminance);
		Suggestion->SetStringField(TEXT("reasoning"), FString::Printf(
			TEXT("Floor point at (%.0f, %.0f) has luminance %.4f, below target %.4f. %s light at ceiling height %.0fcm."),
			S.Location.X, S.Location.Y, S.AnalyticLuminance, Config.TargetLuminance,
			*Config.LightType, LightHeight));

		Suggestions.Add(MakeShared<FJsonValueObject>(Suggestion));
		PlacedPositions.Add(ProposedPos);
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("volume"), VolumeName);
	Root->SetStringField(TEXT("mood"), Mood);
	Root->SetStringField(TEXT("mood_description"), Config.Description);
	Root->SetNumberField(TEXT("target_luminance"), Config.TargetLuminance);
	Root->SetNumberField(TEXT("suggested_light_count"), Suggestions.Num());
	Root->SetArrayField(TEXT("suggestions"), Suggestions);
	Root->SetNumberField(TEXT("existing_light_count"), ExistingLights.Num());

	// Existing lights summary
	TArray<TSharedPtr<FJsonValue>> ExistingArr;
	for (const MonolithLightingCapture::FLightInfo& L : ExistingLights)
	{
		ExistingArr.Add(MakeShared<FJsonValueObject>(LightInfoToJson(L)));
	}
	Root->SetArrayField(TEXT("existing_lights"), ExistingArr);

	if (Suggestions.Num() == 0)
	{
		Root->SetStringField(TEXT("assessment"), TEXT("Existing lighting already meets target luminance for this mood — no additional lights needed"));
	}
	else
	{
		Root->SetStringField(TEXT("assessment"), FString::Printf(
			TEXT("%d lights suggested to achieve %s mood. Review positions and adjust intensity to taste."),
			Suggestions.Num(), *Mood));
	}

	return FMonolithActionResult::Success(Root);
}
