#include "MonolithMeshBuildingValidationActions.h"
#include "MonolithMeshSpatialRegistry.h"
#include "MonolithMeshBuildingTypes.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "Engine/World.h"
#include "CollisionShape.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshBuildingValidationActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("mesh"), TEXT("validate_building"),
		TEXT("Post-generation validation of a procedural building. Checks door passability (capsule sweeps), "
			"room connectivity (BFS from entrance), window openings (raycasts), and stair angles. "
			"Returns a per-check breakdown with an overall playability score."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshBuildingValidationActions::ValidateBuilding),
		FParamSchemaBuilder()
			.Required(TEXT("building_id"), TEXT("string"), TEXT("Building ID in the spatial registry"))
			.Optional(TEXT("block_id"), TEXT("string"), TEXT("Block ID in the spatial registry"), TEXT("default"))
			.Optional(TEXT("capsule_radius"), TEXT("number"), TEXT("Player capsule radius in cm"), TEXT("42"))
			.Optional(TEXT("capsule_half_height"), TEXT("number"), TEXT("Player capsule half-height in cm"), TEXT("96"))
			.Optional(TEXT("min_door_width"), TEXT("number"), TEXT("Minimum passable door width in cm"), TEXT("100"))
			.Optional(TEXT("check_doors"), TEXT("boolean"), TEXT("Validate door passability with capsule sweeps"), TEXT("true"))
			.Optional(TEXT("check_connectivity"), TEXT("boolean"), TEXT("Validate all rooms reachable from entrance via BFS"), TEXT("true"))
			.Optional(TEXT("check_windows"), TEXT("boolean"), TEXT("Validate window openings with raycasts"), TEXT("true"))
			.Optional(TEXT("check_stairs"), TEXT("boolean"), TEXT("Validate stair angles against max walkable"), TEXT("true"))
			.Optional(TEXT("max_stair_angle"), TEXT("number"), TEXT("Maximum walkable stair angle in degrees"), TEXT("44.76"))
			.Build());
}

// ============================================================================
// Helpers
// ============================================================================

namespace BuildingValidationHelpers
{
	/** Make a JSON array from a FVector */
	TArray<TSharedPtr<FJsonValue>> VecToJsonArray(const FVector& V)
	{
		TArray<TSharedPtr<FJsonValue>> Arr;
		Arr.Add(MakeShared<FJsonValueNumber>(V.X));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
		return Arr;
	}

	/** Parse a boolean param with default */
	bool GetBoolParam(const TSharedPtr<FJsonObject>& Params, const FString& Key, bool Default)
	{
		if (Params->HasField(Key))
		{
			// Handle both bool and string "true"/"false"
			const TSharedPtr<FJsonValue>& Val = Params->Values.FindChecked(MonolithMakeJsonKey(Key));
			if (Val->Type == EJson::Boolean)
			{
				return Val->AsBool();
			}
			FString Str = Val->AsString();
			return Str.Equals(TEXT("true"), ESearchCase::IgnoreCase);
		}
		return Default;
	}

	/** Parse a number param with default */
	double GetNumberParam(const TSharedPtr<FJsonObject>& Params, const FString& Key, double Default)
	{
		if (Params->HasField(Key))
		{
			return Params->GetNumberField(Key);
		}
		return Default;
	}

	/** Get wall normal direction from string */
	FVector WallNormal(const FString& Wall)
	{
		if (Wall == TEXT("north")) return FVector(0, -1, 0);
		if (Wall == TEXT("south")) return FVector(0, 1, 0);
		if (Wall == TEXT("east"))  return FVector(1, 0, 0);
		if (Wall == TEXT("west"))  return FVector(-1, 0, 0);
		return FVector::ZeroVector;
	}
}

TSet<FString> FMonolithMeshBuildingValidationActions::BFSReachable(
	const FSpatialBlock& Block,
	const FString& StartRoomId)
{
	TSet<FString> Visited;
	TQueue<FString> Queue;

	Queue.Enqueue(StartRoomId);
	Visited.Add(StartRoomId);

	FString Current;
	while (Queue.Dequeue(Current))
	{
		if (const TArray<FSpatialAdjacencyEdge>* Edges = Block.AdjacencyGraph.Find(Current))
		{
			for (const FSpatialAdjacencyEdge& Edge : *Edges)
			{
				if (!Visited.Contains(Edge.ConnectedRoomId))
				{
					Visited.Add(Edge.ConnectedRoomId);
					Queue.Enqueue(Edge.ConnectedRoomId);
				}
			}
		}
	}

	return Visited;
}

FString FMonolithMeshBuildingValidationActions::FindEntranceRoom(
	const FSpatialBlock& Block,
	const FString& BuildingId)
{
	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building) return FString();

	// Look for exterior doors — the room connected to an exterior door is the entrance
	for (const FString& DoorId : Building->ExteriorDoorIds)
	{
		if (const FSpatialDoor* Door = Block.Doors.Find(DoorId))
		{
			// Exterior doors connect a room (RoomA) to exterior (RoomB may be empty or "exterior")
			if (!Door->RoomA.IsEmpty() && Block.Rooms.Contains(Door->RoomA))
			{
				return Door->RoomA;
			}
			if (!Door->RoomB.IsEmpty() && Block.Rooms.Contains(Door->RoomB))
			{
				return Door->RoomB;
			}
		}
	}

	// Fallback: first room on floor 0
	if (const TArray<FString>* Floor0Rooms = Building->FloorToRoomIds.Find(0))
	{
		if (Floor0Rooms->Num() > 0)
		{
			return (*Floor0Rooms)[0];
		}
	}

	return FString();
}

TArray<FString> FMonolithMeshBuildingValidationActions::GetBuildingRoomIds(
	const FSpatialBlock& Block,
	const FString& BuildingId)
{
	TArray<FString> RoomIds;
	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building) return RoomIds;

	for (const auto& FloorPair : Building->FloorToRoomIds)
	{
		RoomIds.Append(FloorPair.Value);
	}
	return RoomIds;
}

// ============================================================================
// Door Validation (Tier 1 — Capsule Sweeps)
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshBuildingValidationActions::ValidateDoors(
	const FSpatialBlock& Block,
	const FString& BuildingId,
	float CapsuleRadius,
	float CapsuleHalfHeight,
	float MinDoorWidth,
	UWorld* World)
{
	auto Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> FailedArr;
	TArray<TSharedPtr<FJsonValue>> WarningArr;

	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building)
	{
		Result->SetNumberField(TEXT("total"), 0);
		Result->SetNumberField(TEXT("passable"), 0);
		Result->SetArrayField(TEXT("failed"), FailedArr);
		Result->SetArrayField(TEXT("warnings"), WarningArr);
		return Result;
	}

	// Collect all doors belonging to this building
	TArray<const FSpatialDoor*> BuildingDoors;
	for (const auto& DoorPair : Block.Doors)
	{
		const FSpatialDoor& Door = DoorPair.Value;
		// Door belongs to building if either room belongs to the building
		bool bBelongs = false;
		if (const FSpatialRoom* RoomA = Block.Rooms.Find(Door.RoomA))
		{
			if (RoomA->BuildingId == BuildingId) bBelongs = true;
		}
		if (!bBelongs)
		{
			if (const FSpatialRoom* RoomB = Block.Rooms.Find(Door.RoomB))
			{
				if (RoomB->BuildingId == BuildingId) bBelongs = true;
			}
		}
		if (bBelongs)
		{
			BuildingDoors.Add(&Door);
		}
	}

	int32 Total = BuildingDoors.Num();
	int32 Passable = 0;

	for (const FSpatialDoor* Door : BuildingDoors)
	{
		bool bDoorOk = true;

		// Check 1: Width >= minimum
		if (Door->Width < MinDoorWidth)
		{
			auto FailObj = MakeShared<FJsonObject>();
			FailObj->SetStringField(TEXT("door_id"), Door->DoorId);
			FailObj->SetStringField(TEXT("reason"), FString::Printf(
				TEXT("Door width %.1f cm < minimum %.1f cm"), Door->Width, MinDoorWidth));
			FailObj->SetNumberField(TEXT("width"), Door->Width);
			FailedArr.Add(MakeShared<FJsonValueObject>(FailObj));
			bDoorOk = false;
		}

		// Check 2: Height >= capsule full height
		float RequiredHeight = CapsuleHalfHeight * 2.0f;
		if (Door->Height < RequiredHeight)
		{
			auto FailObj = MakeShared<FJsonObject>();
			FailObj->SetStringField(TEXT("door_id"), Door->DoorId);
			FailObj->SetStringField(TEXT("reason"), FString::Printf(
				TEXT("Door height %.1f cm < required %.1f cm (capsule_half_height * 2)"),
				Door->Height, RequiredHeight));
			FailObj->SetNumberField(TEXT("height"), Door->Height);
			FailedArr.Add(MakeShared<FJsonValueObject>(FailObj));
			bDoorOk = false;
		}

		// Check 3: Capsule sweep through door opening (if world available)
		if (bDoorOk && World)
		{
			// Compute sweep direction from wall normal
			FVector DoorPos = Door->WorldPosition;
			FVector SweepDir = BuildingValidationHelpers::WallNormal(Door->Wall);

			// If wall normal is zero (unknown wall), skip sweep
			if (!SweepDir.IsNearlyZero())
			{
				// Sweep from 50cm inside room A, through door, to 50cm inside room B
				// "Inside" room A = opposite of wall normal; "Inside" room B = along wall normal
				float SweepOffset = 50.0f;
				// Capsule center is at CapsuleHalfHeight above floor
				FVector CapsuleCenter = DoorPos + FVector(0, 0, CapsuleHalfHeight);
				FVector Start = CapsuleCenter - SweepDir * SweepOffset;
				FVector End = CapsuleCenter + SweepDir * SweepOffset;

				FCollisionShape CapsuleShape = FCollisionShape::MakeCapsule(CapsuleRadius, CapsuleHalfHeight);
				FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ValidateBuildingDoor), false);

				FHitResult Hit;
				bool bHit = World->SweepSingleByChannel(
					Hit, Start, End,
					FQuat::Identity,
					ECC_WorldStatic,
					CapsuleShape,
					QueryParams);

				if (bHit && !Hit.bStartPenetrating)
				{
					auto FailObj = MakeShared<FJsonObject>();
					FailObj->SetStringField(TEXT("door_id"), Door->DoorId);
					FailObj->SetStringField(TEXT("reason"), FString::Printf(
						TEXT("Capsule sweep blocked at (%.0f, %.0f, %.0f) — door opening may be obstructed"),
						Hit.ImpactPoint.X, Hit.ImpactPoint.Y, Hit.ImpactPoint.Z));
					FailObj->SetArrayField(TEXT("impact_point"),
						BuildingValidationHelpers::VecToJsonArray(Hit.ImpactPoint));
					if (Hit.GetActor())
					{
						FailObj->SetStringField(TEXT("blocking_actor"), Hit.GetActor()->GetName());
					}
					FailedArr.Add(MakeShared<FJsonValueObject>(FailObj));
					bDoorOk = false;
				}
				else if (bHit && Hit.bStartPenetrating)
				{
					auto WarnObj = MakeShared<FJsonObject>();
					WarnObj->SetStringField(TEXT("door_id"), Door->DoorId);
					WarnObj->SetStringField(TEXT("reason"),
						TEXT("Capsule starts inside geometry at door position — potential overlap issue"));
					WarningArr.Add(MakeShared<FJsonValueObject>(WarnObj));
					// Count as warning, not hard fail — geometry might just be tight
				}
			}
		}

		if (bDoorOk)
		{
			Passable++;
		}
	}

	Result->SetNumberField(TEXT("total"), Total);
	Result->SetNumberField(TEXT("passable"), Passable);
	Result->SetArrayField(TEXT("failed"), FailedArr);
	Result->SetArrayField(TEXT("warnings"), WarningArr);
	return Result;
}

// ============================================================================
// Connectivity Validation (Tier 2 — BFS)
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshBuildingValidationActions::ValidateConnectivity(
	const FSpatialBlock& Block,
	const FString& BuildingId)
{
	auto Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> UnreachableArr;

	TArray<FString> AllRoomIds = GetBuildingRoomIds(Block, BuildingId);
	int32 TotalRooms = AllRoomIds.Num();

	FString EntranceRoom = FindEntranceRoom(Block, BuildingId);
	bool bHasEntrance = !EntranceRoom.IsEmpty();

	int32 Reachable = 0;

	if (bHasEntrance)
	{
		TSet<FString> ReachableSet = BFSReachable(Block, EntranceRoom);

		// Only count rooms that belong to this building
		TSet<FString> BuildingRoomSet(AllRoomIds);
		for (const FString& RoomId : AllRoomIds)
		{
			if (ReachableSet.Contains(RoomId))
			{
				Reachable++;
			}
			else
			{
				UnreachableArr.Add(MakeShared<FJsonValueString>(RoomId));
			}
		}
	}
	else
	{
		// No entrance — all rooms are "unreachable" from outside
		for (const FString& RoomId : AllRoomIds)
		{
			UnreachableArr.Add(MakeShared<FJsonValueString>(RoomId));
		}
	}

	Result->SetNumberField(TEXT("total_rooms"), TotalRooms);
	Result->SetNumberField(TEXT("reachable"), Reachable);
	Result->SetArrayField(TEXT("unreachable"), UnreachableArr);
	Result->SetStringField(TEXT("entrance_room"), EntranceRoom);
	Result->SetBoolField(TEXT("has_entrance"), bHasEntrance);
	return Result;
}

// ============================================================================
// Window Validation (Tier 1 — Raycasts)
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshBuildingValidationActions::ValidateWindows(
	const FSpatialBlock& Block,
	const FString& BuildingId,
	UWorld* World)
{
	auto Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> BlockedArr;

	// Windows are stored as doors with bExterior=true that aren't in ExteriorDoorIds,
	// or we can identify them by looking for doors between a room and "exterior"/"window" type.
	// The spatial registry stores all openings as FSpatialDoor with bExterior flag.
	// We'll check doors that look like windows: exterior, and not in the building's ExteriorDoorIds
	// (which are actual walk-through doors).

	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building || !World)
	{
		Result->SetNumberField(TEXT("total"), 0);
		Result->SetNumberField(TEXT("open"), 0);
		Result->SetArrayField(TEXT("blocked"), BlockedArr);
		return Result;
	}

	// Collect exterior doors that are NOT walk-through entrances (likely windows)
	TSet<FString> ExteriorDoorSet(Building->ExteriorDoorIds);
	TArray<const FSpatialDoor*> WindowDoors;

	for (const auto& DoorPair : Block.Doors)
	{
		const FSpatialDoor& Door = DoorPair.Value;
		if (!Door.bExterior) continue;
		if (ExteriorDoorSet.Contains(Door.DoorId)) continue; // Actual entrance door, skip

		// Check if this door belongs to the building
		bool bBelongs = false;
		if (const FSpatialRoom* RoomA = Block.Rooms.Find(Door.RoomA))
		{
			if (RoomA->BuildingId == BuildingId) bBelongs = true;
		}
		if (!bBelongs && !Door.RoomB.IsEmpty())
		{
			if (const FSpatialRoom* RoomB = Block.Rooms.Find(Door.RoomB))
			{
				if (RoomB->BuildingId == BuildingId) bBelongs = true;
			}
		}
		if (bBelongs)
		{
			WindowDoors.Add(&Door);
		}
	}

	int32 Total = WindowDoors.Num();
	int32 Open = 0;

	for (const FSpatialDoor* Window : WindowDoors)
	{
		FVector WindowPos = Window->WorldPosition;
		FVector Normal = BuildingValidationHelpers::WallNormal(Window->Wall);

		if (Normal.IsNearlyZero())
		{
			// Can't validate without known wall direction
			Open++;
			continue;
		}

		// Cast ray from outside (100cm out from wall) through the window position
		// to inside (100cm inside). If it hits, the opening is blocked.
		float WindowCenterZ = WindowPos.Z + Window->Height * 0.5f;
		FVector RayCenter = FVector(WindowPos.X, WindowPos.Y, WindowCenterZ);
		FVector Start = RayCenter + Normal * 100.0f;   // Outside
		FVector End = RayCenter - Normal * 100.0f;      // Inside

		FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ValidateBuildingWindow), false);

		FHitResult Hit;
		bool bHit = World->LineTraceSingleByChannel(
			Hit, Start, End,
			ECC_WorldStatic,
			QueryParams);

		if (bHit)
		{
			// Ray hit something — window is blocked
			BlockedArr.Add(MakeShared<FJsonValueString>(Window->DoorId));
		}
		else
		{
			Open++;
		}
	}

	Result->SetNumberField(TEXT("total"), Total);
	Result->SetNumberField(TEXT("open"), Open);
	Result->SetArrayField(TEXT("blocked"), BlockedArr);
	return Result;
}

// ============================================================================
// Stair Validation (Tier 2 — Angle Check)
// ============================================================================

TSharedPtr<FJsonObject> FMonolithMeshBuildingValidationActions::ValidateStairs(
	const FSpatialBlock& Block,
	const FString& BuildingId,
	float MaxStairAngle)
{
	auto Result = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> TooSteepArr;

	// Stairwells are in the adjacency graph connecting rooms on different floors.
	// We need to find stairwell connections and compute their angle from the spatial data.
	// Stairwells occupy grid cells — their run length can be estimated from world bounds,
	// and floor height comes from the Z difference between floors.

	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building)
	{
		Result->SetNumberField(TEXT("total"), 0);
		Result->SetNumberField(TEXT("valid"), 0);
		Result->SetArrayField(TEXT("too_steep"), TooSteepArr);
		return Result;
	}

	// Find stairwell rooms — rooms with type containing "stair" or "stairwell"
	struct FStairwellInfo
	{
		FString RoomId;
		FBox Bounds;
		int32 FloorIndex;
	};
	TArray<FStairwellInfo> Stairwells;

	TArray<FString> AllRoomIds = GetBuildingRoomIds(Block, BuildingId);
	for (const FString& RoomId : AllRoomIds)
	{
		const FSpatialRoom* Room = Block.Rooms.Find(RoomId);
		if (!Room) continue;

		FString RoomTypeLower = Room->RoomType.ToLower();
		if (RoomTypeLower.Contains(TEXT("stair")) || RoomTypeLower.Contains(TEXT("stairwell")))
		{
			FStairwellInfo Info;
			Info.RoomId = RoomId;
			Info.Bounds = Room->WorldBounds;
			Info.FloorIndex = Room->FloorIndex;
			Stairwells.Add(Info);
		}
	}

	// Group stairwells by approximate XY position (stairwells on consecutive floors share XY footprint)
	// For each stairwell, compute angle from its run length and floor height
	int32 Total = 0;
	int32 Valid = 0;

	// Find stairwell pairs on consecutive floors
	for (int32 i = 0; i < Stairwells.Num(); i++)
	{
		for (int32 j = i + 1; j < Stairwells.Num(); j++)
		{
			// Check if they're on consecutive floors
			int32 FloorDiff = FMath::Abs(Stairwells[i].FloorIndex - Stairwells[j].FloorIndex);
			if (FloorDiff != 1) continue;

			// Check if they overlap in XY (same stairwell column)
			FBox BoundsA = Stairwells[i].Bounds;
			FBox BoundsB = Stairwells[j].Bounds;

			// Project to XY and check overlap
			FBox2D XYA(FVector2D(BoundsA.Min.X, BoundsA.Min.Y), FVector2D(BoundsA.Max.X, BoundsA.Max.Y));
			FBox2D XYB(FVector2D(BoundsB.Min.X, BoundsB.Min.Y), FVector2D(BoundsB.Max.X, BoundsB.Max.Y));

			// Simple AABB overlap in XY
			bool bOverlap = XYA.Min.X < XYB.Max.X && XYA.Max.X > XYB.Min.X &&
			                XYA.Min.Y < XYB.Max.Y && XYA.Max.Y > XYB.Min.Y;

			if (!bOverlap) continue;

			Total++;

			// Floor height = Z difference between the two stairwell rooms
			float FloorHeight = FMath::Abs(BoundsB.Min.Z - BoundsA.Min.Z);
			if (FloorHeight < 1.0f)
			{
				FloorHeight = FMath::Abs(BoundsB.Max.Z - BoundsA.Max.Z);
			}

			// Run length = the longer XY dimension of the stairwell footprint
			FVector SizeA = BoundsA.GetSize();
			float RunLength = FMath::Max(SizeA.X, SizeA.Y);

			if (RunLength < 1.0f)
			{
				// Degenerate stairwell — can't compute angle
				auto SteepObj = MakeShared<FJsonObject>();
				SteepObj->SetStringField(TEXT("stairwell"),
					FString::Printf(TEXT("%s->%s"), *Stairwells[i].RoomId, *Stairwells[j].RoomId));
				SteepObj->SetStringField(TEXT("reason"), TEXT("Degenerate stairwell — zero run length"));
				SteepObj->SetNumberField(TEXT("angle"), 90.0f);
				TooSteepArr.Add(MakeShared<FJsonValueObject>(SteepObj));
				continue;
			}

			float AngleRad = FMath::Atan2(FloorHeight, RunLength);
			float AngleDeg = FMath::RadiansToDegrees(AngleRad);

			if (AngleDeg > MaxStairAngle)
			{
				auto SteepObj = MakeShared<FJsonObject>();
				SteepObj->SetStringField(TEXT("stairwell"),
					FString::Printf(TEXT("%s->%s"), *Stairwells[i].RoomId, *Stairwells[j].RoomId));
				SteepObj->SetNumberField(TEXT("angle"), AngleDeg);
				SteepObj->SetNumberField(TEXT("max_allowed"), MaxStairAngle);
				SteepObj->SetNumberField(TEXT("floor_height"), FloorHeight);
				SteepObj->SetNumberField(TEXT("run_length"), RunLength);
				TooSteepArr.Add(MakeShared<FJsonValueObject>(SteepObj));
			}
			else
			{
				Valid++;
			}
		}
	}

	// If no pairs found but we have stairwell rooms, try single-stairwell angle estimation
	// (stairwell room spans the full height internally)
	if (Total == 0 && Stairwells.Num() > 0)
	{
		for (const FStairwellInfo& SW : Stairwells)
		{
			FVector Size = SW.Bounds.GetSize();
			float Height = Size.Z;
			float RunLength = FMath::Max(Size.X, Size.Y);

			if (RunLength < 1.0f || Height < 1.0f) continue;

			Total++;
			float AngleRad = FMath::Atan2(Height, RunLength);
			float AngleDeg = FMath::RadiansToDegrees(AngleRad);

			if (AngleDeg > MaxStairAngle)
			{
				auto SteepObj = MakeShared<FJsonObject>();
				SteepObj->SetStringField(TEXT("stairwell"), SW.RoomId);
				SteepObj->SetNumberField(TEXT("angle"), AngleDeg);
				SteepObj->SetNumberField(TEXT("max_allowed"), MaxStairAngle);
				SteepObj->SetNumberField(TEXT("floor_height"), Height);
				SteepObj->SetNumberField(TEXT("run_length"), RunLength);
				TooSteepArr.Add(MakeShared<FJsonValueObject>(SteepObj));
			}
			else
			{
				Valid++;
			}
		}
	}

	Result->SetNumberField(TEXT("total"), Total);
	Result->SetNumberField(TEXT("valid"), Valid);
	Result->SetArrayField(TEXT("too_steep"), TooSteepArr);
	return Result;
}

// ============================================================================
// Main Action Handler
// ============================================================================

FMonolithActionResult FMonolithMeshBuildingValidationActions::ValidateBuilding(
	const TSharedPtr<FJsonObject>& Params)
{
	using namespace BuildingValidationHelpers;

	// ---- Parse params ----
	FString BuildingId;
	if (!Params->TryGetStringField(TEXT("building_id"), BuildingId) || BuildingId.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("building_id is required"));
	}

	FString BlockId = TEXT("default");
	Params->TryGetStringField(TEXT("block_id"), BlockId);

	if (!FMonolithMeshSpatialRegistry::HasBlock(BlockId))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Block '%s' not found in spatial registry. Use register_building or load_block_descriptor first."),
			*BlockId));
	}

	const FSpatialBlock& Block = FMonolithMeshSpatialRegistry::GetBlock(BlockId);

	if (!Block.Buildings.Contains(BuildingId))
	{
		TArray<FString> AvailableKeys;
		Block.Buildings.GetKeys(AvailableKeys);
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Building '%s' not found in block '%s'. Available: %s"),
			*BuildingId, *BlockId,
			*FString::Join(AvailableKeys, TEXT(", "))));
	}

	float CapsuleRadius = static_cast<float>(GetNumberParam(Params, TEXT("capsule_radius"), 42.0));
	float CapsuleHalfHeight = static_cast<float>(GetNumberParam(Params, TEXT("capsule_half_height"), 96.0));
	float MinDoorWidth = static_cast<float>(GetNumberParam(Params, TEXT("min_door_width"), 100.0));
	float MaxStairAngle = static_cast<float>(GetNumberParam(Params, TEXT("max_stair_angle"), 44.76));
	bool bCheckDoors = GetBoolParam(Params, TEXT("check_doors"), true);
	bool bCheckConnectivity = GetBoolParam(Params, TEXT("check_connectivity"), true);
	bool bCheckWindows = GetBoolParam(Params, TEXT("check_windows"), true);
	bool bCheckStairs = GetBoolParam(Params, TEXT("check_stairs"), true);

	// Get editor world for physics queries (optional — validation degrades gracefully without it)
	UWorld* World = MonolithMeshUtils::GetEditorWorld();

	// ---- Run checks ----
	auto ChecksObj = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> Issues;

	// Accumulators for score
	int32 ScoreNumerator = 0;
	int32 ScoreDenominator = 0;

	// Doors
	if (bCheckDoors)
	{
		auto DoorResult = ValidateDoors(Block, BuildingId, CapsuleRadius, CapsuleHalfHeight, MinDoorWidth, World);
		ChecksObj->SetObjectField(TEXT("doors"), DoorResult);

		int32 Total = static_cast<int32>(DoorResult->GetNumberField(TEXT("total")));
		int32 Passable = static_cast<int32>(DoorResult->GetNumberField(TEXT("passable")));
		ScoreNumerator += Passable;
		ScoreDenominator += Total;

		int32 FailedCount = DoorResult->GetArrayField(TEXT("failed")).Num();
		if (FailedCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), FailedCount > 0 ? TEXT("error") : TEXT("warning"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("%d/%d doors failed passability checks"), FailedCount, Total));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}

		int32 WarningCount = DoorResult->GetArrayField(TEXT("warnings")).Num();
		if (WarningCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("warning"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("%d doors have capsule overlap warnings"), WarningCount));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}
	}

	// Connectivity
	if (bCheckConnectivity)
	{
		auto ConnResult = ValidateConnectivity(Block, BuildingId);
		ChecksObj->SetObjectField(TEXT("connectivity"), ConnResult);

		int32 TotalRooms = static_cast<int32>(ConnResult->GetNumberField(TEXT("total_rooms")));
		int32 Reachable = static_cast<int32>(ConnResult->GetNumberField(TEXT("reachable")));
		ScoreNumerator += Reachable;
		ScoreDenominator += TotalRooms;

		bool bHasEntrance = ConnResult->GetBoolField(TEXT("has_entrance"));
		if (!bHasEntrance)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("error"));
			Issue->SetStringField(TEXT("message"), TEXT("Building has no entrance — no exterior door found"));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}

		int32 UnreachableCount = ConnResult->GetArrayField(TEXT("unreachable")).Num();
		if (UnreachableCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("error"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("%d/%d rooms unreachable from entrance"), UnreachableCount, TotalRooms));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}
	}

	// Windows
	if (bCheckWindows)
	{
		auto WindowResult = ValidateWindows(Block, BuildingId, World);
		ChecksObj->SetObjectField(TEXT("windows"), WindowResult);

		int32 Total = static_cast<int32>(WindowResult->GetNumberField(TEXT("total")));
		int32 Open = static_cast<int32>(WindowResult->GetNumberField(TEXT("open")));
		ScoreNumerator += Open;
		ScoreDenominator += Total;

		int32 BlockedCount = WindowResult->GetArrayField(TEXT("blocked")).Num();
		if (BlockedCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("warning"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("%d windows appear blocked (boolean may have failed)"), BlockedCount));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}
	}

	// Stairs
	if (bCheckStairs)
	{
		auto StairResult = ValidateStairs(Block, BuildingId, MaxStairAngle);
		ChecksObj->SetObjectField(TEXT("stairs"), StairResult);

		int32 Total = static_cast<int32>(StairResult->GetNumberField(TEXT("total")));
		int32 ValidCount = static_cast<int32>(StairResult->GetNumberField(TEXT("valid")));
		ScoreNumerator += ValidCount;
		ScoreDenominator += Total;

		int32 SteepCount = StairResult->GetArrayField(TEXT("too_steep")).Num();
		if (SteepCount > 0)
		{
			auto Issue = MakeShared<FJsonObject>();
			Issue->SetStringField(TEXT("severity"), TEXT("error"));
			Issue->SetStringField(TEXT("message"), FString::Printf(
				TEXT("%d stairwells exceed max angle of %.1f degrees"), SteepCount, MaxStairAngle));
			Issues.Add(MakeShared<FJsonValueObject>(Issue));
		}
	}

	// ---- Compute score ----
	float Score = (ScoreDenominator > 0)
		? static_cast<float>(ScoreNumerator) / static_cast<float>(ScoreDenominator)
		: 1.0f;  // No checks had items -> trivially valid

	bool bHasErrors = false;
	for (const TSharedPtr<FJsonValue>& IssueVal : Issues)
	{
		const TSharedPtr<FJsonObject>* IssueObj = nullptr;
		if (IssueVal->TryGetObject(IssueObj) && IssueObj && (*IssueObj).IsValid())
		{
			FString Severity;
			(*IssueObj)->TryGetStringField(TEXT("severity"), Severity);
			if (Severity == TEXT("error"))
			{
				bHasErrors = true;
				break;
			}
		}
	}
	bool bValid = !bHasErrors;

	// ---- Build response ----
	auto Response = MakeShared<FJsonObject>();
	Response->SetStringField(TEXT("building_id"), BuildingId);
	Response->SetBoolField(TEXT("valid"), bValid);
	Response->SetNumberField(TEXT("score"), FMath::RoundToFloat(Score * 100.0f) / 100.0f);
	Response->SetObjectField(TEXT("checks"), ChecksObj);
	Response->SetArrayField(TEXT("issues"), Issues);

	if (!World)
	{
		auto WarnObj = MakeShared<FJsonObject>();
		WarnObj->SetStringField(TEXT("severity"), TEXT("info"));
		WarnObj->SetStringField(TEXT("message"),
			TEXT("No editor world available — capsule sweeps and raycasts were skipped. "
				"Door size and connectivity checks still ran."));
		Issues.Add(MakeShared<FJsonValueObject>(WarnObj));
		Response->SetArrayField(TEXT("issues"), Issues);
	}

	return FMonolithActionResult::Success(Response);
}
