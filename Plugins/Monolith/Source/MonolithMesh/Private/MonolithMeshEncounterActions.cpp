#include "MonolithMeshEncounterActions.h"
#include "MonolithMeshUtils.h"
#include "MonolithMeshAnalysis.h"
#include "MonolithMeshLightingCapture.h"
#include "MonolithMeshAcoustics.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Components/PrimitiveComponent.h"
#include "CollisionQueryParams.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "AI/Navigation/NavigationTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"

// ============================================================================
// Helpers
// ============================================================================

namespace
{
	TArray<TSharedPtr<FJsonValue>> MEnc_VecToArr(const FVector& V)
	{
		return MonolithMeshAnalysis::VectorToJsonArray(V);
	}

	/** Parse an array of [x,y,z] arrays from a JSON field */
	bool MEnc_ParseVectorArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FVector>& Out)
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

	/** Parse a string array from a JSON field */
	bool MEnc_ParseStringArray(const TSharedPtr<FJsonObject>& Params, const FString& Key, TArray<FString>& Out)
	{
		const TArray<TSharedPtr<FJsonValue>>* Arr;
		if (!Params->TryGetArrayField(Key, Arr))
		{
			return false;
		}
		for (const TSharedPtr<FJsonValue>& Val : *Arr)
		{
			Out.Add(Val->AsString());
		}
		return Out.Num() > 0;
	}

	/** Resample a polyline at regular intervals. Returns at least start and end. */
	TArray<FVector> ResamplePath(const TArray<FVector>& PathPoints, float Interval)
	{
		TArray<FVector> Result;
		if (PathPoints.Num() < 2)
		{
			Result = PathPoints;
			return Result;
		}

		Result.Add(PathPoints[0]);
		float AccumDist = 0.0f;
		float NextSample = Interval;

		for (int32 i = 1; i < PathPoints.Num(); ++i)
		{
			float SegLen = FVector::Dist(PathPoints[i - 1], PathPoints[i]);
			FVector SegDir = (PathPoints[i] - PathPoints[i - 1]).GetSafeNormal();
			float SegProgress = 0.0f;

			while (true)
			{
				float Remaining = NextSample - (AccumDist + SegProgress);
				float SegRemaining = SegLen - SegProgress;
				if (Remaining <= SegRemaining)
				{
					SegProgress += Remaining;
					Result.Add(PathPoints[i - 1] + SegDir * SegProgress);
					NextSample += Interval;
				}
				else
				{
					break;
				}
			}
			AccumDist += SegLen;
		}

		if (Result.Num() > 0 && FVector::Dist(Result.Last(), PathPoints.Last()) > 10.0f)
		{
			Result.Add(PathPoints.Last());
		}

		return Result;
	}

	/** Compute total polyline distance */
	float PathLength(const TArray<FVector>& Points)
	{
		float Dist = 0.0f;
		for (int32 i = 1; i < Points.Num(); ++i)
		{
			Dist += FVector::Dist(Points[i - 1], Points[i]);
		}
		return Dist;
	}

	/** Quick 8-direction average sightline distance at a point (eye height offset) */
	float QuickAvgSightlineDistance(UWorld* World, const FVector& Location)
	{
		FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithEncounterSightline), true);
		FVector Origin = Location + FVector(0, 0, 170.0f);
		float TotalDist = 0.0f;
		const int32 Dirs = 8;
		for (int32 d = 0; d < Dirs; ++d)
		{
			float Angle = (2.0f * PI / static_cast<float>(Dirs)) * static_cast<float>(d);
			FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, Origin, Origin + Dir * 5000.0f, ECC_Visibility, QP);
			TotalDist += bHit ? Hit.Distance : 5000.0f;
		}
		return TotalDist / static_cast<float>(Dirs);
	}

	/** Quick tension score at a point (sightlines + ceiling only) */
	float QuickTensionScore(UWorld* World, const FVector& Location)
	{
		MonolithMeshAnalysis::FTensionInputs Inputs;
		Inputs.AverageSightlineDistance = QuickAvgSightlineDistance(World, Location);
		Inputs.CeilingHeight = MonolithMeshAnalysis::MeasureCeilingHeight(World, Location);
		Inputs.RoomVolume = 0.0f;
		Inputs.ExitCount = 2;
		return MonolithMeshAnalysis::ComputeTensionScore(Inputs);
	}

	/** Full tension score with all factors */
	float FullTensionScore(UWorld* World, const FVector& Location)
	{
		MonolithMeshAnalysis::FTensionInputs Inputs;
		Inputs.AverageSightlineDistance = QuickAvgSightlineDistance(World, Location);
		Inputs.CeilingHeight = MonolithMeshAnalysis::MeasureCeilingHeight(World, Location);
		Inputs.RoomVolume = MonolithMeshAnalysis::ApproximateRoomVolume(World, Location);
		Inputs.ExitCount = MonolithMeshAnalysis::CountExits(World, Location);
		return MonolithMeshAnalysis::ComputeTensionScore(Inputs);
	}

	/** Minimum distance from a point to the nearest wall (any horizontal direction) */
	float MinWallDistance(UWorld* World, const FVector& Location)
	{
		FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithEncounterWall), true);
		FVector TestPt = Location + FVector(0, 0, 50.0f);
		const float MaxDist = 500.0f;
		float MinDist = MaxDist;

		for (int32 d = 0; d < 8; ++d)
		{
			float Angle = (2.0f * PI / 8.0f) * static_cast<float>(d);
			FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
			FHitResult Hit;
			if (World->LineTraceSingleByChannel(Hit, TestPt, TestPt + Dir * MaxDist, ECC_Visibility, QP))
			{
				MinDist = FMath::Min(MinDist, Hit.Distance);
			}
		}
		return MinDist;
	}

	/** Parse region center + radius from JSON */
	bool ParseRegion(const TSharedPtr<FJsonObject>& Params, FVector& OutCenter, float& OutRadius)
	{
		const TSharedPtr<FJsonObject>* RegionObj;
		if (Params->TryGetObjectField(TEXT("region"), RegionObj))
		{
			const TArray<TSharedPtr<FJsonValue>>* CenterArr;
			if ((*RegionObj)->TryGetArrayField(TEXT("center"), CenterArr) && CenterArr->Num() >= 3)
			{
				OutCenter.X = (*CenterArr)[0]->AsNumber();
				OutCenter.Y = (*CenterArr)[1]->AsNumber();
				OutCenter.Z = (*CenterArr)[2]->AsNumber();
			}
			else
			{
				return false;
			}
			double R = 2000.0;
			(*RegionObj)->TryGetNumberField(TEXT("radius"), R);
			OutRadius = FMath::Clamp(static_cast<float>(R), 100.0f, 50000.0f);
			return true;
		}
		return false;
	}

	/** Project a point onto navmesh, returns false if no projection possible */
	bool ProjectToNav(UNavigationSystemV1* NavSys, const FVector& Point, FVector& OutNavPoint, float SearchExtent = 500.0f)
	{
		FNavLocation NavLoc;
		if (NavSys->ProjectPointToNavigation(Point, NavLoc, FVector(SearchExtent, SearchExtent, SearchExtent)))
		{
			OutNavPoint = NavLoc.Location;
			return true;
		}
		return false;
	}

	/** Sample grid points within a circle on navmesh */
	TArray<FVector> SampleNavGrid(UWorld* World, UNavigationSystemV1* NavSys, const FVector& Center, float Radius, float GridSize)
	{
		TArray<FVector> Points;
		int32 Count = FMath::CeilToInt(Radius * 2.0f / GridSize);
		Count = FMath::Clamp(Count, 2, 50); // cap for performance

		for (int32 X = 0; X < Count; ++X)
		{
			for (int32 Y = 0; Y < Count; ++Y)
			{
				FVector TestPt = Center + FVector(
					(-Radius + (static_cast<float>(X) + 0.5f) * GridSize),
					(-Radius + (static_cast<float>(Y) + 0.5f) * GridSize),
					0.0f);

				if (FVector::DistSquared2D(TestPt, Center) > Radius * Radius) continue;

				FVector NavPt;
				if (ProjectToNav(NavSys, TestPt, NavPt))
				{
					Points.Add(NavPt);
				}
			}
		}
		return Points;
	}

	/** Detect entrances to a room by tracing outward and finding gaps (navmesh-passable openings) */
	struct FEntranceInfo
	{
		FVector Location = FVector::ZeroVector;
		FVector Direction = FVector::ZeroVector; // outward-facing direction
		float Width = 0.0f;
		bool bHasDoor = false;
	};

	TArray<FEntranceInfo> DetectEntrances(UWorld* World, UNavigationSystemV1* NavSys, ANavigationData* NavData,
		const FVector& RoomCenter, float RoomRadius)
	{
		TArray<FEntranceInfo> Entrances;
		FCollisionQueryParams QP(SCENE_QUERY_STAT(MonolithEntranceDetect), true);
		FNavAgentProperties AgentProps;
		AgentProps.AgentRadius = 42.0f;
		AgentProps.AgentHeight = 192.0f;

		const int32 Directions = 16;
		const float TestDist = RoomRadius + 300.0f;
		const float WallTestDist = RoomRadius * 1.2f;

		struct FGapCandidate
		{
			FVector WallPoint;
			FVector Direction;
			float AngleDeg;
			bool bIsGap;
		};

		TArray<FGapCandidate> Candidates;
		FVector TestOrigin = RoomCenter + FVector(0, 0, 100.0f);

		for (int32 d = 0; d < Directions; ++d)
		{
			float Angle = (2.0f * PI / static_cast<float>(Directions)) * static_cast<float>(d);
			FVector Dir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);

			// Check if there's a wall in this direction
			FHitResult Hit;
			bool bWallHit = World->LineTraceSingleByChannel(Hit, TestOrigin, TestOrigin + Dir * WallTestDist, ECC_Visibility, QP);

			// Check if we can navigate through this direction (navmesh path to outside)
			FVector OutsidePoint = RoomCenter + Dir * TestDist;
			FPathFindingQuery Query(nullptr, *NavData, RoomCenter, OutsidePoint);
			Query.SetAllowPartialPaths(false);
			FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);
			bool bCanNavigate = PathResult.IsSuccessful() && PathResult.Path.IsValid() && !PathResult.Path->IsPartial();

			FGapCandidate Cand;
			Cand.WallPoint = bWallHit ? Hit.ImpactPoint : (RoomCenter + Dir * WallTestDist);
			Cand.Direction = Dir;
			Cand.AngleDeg = FMath::RadiansToDegrees(Angle);
			Cand.bIsGap = bCanNavigate && (!bWallHit || Hit.Distance > WallTestDist * 0.9f);
			Candidates.Add(Cand);
		}

		// Group adjacent gaps into entrances
		for (int32 d = 0; d < Directions; ++d)
		{
			if (!Candidates[d].bIsGap) continue;

			// Check if previous candidate was also a gap (merge into same entrance)
			int32 Prev = (d + Directions - 1) % Directions;
			if (Candidates[Prev].bIsGap) continue; // This gap continues a previous one — skip to avoid duplicates

			// Find contiguous gap span
			int32 GapStart = d;
			int32 GapEnd = d;
			int32 Next = (d + 1) % Directions;
			while (Candidates[Next].bIsGap && Next != GapStart)
			{
				GapEnd = Next;
				Next = (Next + 1) % Directions;
			}

			// Compute entrance properties
			int32 MidIdx = (GapStart + GapEnd) / 2;
			if (GapEnd < GapStart) MidIdx = ((GapStart + GapEnd + Directions) / 2) % Directions;

			FEntranceInfo Entrance;
			Entrance.Direction = Candidates[MidIdx].Direction;
			Entrance.Location = Candidates[MidIdx].WallPoint;

			// Width from gap angular span
			float AngleSpan = static_cast<float>(GapEnd - GapStart + 1) / static_cast<float>(Directions) * 2.0f * PI;
			float AvgDist = FVector::Dist2D(RoomCenter, Entrance.Location);
			Entrance.Width = AvgDist * AngleSpan;
			Entrance.Width = FMath::Clamp(Entrance.Width, 50.0f, 1000.0f);

			// Door detection: look for actors with "Door" tag or class near entrance
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				AActor* Actor = *It;
				if (FVector::Dist(Actor->GetActorLocation(), Entrance.Location) < 200.0f)
				{
					for (const FName& Tag : Actor->Tags)
					{
						if (Tag.ToString().Contains(TEXT("Door"), ESearchCase::IgnoreCase))
						{
							Entrance.bHasDoor = true;
							break;
						}
					}
					if (!Entrance.bHasDoor)
					{
						FString ClassName = Actor->GetClass()->GetName();
						if (ClassName.Contains(TEXT("Door"), ESearchCase::IgnoreCase))
						{
							Entrance.bHasDoor = true;
						}
					}
				}
				if (Entrance.bHasDoor) break;
			}

			Entrances.Add(MoveTemp(Entrance));
		}

		return Entrances;
	}

	/** Compute an overall letter grade from a 0-100 score */
	FString ScoreToGrade(float Score)
	{
		if (Score >= 90.0f) return TEXT("S");
		if (Score >= 80.0f) return TEXT("A");
		if (Score >= 65.0f) return TEXT("B");
		if (Score >= 50.0f) return TEXT("C");
		if (Score >= 35.0f) return TEXT("D");
		return TEXT("F");
	}

	/** Helper to create a JSON vector array parameter for sub-calls */
	void SetVectorParam(const TSharedPtr<FJsonObject>& Obj, const FString& Key, const FVector& V)
	{
		TArray<TSharedPtr<FJsonValue>> Arr;
		Arr.Add(MakeShared<FJsonValueNumber>(V.X));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
		Obj->SetArrayField(Key, Arr);
	}
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshEncounterActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. design_encounter
	Registry.RegisterAction(TEXT("mesh"), TEXT("design_encounter"),
		TEXT("Capstone: compose spawn points, patrol routes, player entry/exit, sightline breaks, and audio zones into a scored encounter specification. Returns a complete encounter blueprint JSON."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::DesignEncounter),
		FParamSchemaBuilder()
			.Required(TEXT("region"), TEXT("object"), TEXT("{ \"center\": [x,y,z], \"radius\": 2000 }"))
			.Optional(TEXT("archetype"), TEXT("string"), TEXT("AI archetype: stalker, patrol, ambusher, swarm"), TEXT("stalker"))
			.Optional(TEXT("difficulty"), TEXT("string"), TEXT("Difficulty: low, medium, high"), TEXT("medium"))
			.Optional(TEXT("enemy_blueprint"), TEXT("string"), TEXT("Blueprint path for the enemy actor"), TEXT(""))
			.Optional(TEXT("constraints"), TEXT("object"), TEXT("{ max_enemies: 3, min_escape_routes: 2 }"), TEXT(""))
			.Optional(TEXT("dry_run"), TEXT("boolean"), TEXT("If true, returns spec only (no actor placement)"), TEXT("true"))
			.Build());

	// 2. suggest_patrol_route
	Registry.RegisterAction(TEXT("mesh"), TEXT("suggest_patrol_route"),
		TEXT("Generate navmesh patrol routes per AI archetype. Stalker: stay in earshot but out of sight. Patrol: regular loop hitting checkpoints. Ambusher: concealed wait position with surprise angle."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::SuggestPatrolRoute),
		FParamSchemaBuilder()
			.Required(TEXT("region"), TEXT("object"), TEXT("{ \"center\": [x,y,z], \"radius\": 2000 }"))
			.Optional(TEXT("archetype"), TEXT("string"), TEXT("AI archetype: stalker, patrol, ambusher"), TEXT("patrol"))
			.Optional(TEXT("waypoint_count"), TEXT("integer"), TEXT("Number of waypoints to generate"), TEXT("5"))
			.Optional(TEXT("patrol_style"), TEXT("string"), TEXT("Style: loop, back_and_forth, random"), TEXT("loop"))
			.Optional(TEXT("constraints"), TEXT("object"), TEXT("{ avoid_well_lit: true, prefer_cover: true }"), TEXT(""))
			.Optional(TEXT("player_path"), TEXT("array"), TEXT("Player path [[x,y,z], ...] for stalker proximity calculation"), TEXT(""))
			.Build());

	// 3. analyze_ai_territory
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_ai_territory"),
		TEXT("Score a region as AI territory: hiding spot density, patrol route coverage, sightline control, ambush potential, escape routes for AI disengagement."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::AnalyzeAiTerritory),
		FParamSchemaBuilder()
			.Required(TEXT("region"), TEXT("object"), TEXT("{ \"center\": [x,y,z], \"radius\": 2000 }"))
			.Optional(TEXT("archetype"), TEXT("string"), TEXT("AI archetype for scoring bias: stalker, patrol, ambusher"), TEXT("stalker"))
			.Optional(TEXT("granularity"), TEXT("number"), TEXT("Grid sampling granularity in cm"), TEXT("200"))
			.Build());

	// 4. evaluate_safe_room
	Registry.RegisterAction(TEXT("mesh"), TEXT("evaluate_safe_room"),
		TEXT("Score a room as a safe room: entrance count, defensibility, lighting quality, sound isolation, size, hospice accessibility. Detects doors via actor tags/class."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::EvaluateSafeRoom),
		FParamSchemaBuilder()
			.Required(TEXT("region"), TEXT("object"), TEXT("{ \"center\": [x,y,z], \"radius\": 500 }"))
			.Build());

	// 5. analyze_level_pacing_structure
	Registry.RegisterAction(TEXT("mesh"), TEXT("analyze_level_pacing_structure"),
		TEXT("Macro-level tension-to-release rhythm across an entire level path. Identifies encounter zones, safe rooms, exploration areas. Compares to ideal pacing curves."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::AnalyzeLevelPacingStructure),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Start position [x, y, z]"))
			.Required(TEXT("end"), TEXT("array"), TEXT("End position [x, y, z]"))
			.Optional(TEXT("waypoints"), TEXT("array"), TEXT("Intermediate waypoints [[x,y,z], ...]"), TEXT(""))
			.Optional(TEXT("sample_interval"), TEXT("number"), TEXT("Tension sample interval in cm"), TEXT("500"))
			.Build());

	// 6. generate_scare_sequence
	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_scare_sequence"),
		TEXT("Procedurally generate a sequence of scare events with variety, escalation, and pacing. Output is a specification, not placed actors."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::GenerateScareSequence),
		FParamSchemaBuilder()
			.Required(TEXT("path_points"), TEXT("array"), TEXT("Player path positions [[x,y,z], ...]"))
			.Optional(TEXT("style"), TEXT("string"), TEXT("Pacing style: slow_burn, escalating, relentless, single_peak"), TEXT("escalating"))
			.Optional(TEXT("intensity_cap"), TEXT("number"), TEXT("Maximum intensity 0-1 (hospice: 0.5)"), TEXT("1.0"))
			.Optional(TEXT("scare_types"), TEXT("array"), TEXT("Allowed types: audio, visual, environmental, entity_spawn"), TEXT(""))
			.Optional(TEXT("count"), TEXT("integer"), TEXT("Number of scare events"), TEXT("5"))
			.Build());

	// 7. validate_horror_intensity
	Registry.RegisterAction(TEXT("mesh"), TEXT("validate_horror_intensity"),
		TEXT("Audit horror intensity for hospice compliance. Checks max tension never exceeds profile ceiling. Verifies generous escape windows. Flags jump scares."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::ValidateHorrorIntensity),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Start position [x, y, z]"))
			.Required(TEXT("end"), TEXT("array"), TEXT("End position [x, y, z]"))
			.Optional(TEXT("intensity_cap"), TEXT("number"), TEXT("Maximum allowed tension 0-100 (hospice default: 50)"), TEXT("50"))
			.Optional(TEXT("flag_jump_scares"), TEXT("boolean"), TEXT("Flag sudden tension spikes as jump scares"), TEXT("true"))
			.Optional(TEXT("min_rest_distance_cm"), TEXT("number"), TEXT("Min distance between high-tension zones in cm"), TEXT("800"))
			.Optional(TEXT("min_escape_routes"), TEXT("integer"), TEXT("Min escape routes at any point"), TEXT("2"))
			.Build());

	// 8. generate_hospice_report
	Registry.RegisterAction(TEXT("mesh"), TEXT("generate_hospice_report"),
		TEXT("Full level audit for hospice patients: intensity caps, rest spacing (every 2-3 min), cognitive load, input demands, one-handed playability, audio alternatives for visual scares. Profiles: motor_impaired, vision_impaired, cognitive_fatigue."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshEncounterActions::GenerateHospiceReport),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Start position [x, y, z]"))
			.Required(TEXT("end"), TEXT("array"), TEXT("End position [x, y, z]"))
			.Optional(TEXT("profile"), TEXT("string"), TEXT("Hospice profile: motor_impaired, vision_impaired, cognitive_fatigue (empty = all)"), TEXT(""))
			.Optional(TEXT("walk_speed_cms"), TEXT("number"), TEXT("Walk speed in cm/s for time estimation"), TEXT("300"))
			.Build());
}

// ============================================================================
// 1. design_encounter
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::DesignEncounter(const TSharedPtr<FJsonObject>& Params)
{
	FVector Center;
	float Radius;
	if (!ParseRegion(Params, Center, Radius))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region (object with center [x,y,z] and radius)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString NavError;
	if (!MonolithMeshAnalysis::GetNavSystem(World, NavSys, NavData, NavError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Navigation not available: %s. Build navmesh first."), *NavError));
	}

	FString Archetype = TEXT("stalker");
	Params->TryGetStringField(TEXT("archetype"), Archetype);

	FString Difficulty = TEXT("medium");
	Params->TryGetStringField(TEXT("difficulty"), Difficulty);

	FString EnemyBlueprint;
	Params->TryGetStringField(TEXT("enemy_blueprint"), EnemyBlueprint);

	// Parse constraints
	int32 MaxEnemies = 3;
	int32 MinEscapeRoutes = 2;
	const TSharedPtr<FJsonObject>* ConstraintsObj;
	if (Params->TryGetObjectField(TEXT("constraints"), ConstraintsObj))
	{
		double V;
		if ((*ConstraintsObj)->TryGetNumberField(TEXT("max_enemies"), V))
		{
			MaxEnemies = FMath::Clamp(static_cast<int32>(V), 1, 20);
		}
		if ((*ConstraintsObj)->TryGetNumberField(TEXT("min_escape_routes"), V))
		{
			MinEscapeRoutes = FMath::Clamp(static_cast<int32>(V), 0, 10);
		}
	}

	// Difficulty modifiers
	float DifficultyMul = 1.0f;
	if (Difficulty.Equals(TEXT("low"), ESearchCase::IgnoreCase))
	{
		DifficultyMul = 0.6f;
		MaxEnemies = FMath::Min(MaxEnemies, 2);
	}
	else if (Difficulty.Equals(TEXT("high"), ESearchCase::IgnoreCase))
	{
		DifficultyMul = 1.4f;
	}

	// ---- 1. Analyze region ----
	float RegionTension = FullTensionScore(World, Center);
	int32 ExitCount = MonolithMeshAnalysis::CountExits(World, Center, Radius);

	// ---- 2. Sample grid for spawn candidates ----
	float GridSize = FMath::Clamp(Radius / 10.0f, 100.0f, 300.0f);
	TArray<FVector> GridPoints = SampleNavGrid(World, NavSys, Center, Radius, GridSize);

	if (GridPoints.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No navmesh points found within region. Check that navmesh covers this area."));
	}

	// ---- 3. Gather lights for lighting analysis ----
	TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);

	// ---- 4. Score each grid point as a spawn candidate ----
	struct FSpawnCandidate
	{
		FVector Location;
		float Concealment = 0.0f;   // from center viewpoint
		float Darkness = 0.0f;      // 0=bright, 1=dark
		float WallProximity = 0.0f; // closer to wall = better for ambush
		float Score = 0.0f;
	};

	TArray<FSpawnCandidate> SpawnCandidates;
	TArray<FVector> CenterViewpoint = { Center + FVector(0, 0, 170.0f) };

	for (const FVector& Pt : GridPoints)
	{
		FSpawnCandidate Cand;
		Cand.Location = Pt;
		Cand.Concealment = MonolithMeshAnalysis::ComputeConcealment(World, Pt, CenterViewpoint);

		int32 DummyIdx;
		float Lum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Pt, Lights, DummyIdx);
		Cand.Darkness = FMath::Clamp(1.0f - (Lum / 5.0f), 0.0f, 1.0f);

		float WallDist = MinWallDistance(World, Pt);
		Cand.WallProximity = FMath::Clamp(1.0f - (WallDist / 300.0f), 0.0f, 1.0f);

		// Archetype-specific scoring
		if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase))
		{
			Cand.Score = Cand.Concealment * 0.4f + Cand.Darkness * 0.35f + Cand.WallProximity * 0.25f;
		}
		else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase))
		{
			Cand.Score = Cand.Concealment * 0.5f + Cand.WallProximity * 0.3f + Cand.Darkness * 0.2f;
		}
		else if (Archetype.Equals(TEXT("swarm"), ESearchCase::IgnoreCase))
		{
			// Swarm prefers wider areas with multiple approach angles
			float SpaceScore = FMath::Clamp(WallDist / 300.0f, 0.0f, 1.0f);
			Cand.Score = SpaceScore * 0.4f + Cand.Darkness * 0.3f + Cand.Concealment * 0.3f;
		}
		else // patrol
		{
			Cand.Score = Cand.Concealment * 0.3f + Cand.Darkness * 0.3f + Cand.WallProximity * 0.4f;
		}

		Cand.Score *= DifficultyMul;
		SpawnCandidates.Add(MoveTemp(Cand));
	}

	// Sort and pick top spawn points with spacing
	SpawnCandidates.Sort([](const FSpawnCandidate& A, const FSpawnCandidate& B)
	{
		return A.Score > B.Score;
	});

	float MinSpawnSpacing = FMath::Max(200.0f, Radius * 0.3f);
	TArray<FSpawnCandidate> SelectedSpawns;
	for (const FSpawnCandidate& Cand : SpawnCandidates)
	{
		if (SelectedSpawns.Num() >= MaxEnemies) break;

		bool bTooClose = false;
		for (const FSpawnCandidate& Sel : SelectedSpawns)
		{
			if (FVector::Dist(Cand.Location, Sel.Location) < MinSpawnSpacing)
			{
				bTooClose = true;
				break;
			}
		}
		if (bTooClose) continue;
		SelectedSpawns.Add(Cand);
	}

	// ---- 5. Generate patrol route for the encounter ----
	// Use the sub-action helper logic directly
	TArray<TSharedPtr<FJsonValue>> PatrolRouteArr;
	if (SelectedSpawns.Num() > 0)
	{
		// Build a simple patrol connecting spawn points
		TArray<FVector> PatrolWaypoints;
		for (const FSpawnCandidate& Sp : SelectedSpawns)
		{
			PatrolWaypoints.Add(Sp.Location);
		}
		// Add a return to first for loop — copy first to avoid
		// self-referencing Add() crash (TArray may realloc)
		if (PatrolWaypoints.Num() > 1)
		{
			FVector FirstWP = PatrolWaypoints[0];
			PatrolWaypoints.Add(FirstWP);
		}

		for (const FVector& WP : PatrolWaypoints)
		{
			auto WPObj = MakeShared<FJsonObject>();
			WPObj->SetArrayField(TEXT("location"), MEnc_VecToArr(WP));
			WPObj->SetNumberField(TEXT("wait_time"), Archetype.Equals(TEXT("stalker")) ? 3.0 : 1.5);
			PatrolRouteArr.Add(MakeShared<FJsonValueObject>(WPObj));
		}
	}

	// ---- 6. Find player escape routes ----
	TArray<TSharedPtr<FJsonValue>> EscapeRouteArr;
	{
		FNavAgentProperties AgentProps;
		AgentProps.AgentRadius = 42.0f;
		AgentProps.AgentHeight = 192.0f;

		const int32 EscapeDirs = 8;
		int32 ViableEscapes = 0;

		for (int32 d = 0; d < EscapeDirs; ++d)
		{
			float Angle = (2.0f * PI / static_cast<float>(EscapeDirs)) * static_cast<float>(d);
			FVector EscapeTarget = Center + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * (Radius + 500.0f);

			FPathFindingQuery Query(nullptr, *NavData, Center, EscapeTarget);
			Query.SetAllowPartialPaths(false);
			FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);

			if (PathResult.IsSuccessful() && PathResult.Path.IsValid() && !PathResult.Path->IsPartial())
			{
				++ViableEscapes;
				auto RouteObj = MakeShared<FJsonObject>();
				RouteObj->SetArrayField(TEXT("direction"), MEnc_VecToArr(FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f)));
				RouteObj->SetArrayField(TEXT("exit_point"), MEnc_VecToArr(EscapeTarget));
				EscapeRouteArr.Add(MakeShared<FJsonValueObject>(RouteObj));
			}
		}
	}

	// ---- 7. Warnings ----
	TArray<TSharedPtr<FJsonValue>> Warnings;
	TArray<TSharedPtr<FJsonValue>> Recommendations;

	if (EscapeRouteArr.Num() < MinEscapeRoutes)
	{
		Warnings.Add(MakeShared<FJsonValueString>(FString::Printf(
			TEXT("HOSPICE CRITICAL: Only %d escape routes found (minimum required: %d). Patients must always have a way out."),
			EscapeRouteArr.Num(), MinEscapeRoutes)));
	}
	if (SelectedSpawns.Num() < 1)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("No viable spawn points found in region. Area may be too bright or too exposed.")));
	}
	if (RegionTension > 80.0f)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("Region already at very high environmental tension. Adding enemies may overwhelm hospice patients.")));
		Recommendations.Add(MakeShared<FJsonValueString>(TEXT("Consider increasing lighting or widening corridors before adding encounters here.")));
	}
	if (ExitCount <= 1)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("ACCESSIBILITY: Region appears to be a dead end. Not recommended for encounters.")));
	}

	// Recommendations based on archetype
	if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase))
	{
		Recommendations.Add(MakeShared<FJsonValueString>(TEXT("Stalker: Add audio cues (breathing, footsteps) audible from spawn points but not immediately visible.")));
		Recommendations.Add(MakeShared<FJsonValueString>(TEXT("Stalker: Ensure sightline breaks every 5-10m so stalker can duck out of view.")));
	}
	else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase))
	{
		Recommendations.Add(MakeShared<FJsonValueString>(TEXT("Ambusher: Position should have a >90 degree surprise angle from primary player approach.")));
	}

	// ---- 8. Score the encounter ----
	float EncounterScore = 0.0f;
	{
		float SpawnQuality = 0.0f;
		for (const FSpawnCandidate& S : SelectedSpawns) SpawnQuality += S.Score;
		SpawnQuality = SelectedSpawns.Num() > 0 ? SpawnQuality / static_cast<float>(SelectedSpawns.Num()) : 0.0f;

		float EscapeScore = FMath::Clamp(static_cast<float>(EscapeRouteArr.Num()) / 4.0f, 0.0f, 1.0f);
		float TensionScore = FMath::Clamp(RegionTension / 100.0f, 0.0f, 1.0f);

		// Good encounter: decent spawn positions + adequate escape + moderate tension
		EncounterScore = SpawnQuality * 40.0f + EscapeScore * 30.0f + TensionScore * 30.0f;
		EncounterScore = FMath::Clamp(EncounterScore, 0.0f, 100.0f);

		// Penalize for warnings
		EncounterScore -= static_cast<float>(Warnings.Num()) * 10.0f;
		EncounterScore = FMath::Max(EncounterScore, 0.0f);
	}

	// Build spawn points JSON
	TArray<TSharedPtr<FJsonValue>> SpawnArr;
	for (const FSpawnCandidate& S : SelectedSpawns)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MEnc_VecToArr(S.Location));
		Obj->SetNumberField(TEXT("concealment"), S.Concealment);
		Obj->SetNumberField(TEXT("darkness"), S.Darkness);
		Obj->SetNumberField(TEXT("score"), S.Score);
		if (!EnemyBlueprint.IsEmpty())
		{
			Obj->SetStringField(TEXT("blueprint"), EnemyBlueprint);
		}
		SpawnArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("encounter_score"), EncounterScore);
	Result->SetStringField(TEXT("grade"), ScoreToGrade(EncounterScore));
	Result->SetStringField(TEXT("archetype"), Archetype);
	Result->SetStringField(TEXT("difficulty"), Difficulty);
	Result->SetArrayField(TEXT("spawn_points"), SpawnArr);
	Result->SetNumberField(TEXT("spawn_count"), SelectedSpawns.Num());
	Result->SetArrayField(TEXT("patrol_route"), PatrolRouteArr);
	Result->SetArrayField(TEXT("player_escape_routes"), EscapeRouteArr);
	Result->SetNumberField(TEXT("escape_route_count"), EscapeRouteArr.Num());
	Result->SetNumberField(TEXT("region_tension"), FMath::RoundToInt(RegionTension));
	Result->SetStringField(TEXT("tension_level"),
		MonolithMeshAnalysis::TensionLevelToString(MonolithMeshAnalysis::ClassifyTension(RegionTension)));
	Result->SetNumberField(TEXT("exit_count"), ExitCount);
	Result->SetArrayField(TEXT("warnings"), Warnings);
	Result->SetArrayField(TEXT("recommendations"), Recommendations);
	Result->SetBoolField(TEXT("dry_run"), true);
	Result->SetNumberField(TEXT("grid_points_sampled"), GridPoints.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. suggest_patrol_route
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::SuggestPatrolRoute(const TSharedPtr<FJsonObject>& Params)
{
	FVector Center;
	float Radius;
	if (!ParseRegion(Params, Center, Radius))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region (object with center [x,y,z] and radius)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString NavError;
	if (!MonolithMeshAnalysis::GetNavSystem(World, NavSys, NavData, NavError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Navigation not available: %s. Navmesh must be built for patrol route generation."), *NavError));
	}

	FString Archetype = TEXT("patrol");
	Params->TryGetStringField(TEXT("archetype"), Archetype);

	int32 WaypointCount = 5;
	{
		double V;
		if (Params->TryGetNumberField(TEXT("waypoint_count"), V))
		{
			WaypointCount = FMath::Clamp(static_cast<int32>(V), 2, 20);
		}
	}

	FString PatrolStyle = TEXT("loop");
	Params->TryGetStringField(TEXT("patrol_style"), PatrolStyle);

	// Parse constraints
	bool bAvoidWellLit = false;
	bool bPreferCover = true;
	const TSharedPtr<FJsonObject>* ConstraintsObj;
	if (Params->TryGetObjectField(TEXT("constraints"), ConstraintsObj))
	{
		(*ConstraintsObj)->TryGetBoolField(TEXT("avoid_well_lit"), bAvoidWellLit);
		(*ConstraintsObj)->TryGetBoolField(TEXT("prefer_cover"), bPreferCover);
	}

	// Parse optional player path for stalker proximity
	TArray<FVector> PlayerPath;
	MEnc_ParseVectorArray(Params, TEXT("player_path"), PlayerPath);

	// Gather lights
	TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);

	// Sample grid
	float GridSize = FMath::Clamp(Radius / 8.0f, 100.0f, 300.0f);
	TArray<FVector> GridPoints = SampleNavGrid(World, NavSys, Center, Radius, GridSize);

	if (GridPoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Insufficient navmesh coverage in region. Need at least 2 navigable points."));
	}

	// Score each grid point per archetype
	struct FScoredPoint
	{
		FVector Location;
		float Score = 0.0f;
		float Darkness = 0.0f;
		float Concealment = 0.0f;
		float WallProximity = 0.0f;
	};

	TArray<FVector> CenterView = { Center + FVector(0, 0, 170.0f) };
	TArray<FScoredPoint> ScoredPoints;

	for (const FVector& Pt : GridPoints)
	{
		FScoredPoint SP;
		SP.Location = Pt;

		int32 DummyIdx;
		float Lum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Pt, Lights, DummyIdx);
		SP.Darkness = FMath::Clamp(1.0f - (Lum / 5.0f), 0.0f, 1.0f);
		SP.Concealment = MonolithMeshAnalysis::ComputeConcealment(World, Pt, CenterView);

		float WallDist = MinWallDistance(World, Pt);
		SP.WallProximity = FMath::Clamp(1.0f - (WallDist / 300.0f), 0.0f, 1.0f);

		if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase))
		{
			// Stalker: concealed but within earshot of player path
			SP.Score = SP.Concealment * 0.4f + SP.Darkness * 0.3f;
			if (PlayerPath.Num() > 0)
			{
				float MinPlayerDist = TNumericLimits<float>::Max();
				for (const FVector& PP : PlayerPath)
				{
					MinPlayerDist = FMath::Min(MinPlayerDist, FVector::Dist(Pt, PP));
				}
				// Sweet spot: 300-800cm from player path (earshot but not visible)
				float ProxScore = 1.0f - FMath::Clamp(FMath::Abs(MinPlayerDist - 550.0f) / 500.0f, 0.0f, 1.0f);
				SP.Score += ProxScore * 0.3f;
			}
			else
			{
				SP.Score += SP.WallProximity * 0.3f;
			}
		}
		else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase))
		{
			// Ambusher: maximum concealment, near walls, preferably in dark spots
			SP.Score = SP.Concealment * 0.5f + SP.WallProximity * 0.3f + SP.Darkness * 0.2f;
		}
		else // patrol
		{
			// Patrol: balanced coverage, prefer edges of room (wall-hugging), moderate darkness
			SP.Score = SP.WallProximity * 0.4f + SP.Darkness * 0.3f + SP.Concealment * 0.3f;
		}

		if (bAvoidWellLit && SP.Darkness < 0.3f) SP.Score *= 0.5f;
		if (bPreferCover && SP.Concealment < 0.3f) SP.Score *= 0.7f;

		ScoredPoints.Add(MoveTemp(SP));
	}

	// Sort by score descending
	ScoredPoints.Sort([](const FScoredPoint& A, const FScoredPoint& B) { return A.Score > B.Score; });

	// Select waypoints with spacing
	float MinSpacing = FMath::Max(150.0f, Radius / static_cast<float>(WaypointCount + 1));
	TArray<FScoredPoint> SelectedWaypoints;

	for (const FScoredPoint& SP : ScoredPoints)
	{
		if (SelectedWaypoints.Num() >= WaypointCount) break;

		bool bTooClose = false;
		for (const FScoredPoint& Sel : SelectedWaypoints)
		{
			if (FVector::Dist(SP.Location, Sel.Location) < MinSpacing)
			{
				bTooClose = true;
				break;
			}
		}
		if (bTooClose) continue;

		SelectedWaypoints.Add(SP);
	}

	if (SelectedWaypoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Could not find enough spaced waypoints. Region may be too small or navmesh too sparse."));
	}

	// Sort waypoints to form a sensible route (nearest-neighbor for loop)
	TArray<FScoredPoint> OrderedWaypoints;
	TSet<int32> Used;
	OrderedWaypoints.Add(SelectedWaypoints[0]);
	Used.Add(0);

	while (OrderedWaypoints.Num() < SelectedWaypoints.Num())
	{
		FVector Last = OrderedWaypoints.Last().Location;
		float BestDist = TNumericLimits<float>::Max();
		int32 BestIdx = -1;

		for (int32 i = 0; i < SelectedWaypoints.Num(); ++i)
		{
			if (Used.Contains(i)) continue;
			float D = FVector::Dist(Last, SelectedWaypoints[i].Location);
			if (D < BestDist)
			{
				BestDist = D;
				BestIdx = i;
			}
		}
		if (BestIdx >= 0)
		{
			OrderedWaypoints.Add(SelectedWaypoints[BestIdx]);
			Used.Add(BestIdx);
		}
		else break;
	}

	// Compute wait times and look directions per archetype
	float BaseWaitTime = 2.0f;
	if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase)) BaseWaitTime = 3.0f;
	else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase)) BaseWaitTime = 8.0f;

	// Build route JSON
	TArray<TSharedPtr<FJsonValue>> WaypointArr;
	float TotalDist = 0.0f;
	float TotalExposure = 0.0f;

	for (int32 i = 0; i < OrderedWaypoints.Num(); ++i)
	{
		if (i > 0)
		{
			TotalDist += FVector::Dist(OrderedWaypoints[i - 1].Location, OrderedWaypoints[i].Location);
		}

		// Look direction: toward center of room (patrol), toward player path (stalker), toward approach (ambusher)
		FVector LookDir;
		if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase) && PlayerPath.Num() > 0)
		{
			float MinD = TNumericLimits<float>::Max();
			FVector Closest = PlayerPath[0];
			for (const FVector& PP : PlayerPath)
			{
				float D = FVector::Dist(OrderedWaypoints[i].Location, PP);
				if (D < MinD) { MinD = D; Closest = PP; }
			}
			LookDir = (Closest - OrderedWaypoints[i].Location).GetSafeNormal();
		}
		else if (i < OrderedWaypoints.Num() - 1)
		{
			LookDir = (OrderedWaypoints[i + 1].Location - OrderedWaypoints[i].Location).GetSafeNormal();
		}
		else
		{
			LookDir = (Center - OrderedWaypoints[i].Location).GetSafeNormal();
		}

		TotalExposure += (1.0f - OrderedWaypoints[i].Concealment);

		auto WPObj = MakeShared<FJsonObject>();
		WPObj->SetArrayField(TEXT("location"), MEnc_VecToArr(OrderedWaypoints[i].Location));
		WPObj->SetNumberField(TEXT("wait_time"), BaseWaitTime);
		WPObj->SetArrayField(TEXT("look_direction"), MEnc_VecToArr(LookDir));
		WPObj->SetNumberField(TEXT("concealment"), OrderedWaypoints[i].Concealment);
		WPObj->SetNumberField(TEXT("darkness"), OrderedWaypoints[i].Darkness);
		WaypointArr.Add(MakeShared<FJsonValueObject>(WPObj));
	}

	// Add return to start for loop style
	if (PatrolStyle.Equals(TEXT("loop"), ESearchCase::IgnoreCase) && OrderedWaypoints.Num() > 1)
	{
		TotalDist += FVector::Dist(OrderedWaypoints.Last().Location, OrderedWaypoints[0].Location);
	}

	float ExposureScore = OrderedWaypoints.Num() > 0
		? (TotalExposure / static_cast<float>(OrderedWaypoints.Num()))
		: 1.0f;

	auto RouteObj = MakeShared<FJsonObject>();
	RouteObj->SetArrayField(TEXT("waypoints"), WaypointArr);
	RouteObj->SetNumberField(TEXT("total_distance"), TotalDist);
	RouteObj->SetNumberField(TEXT("exposure_score"), ExposureScore);
	RouteObj->SetStringField(TEXT("patrol_style"), PatrolStyle);

	auto Result = MakeShared<FJsonObject>();
	Result->SetObjectField(TEXT("route"), RouteObj);
	Result->SetStringField(TEXT("archetype"), Archetype);
	Result->SetNumberField(TEXT("waypoint_count"), OrderedWaypoints.Num());
	Result->SetNumberField(TEXT("grid_points_sampled"), GridPoints.Num());

	if (OrderedWaypoints.Num() < WaypointCount)
	{
		Result->SetStringField(TEXT("warning"), FString::Printf(
			TEXT("Only %d of %d requested waypoints could be placed with adequate spacing."),
			OrderedWaypoints.Num(), WaypointCount));
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. analyze_ai_territory
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::AnalyzeAiTerritory(const TSharedPtr<FJsonObject>& Params)
{
	FVector Center;
	float Radius;
	if (!ParseRegion(Params, Center, Radius))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region (object with center [x,y,z] and radius)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString NavError;
	if (!MonolithMeshAnalysis::GetNavSystem(World, NavSys, NavData, NavError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Navigation not available: %s. Build navmesh first."), *NavError));
	}

	FString Archetype = TEXT("stalker");
	Params->TryGetStringField(TEXT("archetype"), Archetype);

	double Granularity = 200.0;
	Params->TryGetNumberField(TEXT("granularity"), Granularity);
	Granularity = FMath::Clamp(Granularity, 100.0, 1000.0);

	// Sample grid
	TArray<FVector> GridPoints = SampleNavGrid(World, NavSys, Center, Radius, static_cast<float>(Granularity));

	if (GridPoints.Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("No navmesh points found within region."));
	}

	// Gather lights
	TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);

	// Score each point
	float TotalConcealment = 0.0f;
	float TotalDarkness = 0.0f;
	float TotalWallProx = 0.0f;
	int32 HighConcealmentCount = 0;
	int32 HighDarknessCount = 0;
	int32 AmbushViableCount = 0;

	TArray<FVector> CenterView = { Center + FVector(0, 0, 170.0f) };

	struct FHeatmapCell
	{
		FVector Location;
		float TerritoryScore;
	};
	TArray<FHeatmapCell> Heatmap;

	for (const FVector& Pt : GridPoints)
	{
		float Concealment = MonolithMeshAnalysis::ComputeConcealment(World, Pt, CenterView);

		int32 DummyIdx;
		float Lum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Pt, Lights, DummyIdx);
		float Darkness = FMath::Clamp(1.0f - (Lum / 5.0f), 0.0f, 1.0f);

		float WallDist = MinWallDistance(World, Pt);
		float WallProx = FMath::Clamp(1.0f - (WallDist / 300.0f), 0.0f, 1.0f);

		TotalConcealment += Concealment;
		TotalDarkness += Darkness;
		TotalWallProx += WallProx;

		if (Concealment > 0.6f) ++HighConcealmentCount;
		if (Darkness > 0.6f) ++HighDarknessCount;
		if (Concealment > 0.5f && WallProx > 0.5f) ++AmbushViableCount;

		float CellScore;
		if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase))
		{
			CellScore = Concealment * 0.4f + Darkness * 0.35f + WallProx * 0.25f;
		}
		else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase))
		{
			CellScore = Concealment * 0.5f + WallProx * 0.3f + Darkness * 0.2f;
		}
		else // patrol
		{
			CellScore = WallProx * 0.4f + Darkness * 0.3f + Concealment * 0.3f;
		}

		FHeatmapCell Cell;
		Cell.Location = Pt;
		Cell.TerritoryScore = CellScore;
		Heatmap.Add(Cell);
	}

	int32 N = GridPoints.Num();
	float AvgConcealment = TotalConcealment / static_cast<float>(N);
	float AvgDarkness = TotalDarkness / static_cast<float>(N);
	float AvgWallProx = TotalWallProx / static_cast<float>(N);

	float HidingDensity = static_cast<float>(HighConcealmentCount) / static_cast<float>(N);
	float AmbushPotential = static_cast<float>(AmbushViableCount) / static_cast<float>(N);

	// Patrol coverage: how many grid cells can be reached from the center
	float PatrolCoverage = static_cast<float>(N); // All sampled points are on navmesh
	float CoverageRatio = static_cast<float>(N) / FMath::Max(1.0f,
		(PI * Radius * Radius) / (static_cast<float>(Granularity) * static_cast<float>(Granularity)));
	CoverageRatio = FMath::Clamp(CoverageRatio, 0.0f, 1.0f);

	// Sightline control: how much of the region the AI can see from the best vantage points
	// (averaged concealment from center — higher concealment = AI has more hiding options = better territory)
	float SightlineControl = AvgConcealment;

	// Overall territory score
	float TerritoryScore;
	if (Archetype.Equals(TEXT("stalker"), ESearchCase::IgnoreCase))
	{
		TerritoryScore = HidingDensity * 30.0f + SightlineControl * 25.0f + AvgDarkness * 25.0f + CoverageRatio * 20.0f;
	}
	else if (Archetype.Equals(TEXT("ambusher"), ESearchCase::IgnoreCase))
	{
		TerritoryScore = AmbushPotential * 35.0f + HidingDensity * 25.0f + AvgDarkness * 20.0f + CoverageRatio * 20.0f;
	}
	else // patrol
	{
		TerritoryScore = CoverageRatio * 30.0f + AvgWallProx * 25.0f + AvgDarkness * 25.0f + HidingDensity * 20.0f;
	}
	TerritoryScore = FMath::Clamp(TerritoryScore * 100.0f, 0.0f, 100.0f);

	// Build heatmap (capped to 100 entries)
	Heatmap.Sort([](const FHeatmapCell& A, const FHeatmapCell& B) { return A.TerritoryScore > B.TerritoryScore; });
	TArray<TSharedPtr<FJsonValue>> HeatmapArr;
	int32 HeatmapLimit = FMath::Min(Heatmap.Num(), 100);
	for (int32 i = 0; i < HeatmapLimit; ++i)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MEnc_VecToArr(Heatmap[i].Location));
		Obj->SetNumberField(TEXT("score"), Heatmap[i].TerritoryScore);
		HeatmapArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Breakdown = MakeShared<FJsonObject>();
	Breakdown->SetNumberField(TEXT("hiding_density"), HidingDensity);
	Breakdown->SetNumberField(TEXT("patrol_coverage"), CoverageRatio);
	Breakdown->SetNumberField(TEXT("sightline_control"), SightlineControl);
	Breakdown->SetNumberField(TEXT("ambush_potential"), AmbushPotential);
	Breakdown->SetNumberField(TEXT("average_darkness"), AvgDarkness);
	Breakdown->SetNumberField(TEXT("average_wall_proximity"), AvgWallProx);

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("territory_score"), FMath::RoundToInt(TerritoryScore));
	Result->SetStringField(TEXT("grade"), ScoreToGrade(TerritoryScore));
	Result->SetStringField(TEXT("archetype"), Archetype);
	Result->SetObjectField(TEXT("breakdown"), Breakdown);
	Result->SetArrayField(TEXT("heatmap"), HeatmapArr);
	Result->SetNumberField(TEXT("grid_points_sampled"), N);
	Result->SetNumberField(TEXT("high_concealment_points"), HighConcealmentCount);
	Result->SetNumberField(TEXT("ambush_viable_points"), AmbushViableCount);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 4. evaluate_safe_room
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::EvaluateSafeRoom(const TSharedPtr<FJsonObject>& Params)
{
	FVector Center;
	float Radius;
	if (!ParseRegion(Params, Center, Radius))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: region (object with center [x,y,z] and radius)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString NavError;
	if (!MonolithMeshAnalysis::GetNavSystem(World, NavSys, NavData, NavError))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Navigation not available: %s. Build navmesh first."), *NavError));
	}

	// ---- 1. Detect entrances ----
	TArray<FEntranceInfo> Entrances = DetectEntrances(World, NavSys, NavData, Center, Radius);

	// ---- 2. Lighting quality ----
	TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);
	int32 DummyIdx;
	float CenterLum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Center, Lights, DummyIdx);
	// Safe room should be well-lit. Score: 0=dark, 1=bright
	float LightingScore = FMath::Clamp(CenterLum / 3.0f, 0.0f, 1.0f);

	// ---- 3. Sound isolation ----
	// Check acoustic occlusion from outside the room to center
	float SoundIsolationScore = 0.0f;
	if (Entrances.Num() > 0)
	{
		float TotalOcclusion = 0.0f;
		int32 Tested = 0;
		for (const FEntranceInfo& Ent : Entrances)
		{
			FVector Outside = Ent.Location + Ent.Direction * 300.0f;
			int32 WallCount = 0;
			float LossdB = 0.0f;
			float Occlusion = MonolithMeshAcoustics::TraceOcclusion(World, Outside, Center, WallCount, LossdB);
			// For doors: non-entrance directions should be occluded
			TotalOcclusion += (1.0f - Occlusion); // Higher occlusion = more isolated
			++Tested;
		}

		// Also test from non-entrance directions
		for (int32 d = 0; d < 4; ++d)
		{
			float Angle = (2.0f * PI / 4.0f) * static_cast<float>(d);
			FVector TestPt = Center + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * (Radius + 500.0f);
			int32 WC;
			float LdB;
			float Occ = MonolithMeshAcoustics::TraceOcclusion(World, TestPt, Center, WC, LdB);
			TotalOcclusion += (1.0f - Occ);
			++Tested;
		}

		SoundIsolationScore = Tested > 0 ? FMath::Clamp(TotalOcclusion / static_cast<float>(Tested), 0.0f, 1.0f) : 0.0f;
	}
	else
	{
		// No entrances detected — might be very open
		SoundIsolationScore = 0.1f;
	}

	// ---- 4. Defensibility ----
	// Single entrance with door = most defensible. Multiple wide openings = least.
	float DefensibilityScore = 0.0f;
	{
		int32 DoorCount = 0;
		float TotalEntranceWidth = 0.0f;
		for (const FEntranceInfo& Ent : Entrances)
		{
			TotalEntranceWidth += Ent.Width;
			if (Ent.bHasDoor) ++DoorCount;
		}

		// Fewer entrances = more defensible
		float EntranceFactor = FMath::Clamp(1.0f - (static_cast<float>(Entrances.Num()) - 1.0f) / 3.0f, 0.0f, 1.0f);
		// Narrower = more defensible
		float WidthFactor = FMath::Clamp(1.0f - (TotalEntranceWidth / 500.0f), 0.0f, 1.0f);
		// Doors help
		float DoorFactor = Entrances.Num() > 0
			? static_cast<float>(DoorCount) / static_cast<float>(Entrances.Num())
			: 0.0f;

		DefensibilityScore = EntranceFactor * 0.4f + WidthFactor * 0.3f + DoorFactor * 0.3f;
	}

	// ---- 5. Room size / hospice accessibility ----
	float RoomVolume = MonolithMeshAnalysis::ApproximateRoomVolume(World, Center, Radius);
	float CeilingHeight = MonolithMeshAnalysis::MeasureCeilingHeight(World, Center);

	// Room should be large enough to feel safe but not so large it feels exposed
	// Sweet spot: 15-50 m^3
	float VolM3 = RoomVolume / 1000000.0f;
	float SizeScore;
	if (VolM3 < 5.0f)
	{
		SizeScore = 0.3f; // Too cramped
	}
	else if (VolM3 < 15.0f)
	{
		SizeScore = 0.6f + 0.4f * ((VolM3 - 5.0f) / 10.0f); // Getting better
	}
	else if (VolM3 < 50.0f)
	{
		SizeScore = 1.0f; // Sweet spot
	}
	else
	{
		SizeScore = FMath::Clamp(1.0f - ((VolM3 - 50.0f) / 100.0f), 0.3f, 1.0f); // Too large
	}

	// Hospice accessibility: path width, rest amenities
	float HospiceScore = 0.0f;
	{
		// Check if paths within room are wide enough (120cm)
		TArray<MonolithMeshAnalysis::FPathClearance> Clearances;
		// Sample a few paths through the room
		for (const FEntranceInfo& Ent : Entrances)
		{
			TArray<FVector> PathPts;
			float PathDist;
			if (MonolithMeshAnalysis::FindNavPath(World, Ent.Location, Center, PathPts, PathDist))
			{
				auto C = MonolithMeshAnalysis::MeasurePathClearance(World, PathPts, 500.0f);
				Clearances.Append(C);
			}
		}

		float MinWidth = 1000.0f;
		for (const auto& C : Clearances)
		{
			MinWidth = FMath::Min(MinWidth, C.TotalWidth);
		}
		float WidthScore = FMath::Clamp(MinWidth / 120.0f, 0.0f, 1.0f);

		// Check for rest amenities (actors tagged "Rest", "Bench", "SavePoint")
		int32 AmenityCount = 0;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (FVector::Dist((*It)->GetActorLocation(), Center) > Radius) continue;
			for (const FName& Tag : (*It)->Tags)
			{
				FString TagStr = Tag.ToString();
				if (TagStr.Contains(TEXT("Rest"), ESearchCase::IgnoreCase) ||
					TagStr.Contains(TEXT("Bench"), ESearchCase::IgnoreCase) ||
					TagStr.Contains(TEXT("Save"), ESearchCase::IgnoreCase))
				{
					++AmenityCount;
					break;
				}
			}
		}
		float AmenityScore = FMath::Clamp(static_cast<float>(AmenityCount) / 2.0f, 0.0f, 1.0f);

		HospiceScore = WidthScore * 0.5f + AmenityScore * 0.3f + SizeScore * 0.2f;
	}

	// ---- 6. Overall safe room score ----
	float SafeRoomScore = DefensibilityScore * 25.0f + LightingScore * 20.0f
		+ SoundIsolationScore * 20.0f + SizeScore * 15.0f + HospiceScore * 20.0f;
	SafeRoomScore = FMath::Clamp(SafeRoomScore, 0.0f, 100.0f);

	// Build entrances JSON
	TArray<TSharedPtr<FJsonValue>> EntranceArr;
	for (const FEntranceInfo& Ent : Entrances)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MEnc_VecToArr(Ent.Location));
		Obj->SetArrayField(TEXT("direction"), MEnc_VecToArr(Ent.Direction));
		Obj->SetNumberField(TEXT("width"), Ent.Width);
		Obj->SetBoolField(TEXT("has_door"), Ent.bHasDoor);
		EntranceArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	// Warnings
	TArray<TSharedPtr<FJsonValue>> Warnings;
	if (Entrances.Num() == 0)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("No entrances detected. Room may be inaccessible or detection failed.")));
	}
	if (Entrances.Num() > 3)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("Too many entrances for an effective safe room. Consider blocking some.")));
	}
	if (LightingScore < 0.3f)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("Safe room is too dark. Players need bright lighting to feel safe.")));
	}
	if (CeilingHeight > 0 && CeilingHeight < 200.0f)
	{
		Warnings.Add(MakeShared<FJsonValueString>(TEXT("Low ceiling may cause claustrophobic feeling — not ideal for a safe room.")));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetNumberField(TEXT("safe_room_score"), FMath::RoundToInt(SafeRoomScore));
	Result->SetStringField(TEXT("grade"), ScoreToGrade(SafeRoomScore));
	Result->SetNumberField(TEXT("entrance_count"), Entrances.Num());
	Result->SetArrayField(TEXT("entrances"), EntranceArr);
	Result->SetNumberField(TEXT("lighting_score"), LightingScore);
	Result->SetNumberField(TEXT("sound_isolation"), SoundIsolationScore);
	Result->SetNumberField(TEXT("defensibility"), DefensibilityScore);
	Result->SetNumberField(TEXT("size_score"), SizeScore);
	Result->SetNumberField(TEXT("hospice_accessibility"), HospiceScore);
	Result->SetNumberField(TEXT("room_volume_m3"), VolM3);
	Result->SetNumberField(TEXT("ceiling_height"), CeilingHeight);
	Result->SetArrayField(TEXT("warnings"), Warnings);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 5. analyze_level_pacing_structure
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::AnalyzeLevelPacingStructure(const TSharedPtr<FJsonObject>& Params)
{
	FVector Start, End;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("start"), Start))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: start (array of 3 numbers)"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("end"), End))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: end (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Parse optional waypoints
	TArray<FVector> Waypoints;
	MEnc_ParseVectorArray(Params, TEXT("waypoints"), Waypoints);

	double SampleInterval = 500.0;
	Params->TryGetNumberField(TEXT("sample_interval"), SampleInterval);
	SampleInterval = FMath::Clamp(SampleInterval, 100.0, 5000.0);

	// Build full path through waypoints
	TArray<FVector> FullPath;
	float TotalDist = 0.0f;
	{
		TArray<FVector> Sequence;
		Sequence.Add(Start);
		for (const FVector& WP : Waypoints) Sequence.Add(WP);
		Sequence.Add(End);

		for (int32 i = 0; i < Sequence.Num() - 1; ++i)
		{
			TArray<FVector> Seg;
			float SegDist;
			if (MonolithMeshAnalysis::FindNavPath(World, Sequence[i], Sequence[i + 1], Seg, SegDist))
			{
				int32 StartIdx = (FullPath.Num() > 0 && Seg.Num() > 0) ? 1 : 0;
				for (int32 j = StartIdx; j < Seg.Num(); ++j)
				{
					FullPath.Add(Seg[j]);
				}
				TotalDist += SegDist;
			}
			else
			{
				return FMonolithActionResult::Error(FString::Printf(
					TEXT("No navmesh path found between segment %d and %d. Build navmesh or adjust waypoints."), i, i + 1));
			}
		}
	}

	if (FullPath.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Resolved path is too short for pacing analysis."));
	}

	// Resample path
	TArray<FVector> SamplePoints = ResamplePath(FullPath, static_cast<float>(SampleInterval));

	// Cap for performance
	if (SamplePoints.Num() > 200)
	{
		int32 Step = (SamplePoints.Num() + 199) / 200;
		TArray<FVector> Thinned;
		for (int32 i = 0; i < SamplePoints.Num(); i += Step) Thinned.Add(SamplePoints[i]);
		SamplePoints = MoveTemp(Thinned);
	}

	// ---- Sample tension along path ----
	struct FPacingSample
	{
		FVector Location;
		float DistanceAlongPath = 0.0f;
		float Tension = 0.0f;
		FString ZoneType; // encounter, safe_room, exploration, transition
	};

	TArray<FPacingSample> Samples;
	float Accum = 0.0f;

	for (int32 i = 0; i < SamplePoints.Num(); ++i)
	{
		if (i > 0) Accum += FVector::Dist(SamplePoints[i - 1], SamplePoints[i]);

		FPacingSample S;
		S.Location = SamplePoints[i];
		S.DistanceAlongPath = Accum;
		S.Tension = FullTensionScore(World, SamplePoints[i]);

		// Classify zone
		if (S.Tension < 20.0f)
		{
			S.ZoneType = TEXT("safe_room");
		}
		else if (S.Tension < 40.0f)
		{
			S.ZoneType = TEXT("exploration");
		}
		else if (S.Tension < 60.0f)
		{
			S.ZoneType = TEXT("transition");
		}
		else
		{
			S.ZoneType = TEXT("encounter");
		}

		Samples.Add(MoveTemp(S));
	}

	// ---- Identify structure ----
	// Find tension peaks
	TArray<TSharedPtr<FJsonValue>> PeaksArr;
	for (int32 i = 1; i < Samples.Num() - 1; ++i)
	{
		if (Samples[i].Tension > Samples[i - 1].Tension && Samples[i].Tension > Samples[i + 1].Tension
			&& Samples[i].Tension > 50.0f)
		{
			auto PeakObj = MakeShared<FJsonObject>();
			PeakObj->SetArrayField(TEXT("location"), MEnc_VecToArr(Samples[i].Location));
			PeakObj->SetNumberField(TEXT("distance"), Samples[i].DistanceAlongPath);
			PeakObj->SetNumberField(TEXT("tension"), FMath::RoundToInt(Samples[i].Tension));
			PeaksArr.Add(MakeShared<FJsonValueObject>(PeakObj));
		}
	}

	// Find rest zones (contiguous calm/uneasy segments)
	TArray<TSharedPtr<FJsonValue>> RestZonesArr;
	int32 RestStart = -1;
	for (int32 i = 0; i <= Samples.Num(); ++i)
	{
		bool bIsRest = (i < Samples.Num()) && (Samples[i].Tension < 25.0f);
		if (bIsRest && RestStart < 0)
		{
			RestStart = i;
		}
		else if (!bIsRest && RestStart >= 0)
		{
			float RestDist = Samples[i - 1].DistanceAlongPath - Samples[RestStart].DistanceAlongPath;
			if (RestDist > 200.0f) // Meaningful rest zone
			{
				auto ZoneObj = MakeShared<FJsonObject>();
				ZoneObj->SetArrayField(TEXT("start_location"), MEnc_VecToArr(Samples[RestStart].Location));
				ZoneObj->SetArrayField(TEXT("end_location"), MEnc_VecToArr(Samples[i - 1].Location));
				ZoneObj->SetNumberField(TEXT("start_distance"), Samples[RestStart].DistanceAlongPath);
				ZoneObj->SetNumberField(TEXT("end_distance"), Samples[i - 1].DistanceAlongPath);
				ZoneObj->SetNumberField(TEXT("length"), RestDist);
				RestZonesArr.Add(MakeShared<FJsonValueObject>(ZoneObj));
			}
			RestStart = -1;
		}
	}

	// Max sustained tension distance
	float MaxSustainedTension = 0.0f;
	float CurrentSustained = 0.0f;
	for (int32 i = 1; i < Samples.Num(); ++i)
	{
		if (Samples[i].Tension > 50.0f)
		{
			CurrentSustained += Samples[i].DistanceAlongPath - Samples[i - 1].DistanceAlongPath;
			MaxSustainedTension = FMath::Max(MaxSustainedTension, CurrentSustained);
		}
		else
		{
			CurrentSustained = 0.0f;
		}
	}

	// ---- Hospice assessment ----
	auto HospiceObj = MakeShared<FJsonObject>();
	{
		// Check rest spacing (every 2-3 min at walk speed ~300 cm/s = 36000-54000 cm)
		float MaxGapBetweenRests = 0.0f;
		float LastRestEnd = 0.0f;

		for (const TSharedPtr<FJsonValue>& RZVal : RestZonesArr)
		{
			float RZStart = RZVal->AsObject()->GetNumberField(TEXT("start_distance"));
			float Gap = RZStart - LastRestEnd;
			MaxGapBetweenRests = FMath::Max(MaxGapBetweenRests, Gap);
			LastRestEnd = RZVal->AsObject()->GetNumberField(TEXT("end_distance"));
		}
		// Check gap from last rest to end
		MaxGapBetweenRests = FMath::Max(MaxGapBetweenRests, TotalDist - LastRestEnd);

		float MaxGapMinutes = MaxGapBetweenRests / (300.0f * 60.0f); // at 300 cm/s
		bool bRestSpacingOk = MaxGapMinutes <= 3.0f;

		HospiceObj->SetNumberField(TEXT("max_gap_between_rests_cm"), MaxGapBetweenRests);
		HospiceObj->SetNumberField(TEXT("max_gap_minutes"), MaxGapMinutes);
		HospiceObj->SetBoolField(TEXT("rest_spacing_adequate"), bRestSpacingOk);

		// Max tension check
		float PeakTension = 0.0f;
		for (const FPacingSample& S : Samples)
		{
			PeakTension = FMath::Max(PeakTension, S.Tension);
		}
		HospiceObj->SetNumberField(TEXT("peak_tension"), FMath::RoundToInt(PeakTension));
		HospiceObj->SetBoolField(TEXT("tension_under_cap"), PeakTension <= 50.0f);

		// Sustained tension check
		float MaxSustainedMinutes = MaxSustainedTension / (300.0f * 60.0f);
		HospiceObj->SetNumberField(TEXT("max_sustained_tension_minutes"), MaxSustainedMinutes);
		HospiceObj->SetBoolField(TEXT("sustained_tension_ok"), MaxSustainedMinutes <= 1.5f);

		bool bOverallSafe = bRestSpacingOk && PeakTension <= 50.0f && MaxSustainedMinutes <= 1.5f;
		HospiceObj->SetBoolField(TEXT("overall_hospice_safe"), bOverallSafe);
	}

	// ---- Warnings ----
	TArray<TSharedPtr<FJsonValue>> WarningsArr;
	if (RestZonesArr.Num() == 0)
	{
		WarningsArr.Add(MakeShared<FJsonValueString>(TEXT("HOSPICE CRITICAL: No rest zones detected along the entire path.")));
	}
	if (MaxSustainedTension > 5000.0f)
	{
		WarningsArr.Add(MakeShared<FJsonValueString>(FString::Printf(
			TEXT("Sustained high tension for %.0f cm without a break. Consider adding a calm zone."), MaxSustainedTension)));
	}
	if (PeaksArr.Num() == 0 && TotalDist > 5000.0f)
	{
		WarningsArr.Add(MakeShared<FJsonValueString>(TEXT("No tension peaks found — level may feel flat and unengaging.")));
	}

	// Build pacing curve
	TArray<TSharedPtr<FJsonValue>> CurveArr;
	for (const FPacingSample& S : Samples)
	{
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetNumberField(TEXT("distance"), S.DistanceAlongPath);
		Obj->SetNumberField(TEXT("tension"), FMath::RoundToInt(S.Tension));
		Obj->SetStringField(TEXT("zone_type"), S.ZoneType);
		CurveArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Structure = MakeShared<FJsonObject>();
	Structure->SetArrayField(TEXT("tension_peaks"), PeaksArr);
	Structure->SetArrayField(TEXT("rest_zones"), RestZonesArr);
	Structure->SetNumberField(TEXT("max_sustained_tension_distance"), MaxSustainedTension);
	Structure->SetNumberField(TEXT("peak_count"), PeaksArr.Num());
	Structure->SetNumberField(TEXT("rest_zone_count"), RestZonesArr.Num());

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("pacing_curve"), CurveArr);
	Result->SetObjectField(TEXT("structure"), Structure);
	Result->SetObjectField(TEXT("hospice_assessment"), HospiceObj);
	Result->SetArrayField(TEXT("warnings"), WarningsArr);
	Result->SetNumberField(TEXT("total_path_length"), TotalDist);
	Result->SetNumberField(TEXT("sample_count"), Samples.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 6. generate_scare_sequence
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::GenerateScareSequence(const TSharedPtr<FJsonObject>& Params)
{
	TArray<FVector> PathPoints;
	if (!MEnc_ParseVectorArray(Params, TEXT("path_points"), PathPoints) || PathPoints.Num() < 2)
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: path_points (array of at least 2 [x,y,z])"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString Style = TEXT("escalating");
	Params->TryGetStringField(TEXT("style"), Style);

	double IntensityCap = 1.0;
	Params->TryGetNumberField(TEXT("intensity_cap"), IntensityCap);
	IntensityCap = FMath::Clamp(IntensityCap, 0.1, 1.0);

	TArray<FString> ScareTypes;
	if (!MEnc_ParseStringArray(Params, TEXT("scare_types"), ScareTypes) || ScareTypes.Num() == 0)
	{
		ScareTypes = { TEXT("audio"), TEXT("visual"), TEXT("environmental"), TEXT("entity_spawn") };
	}

	int32 Count = 5;
	{
		double V;
		if (Params->TryGetNumberField(TEXT("count"), V))
		{
			Count = FMath::Clamp(static_cast<int32>(V), 1, 20);
		}
	}

	float TotalLength = PathLength(PathPoints);
	if (TotalLength < 500.0f)
	{
		return FMonolithActionResult::Error(TEXT("Path too short for scare sequence generation. Need at least 500cm."));
	}

	// Resample path
	float Interval = FMath::Max(100.0f, TotalLength / static_cast<float>(FMath::Max(Count * 5, 20)));
	TArray<FVector> Sampled = ResamplePath(PathPoints, Interval);

	// Score each sample point for scare suitability
	struct FScareSample
	{
		FVector Location;
		float DistAlongPath;
		float Tension;
		float Darkness;
		int32 EscapeCount;
	};

	TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);
	TArray<FScareSample> ScareSamples;
	float Dist = 0.0f;

	for (int32 i = 0; i < Sampled.Num(); ++i)
	{
		if (i > 0) Dist += FVector::Dist(Sampled[i - 1], Sampled[i]);

		FScareSample S;
		S.Location = Sampled[i];
		S.DistAlongPath = Dist;
		S.Tension = QuickTensionScore(World, Sampled[i]);

		int32 DummyIdx;
		float Lum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Sampled[i], Lights, DummyIdx);
		S.Darkness = FMath::Clamp(1.0f - (Lum / 5.0f), 0.0f, 1.0f);
		S.EscapeCount = MonolithMeshAnalysis::CountExits(World, Sampled[i], 1500.0f, 6);

		ScareSamples.Add(S);
	}

	// Generate scare events with style-based intensity distribution
	struct FScareEvent
	{
		FVector Location;
		float DistAlongPath;
		float Intensity; // 0-1
		FString Type;
		float Duration; // seconds
		FString Description;
		int32 EscapeCount;
	};

	// Determine placement positions based on style
	TArray<float> TargetPositions; // 0-1 normalized path positions
	if (Style.Equals(TEXT("slow_burn"), ESearchCase::IgnoreCase))
	{
		// Quiet, quiet, quiet... PEAK at 80-90%
		for (int32 i = 0; i < Count; ++i)
		{
			float T = 0.2f + (0.7f * static_cast<float>(i) / static_cast<float>(FMath::Max(Count - 1, 1)));
			TargetPositions.Add(T);
		}
	}
	else if (Style.Equals(TEXT("relentless"), ESearchCase::IgnoreCase))
	{
		// Evenly distributed, consistently high
		for (int32 i = 0; i < Count; ++i)
		{
			float T = 0.1f + 0.8f * static_cast<float>(i) / static_cast<float>(FMath::Max(Count - 1, 1));
			TargetPositions.Add(T);
		}
	}
	else if (Style.Equals(TEXT("single_peak"), ESearchCase::IgnoreCase))
	{
		// Build to one big moment at ~70% then release
		for (int32 i = 0; i < Count; ++i)
		{
			float T;
			if (i < Count - 1)
			{
				T = 0.15f + 0.5f * static_cast<float>(i) / static_cast<float>(FMath::Max(Count - 2, 1));
			}
			else
			{
				T = 0.7f; // The peak
			}
			TargetPositions.Add(T);
		}
	}
	else // escalating (default)
	{
		for (int32 i = 0; i < Count; ++i)
		{
			float T = 0.15f + 0.75f * static_cast<float>(i) / static_cast<float>(FMath::Max(Count - 1, 1));
			TargetPositions.Add(T);
		}
	}

	// Generate events
	TArray<FScareEvent> Events;
	for (int32 i = 0; i < TargetPositions.Num(); ++i)
	{
		float TargetDist = TargetPositions[i] * TotalLength;

		// Find closest sample
		int32 BestIdx = 0;
		float BestDelta = TNumericLimits<float>::Max();
		for (int32 j = 0; j < ScareSamples.Num(); ++j)
		{
			float Delta = FMath::Abs(ScareSamples[j].DistAlongPath - TargetDist);
			if (Delta < BestDelta)
			{
				BestDelta = Delta;
				BestIdx = j;
			}
		}

		FScareEvent Event;
		Event.Location = ScareSamples[BestIdx].Location;
		Event.DistAlongPath = ScareSamples[BestIdx].DistAlongPath;
		Event.EscapeCount = ScareSamples[BestIdx].EscapeCount;

		// Compute intensity based on style
		float NormPos = static_cast<float>(i) / static_cast<float>(FMath::Max(Count - 1, 1));
		if (Style.Equals(TEXT("slow_burn"), ESearchCase::IgnoreCase))
		{
			Event.Intensity = (i == Count - 1) ? 1.0f : (0.1f + NormPos * 0.3f);
		}
		else if (Style.Equals(TEXT("relentless"), ESearchCase::IgnoreCase))
		{
			Event.Intensity = 0.6f + FMath::FRand() * 0.3f;
		}
		else if (Style.Equals(TEXT("single_peak"), ESearchCase::IgnoreCase))
		{
			Event.Intensity = (i == Count - 1) ? 1.0f : (0.15f + NormPos * 0.35f);
		}
		else // escalating
		{
			Event.Intensity = 0.2f + NormPos * 0.8f;
		}

		// Apply cap
		Event.Intensity = FMath::Min(Event.Intensity, static_cast<float>(IntensityCap));

		// Select type — rotate through available types with variety
		Event.Type = ScareTypes[i % ScareTypes.Num()];

		// Duration based on type
		if (Event.Type == TEXT("audio"))
		{
			Event.Duration = 3.0f + Event.Intensity * 5.0f;
			Event.Description = FString::Printf(TEXT("Audio scare at %.0f%% intensity — %s"),
				Event.Intensity * 100.0f,
				Event.Intensity > 0.7f ? TEXT("sharp sudden sound") : TEXT("ambient creaking/whisper"));
		}
		else if (Event.Type == TEXT("visual"))
		{
			Event.Duration = 2.0f + Event.Intensity * 4.0f;
			Event.Description = FString::Printf(TEXT("Visual scare at %.0f%% — %s"),
				Event.Intensity * 100.0f,
				Event.Intensity > 0.7f ? TEXT("entity glimpse or light failure") : TEXT("shadow movement or flickering"));
		}
		else if (Event.Type == TEXT("environmental"))
		{
			Event.Duration = 4.0f + Event.Intensity * 6.0f;
			Event.Description = FString::Printf(TEXT("Environmental scare at %.0f%% — %s"),
				Event.Intensity * 100.0f,
				Event.Intensity > 0.7f ? TEXT("door slam, debris fall, power outage") : TEXT("temperature drop, distant rumble"));
		}
		else // entity_spawn
		{
			Event.Duration = 5.0f + Event.Intensity * 10.0f;
			Event.Description = FString::Printf(TEXT("Entity encounter at %.0f%% — %s"),
				Event.Intensity * 100.0f,
				Event.Intensity > 0.7f ? TEXT("direct confrontation, chase sequence") : TEXT("distant sighting, evidence of presence"));
		}

		Events.Add(MoveTemp(Event));
	}

	// Build result
	TArray<TSharedPtr<FJsonValue>> EventsArr;
	for (int32 i = 0; i < Events.Num(); ++i)
	{
		const FScareEvent& E = Events[i];
		auto Obj = MakeShared<FJsonObject>();
		Obj->SetNumberField(TEXT("sequence_index"), i);
		Obj->SetArrayField(TEXT("location"), MEnc_VecToArr(E.Location));
		Obj->SetNumberField(TEXT("distance_along_path"), E.DistAlongPath);
		Obj->SetNumberField(TEXT("intensity"), E.Intensity);
		Obj->SetStringField(TEXT("type"), E.Type);
		Obj->SetNumberField(TEXT("duration_seconds"), E.Duration);
		Obj->SetStringField(TEXT("description"), E.Description);
		Obj->SetNumberField(TEXT("escape_routes_available"), E.EscapeCount);
		EventsArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("style"), Style);
	Result->SetNumberField(TEXT("intensity_cap"), IntensityCap);
	Result->SetNumberField(TEXT("event_count"), Events.Num());
	Result->SetArrayField(TEXT("events"), EventsArr);
	Result->SetNumberField(TEXT("total_path_length"), TotalLength);

	// Warnings
	TArray<TSharedPtr<FJsonValue>> Warnings;
	for (const FScareEvent& E : Events)
	{
		if (E.EscapeCount < 1)
		{
			Warnings.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("HOSPICE: Event at distance %.0f cm has no escape routes. Patients MUST have a way out."),
				E.DistAlongPath)));
		}
		if (E.Intensity > 0.5f && E.Type == TEXT("entity_spawn"))
		{
			Warnings.Add(MakeShared<FJsonValueString>(FString::Printf(
				TEXT("High-intensity entity spawn at %.0f cm. If hospice mode, cap to 0.5 or use audio/visual instead."),
				E.DistAlongPath)));
		}
	}
	Result->SetArrayField(TEXT("warnings"), Warnings);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 7. validate_horror_intensity
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::ValidateHorrorIntensity(const TSharedPtr<FJsonObject>& Params)
{
	FVector Start, End;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("start"), Start))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: start (array of 3 numbers)"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("end"), End))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: end (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	double IntensityCap = 50.0;
	Params->TryGetNumberField(TEXT("intensity_cap"), IntensityCap);
	IntensityCap = FMath::Clamp(IntensityCap, 0.0, 100.0);

	bool bFlagJumpScares = true;
	Params->TryGetBoolField(TEXT("flag_jump_scares"), bFlagJumpScares);

	double MinRestDistance = 800.0;
	Params->TryGetNumberField(TEXT("min_rest_distance_cm"), MinRestDistance);

	int32 MinEscapeRoutes = 2;
	{
		double V;
		if (Params->TryGetNumberField(TEXT("min_escape_routes"), V))
		{
			MinEscapeRoutes = FMath::Clamp(static_cast<int32>(V), 0, 10);
		}
	}

	// Build navmesh path
	TArray<FVector> PathPoints;
	float PathDist;
	if (!MonolithMeshAnalysis::FindNavPath(World, Start, End, PathPoints, PathDist))
	{
		return FMonolithActionResult::Error(TEXT("No navmesh path found. Build navigation first."));
	}

	// Resample at reasonable interval
	float SampleInterval = FMath::Clamp(PathDist / 100.0f, 100.0f, 500.0f);
	TArray<FVector> Sampled = ResamplePath(PathPoints, SampleInterval);

	// Cap for performance
	if (Sampled.Num() > 200)
	{
		int32 Step = (Sampled.Num() + 199) / 200;
		TArray<FVector> Thinned;
		for (int32 i = 0; i < Sampled.Num(); i += Step) Thinned.Add(Sampled[i]);
		Sampled = MoveTemp(Thinned);
	}

	// Sample tension and escape counts
	struct FIntensitySample
	{
		FVector Location;
		float Distance;
		float Tension;
		int32 EscapeRoutes;
	};

	TArray<FIntensitySample> Samples;
	float Accum = 0.0f;

	for (int32 i = 0; i < Sampled.Num(); ++i)
	{
		if (i > 0) Accum += FVector::Dist(Sampled[i - 1], Sampled[i]);

		FIntensitySample S;
		S.Location = Sampled[i];
		S.Distance = Accum;
		S.Tension = FullTensionScore(World, Sampled[i]);
		S.EscapeRoutes = MonolithMeshAnalysis::CountExits(World, Sampled[i], 1500.0f, 6);
		Samples.Add(S);
	}

	// ---- Find violations ----
	struct FViolation
	{
		FVector Location;
		float Distance;
		FString Type;
		FString Severity;
		FString Description;
		float Value;
		float Threshold;
	};

	TArray<FViolation> Violations;

	// 1. Tension cap violations
	for (const FIntensitySample& S : Samples)
	{
		if (S.Tension > static_cast<float>(IntensityCap))
		{
			// Check if near an existing violation (merge nearby)
			bool bMerged = false;
			for (FViolation& Existing : Violations)
			{
				if (Existing.Type == TEXT("tension_exceeds_cap") && FMath::Abs(S.Distance - Existing.Distance) < 300.0f)
				{
					if (S.Tension > Existing.Value) // Keep the worst one
					{
						Existing.Location = S.Location;
						Existing.Distance = S.Distance;
						Existing.Value = S.Tension;
						Existing.Description = FString::Printf(
							TEXT("Tension %.0f exceeds cap %.0f at distance %.0f cm"),
							S.Tension, IntensityCap, S.Distance);
					}
					bMerged = true;
					break;
				}
			}
			if (!bMerged)
			{
				FViolation V;
				V.Location = S.Location;
				V.Distance = S.Distance;
				V.Type = TEXT("tension_exceeds_cap");
				V.Severity = TEXT("critical");
				V.Value = S.Tension;
				V.Threshold = static_cast<float>(IntensityCap);
				V.Description = FString::Printf(
					TEXT("Tension %.0f exceeds cap %.0f at distance %.0f cm"),
					S.Tension, IntensityCap, S.Distance);
				Violations.Add(MoveTemp(V));
			}
		}
	}

	// 2. Jump scare detection (sudden tension spike > 30 points between adjacent samples)
	if (bFlagJumpScares)
	{
		for (int32 i = 1; i < Samples.Num(); ++i)
		{
			float TensionDelta = Samples[i].Tension - Samples[i - 1].Tension;
			if (TensionDelta > 30.0f)
			{
				FViolation V;
				V.Location = Samples[i].Location;
				V.Distance = Samples[i].Distance;
				V.Type = TEXT("jump_scare");
				V.Severity = TEXT("warning");
				V.Value = TensionDelta;
				V.Threshold = 30.0f;
				V.Description = FString::Printf(
					TEXT("Sudden tension spike of +%.0f at distance %.0f cm (%.0f -> %.0f). Potential jump scare."),
					TensionDelta, Samples[i].Distance, Samples[i - 1].Tension, Samples[i].Tension);
				Violations.Add(MoveTemp(V));
			}
		}
	}

	// 3. Insufficient rest between high-tension zones
	float LastHighTensionEnd = -1.0f;
	bool bInHighTension = false;
	for (const FIntensitySample& S : Samples)
	{
		bool bHigh = S.Tension > static_cast<float>(IntensityCap) * 0.8f;
		if (bHigh && !bInHighTension)
		{
			// Entering high-tension zone
			if (LastHighTensionEnd >= 0.0f)
			{
				float Gap = S.Distance - LastHighTensionEnd;
				if (Gap < static_cast<float>(MinRestDistance))
				{
					FViolation V;
					V.Location = S.Location;
					V.Distance = S.Distance;
					V.Type = TEXT("insufficient_rest");
					V.Severity = TEXT("critical");
					V.Value = Gap;
					V.Threshold = static_cast<float>(MinRestDistance);
					V.Description = FString::Printf(
						TEXT("Only %.0f cm of rest between high-tension zones (minimum: %.0f cm) at distance %.0f"),
						Gap, MinRestDistance, S.Distance);
					Violations.Add(MoveTemp(V));
				}
			}
			bInHighTension = true;
		}
		else if (!bHigh && bInHighTension)
		{
			LastHighTensionEnd = S.Distance;
			bInHighTension = false;
		}
	}

	// 4. Insufficient escape routes
	for (const FIntensitySample& S : Samples)
	{
		if (S.Tension > 40.0f && S.EscapeRoutes < MinEscapeRoutes)
		{
			// Merge nearby
			bool bMerged = false;
			for (FViolation& Existing : Violations)
			{
				if (Existing.Type == TEXT("insufficient_escape") && FMath::Abs(S.Distance - Existing.Distance) < 500.0f)
				{
					bMerged = true;
					break;
				}
			}
			if (!bMerged)
			{
				FViolation V;
				V.Location = S.Location;
				V.Distance = S.Distance;
				V.Type = TEXT("insufficient_escape");
				V.Severity = TEXT("critical");
				V.Value = static_cast<float>(S.EscapeRoutes);
				V.Threshold = static_cast<float>(MinEscapeRoutes);
				V.Description = FString::Printf(
					TEXT("Only %d escape routes at tension=%.0f, distance %.0f cm (minimum: %d). Hospice patients need a way out."),
					S.EscapeRoutes, S.Tension, S.Distance, MinEscapeRoutes);
				Violations.Add(MoveTemp(V));
			}
		}
	}

	// Sort by distance
	Violations.Sort([](const FViolation& A, const FViolation& B) { return A.Distance < B.Distance; });

	// Count severities
	int32 CriticalCount = 0, WarningCount = 0;
	TArray<TSharedPtr<FJsonValue>> ViolArr;
	for (const FViolation& V : Violations)
	{
		if (V.Severity == TEXT("critical")) ++CriticalCount;
		else ++WarningCount;

		auto Obj = MakeShared<FJsonObject>();
		Obj->SetArrayField(TEXT("location"), MEnc_VecToArr(V.Location));
		Obj->SetNumberField(TEXT("distance_along_path"), V.Distance);
		Obj->SetStringField(TEXT("type"), V.Type);
		Obj->SetStringField(TEXT("severity"), V.Severity);
		Obj->SetStringField(TEXT("description"), V.Description);
		Obj->SetNumberField(TEXT("value"), V.Value);
		Obj->SetNumberField(TEXT("threshold"), V.Threshold);
		ViolArr.Add(MakeShared<FJsonValueObject>(Obj));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetBoolField(TEXT("overall_hospice_safe"), CriticalCount == 0);
	Result->SetNumberField(TEXT("violation_count"), Violations.Num());
	Result->SetNumberField(TEXT("critical_violations"), CriticalCount);
	Result->SetNumberField(TEXT("warning_violations"), WarningCount);
	Result->SetArrayField(TEXT("violations"), ViolArr);
	Result->SetNumberField(TEXT("intensity_cap"), IntensityCap);
	Result->SetBoolField(TEXT("jump_scare_detection"), bFlagJumpScares);
	Result->SetNumberField(TEXT("min_rest_distance_cm"), MinRestDistance);
	Result->SetNumberField(TEXT("min_escape_routes"), MinEscapeRoutes);
	Result->SetNumberField(TEXT("path_length"), PathDist);
	Result->SetNumberField(TEXT("samples_analyzed"), Samples.Num());

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 8. generate_hospice_report
// ============================================================================

FMonolithActionResult FMonolithMeshEncounterActions::GenerateHospiceReport(const TSharedPtr<FJsonObject>& Params)
{
	FVector Start, End;
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("start"), Start))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: start (array of 3 numbers)"));
	}
	if (!MonolithMeshUtils::ParseVector(Params, TEXT("end"), End))
	{
		return FMonolithActionResult::Error(TEXT("Missing or invalid required param: end (array of 3 numbers)"));
	}

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FString Profile;
	Params->TryGetStringField(TEXT("profile"), Profile);

	double WalkSpeed = 300.0;
	Params->TryGetNumberField(TEXT("walk_speed_cms"), WalkSpeed);
	WalkSpeed = FMath::Clamp(WalkSpeed, 50.0, 1000.0);

	// Determine which profiles to run
	TArray<FString> Profiles;
	if (Profile.IsEmpty())
	{
		Profiles = { TEXT("motor_impaired"), TEXT("vision_impaired"), TEXT("cognitive_fatigue") };
	}
	else
	{
		Profiles.Add(Profile);
	}

	// Build navmesh path
	TArray<FVector> PathPoints;
	float PathDist;
	if (!MonolithMeshAnalysis::FindNavPath(World, Start, End, PathPoints, PathDist))
	{
		return FMonolithActionResult::Error(TEXT("No navmesh path found. Build navigation first."));
	}

	float EstimatedTimeMinutes = PathDist / (static_cast<float>(WalkSpeed) * 60.0f);

	auto Report = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> AllIssues;
	int32 CriticalCount = 0, WarningCount = 0;

	// ============================================
	// Section 1: Intensity Audit (all profiles)
	// ============================================
	{
		auto IntensityParams = MakeShared<FJsonObject>();
		SetVectorParam(IntensityParams, TEXT("start"), Start);
		SetVectorParam(IntensityParams, TEXT("end"), End);
		IntensityParams->SetNumberField(TEXT("intensity_cap"), 50.0); // Hospice cap
		IntensityParams->SetBoolField(TEXT("flag_jump_scares"), true);
		IntensityParams->SetNumberField(TEXT("min_rest_distance_cm"), 800.0);
		IntensityParams->SetNumberField(TEXT("min_escape_routes"), 2);

		FMonolithActionResult IntResult = ValidateHorrorIntensity(IntensityParams);
		if (IntResult.bSuccess)
		{
			Report->SetObjectField(TEXT("intensity"), IntResult.Result);
			if (!IntResult.Result->GetBoolField(TEXT("overall_hospice_safe")))
			{
				int32 IntViolations = static_cast<int32>(IntResult.Result->GetNumberField(TEXT("critical_violations")));
				auto Issue = MakeShared<FJsonObject>();
				Issue->SetStringField(TEXT("category"), TEXT("intensity"));
				Issue->SetStringField(TEXT("severity"), TEXT("critical"));
				Issue->SetStringField(TEXT("description"), FString::Printf(
					TEXT("%d critical intensity violations. Hospice patients require tension under 50."), IntViolations));
				AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
				CriticalCount += IntViolations;
			}
		}
	}

	// ============================================
	// Section 2: Rest Spacing
	// ============================================
	{
		// Walk the path and find calm zones (tension < 25)
		float SampleInterval = FMath::Clamp(PathDist / 80.0f, 100.0f, 500.0f);
		TArray<FVector> Sampled = ResamplePath(PathPoints, SampleInterval);

		// Cap
		if (Sampled.Num() > 150)
		{
			int32 Step = (Sampled.Num() + 149) / 150;
			TArray<FVector> T;
			for (int32 i = 0; i < Sampled.Num(); i += Step) T.Add(Sampled[i]);
			Sampled = MoveTemp(T);
		}

		float Accum = 0.0f;
		float LastRestDist = 0.0f;
		float MaxGap = 0.0f;
		int32 RestCount = 0;
		TArray<TSharedPtr<FJsonValue>> GapsArr;

		for (int32 i = 0; i < Sampled.Num(); ++i)
		{
			if (i > 0) Accum += FVector::Dist(Sampled[i - 1], Sampled[i]);

			float Tension = QuickTensionScore(World, Sampled[i]);
			if (Tension < 25.0f)
			{
				float Gap = Accum - LastRestDist;
				if (Gap > 100.0f && RestCount > 0) // Not the first calm point
				{
					float GapMinutes = Gap / (static_cast<float>(WalkSpeed) * 60.0f);
					MaxGap = FMath::Max(MaxGap, Gap);

					if (GapMinutes > 3.0f) // Hospice: rest every 2-3 minutes
					{
						auto GapObj = MakeShared<FJsonObject>();
						GapObj->SetNumberField(TEXT("start_distance"), LastRestDist);
						GapObj->SetNumberField(TEXT("end_distance"), Accum);
						GapObj->SetNumberField(TEXT("gap_cm"), Gap);
						GapObj->SetNumberField(TEXT("gap_minutes"), GapMinutes);
						GapsArr.Add(MakeShared<FJsonValueObject>(GapObj));

						auto Issue = MakeShared<FJsonObject>();
						Issue->SetStringField(TEXT("category"), TEXT("rest_spacing"));
						Issue->SetStringField(TEXT("severity"), TEXT("critical"));
						Issue->SetStringField(TEXT("description"), FString::Printf(
							TEXT("%.1f minute gap without rest opportunity (%.0f cm). Hospice max: 3 minutes."),
							GapMinutes, Gap));
						AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
						++CriticalCount;
					}
				}
				LastRestDist = Accum;
				++RestCount;
			}
		}

		auto RestObj = MakeShared<FJsonObject>();
		RestObj->SetNumberField(TEXT("rest_points_found"), RestCount);
		RestObj->SetNumberField(TEXT("max_gap_cm"), MaxGap);
		RestObj->SetNumberField(TEXT("max_gap_minutes"), MaxGap / (static_cast<float>(WalkSpeed) * 60.0f));
		RestObj->SetArrayField(TEXT("excessive_gaps"), GapsArr);
		RestObj->SetBoolField(TEXT("passes"), GapsArr.Num() == 0);
		Report->SetObjectField(TEXT("rest_spacing"), RestObj);
	}

	// ============================================
	// Section 3: Cognitive Load
	// ============================================
	{
		// Navigation complexity analysis
		int32 TurnCount = 0, SharpCorners = 0;
		for (int32 i = 1; i < PathPoints.Num() - 1; ++i)
		{
			FVector Dir1 = (PathPoints[i] - PathPoints[i - 1]).GetSafeNormal();
			FVector Dir2 = (PathPoints[i + 1] - PathPoints[i]).GetSafeNormal();
			float Dot = FVector::DotProduct(Dir1, Dir2);
			if (Dot < 0.707f) ++TurnCount;
			if (Dot < 0.0f) ++SharpCorners;
		}

		float TurnsPer10m = (PathDist > 0) ? (static_cast<float>(TurnCount) / (PathDist / 1000.0f)) : 0.0f;
		float CogScore = FMath::Clamp(TurnsPer10m * 10.0f + static_cast<float>(SharpCorners) * 8.0f, 0.0f, 100.0f);

		FString CogRating;
		if (CogScore < 15.0f)      CogRating = TEXT("simple");
		else if (CogScore < 35.0f) CogRating = TEXT("moderate");
		else if (CogScore < 60.0f) CogRating = TEXT("complex");
		else                       CogRating = TEXT("confusing");

		float CogThreshold = 30.0f; // Hospice default
		if (Profile == TEXT("cognitive_fatigue")) CogThreshold = 20.0f;

		if (CogScore > CogThreshold)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("category"), TEXT("cognitive_load"));
			Issue->SetStringField(TEXT("severity"), CogScore > 60.0f ? TEXT("critical") : TEXT("warning"));
			Issue->SetStringField(TEXT("description"), FString::Printf(
				TEXT("Navigation complexity %.0f exceeds hospice threshold %.0f (%s). Simplify path or add wayfinding."),
				CogScore, CogThreshold, *CogRating));
			AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
			if (CogScore > 60.0f) ++CriticalCount; else ++WarningCount;
		}

		auto CogObj = MakeShared<FJsonObject>();
		CogObj->SetNumberField(TEXT("complexity_score"), FMath::RoundToInt(CogScore));
		CogObj->SetStringField(TEXT("rating"), CogRating);
		CogObj->SetNumberField(TEXT("turn_count"), TurnCount);
		CogObj->SetNumberField(TEXT("sharp_corners"), SharpCorners);
		CogObj->SetBoolField(TEXT("passes"), CogScore <= CogThreshold);
		Report->SetObjectField(TEXT("cognitive_load"), CogObj);
	}

	// ============================================
	// Section 4: Input Demands / One-Handed Play
	// ============================================
	{
		// Check for QTE actors, precision-requiring interactables
		int32 QTECount = 0;
		int32 PrecisionCount = 0;
		int32 HighReachCount = 0;

		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Actor = *It;
			if (FVector::Dist(Actor->GetActorLocation(), (Start + End) * 0.5f) > PathDist) continue;

			for (const FName& Tag : Actor->Tags)
			{
				FString TagStr = Tag.ToString();
				if (TagStr.Contains(TEXT("QTE"), ESearchCase::IgnoreCase))
				{
					++QTECount;
				}
				if (TagStr.Contains(TEXT("Precision"), ESearchCase::IgnoreCase))
				{
					++PrecisionCount;
				}
			}

			// Check height (items above 180cm or below 60cm are hard to reach)
			float ActorZ = Actor->GetActorLocation().Z - Start.Z; // Relative height
			if (ActorZ > 180.0f || (ActorZ < 60.0f && ActorZ > -50.0f))
			{
				for (const FName& Tag : Actor->Tags)
				{
					if (Tag.ToString().Contains(TEXT("Interactable"), ESearchCase::IgnoreCase))
					{
						++HighReachCount;
						break;
					}
				}
			}
		}

		auto InputObj = MakeShared<FJsonObject>();
		InputObj->SetNumberField(TEXT("qte_count"), QTECount);
		InputObj->SetNumberField(TEXT("precision_interactions"), PrecisionCount);
		InputObj->SetNumberField(TEXT("difficult_reach_items"), HighReachCount);
		InputObj->SetBoolField(TEXT("one_handed_compatible"), QTECount == 0 && PrecisionCount == 0);

		if (QTECount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("category"), TEXT("input_demands"));
			Issue->SetStringField(TEXT("severity"), TEXT("critical"));
			Issue->SetStringField(TEXT("description"), FString::Printf(
				TEXT("Found %d QTE elements. QTEs are NOT allowed in hospice mode — patients may have limited motor function."),
				QTECount));
			AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
			++CriticalCount;
		}
		if (PrecisionCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("category"), TEXT("input_demands"));
			Issue->SetStringField(TEXT("severity"), TEXT("warning"));
			Issue->SetStringField(TEXT("description"), FString::Printf(
				TEXT("Found %d precision interactions. Consider generous aim assist or auto-complete for hospice."),
				PrecisionCount));
			AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
			++WarningCount;
		}

		Report->SetObjectField(TEXT("input_demands"), InputObj);
	}

	// ============================================
	// Section 5: Profile-Specific Analysis
	// ============================================
	{
		TArray<TSharedPtr<FJsonValue>> ProfileArr;
		for (const FString& P : Profiles)
		{
			auto PObj = MakeShared<FJsonObject>();
			PObj->SetStringField(TEXT("profile"), P);

			if (P == TEXT("motor_impaired"))
			{
				// Check path width (150cm for wheelchair + companion)
				TArray<MonolithMeshAnalysis::FPathClearance> Clearances = MonolithMeshAnalysis::MeasurePathClearance(World, PathPoints, 500.0f);
				float MinWidth = 1000.0f;
				int32 NarrowCount = 0;
				for (const auto& C : Clearances)
				{
					MinWidth = FMath::Min(MinWidth, C.TotalWidth);
					if (C.TotalWidth < 150.0f) ++NarrowCount;
				}

				PObj->SetNumberField(TEXT("min_path_width"), MinWidth);
				PObj->SetNumberField(TEXT("narrow_points"), NarrowCount);
				PObj->SetBoolField(TEXT("passes"), NarrowCount == 0);
				PObj->SetStringField(TEXT("note"), TEXT("Motor impairment: paths must be 150cm+ wide, no stairs-only routes, low reach requirements."));

				if (NarrowCount > 0)
				{
					auto Issue = MakeShared<FJsonObject>();
					Issue->SetStringField(TEXT("category"), TEXT("motor_impaired"));
					Issue->SetStringField(TEXT("severity"), TEXT("critical"));
					Issue->SetStringField(TEXT("description"), FString::Printf(
						TEXT("%d narrow points below 150cm. Wheelchair users need wider paths."), NarrowCount));
					AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
					++CriticalCount;
				}
			}
			else if (P == TEXT("vision_impaired"))
			{
				// Check contrast and lighting
				TArray<MonolithLightingCapture::FLightInfo> Lights = MonolithLightingCapture::GatherLights(World);

				int32 DarkSampleCount = 0;
				float SampleInterval = FMath::Clamp(PathDist / 30.0f, 200.0f, 1000.0f);
				TArray<FVector> LightSamples = ResamplePath(PathPoints, SampleInterval);

				for (const FVector& Pt : LightSamples)
				{
					int32 DummyIdx;
					float Lum = MonolithLightingCapture::ComputeAnalyticLuminance(World, Pt, Lights, DummyIdx);
					if (Lum < 0.5f) ++DarkSampleCount; // Very dark
				}

				float DarkPercent = LightSamples.Num() > 0
					? (static_cast<float>(DarkSampleCount) / static_cast<float>(LightSamples.Num())) * 100.0f
					: 0.0f;

				PObj->SetNumberField(TEXT("dark_sample_percent"), DarkPercent);
				PObj->SetNumberField(TEXT("dark_samples"), DarkSampleCount);
				PObj->SetNumberField(TEXT("total_samples"), LightSamples.Num());
				PObj->SetBoolField(TEXT("passes"), DarkPercent < 30.0f);
				PObj->SetStringField(TEXT("note"), TEXT("Vision impairment: high contrast required, audio cues for all visual scares, minimal dark stretches."));

				if (DarkPercent > 30.0f)
				{
					auto Issue = MakeShared<FJsonObject>();
					Issue->SetStringField(TEXT("category"), TEXT("vision_impaired"));
					Issue->SetStringField(TEXT("severity"), TEXT("warning"));
					Issue->SetStringField(TEXT("description"), FString::Printf(
						TEXT("%.0f%% of path is very dark. Vision-impaired players need audio cues and higher contrast."),
						DarkPercent));
					AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
					++WarningCount;
				}
			}
			else if (P == TEXT("cognitive_fatigue"))
			{
				// Simple navigation check (already in cognitive_load section above, cross-reference)
				PObj->SetStringField(TEXT("note"), TEXT("Cognitive fatigue: simple navigation (max 20 complexity), frequent rest (every 2 min), clear wayfinding cues, no multi-step puzzles."));

				// Check for puzzle actors
				int32 PuzzleCount = 0;
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					if (FVector::Dist((*It)->GetActorLocation(), (Start + End) * 0.5f) > PathDist) continue;
					for (const FName& Tag : (*It)->Tags)
					{
						if (Tag.ToString().Contains(TEXT("Puzzle"), ESearchCase::IgnoreCase))
						{
							++PuzzleCount;
							break;
						}
					}
				}

				PObj->SetNumberField(TEXT("puzzle_count"), PuzzleCount);
				PObj->SetBoolField(TEXT("passes"), PuzzleCount == 0);

				if (PuzzleCount > 0)
				{
					auto Issue = MakeShared<FJsonObject>();
					Issue->SetStringField(TEXT("category"), TEXT("cognitive_fatigue"));
					Issue->SetStringField(TEXT("severity"), TEXT("warning"));
					Issue->SetStringField(TEXT("description"), FString::Printf(
						TEXT("%d puzzle elements found. Consider optional hints or auto-solve for cognitive fatigue profile."),
						PuzzleCount));
					AllIssues.Add(MakeShared<FJsonValueObject>(Issue));
					++WarningCount;
				}
			}

			ProfileArr.Add(MakeShared<FJsonValueObject>(PObj));
		}
		Report->SetArrayField(TEXT("profile_assessments"), ProfileArr);
	}

	// ============================================
	// Overall Grade
	// ============================================
	FString Grade;
	if (CriticalCount == 0 && WarningCount == 0)
	{
		Grade = TEXT("A");
	}
	else if (CriticalCount == 0 && WarningCount <= 2)
	{
		Grade = TEXT("B");
	}
	else if (CriticalCount <= 1)
	{
		Grade = TEXT("C");
	}
	else if (CriticalCount <= 3)
	{
		Grade = TEXT("D");
	}
	else
	{
		Grade = TEXT("F");
	}

	// Sort issues by severity
	AllIssues.Sort([](const TSharedPtr<FJsonValue>& A, const TSharedPtr<FJsonValue>& B)
	{
		FString SA = A->AsObject()->GetStringField(TEXT("severity"));
		FString SB = B->AsObject()->GetStringField(TEXT("severity"));
		return SA < SB; // critical < warning alphabetically
	});

	// Recommendations
	TArray<TSharedPtr<FJsonValue>> RecsArr;
	if (CriticalCount > 0)
	{
		RecsArr.Add(MakeShared<FJsonValueString>(TEXT("Address all critical issues before shipping. These represent barriers for hospice patients.")));
	}
	if (WarningCount > 0)
	{
		RecsArr.Add(MakeShared<FJsonValueString>(TEXT("Review warnings — each represents a potential discomfort or accessibility barrier.")));
	}
	RecsArr.Add(MakeShared<FJsonValueString>(TEXT("Playtest with accessibility profiles enabled. Auto-collect data on death locations, rest frequency, and session length.")));
	RecsArr.Add(MakeShared<FJsonValueString>(TEXT("Ensure all visual scares have corresponding audio cues for vision-impaired players.")));
	RecsArr.Add(MakeShared<FJsonValueString>(TEXT("Test one-handed controller layout — all critical actions must be reachable single-handed.")));

	Report->SetStringField(TEXT("overall_grade"), Grade);
	Report->SetArrayField(TEXT("issues"), AllIssues);
	Report->SetNumberField(TEXT("critical_issues"), CriticalCount);
	Report->SetNumberField(TEXT("warning_issues"), WarningCount);
	Report->SetNumberField(TEXT("total_issues"), CriticalCount + WarningCount);
	Report->SetArrayField(TEXT("recommendations"), RecsArr);
	Report->SetNumberField(TEXT("path_length_cm"), PathDist);
	Report->SetNumberField(TEXT("estimated_time_minutes"), EstimatedTimeMinutes);
	Report->SetStringField(TEXT("walk_speed_cms"), FString::Printf(TEXT("%.0f"), WalkSpeed));
	Report->SetStringField(TEXT("profile_requested"), Profile.IsEmpty() ? TEXT("all") : Profile);

	return FMonolithActionResult::Success(Report);
}
