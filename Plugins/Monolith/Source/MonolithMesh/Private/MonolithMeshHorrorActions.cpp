#include "MonolithMeshHorrorActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithMeshAnalysis.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "CollisionQueryParams.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "AI/Navigation/NavigationTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshHorrorActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. analyze_sightlines
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_sightlines"),
		TEXT("Fan-of-rays sightline analysis from a location. Returns claustrophobia score 0-100, blocked percentages at distance thresholds, longest clear sightline."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::AnalyzeSightlines),
		FParamSchemaBuilder()
			.Required(TEXT("location"), TEXT("array"), TEXT("Origin position [x, y, z]"))
			.Optional(TEXT("forward"), TEXT("array"), TEXT("Player facing direction [x, y, z] (default: +X)"), TEXT(""))
			.Optional(TEXT("fov"), TEXT("number"), TEXT("Field of view in degrees"), TEXT("90"))
			.Optional(TEXT("ray_count"), TEXT("integer"), TEXT("Number of rays to cast within FOV"), TEXT("36"))
			.Optional(TEXT("max_distance"), TEXT("number"), TEXT("Maximum ray distance in cm"), TEXT("5000"))
			.Build());

	// 2. find_hiding_spots
	Registry.RegisterAction(TEXT("mesh"), TEXT("find_hiding_spots"),
		TEXT("Grid-sample a region and score each point for concealment from given viewpoints. Returns spots sorted by quality."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::FindHidingSpots),
		FParamSchemaBuilder()
			.Required(TEXT("region_min"), TEXT("array"), TEXT("Min corner of search region [x, y, z]"))
			.Required(TEXT("region_max"), TEXT("array"), TEXT("Max corner of search region [x, y, z]"))
			.Required(TEXT("viewpoints"), TEXT("array"), TEXT("Array of viewpoint positions [[x,y,z], ...]"))
			.Optional(TEXT("grid_size"), TEXT("number"), TEXT("Grid spacing in cm"), TEXT("100"))
			.Optional(TEXT("min_concealment"), TEXT("number"), TEXT("Minimum concealment threshold 0-1"), TEXT("0.6"))
			.Build());

	// 3. find_ambush_points
	Registry.RegisterAction(TEXT("mesh"), TEXT("find_ambush_points"),
		TEXT("Find ambush positions lateral to a path. Scores concealment + surprise angle (180 degrees from player forward = perfect ambush)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::FindAmbushPoints),
		FParamSchemaBuilder()
			.Required(TEXT("path_points"), TEXT("array"), TEXT("Array of path positions [[x,y,z], ...]"))
			.Optional(TEXT("lateral_range"), TEXT("number"), TEXT("Max lateral distance to sample in cm"), TEXT("500"))
			.Optional(TEXT("concealment_threshold"), TEXT("number"), TEXT("Min concealment to qualify 0-1"), TEXT("0.7"))
			.Build());

	// 4. analyze_choke_points
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_choke_points"),
		TEXT("Find narrow passages along a navmesh path. Returns choke points with width, flank possibility, and bypass routes."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::AnalyzeChokePoints),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Start position [x, y, z]"))
			.Required(TEXT("end"), TEXT("array"), TEXT("End position [x, y, z]"))
			.Optional(TEXT("agent_radius"), TEXT("number"), TEXT("Navigation agent radius in cm"), TEXT("45"))
			.Build());

	// 5. analyze_escape_routes
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_escape_routes"),
		TEXT("Find and score escape routes from a location to tagged exit actors. Critical for hospice: ensures no inescapable encounters."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::AnalyzeEscapeRoutes),
		FParamSchemaBuilder()
			.Required(TEXT("location"), TEXT("array"), TEXT("Player position [x, y, z]"))
			.Optional(TEXT("exit_tags"), TEXT("array"), TEXT("Actor tags to search for as exits"), TEXT(""))
			.Optional(TEXT("max_routes"), TEXT("integer"), TEXT("Maximum routes to return"), TEXT("5"))
			.Build());

	// 6. classify_zone_tension
	Registry.RegisterAction(TEXT("mesh"), TEXT("classify_zone_tension"),
		TEXT("Composite tension analysis: sightline distance + ceiling height + room volume + exit count. Returns calm/uneasy/tense/dread/panic."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::ClassifyZoneTension),
		FParamSchemaBuilder()
			.Required(TEXT("location"), TEXT("array"), TEXT("Center of zone to analyze [x, y, z]"))
			.Optional(TEXT("radius"), TEXT("number"), TEXT("Analysis radius in cm"), TEXT("500"))
			.Build());

	// 7. analyze_pacing_curve
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_pacing_curve"),
		TEXT("Sample tension at intervals along a path. Identifies monotonous stretches, optimal scare placement, and false-calm opportunities."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::AnalyzePacingCurve),
		FParamSchemaBuilder()
			.Required(TEXT("path_points"), TEXT("array"), TEXT("Array of path positions [[x,y,z], ...]"))
			.Optional(TEXT("sample_interval"), TEXT("number"), TEXT("Distance between samples in cm"), TEXT("200"))
			.Build());

	// 8. find_dead_ends
	Registry.RegisterAction(TEXT("mesh"), TEXT("find_dead_ends"),
		TEXT("Navmesh flood-fill to find single-exit (dead-end) regions. Returns depth, width, exit direction for each."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshHorrorActions::FindDeadEnds),
		FParamSchemaBuilder()
			.Optional(TEXT("region_min"), TEXT("array"), TEXT("Min corner [x, y, z] (default: whole navmesh)"), TEXT(""))
			.Optional(TEXT("region_max"), TEXT("array"), TEXT("Max corner [x, y, z] (default: whole navmesh)"), TEXT(""))
			.Optional(TEXT("grid_size"), TEXT("number"), TEXT("Flood-fill grid spacing in cm"), TEXT("200"))
			.Build());
}

// ============================================================================
// Helpers
// ============================================================================

namespace
{
	TArray<TSharedPtr<FJsonValue>> MHorror_VecToArr(const FVector& V)
	{
		return MonolithMeshAnalysis::VectorToJsonArray(V);
	}

	/** Parse an array of [x,y,z] arrays from a JSON field */
	bool MHorror_ParseVectorArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FVector>& Out)
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
}

// ============================================================================
// 1. analyze_sightlines
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::AnalyzeSightlines(const TSharedPtr<FJsonObject>& Params)
{
	FVector Location;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: location (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Parse forward direction
	FVector Forward = FVector::ForwardVector;
	MonolithMeshUtils::ParseVector(Params, TEXT("forward"), Forward);
	Forward = Forward.GetSafeNormal();
	if (Forward.IsNearlyZero())
	{
		Forward = FVector::ForwardVector;
	}

	double FOV = 90.0;
	Params->TryGetNumberField(TEXT("fov"), FOV);
	FOV = FMath::Clamp(FOV, 10.0, 360.0);

	int32 RayCount = 36;
	double RayCountD;
	if (Params->TryGetNumberField(TEXT("ray_count"), RayCountD))
	{
		RayCount = FMath::Clamp(static_cast<int32>(RayCountD), 4, 128);
	}

	double MaxDistance = 5000.0;
	Params->TryGetNumberField(TEXT("max_distance"), MaxDistance);
	MaxDistance = FMath::Clamp(MaxDistance, 100.0, 100000.0);

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithSightlines), true);

	// Compute the right vector for the fan spread
	FVector Right = FVector::CrossProduct(Forward, FVector::UpVector).GetSafeNormal();
	if (Right.IsNearlyZero())
	{
		Right = FVector::RightVector;
	}

	float HalfFOVRad = FMath::DegreesToRadians(static_cast<float>(FOV) * 0.5f);

	TArray<float> Distances;
	Distances.Reserve(RayCount);

	float LongestDistance = 0.0f;
	FVector LongestDirection = Forward;
	int32 Blocked5m = 0, Blocked10m = 0, Blocked20m = 0;

	// Raise origin to eye height
	FVector Origin = Location + FVector(0, 0, 170.0f);

	for (int32 i = 0; i < RayCount; ++i)
	{
		// Spread rays evenly within the FOV
		float T = (RayCount == 1) ? 0.0f : (static_cast<float>(i) / static_cast<float>(RayCount - 1));
		float Angle = FMath::Lerp(-HalfFOVRad, HalfFOVRad, T);

		FVector Dir = Forward * FMath::Cos(Angle) + Right * FMath::Sin(Angle);
		Dir.Normalize();

		FVector End = Origin + Dir * static_cast<float>(MaxDistance);

		FHitResult Hit;
		bool bHit = World->LineTraceSingleByChannel(Hit, Origin, End, ECC_Visibility, QueryParams);

		float Dist = bHit ? Hit.Distance : static_cast<float>(MaxDistance);
		Distances.Add(Dist);

		if (Dist > LongestDistance)
		{
			LongestDistance = Dist;
			LongestDirection = Dir;
		}

		if (Dist < 500.0f)  ++Blocked5m;
		if (Dist < 1000.0f) ++Blocked10m;
		if (Dist < 2000.0f) ++Blocked20m;
	}

	// Compute average
	float Sum = 0.0f;
	for (float D : Distances) Sum += D;
	float AvgDistance = Sum / static_cast<float>(Distances.Num());

	// Claustrophobia score: shorter average sightlines = higher score
	// 0cm avg -> 100, 200cm -> 80, 1000cm -> 40, 5000cm -> 0
	float ClaustroScore = FMath::Clamp(100.0f * (1.0f - (AvgDistance / static_cast<float>(MaxDistance))), 0.0f, 100.0f);

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("claustrophobia_score"), FMath::RoundToInt(ClaustroScore));
	Result->SetNumberField(TEXT("blocked_pct_5m"), FMath::RoundToInt(100.0f * static_cast<float>(Blocked5m) / static_cast<float>(RayCount)));
	Result->SetNumberField(TEXT("blocked_pct_10m"), FMath::RoundToInt(100.0f * static_cast<float>(Blocked10m) / static_cast<float>(RayCount)));
	Result->SetNumberField(TEXT("blocked_pct_20m"), FMath::RoundToInt(100.0f * static_cast<float>(Blocked20m) / static_cast<float>(RayCount)));
	Result->SetNumberField(TEXT("longest_clear_sightline"), LongestDistance);
	Result->SetArrayField(TEXT("direction_of_longest"), MHorror_VecToArr(LongestDirection));
	Result->SetNumberField(TEXT("average_sightline_distance"), AvgDistance);
	Result->SetNumberField(TEXT("ray_count"), RayCount);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. find_hiding_spots
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::FindHidingSpots(const TSharedPtr<FJsonObject>& Params)
{
	FVector RegionMin, RegionMax;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_min"), RegionMin))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_min"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("region_max"), RegionMax))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region_max"));
	}

	TArray<FVector> Viewpoints;
	if (!MHorror_ParseVectorArray(Params, TEXT("viewpoints"), Viewpoints))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: viewpoints (array of [x,y,z])"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	double GridSize = 100.0;
	Params->TryGetNumberField(TEXT("grid_size"), GridSize);
	GridSize = FMath::Clamp(GridSize, 25.0, 1000.0);

	double MinConcealment = 0.6;
	Params->TryGetNumberField(TEXT("min_concealment"), MinConcealment);
	MinConcealment = FMath::Clamp(MinConcealment, 0.0, 1.0);

	// Grid sample the region
	FVector Size = RegionMax - RegionMin;
	int32 XCount = FMath::Max(1, FMath::CeilToInt(Size.X / GridSize));
	int32 YCount = FMath::Max(1, FMath::CeilToInt(Size.Y / GridSize));

	// Cap grid to prevent runaway
	const int32 MaxSamples = 2500;
	if (XCount * YCount > MaxSamples)
	{
		float Scale = FMath::Sqrt(static_cast<float>(MaxSamples) / static_cast<float>(XCount * YCount));
		XCount = FMath::Max(1, FMath::FloorToInt(XCount * Scale));
		YCount = FMath::Max(1, FMath::FloorToInt(YCount * Scale));
	}

	// Check navmesh availability for point validation
	UNavigationSystemV1* NavSys = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);

	struct FSpot
	{
		FVector Location;
		float Concealment;
	};

	TArray<FSpot> Spots;

	for (int32 X = 0; X < XCount; ++X)
	{
		for (int32 Y = 0; Y < YCount; ++Y)
		{
			FVector TestPt = RegionMin + FVector(
				(static_cast<float>(X) + 0.5f) * static_cast<float>(GridSize),
				(static_cast<float>(Y) + 0.5f) * static_cast<float>(GridSize),
				Size.Z * 0.5f);

			// Project to navmesh if available (ensures point is walkable)
			if (NavSys)
			{
				FNavLocation NavLoc;
				if (!NavSys->ProjectPointToNavigation(TestPt, NavLoc, FVector(static_cast<float>(GridSize) * 0.5f, static_cast<float>(GridSize) * 0.5f, 500.0f)))
				{
					continue; // Not on navmesh — skip
				}
				TestPt = NavLoc.Location;
			}

			float Concealment = MonolithMeshAnalysis::ComputeConcealment(World, TestPt, Viewpoints);
			if (Concealment >= static_cast<float>(MinConcealment))
			{
				Spots.Add({ TestPt, Concealment });
			}
		}
	}

	// Sort by concealment descending
	Spots.Sort([](const FSpot& A, const FSpot& B) { return A.Concealment > B.Concealment; });

	// Cap output
	const int32 MaxResults = 50;
	if (Spots.Num() > MaxResults)
	{
		Spots.SetNum(MaxResults);
	}

	TArray<TSharedPtr<FJsonValue>> SpotsArr;
	for (const FSpot& S : Spots)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(S.Location));
		Obj->SetNumberField(TEXT("concealment"), S.Concealment);
		SpotsArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("spots_found"), Spots.Num());
	Result->SetArrayField(TEXT("hiding_spots"), SpotsArr);
	Result->SetNumberField(TEXT("grid_samples"), XCount * YCount);
	Result->SetNumberField(TEXT("min_concealment"), MinConcealment);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. find_ambush_points
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::FindAmbushPoints(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FVector> PathPoints;
	if (!MHorror_ParseVectorArray(Params, TEXT("path_points"), PathPoints) || PathPoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: path_points (array of at least 2 [x,y,z])"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	double LateralRange = 500.0;
	Params->TryGetNumberField(TEXT("lateral_range"), LateralRange);

	double ConcealmentThreshold = 0.7;
	Params->TryGetNumberField(TEXT("concealment_threshold"), ConcealmentThreshold);

	struct FAmbushPoint
	{
		FVector Location;
		float Concealment;
		float SurpriseAngle; // 0-180, 180 = perfect (behind player)
		float Score;         // Combined
		int32 PathSegment;
	};

	TArray<FAmbushPoint> Ambushes;
	const int32 LateralSamples = 5;

	for (int32 i = 0; i < PathPoints.Num() - 1; ++i)
	{
		FVector SegDir = (PathPoints[i + 1] - PathPoints[i]).GetSafeNormal();
		FVector Right = FVector::CrossProduct(SegDir, FVector::UpVector).GetSafeNormal();
		if (Right.IsNearlyZero()) Right = FVector::RightVector;

		FVector SegMid = (PathPoints[i] + PathPoints[i + 1]) * 0.5f;

		for (int32 s = 0; s < LateralSamples; ++s)
		{
			// Sample left and right
			float Dist = static_cast<float>(LateralRange) * (static_cast<float>(s + 1) / static_cast<float>(LateralSamples));

			for (float Side : { 1.0f, -1.0f })
			{
				FVector TestPt = SegMid + Right * Side * Dist;

				// Viewpoint is the path midpoint (where the player would be)
				TArray<FVector> Viewpoints = { SegMid };
				float Concealment = MonolithMeshAnalysis::ComputeConcealment(World, TestPt, Viewpoints);

				if (Concealment < static_cast<float>(ConcealmentThreshold))
				{
					continue;
				}

				// Surprise angle: angle between player's forward direction and direction to ambush point
				FVector ToAmbush = (TestPt - SegMid).GetSafeNormal();
				float DotVal = FVector::DotProduct(SegDir, ToAmbush);
				float SurpriseAngle = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(DotVal, -1.0f, 1.0f)));
				// 180 = directly behind player (perfect), 0 = in front (bad ambush)

				float Score = Concealment * (SurpriseAngle / 180.0f);

				FAmbushPoint AP;
				AP.Location = TestPt;
				AP.Concealment = Concealment;
				AP.SurpriseAngle = SurpriseAngle;
				AP.Score = Score;
				AP.PathSegment = i;
				Ambushes.Add(AP);
			}
		}
	}

	// Sort by combined score descending
	Ambushes.Sort([](const FAmbushPoint& A, const FAmbushPoint& B) { return A.Score > B.Score; });

	const int32 MaxResults = 30;
	if (Ambushes.Num() > MaxResults)
	{
		Ambushes.SetNum(MaxResults);
	}

	TArray<TSharedPtr<FJsonValue>> AmbushArr;
	for (const FAmbushPoint& AP : Ambushes)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(AP.Location));
		Obj->SetNumberField(TEXT("concealment"), AP.Concealment);
		Obj->SetNumberField(TEXT("surprise_angle"), AP.SurpriseAngle);
		Obj->SetNumberField(TEXT("score"), AP.Score);
		Obj->SetNumberField(TEXT("path_segment"), AP.PathSegment);
		AmbushArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("ambush_points_found"), Ambushes.Num());
	Result->SetArrayField(TEXT("ambush_points"), AmbushArr);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. analyze_choke_points
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::AnalyzeChokePoints(const TSharedPtr<FJsonObject>& Params)
{
	FVector Start, End;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("start"), Start))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: start"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("end"), End))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: end"));
	}

	double AgentRadius = 45.0;
	Params->TryGetNumberField(TEXT("agent_radius"), AgentRadius);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Find navmesh path
	TArray<FVector> PathPoints;
	float PathDist;
	if (!MonolithMeshAnalysis::FindNavPath(World, Start, End, PathPoints, PathDist, static_cast<float>(AgentRadius)))
	{
		return FMonolithActionResult::Error(TEXT("No navmesh path found between start and end. Build navigation first."));
	}

	// Measure clearance along path
	TArray<MonolithMeshAnalysis::FPathClearance> Clearances = MonolithMeshAnalysis::MeasurePathClearance(World, PathPoints, 500.0f);

	// Find choke points — where width drops below threshold
	// A doorway is typically ~90cm, a corridor ~150cm, a comfortable passage ~250cm
	float ChokeThreshold = static_cast<float>(AgentRadius) * 4.0f; // ~180cm for standard agent

	struct FChokePoint
	{
		FVector Location;
		float Width;
		FString LeftObstruction;
		FString RightObstruction;
		bool bFlankPossible;
	};

	TArray<FChokePoint> Chokes;

	for (int32 i = 0; i < Clearances.Num(); ++i)
	{
		const auto& C = Clearances[i];
		if (C.TotalWidth < ChokeThreshold)
		{
			// Check if flanking is possible via alternate navmesh path
			// Offset start perpendicular, see if we can reach the other side
			FVector Forward = FVector::ZeroVector;
			if (i < Clearances.Num() - 1)
			{
				Forward = (Clearances[i + 1].Location - C.Location).GetSafeNormal();
			}
			else if (i > 0)
			{
				Forward = (C.Location - Clearances[i - 1].Location).GetSafeNormal();
			}

			FVector Perp = FVector::CrossProduct(Forward, FVector::UpVector).GetSafeNormal();
			if (Perp.IsNearlyZero()) Perp = FVector::RightVector;

			bool bFlank = false;
			// Try to find path around the choke
			FVector FlankStart = C.Location + Perp * 300.0f;
			FVector FlankEnd = C.Location - Perp * 300.0f;
			TArray<FVector> FlankPath;
			float FlankDist;
			if (MonolithMeshAnalysis::FindNavPath(World, FlankStart, FlankEnd, FlankPath, FlankDist))
			{
				// Flanking possible if alternate path doesn't also go through the choke
				bFlank = FlankDist < 1500.0f; // Reasonable flank distance
			}

			FChokePoint CP;
			CP.Location = C.Location;
			CP.Width = C.TotalWidth;
			CP.LeftObstruction = C.LeftObstruction;
			CP.RightObstruction = C.RightObstruction;
			CP.bFlankPossible = bFlank;
			Chokes.Add(CP);
		}
	}

	// Merge nearby choke points (within 200cm)
	TArray<FChokePoint> MergedChokes;
	for (const FChokePoint& CP : Chokes)
	{
		bool bMerged = false;
		for (FChokePoint& Existing : MergedChokes)
		{
			if (FVector::Dist(CP.Location, Existing.Location) < 200.0f)
			{
				// Keep the narrowest
				if (CP.Width < Existing.Width)
				{
					Existing = CP;
				}
				bMerged = true;
				break;
			}
		}
		if (!bMerged)
		{
			MergedChokes.Add(CP);
		}
	}

	TArray<TSharedPtr<FJsonValue>> ChokesArr;
	for (const FChokePoint& CP : MergedChokes)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(CP.Location));
		Obj->SetNumberField(TEXT("width"), CP.Width);
		Obj->SetStringField(TEXT("left_obstruction"), CP.LeftObstruction);
		Obj->SetStringField(TEXT("right_obstruction"), CP.RightObstruction);
		Obj->SetBoolField(TEXT("flank_possible"), CP.bFlankPossible);
		ChokesArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("choke_points_found"), MergedChokes.Num());
	Result->SetArrayField(TEXT("choke_points"), ChokesArr);
	Result->SetNumberField(TEXT("path_distance"), PathDist);
	Result->SetNumberField(TEXT("choke_threshold"), ChokeThreshold);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 5. analyze_escape_routes
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::AnalyzeEscapeRoutes(const TSharedPtr<FJsonObject>& Params)
{
	FVector Location;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: location"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Parse exit tags
	TArray<FString> ExitTags;
	const TArray<TSharedPtr<FJsonValue>>* TagsArr;
	if (Params->TryGetArrayField(TEXT("exit_tags"), TagsArr))
	{
		for (const auto& V : *TagsArr)
		{
			ExitTags.Add(V->AsString());
		}
	}
	if (ExitTags.Num() == 0)
	{
		ExitTags.Add(TEXT("SafeRoom"));
		ExitTags.Add(TEXT("Exit"));
	}

	int32 MaxRoutes = 5;
	double MaxRoutesD;
	if (Params->TryGetNumberField(TEXT("max_routes"), MaxRoutesD))
	{
		MaxRoutes = FMath::Clamp(static_cast<int32>(MaxRoutesD), 1, 20);
	}

	// Find all actors with exit tags
	struct FExitActor
	{
		AActor* Actor;
		FString Name;
		FString Tag;
	};

	TArray<FExitActor> Exits;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		for (const FName& ActorTag : Actor->Tags)
		{
			FString TagStr = ActorTag.ToString();
			for (const FString& ExitTag : ExitTags)
			{
				if (TagStr.Contains(ExitTag, ESearchCase::IgnoreCase))
				{
					FExitActor EA;
					EA.Actor = Actor;
					EA.Name = Actor->GetActorNameOrLabel();
					EA.Tag = TagStr;
					Exits.Add(EA);
					break;
				}
			}
		}
	}

	if (Exits.Num() == 0)
	{
		auto Result = MakeShared<FJsonObject>();
		Result->SetNumberField(TEXT("routes_found"), 0);
		Result->SetArrayField(TEXT("escape_routes"), TArray<TSharedPtr<FJsonValue>>());
		Result->SetStringField(TEXT("warning"), FString::Printf(
			TEXT("No actors found with tags: [%s]. Tag exit points in your level."),
			*FString::Join(ExitTags, TEXT(", "))));
		return FMonolithActionResult::Success(Result);
	}

	// Path to each exit, score it
	struct FRoute
	{
		FString ExitName;
		FString ExitTag;
		float Distance;
		float ThreatExposure; // 0-1, how exposed the path is
		int32 TurnCount;
		TArray<FVector> PathPoints;
	};

	TArray<FRoute> Routes;
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithEscape), true);

	for (const FExitActor& Exit : Exits)
	{
		FVector ExitLoc = Exit.Actor->GetActorLocation();
		TArray<FVector> PathPts;
		float PathDist;

		if (!MonolithMeshAnalysis::FindNavPath(World, Location, ExitLoc, PathPts, PathDist))
		{
			continue;
		}

		FRoute Route;
		Route.ExitName = Exit.Name;
		Route.ExitTag = Exit.Tag;
		Route.Distance = PathDist;
		Route.PathPoints = PathPts;

		// Compute threat exposure: sample sightlines along path
		int32 ExposedSamples = 0;
		int32 TotalSamples = 0;
		for (int32 i = 0; i < PathPts.Num(); i += 2) // Sample every other point
		{
			FVector SamplePt = PathPts[i] + FVector(0, 0, 90.0f);
			// Count how many directions have long sightlines (exposed)
			int32 LongSightlines = 0;
			for (int32 d = 0; d < 8; ++d)
			{
				float Angle = (2.0f * PI / 8.0f) * static_cast<float>(d);
				FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
				FHitResult Hit;
				bool bHit = World->LineTraceSingleByChannel(Hit, SamplePt, SamplePt + Dir * 2000.0f, ECC_Visibility, QueryParams);
				if (!bHit || Hit.Distance > 1000.0f)
				{
					++LongSightlines;
				}
			}
			if (LongSightlines >= 4) ++ExposedSamples;
			++TotalSamples;
		}
		Route.ThreatExposure = TotalSamples > 0 ? static_cast<float>(ExposedSamples) / static_cast<float>(TotalSamples) : 0.0f;

		// Count turns (direction changes > 45 degrees)
		Route.TurnCount = 0;
		for (int32 i = 1; i < PathPts.Num() - 1; ++i)
		{
			FVector Dir1 = (PathPts[i] - PathPts[i - 1]).GetSafeNormal();
			FVector Dir2 = (PathPts[i + 1] - PathPts[i]).GetSafeNormal();
			float Dot = FVector::DotProduct(Dir1, Dir2);
			if (Dot < 0.707f) // > ~45 degrees
			{
				++Route.TurnCount;
			}
		}

		Routes.Add(MoveTemp(Route));
	}

	// Score routes: lower distance + lower exposure + fewer turns = better
	Routes.Sort([](const FRoute& A, const FRoute& B)
	{
		// Weighted score: distance (normalized) + exposure + turns
		float ScoreA = (A.Distance / 10000.0f) + A.ThreatExposure * 2.0f + static_cast<float>(A.TurnCount) * 0.1f;
		float ScoreB = (B.Distance / 10000.0f) + B.ThreatExposure * 2.0f + static_cast<float>(B.TurnCount) * 0.1f;
		return ScoreA < ScoreB;
	});

	if (Routes.Num() > MaxRoutes)
	{
		Routes.SetNum(MaxRoutes);
	}

	TArray<TSharedPtr<FJsonValue>> RoutesArr;
	for (const FRoute& R : Routes)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("exit_name"), R.ExitName);
		Obj->SetStringField(TEXT("exit_tag"), R.ExitTag);
		Obj->SetNumberField(TEXT("distance"), R.Distance);
		Obj->SetNumberField(TEXT("threat_exposure"), R.ThreatExposure);
		Obj->SetNumberField(TEXT("turn_count"), R.TurnCount);
		Obj->SetNumberField(TEXT("path_point_count"), R.PathPoints.Num());

		TArray<TSharedPtr<FJsonValue>> PtsArr;
		for (const FVector& Pt : R.PathPoints)
		{
			PtsArr.Add(MakeShared<FJsonValueArray>(MHorror_VecToArr(Pt)));
		}
		Obj->SetArrayField(TEXT("path_points"), PtsArr);
		RoutesArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("routes_found"), Routes.Num());
	Result->SetArrayField(TEXT("escape_routes"), RoutesArr);

	if (Routes.Num() == 0)
	{
		Result->SetStringField(TEXT("warning"), TEXT("No navigable escape routes found. This location may be inescapable — critical accessibility concern for hospice patients."));
	}
	else if (Routes.Num() == 1)
	{
		Result->SetStringField(TEXT("warning"), TEXT("Only one escape route available. Consider adding an additional exit for player safety."));
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 6. classify_zone_tension
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::ClassifyZoneTension(const TSharedPtr<FJsonObject>& Params)
{
	FVector Location;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: location"));
	}

	double Radius = 500.0;
	Params->TryGetNumberField(TEXT("radius"), Radius);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Gather spatial inputs
	MonolithMeshAnalysis::FTensionInputs Inputs;

	// Average sightline distance (quick 8-direction sweep)
	{
		FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithTension), true);
		FVector Origin = Location + FVector(0, 0, 170.0f);
		float TotalDist = 0.0f;
		const int32 Dirs = 8;
		for (int32 i = 0; i < Dirs; ++i)
		{
			float Angle = (2.0f * PI / static_cast<float>(Dirs)) * static_cast<float>(i);
			FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, Origin, Origin + Dir * 5000.0f, ECC_Visibility, QP);
			TotalDist += bHit ? Hit.Distance : 5000.0f;
		}
		Inputs.AverageSightlineDistance = TotalDist / static_cast<float>(Dirs);
	}

	Inputs.CeilingHeight = MonolithMeshAnalysis::MeasureCeilingHeight(World, Location);
	Inputs.RoomVolume = MonolithMeshAnalysis::ApproximateRoomVolume(World, Location, static_cast<float>(Radius) * 3.0f);
	Inputs.ExitCount = MonolithMeshAnalysis::CountExits(World, Location, static_cast<float>(Radius) * 4.0f);

	float TensionScore = MonolithMeshAnalysis::ComputeTensionScore(Inputs);
	MonolithMeshAnalysis::ETensionLevel Level = MonolithMeshAnalysis::ClassifyTension(TensionScore);

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("tension_score"), FMath::RoundToInt(TensionScore));
	Result->SetStringField(TEXT("tension_level"), MonolithMeshAnalysis::TensionLevelToString(Level));

	// Breakdown
	auto Breakdown = MakeShared<FJsonObject>();
	Breakdown->SetNumberField(TEXT("avg_sightline_distance"), Inputs.AverageSightlineDistance);
	Breakdown->SetNumberField(TEXT("ceiling_height"), Inputs.CeilingHeight);
	Breakdown->SetNumberField(TEXT("approx_room_volume"), Inputs.RoomVolume);
	Breakdown->SetNumberField(TEXT("exit_count"), Inputs.ExitCount);
	Result->SetObjectField(TEXT("breakdown"), Breakdown);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 7. analyze_pacing_curve
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::AnalyzePacingCurve(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FVector> PathPoints;
	if (!MHorror_ParseVectorArray(Params, TEXT("path_points"), PathPoints) || PathPoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: path_points (array of at least 2 [x,y,z])"));
	}

	double SampleInterval = 200.0;
	Params->TryGetNumberField(TEXT("sample_interval"), SampleInterval);
	SampleInterval = FMath::Clamp(SampleInterval, 50.0, 2000.0);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Resample path at regular intervals
	TArray<FVector> SamplePoints;
	{
		float AccumDist = 0.0f;
		SamplePoints.Add(PathPoints[0]);
		float NextSample = static_cast<float>(SampleInterval);

		for (int32 i = 1; i < PathPoints.Num(); ++i)
		{
			float SegLen = FVector::Dist(PathPoints[i - 1], PathPoints[i]);
			FVector SegDir = (PathPoints[i] - PathPoints[i - 1]).GetSafeNormal();

			float SegProgress = 0.0f;
			while (AccumDist + SegProgress + (SegLen - SegProgress > 0 ? 0 : 0) < AccumDist + SegLen)
			{
				float Remaining = NextSample - (AccumDist + SegProgress);
				float SegRemaining = SegLen - SegProgress;
				if (Remaining <= SegRemaining)
				{
					SegProgress += Remaining;
					FVector Pt = PathPoints[i - 1] + SegDir * SegProgress;
					SamplePoints.Add(Pt);
					NextSample += static_cast<float>(SampleInterval);
				}
				else
				{
					break;
				}
			}
			AccumDist += SegLen;
		}

		// Always include the last point
		if (SamplePoints.Num() > 0 && FVector::Dist(SamplePoints.Last(), PathPoints.Last()) > 10.0f)
		{
			SamplePoints.Add(PathPoints.Last());
		}
	}

	// Cap sample count
	const int32 MaxSamples = 200;
	if (SamplePoints.Num() > MaxSamples)
	{
		// Thin by taking every Nth
		int32 Step = (SamplePoints.Num() + MaxSamples - 1) / MaxSamples;
		TArray<FVector> Thinned;
		for (int32 i = 0; i < SamplePoints.Num(); i += Step)
		{
			Thinned.Add(SamplePoints[i]);
		}
		if (FVector::Dist(Thinned.Last(), SamplePoints.Last()) > 10.0f)
		{
			Thinned.Add(SamplePoints.Last());
		}
		SamplePoints = MoveTemp(Thinned);
	}

	// Sample tension at each point
	struct FPacingSample
	{
		FVector Location;
		float TensionScore;
		FString TensionLevel;
		float DistanceAlongPath;
	};

	TArray<FPacingSample> Samples;
	float CumulativeDist = 0.0f;

	for (int32 i = 0; i < SamplePoints.Num(); ++i)
	{
		if (i > 0)
		{
			CumulativeDist += FVector::Dist(SamplePoints[i - 1], SamplePoints[i]);
		}

		MonolithMeshAnalysis::FTensionInputs Inputs;

		// Quick sightline sample
		FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithPacing), true);
		FVector Origin = SamplePoints[i] + FVector(0, 0, 170.0f);
		float TotalDist = 0.0f;
		for (int32 d = 0; d < 8; ++d)
		{
			float Angle = (2.0f * PI / 8.0f) * static_cast<float>(d);
			FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, Origin, Origin + Dir * 5000.0f, ECC_Visibility, QP);
			TotalDist += bHit ? Hit.Distance : 5000.0f;
		}
		Inputs.AverageSightlineDistance = TotalDist / 8.0f;
		Inputs.CeilingHeight = MonolithMeshAnalysis::MeasureCeilingHeight(World, SamplePoints[i]);
		// Use lighter-weight checks for pacing (skip volume/exits for speed)
		Inputs.RoomVolume = 0.0f; // Neutral contribution
		Inputs.ExitCount = 2;     // Neutral contribution

		float Score = MonolithMeshAnalysis::ComputeTensionScore(Inputs);
		auto Level = MonolithMeshAnalysis::ClassifyTension(Score);

		FPacingSample S;
		S.Location = SamplePoints[i];
		S.TensionScore = Score;
		S.TensionLevel = MonolithMeshAnalysis::TensionLevelToString(Level);
		S.DistanceAlongPath = CumulativeDist;
		Samples.Add(S);
	}

	// Analyze pacing patterns
	TArray<TSharedPtr<FJsonValue>> CurveArr;
	for (const FPacingSample& S : Samples)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(S.Location));
		Obj->SetNumberField(TEXT("tension_score"), FMath::RoundToInt(S.TensionScore));
		Obj->SetStringField(TEXT("tension_level"), S.TensionLevel);
		Obj->SetNumberField(TEXT("distance_along_path"), S.DistanceAlongPath);
		CurveArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	// Find monotonous stretches (>3 consecutive samples at same tension level)
	TArray<TSharedPtr<FJsonValue>> MonotonousArr;
	{
		int32 RunStart = 0;
		for (int32 i = 1; i <= Samples.Num(); ++i)
		{
			bool bSameLevel = (i < Samples.Num()) && (Samples[i].TensionLevel == Samples[RunStart].TensionLevel);
			if (!bSameLevel)
			{
				int32 RunLen = i - RunStart;
				if (RunLen > 3)
				{
					auto Obj = MakeShared<FJsonObject>();
					Obj->SetStringField(TEXT("tension_level"), Samples[RunStart].TensionLevel);
					Obj->SetNumberField(TEXT("start_distance"), Samples[RunStart].DistanceAlongPath);
					Obj->SetNumberField(TEXT("end_distance"), Samples[i - 1].DistanceAlongPath);
					Obj->SetNumberField(TEXT("length"), Samples[i - 1].DistanceAlongPath - Samples[RunStart].DistanceAlongPath);
					Obj->SetNumberField(TEXT("sample_count"), RunLen);
					MonotonousArr.Add(MakeShared<FJsonValueObject>(Obj));
				}
				RunStart = i;
			}
		}
	}

	// Find scare opportunities (tension dips preceded by calm — good for jump scares)
	TArray<TSharedPtr<FJsonValue>> ScareOpArr;
	for (int32 i = 2; i < Samples.Num(); ++i)
	{
		if (Samples[i - 2].TensionScore < 30.0f && Samples[i - 1].TensionScore < 30.0f && Samples[i].TensionScore > 50.0f)
		{
			auto Obj = MakeShared<FJsonObject>();
			Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(Samples[i].Location));
			Obj->SetNumberField(TEXT("distance_along_path"), Samples[i].DistanceAlongPath);
			Obj->SetStringField(TEXT("type"), TEXT("tension_spike_after_calm"));
			ScareOpArr.Add(MakeShared<FJsonValueObject>(Obj));
		}

		// False-calm opportunities: high tension dropping to calm (good for fake-out)
		if (Samples[i - 1].TensionScore > 60.0f && Samples[i].TensionScore < 30.0f)
		{
			auto Obj = MakeShared<FJsonObject>();
			Obj->SetArrayField(TEXT("location"), MHorror_VecToArr(Samples[i].Location));
			Obj->SetNumberField(TEXT("distance_along_path"), Samples[i].DistanceAlongPath);
			Obj->SetStringField(TEXT("type"), TEXT("false_calm_after_tension"));
			ScareOpArr.Add(MakeShared<FJsonValueObject>(Obj));
		}
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("sample_count"), Samples.Num());
	Result->SetNumberField(TEXT("total_path_length"), CumulativeDist);
	Result->SetArrayField(TEXT("pacing_curve"), CurveArr);
	Result->SetArrayField(TEXT("monotonous_stretches"), MonotonousArr);
	Result->SetArrayField(TEXT("scare_opportunities"), ScareOpArr);

	// Average tension
	float AvgTension = 0.0f;
	for (const FPacingSample& S : Samples) AvgTension += S.TensionScore;
	if (Samples.Num() > 0) AvgTension /= static_cast<float>(Samples.Num());
	Result->SetNumberField(TEXT("average_tension"), FMath::RoundToInt(AvgTension));

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 8. find_dead_ends
// ============================================================================

FMonolithActionResult FMonolithMeshHorrorActions::FindDeadEnds(const TSharedPtr<FJsonObject>& Params)
{
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Parse optional region
	FVector RegionMin, RegionMax;
	bool bHasRegion = MonolithMeshUtils::ParseVector(Params, TEXT("region_min"), RegionMin)
		&& MonolithMeshUtils::ParseVector(Params, TEXT("region_max"), RegionMax);

	if (!bHasRegion)
	{
		// Use navmesh bounds
		UNavigationSystemV1* NavSys = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
		if (!NavSys)
		{
			return FMonolithActionResult::Error(TEXT("Navigation system not available. Build navigation first."));
		}

		ANavigationData* NavData = NavSys->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
		if (!NavData)
		{
			return FMonolithActionResult::Error(TEXT("Navmesh not built."));
		}

		// Use the navigation data's bounds
		FBox NavBounds = NavData->GetBounds();
		if (!NavBounds.IsValid)
		{
			return FMonolithActionResult::Error(TEXT("Could not determine navmesh bounds. Specify region_min/region_max manually."));
		}
		RegionMin = NavBounds.Min;
		RegionMax = NavBounds.Max;
	}

	double GridSize = 200.0;
	Params->TryGetNumberField(TEXT("grid_size"), GridSize);
	GridSize = FMath::Clamp(GridSize, 50.0, 1000.0);

	FBox Region(RegionMin, RegionMax);
	TArray<MonolithMeshAnalysis::FDeadEnd> DeadEnds = MonolithMeshAnalysis::FloodFillDeadEnds(World, Region, static_cast<float>(GridSize));

	TArray<TSharedPtr<FJsonValue>> DEArr;
	for (const auto& DE : DeadEnds)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("center"), MHorror_VecToArr(DE.Center));
		Obj->SetArrayField(TEXT("exit_direction"), MHorror_VecToArr(DE.ExitDirection));
		Obj->SetNumberField(TEXT("depth"), DE.Depth);
		Obj->SetNumberField(TEXT("width"), DE.Width);
		Obj->SetNumberField(TEXT("exit_width"), DE.ExitWidth);

		TArray<TSharedPtr<FJsonValue>> BoundsArr;
		for (const FVector& Pt : DE.BoundaryPoints)
		{
			BoundsArr.Add(MakeShared<FJsonValueArray>(MHorror_VecToArr(Pt)));
		}
		Obj->SetArrayField(TEXT("boundary_points"), BoundsArr);
		DEArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("dead_ends_found"), DeadEnds.Num());
	Result->SetArrayField(TEXT("dead_ends"), DEArr);

	if (DeadEnds.Num() > 0)
	{
		Result->SetStringField(TEXT("note"), TEXT("Dead ends are critical in survival horror. Each one should have a gameplay purpose (item reward, story beat) and the player should be warned visually before entering."));
	}

	return FMonolithActionResult::Success(Result);
}
