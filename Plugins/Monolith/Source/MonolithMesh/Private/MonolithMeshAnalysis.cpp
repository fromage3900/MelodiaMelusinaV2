#include "MonolithMeshAnalysis.h"
#include "MonolithMeshUtils.h"

#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "AI/Navigation/NavigationTypes.h"
#include "Dom/JsonValue.h"

// ============================================================================
// JSON Helper
// ============================================================================

TArray<TSharedPtr<FJsonValue>> MonolithMeshAnalysis::VectorToJsonArray(const FVector& V)
{
	TArray<TSharedPtr<FJsonValue>> Arr;
	Arr.Add(MakeShared<FJsonValueNumber>(V.X));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
	Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
	return Arr;
}

// ============================================================================
// Concealment
// ============================================================================

float MonolithMeshAnalysis::ComputeConcealment(UWorld* World, const FVector& TestPoint, const TArray<FVector>& Viewpoints)
{
	if (!World || Viewpoints.Num() == 0)
	{
		return 0.0f;
	}

	// Fire multiple rays from test point toward each viewpoint at slightly varied offsets
	// to get a volumetric concealment score (not just center-to-center)
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithConcealment), true);

	int32 TotalRays = 0;
	int32 BlockedRays = 0;

	// Offsets around the test point to simulate a character-sized volume
	static const FVector Offsets[] = {
		FVector(0, 0, 0),
		FVector(0, 0, 90),   // Head height
		FVector(30, 0, 45),
		FVector(-30, 0, 45),
		FVector(0, 30, 45),
	};

	for (const FVector& Viewpoint : Viewpoints)
	{
		for (const FVector& Offset : Offsets)
		{
			FVector From = TestPoint + Offset;
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, From, Viewpoint, ECC_Visibility, QueryParams);
			++TotalRays;
			if (bHit)
			{
				++BlockedRays;
			}
		}
	}

	return (TotalRays > 0) ? static_cast<float>(BlockedRays) / static_cast<float>(TotalRays) : 0.0f;
}

// ============================================================================
// Path Clearance
// ============================================================================

TArray<MonolithMeshAnalysis::FPathClearance> MonolithMeshAnalysis::MeasurePathClearance(
	UWorld* World, const TArray<FVector>& PathPoints, float MaxWidth)
{
	TArray<FPathClearance> Results;
	if (!World || PathPoints.Num() < 2)
	{
		return Results;
	}

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithClearance), true);
	QueryParams.bReturnPhysicalMaterial = false;

	for (int32 i = 0; i < PathPoints.Num(); ++i)
	{
		const FVector& Pt = PathPoints[i];

		// Compute path direction at this point
		FVector Forward;
		if (i < PathPoints.Num() - 1)
		{
			Forward = (PathPoints[i + 1] - Pt).GetSafeNormal();
		}
		else
		{
			Forward = (Pt - PathPoints[i - 1]).GetSafeNormal();
		}

		// Perpendicular (horizontal only)
		FVector Right = FVector::CrossProduct(Forward, FVector::UpVector).GetSafeNormal();
		if (Right.IsNearlyZero())
		{
			Right = FVector::RightVector;
		}

		// Raise slightly off floor to avoid ground hits
		FVector TestPt = Pt + FVector(0, 0, 50.0f);

		FPathClearance Clearance;
		Clearance.Location = Pt;

		// Right clearance
		{
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, TestPt, TestPt + Right * MaxWidth, ECC_Visibility, QueryParams);
			Clearance.RightClearance = bHit ? Hit.Distance : MaxWidth;
			Clearance.RightObstruction = (bHit && Hit.GetActor()) ? Hit.GetActor()->GetActorNameOrLabel() : TEXT("");
		}

		// Left clearance
		{
			FHitResult Hit;
			bool bHit = World->LineTraceSingleByChannel(Hit, TestPt, TestPt - Right * MaxWidth, ECC_Visibility, QueryParams);
			Clearance.LeftClearance = bHit ? Hit.Distance : MaxWidth;
			Clearance.LeftObstruction = (bHit && Hit.GetActor()) ? Hit.GetActor()->GetActorNameOrLabel() : TEXT("");
		}

		Clearance.TotalWidth = Clearance.LeftClearance + Clearance.RightClearance;
		Results.Add(MoveTemp(Clearance));
	}

	return Results;
}

// ============================================================================
// Tension Scoring
// ============================================================================

const TCHAR* MonolithMeshAnalysis::TensionLevelToString(ETensionLevel Level)
{
	switch (Level)
	{
	case ETensionLevel::Calm:   return TEXT("calm");
	case ETensionLevel::Uneasy: return TEXT("uneasy");
	case ETensionLevel::Tense:  return TEXT("tense");
	case ETensionLevel::Dread:  return TEXT("dread");
	case ETensionLevel::Panic:  return TEXT("panic");
	default:                    return TEXT("unknown");
	}
}

float MonolithMeshAnalysis::ComputeTensionScore(const FTensionInputs& Inputs)
{
	// Each factor contributes 0-25 points, total 0-100

	// Sightline factor: shorter average = higher tension
	// 0cm -> 25, 500cm -> 20, 2000cm -> 10, 5000cm+ -> 0
	float SightlineFactor = FMath::Clamp(1.0f - (Inputs.AverageSightlineDistance / 5000.0f), 0.0f, 1.0f) * 25.0f;

	// Ceiling factor: lower ceiling = higher tension
	// 150cm -> 25, 250cm -> 15, 500cm+ -> 0, 0 (no ceiling) -> 5 (outdoor = slightly uneasy in horror)
	float CeilingFactor;
	if (Inputs.CeilingHeight <= 0.0f)
	{
		CeilingFactor = 5.0f; // Open sky — slightly uneasy in a horror game
	}
	else
	{
		CeilingFactor = FMath::Clamp(1.0f - ((Inputs.CeilingHeight - 150.0f) / 350.0f), 0.0f, 1.0f) * 25.0f;
	}

	// Volume factor: smaller room = higher tension
	// Volume in cubic cm. A 3m x 3m x 3m room = 27,000,000 cm3
	// Tiny closet (1.5m^3 = ~3.4M cm3) -> 25, medium room (~27M) -> 12, large (>100M) -> 0
	float VolumeM3 = Inputs.RoomVolume / 1000000.0f; // Convert to m^3
	float VolumeFactor = FMath::Clamp(1.0f - (VolumeM3 / 100.0f), 0.0f, 1.0f) * 25.0f;

	// Exit factor: fewer exits = higher tension
	// 0 exits -> 25, 1 -> 20, 2 -> 12, 3+ -> 5, 5+ -> 0
	float ExitFactor;
	if (Inputs.ExitCount <= 0)
	{
		ExitFactor = 25.0f;
	}
	else if (Inputs.ExitCount == 1)
	{
		ExitFactor = 20.0f;
	}
	else
	{
		ExitFactor = FMath::Clamp(25.0f - (static_cast<float>(Inputs.ExitCount) * 5.0f), 0.0f, 25.0f);
	}

	return FMath::Clamp(SightlineFactor + CeilingFactor + VolumeFactor + ExitFactor, 0.0f, 100.0f);
}

MonolithMeshAnalysis::ETensionLevel MonolithMeshAnalysis::ClassifyTension(float Score)
{
	if (Score < 20.0f) return ETensionLevel::Calm;
	if (Score < 40.0f) return ETensionLevel::Uneasy;
	if (Score < 60.0f) return ETensionLevel::Tense;
	if (Score < 80.0f) return ETensionLevel::Dread;
	return ETensionLevel::Panic;
}

// ============================================================================
// Spatial Measurements
// ============================================================================

float MonolithMeshAnalysis::MeasureCeilingHeight(UWorld* World, const FVector& Location, float MaxHeight)
{
	if (!World)
	{
		return 0.0f;
	}

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithCeiling), true);
	FHitResult Hit;
	FVector Start = Location + FVector(0, 0, 10.0f); // Slightly above to avoid floor hit
	FVector End = Location + FVector(0, 0, MaxHeight);

	bool bHit = World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, QueryParams);
	return bHit ? Hit.Distance : 0.0f; // 0 = no ceiling (open sky)
}

float MonolithMeshAnalysis::ApproximateRoomVolume(UWorld* World, const FVector& Location, float MaxRadius, int32 RayCount)
{
	if (!World || RayCount < 4)
	{
		return 0.0f;
	}

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithVolume), true);

	// Fire horizontal rays to estimate floor area, then multiply by ceiling height
	TArray<float> WallDistances;
	WallDistances.Reserve(RayCount);

	for (int32 i = 0; i < RayCount; ++i)
	{
		float AngleRad = (2.0f * PI / static_cast<float>(RayCount)) * static_cast<float>(i);
		FVector Dir(FMath::Cos(AngleRad), FMath::Sin(AngleRad), 0.0f);

		FHitResult Hit;
		bool bHit = World->LineTraceSingleByChannel(Hit, Location, Location + Dir * MaxRadius, ECC_Visibility, QueryParams);
		WallDistances.Add(bHit ? Hit.Distance : MaxRadius);
	}

	// Approximate area using triangulation (sum of triangles formed by consecutive rays)
	float Area = 0.0f;
	for (int32 i = 0; i < RayCount; ++i)
	{
		int32 Next = (i + 1) % RayCount;
		float AngleDiff = (2.0f * PI) / static_cast<float>(RayCount);
		// Triangle area = 0.5 * a * b * sin(theta)
		Area += 0.5f * WallDistances[i] * WallDistances[Next] * FMath::Sin(AngleDiff);
	}

	float CeilingH = MeasureCeilingHeight(World, Location);
	if (CeilingH <= 0.0f)
	{
		CeilingH = 300.0f; // Assume 3m default if open sky
	}

	return Area * CeilingH;
}

int32 MonolithMeshAnalysis::CountExits(UWorld* World, const FVector& Location, float TestRadius, int32 Directions)
{
	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString Error;

	if (!GetNavSystem(World, NavSys, NavData, Error))
	{
		return 0;
	}

	int32 ExitCount = 0;
	FNavAgentProperties AgentProps;
	AgentProps.AgentRadius = 42.0f;
	AgentProps.AgentHeight = 192.0f;

	for (int32 i = 0; i < Directions; ++i)
	{
		float AngleRad = (2.0f * PI / static_cast<float>(Directions)) * static_cast<float>(i);
		FVector TestPt = Location + FVector(FMath::Cos(AngleRad), FMath::Sin(AngleRad), 0.0f) * TestRadius;

		FPathFindingQuery Query(nullptr, *NavData, Location, TestPt);
		Query.SetAllowPartialPaths(false);
		FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);

		if (PathResult.IsSuccessful() && PathResult.Path.IsValid() && !PathResult.Path->IsPartial())
		{
			++ExitCount;
		}
	}

	return ExitCount;
}

// ============================================================================
// Navmesh Flood Fill
// ============================================================================

TArray<MonolithMeshAnalysis::FDeadEnd> MonolithMeshAnalysis::FloodFillDeadEnds(UWorld* World, const FBox& Region, float GridSize)
{
	TArray<FDeadEnd> Results;

	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString Error;

	if (!GetNavSystem(World, NavSys, NavData, Error))
	{
		return Results;
	}

	// Build a grid of navmesh-valid points within the region
	struct FGridNode
	{
		FVector Location;
		int32 Index;
		TArray<int32> Neighbors;
	};

	TArray<FGridNode> Nodes;
	TMap<FIntVector, int32> GridMap; // Grid coord -> node index

	FVector RegionSize = Region.Max - Region.Min;
	int32 XCount = FMath::Max(1, FMath::CeilToInt(RegionSize.X / GridSize));
	int32 YCount = FMath::Max(1, FMath::CeilToInt(RegionSize.Y / GridSize));

	// Cap grid size to prevent runaway
	const int32 MaxNodes = 2500;
	if (XCount * YCount > MaxNodes)
	{
		float Scale = FMath::Sqrt(static_cast<float>(MaxNodes) / static_cast<float>(XCount * YCount));
		XCount = FMath::Max(1, FMath::FloorToInt(XCount * Scale));
		YCount = FMath::Max(1, FMath::FloorToInt(YCount * Scale));
	}

	// Sample grid points on navmesh
	for (int32 X = 0; X < XCount; ++X)
	{
		for (int32 Y = 0; Y < YCount; ++Y)
		{
			FVector TestPt = Region.Min + FVector(
				(static_cast<float>(X) + 0.5f) * GridSize,
				(static_cast<float>(Y) + 0.5f) * GridSize,
				RegionSize.Z * 0.5f);

			FNavLocation NavLoc;
			if (NavSys->ProjectPointToNavigation(TestPt, NavLoc, FVector(GridSize * 0.5f, GridSize * 0.5f, 500.0f)))
			{
				int32 Idx = Nodes.Num();
				FGridNode Node;
				Node.Location = NavLoc.Location;
				Node.Index = Idx;
				Nodes.Add(Node);
				GridMap.Add(FIntVector(X, Y, 0), Idx);
			}
		}
	}

	if (Nodes.Num() < 3)
	{
		return Results;
	}

	// Build adjacency (4-connected neighbors that are also on navmesh)
	FNavAgentProperties AgentProps;
	AgentProps.AgentRadius = 42.0f;
	AgentProps.AgentHeight = 192.0f;

	static const FIntVector Offsets4[] = {
		FIntVector(1, 0, 0), FIntVector(-1, 0, 0),
		FIntVector(0, 1, 0), FIntVector(0, -1, 0)
	};

	for (int32 X = 0; X < XCount; ++X)
	{
		for (int32 Y = 0; Y < YCount; ++Y)
		{
			int32* IdxPtr = GridMap.Find(FIntVector(X, Y, 0));
			if (!IdxPtr) continue;

			for (const FIntVector& Off : Offsets4)
			{
				int32* NeighborPtr = GridMap.Find(FIntVector(X + Off.X, Y + Off.Y, 0));
				if (NeighborPtr)
				{
					// Verify navmesh connectivity
					FPathFindingQuery Query(nullptr, *NavData, Nodes[*IdxPtr].Location, Nodes[*NeighborPtr].Location);
					Query.SetAllowPartialPaths(false);
					FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);

					if (PathResult.IsSuccessful() && PathResult.Path.IsValid() && !PathResult.Path->IsPartial())
					{
						Nodes[*IdxPtr].Neighbors.Add(*NeighborPtr);
					}
				}
			}
		}
	}

	// Find dead-end clusters: nodes with only 1 neighbor (leaf nodes)
	// Then trace back to find connected dead-end chains
	TSet<int32> Visited;

	for (int32 i = 0; i < Nodes.Num(); ++i)
	{
		if (Nodes[i].Neighbors.Num() != 1 || Visited.Contains(i))
		{
			continue;
		}

		// Walk from leaf back until we hit a junction (>2 neighbors)
		TArray<int32> Chain;
		int32 Current = i;

		while (Current >= 0 && !Visited.Contains(Current))
		{
			Visited.Add(Current);
			Chain.Add(Current);

			if (Nodes[Current].Neighbors.Num() > 2)
			{
				break; // Hit a junction
			}

			// Find unvisited neighbor
			int32 Next = -1;
			for (int32 N : Nodes[Current].Neighbors)
			{
				if (!Visited.Contains(N))
				{
					Next = N;
					break;
				}
			}
			Current = Next;
		}

		if (Chain.Num() >= 2)
		{
			FDeadEnd DE;

			// Center = average of chain points
			FVector Sum = FVector::ZeroVector;
			for (int32 Idx : Chain)
			{
				Sum += Nodes[Idx].Location;
			}
			DE.Center = Sum / static_cast<float>(Chain.Num());

			// Exit direction = from deepest point toward the exit
			DE.ExitDirection = (Nodes[Chain.Last()].Location - Nodes[Chain[0]].Location).GetSafeNormal();

			// Depth = distance from leaf to junction
			DE.Depth = 0.0f;
			for (int32 j = 1; j < Chain.Num(); ++j)
			{
				DE.Depth += FVector::Dist(Nodes[Chain[j - 1]].Location, Nodes[Chain[j]].Location);
			}

			// Width = average clearance along the chain
			TArray<FVector> ChainPoints;
			for (int32 Idx : Chain)
			{
				ChainPoints.Add(Nodes[Idx].Location);
			}
			TArray<FPathClearance> Clearances = MeasurePathClearance(World, ChainPoints, 500.0f);

			float TotalW = 0.0f;
			float MinW = TNumericLimits<float>::Max();
			for (const FPathClearance& C : Clearances)
			{
				TotalW += C.TotalWidth;
				MinW = FMath::Min(MinW, C.TotalWidth);
			}
			DE.Width = Clearances.Num() > 0 ? TotalW / Clearances.Num() : 0.0f;
			DE.ExitWidth = (MinW < TNumericLimits<float>::Max()) ? MinW : 0.0f;

			for (int32 Idx : Chain)
			{
				DE.BoundaryPoints.Add(Nodes[Idx].Location);
			}

			Results.Add(MoveTemp(DE));
		}
	}

	return Results;
}

// ============================================================================
// Navigation Helpers
// ============================================================================

bool MonolithMeshAnalysis::GetNavSystem(UWorld* World, UNavigationSystemV1*& OutNavSys, ANavigationData*& OutNavData, FString& OutError)
{
	if (!World)
	{
		OutError = TEXT("No editor world available");
		return false;
	}

	OutNavSys = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!OutNavSys)
	{
		OutError = TEXT("Navigation system not available. Build navigation first (Build > Build Paths).");
		return false;
	}

	OutNavData = OutNavSys->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
	if (!OutNavData)
	{
		OutError = TEXT("Navmesh not built. Build navigation in the editor first (Build > Build Paths).");
		return false;
	}

	return true;
}

bool MonolithMeshAnalysis::FindNavPath(UWorld* World, const FVector& Start, const FVector& End,
	TArray<FVector>& OutPoints, float& OutDistance, float AgentRadius)
{
	UNavigationSystemV1* NavSys = nullptr;
	ANavigationData* NavData = nullptr;
	FString Error;

	if (!GetNavSystem(World, NavSys, NavData, Error))
	{
		return false;
	}

	FNavAgentProperties AgentProps;
	AgentProps.AgentRadius = AgentRadius;
	AgentProps.AgentHeight = 192.0f;

	FPathFindingQuery Query(nullptr, *NavData, Start, End);
	Query.SetAllowPartialPaths(true);
	FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);

	if (!PathResult.IsSuccessful() || !PathResult.Path.IsValid())
	{
		return false;
	}

	OutPoints.Empty();
	OutDistance = 0.0;
	const TArray<FNavPathPoint>& PathPts = PathResult.Path->GetPathPoints();

	for (int32 i = 0; i < PathPts.Num(); ++i)
	{
		OutPoints.Add(PathPts[i].Location);
		if (i > 0)
		{
			OutDistance += FVector::Dist(PathPts[i - 1].Location, PathPts[i].Location);
		}
	}

	return true;
}
