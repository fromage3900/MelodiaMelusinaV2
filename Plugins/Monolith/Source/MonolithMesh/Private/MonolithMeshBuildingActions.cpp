#if WITH_GEOMETRYSCRIPT

#include "MonolithMeshBuildingActions.h"
#include "MonolithMeshFacadeActions.h"
#include "MonolithMeshProceduralActions.h"
#include "MonolithMeshHandlePool.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"
#include "MonolithAssetUtils.h"

#include "UDynamicMesh.h"
#include "DynamicMesh/DynamicMesh3.h"

#include "GeometryScript/MeshPrimitiveFunctions.h"
#include "GeometryScript/MeshBooleanFunctions.h"
#include "GeometryScript/MeshNormalsFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshTransformFunctions.h"
#include "GeometryScript/MeshUVFunctions.h"
#include "GeometryScript/MeshQueryFunctions.h"

#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Editor.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

using namespace UE::Geometry;

static const FString GS_ERROR_BUILDING = TEXT("Enable the GeometryScripting plugin in your .uproject to use building construction.");

UMonolithMeshHandlePool* FMonolithMeshBuildingActions::Pool = nullptr;

void FMonolithMeshBuildingActions::SetHandlePool(UMonolithMeshHandlePool* InPool)
{
	Pool = InPool;
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshBuildingActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	Registry.RegisterAction(TEXT("mesh"), TEXT("create_building_from_grid"),
		TEXT("Generate a multi-room building from a 2D grid of room IDs. Walls placed only at room-ID boundaries (no shared-wall duplication). "
			"Doors as boolean subtracts at grid edges. Returns the Building Descriptor JSON consumed by all downstream SPs (facades, roofs, furnishing, etc)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshBuildingActions::CreateBuildingFromGrid),
		FParamSchemaBuilder()
			.Required(TEXT("grid"), TEXT("array"), TEXT("2D array of room indices. -1 = empty, -2 = stairwell. E.g. [[0,0,1],[0,0,1],[-1,-1,1]]"))
			.Required(TEXT("rooms"), TEXT("array"), TEXT("Array of room defs: { room_id, room_type, grid_cells: [[x,y],...] }"))
			.Required(TEXT("doors"), TEXT("array"), TEXT("Array of door defs: { door_id, room_a, room_b, edge_start: [x,y], edge_end: [x,y], width?, height? }"))
			.RequiredAssetPath(TEXT("save_path"), TEXT("Asset path to save building mesh (e.g. /Game/CityBlock/Mesh/SM_Building_01)"))
			.Optional(TEXT("stairwells"), TEXT("array"), TEXT("Array of stairwell defs: { stairwell_id, grid_cells: [[x,y],...], connects_floor_a, connects_floor_b }"))
			.Optional(TEXT("floors"), TEXT("array"), TEXT("Array of floor definitions for multi-story. Default: single floor"))
			.Optional(TEXT("cell_size"), TEXT("number"), TEXT("Grid cell size in cm"), TEXT("50"))
			.Optional(TEXT("exterior_wall_thickness"), TEXT("number"), TEXT("Exterior wall thickness in cm"), TEXT("15"))
			.Optional(TEXT("interior_wall_thickness"), TEXT("number"), TEXT("Interior wall thickness in cm"), TEXT("10"))
			.Optional(TEXT("floor_height"), TEXT("number"), TEXT("Floor height in cm"), TEXT("270"))
			.Optional(TEXT("floor_thickness"), TEXT("number"), TEXT("Floor/ceiling slab thickness in cm"), TEXT("3"))
			.Optional(TEXT("materials"), TEXT("object"), TEXT("Map of slot ID to material asset path (0=exterior, 1=interior, 2=floor, 3=trim)"))
			.Optional(TEXT("location"), TEXT("array"), TEXT("World location [x, y, z]"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Optional(TEXT("building_id"), TEXT("string"), TEXT("Building ID for the descriptor"))
			.Optional(TEXT("omit_exterior_walls"), TEXT("boolean"), TEXT("Skip exterior wall geometry (use when facade will replace exterior walls). FExteriorFaceDef entries still emitted."), TEXT("false"))
			.Optional(TEXT("facade_style"), TEXT("string"), TEXT("Facade style name (loads from FacadeStyles/ presets). When set, generates integrated facade with windows/doors/trim. Automatically enables omit_exterior_walls."))
			.Optional(TEXT("facade_seed"), TEXT("integer"), TEXT("Random seed for facade variation (window placement, doors)"), TEXT("0"))
			.Optional(TEXT("overwrite"), TEXT("boolean"), TEXT("Allow overwriting existing asset at save_path"), TEXT("false"))
			.Build());

	Registry.RegisterAction(TEXT("mesh"), TEXT("create_grid_from_rooms"),
		TEXT("Helper: takes a list of room rectangles and generates a 2D grid + room definitions. "
			"Output feeds directly into create_building_from_grid."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshBuildingActions::CreateGridFromRooms),
		FParamSchemaBuilder()
			.Required(TEXT("rooms"), TEXT("array"), TEXT("Array of room rects: { room_id, room_type, x, y, width, height } in grid coordinates"))
			.Optional(TEXT("cell_size"), TEXT("number"), TEXT("Grid cell size in cm (for reference in output)"), TEXT("50"))
			.Build());
}

// ============================================================================
// JSON Parsing Helpers
// ============================================================================

bool FMonolithMeshBuildingActions::ParseGrid(const TSharedPtr<FJsonObject>& Params,
	TArray<TArray<int32>>& OutGrid, int32& OutGridW, int32& OutGridH, FString& OutError)
{
	const TArray<TSharedPtr<FJsonValue>>* GridArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("grid"), GridArr) || !GridArr || GridArr->Num() == 0)
	{
		OutError = TEXT("Missing or empty 'grid' array");
		return false;
	}

	OutGridH = GridArr->Num();
	OutGridW = 0;

	for (int32 Row = 0; Row < OutGridH; ++Row)
	{
		const TArray<TSharedPtr<FJsonValue>>* RowArr = nullptr;
		if (!(*GridArr)[Row]->TryGetArray(RowArr) || !RowArr)
		{
			OutError = FString::Printf(TEXT("Grid row %d is not an array"), Row);
			return false;
		}

		if (Row == 0)
		{
			OutGridW = RowArr->Num();
		}
		else if (RowArr->Num() != OutGridW)
		{
			OutError = FString::Printf(TEXT("Grid row %d has %d columns, expected %d"), Row, RowArr->Num(), OutGridW);
			return false;
		}

		TArray<int32> RowData;
		RowData.Reserve(OutGridW);
		for (int32 Col = 0; Col < OutGridW; ++Col)
		{
			RowData.Add(static_cast<int32>((*RowArr)[Col]->AsNumber()));
		}
		OutGrid.Add(MoveTemp(RowData));
	}

	if (OutGridW == 0)
	{
		OutError = TEXT("Grid has zero columns");
		return false;
	}

	return true;
}

bool FMonolithMeshBuildingActions::ParseRooms(const TArray<TSharedPtr<FJsonValue>>& RoomsArr,
	TArray<FRoomDef>& OutRooms, FString& OutError)
{
	for (int32 i = 0; i < RoomsArr.Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* RoomObj = nullptr;
		if (!RoomsArr[i]->TryGetObject(RoomObj) || !RoomObj || !(*RoomObj).IsValid())
		{
			OutError = FString::Printf(TEXT("rooms[%d] is not an object"), i);
			return false;
		}

		FRoomDef Room;
		if (!(*RoomObj)->TryGetStringField(TEXT("room_id"), Room.RoomId))
		{
			OutError = FString::Printf(TEXT("rooms[%d] missing 'room_id'"), i);
			return false;
		}
		(*RoomObj)->TryGetStringField(TEXT("room_type"), Room.RoomType);

		const TArray<TSharedPtr<FJsonValue>>* CellsArr = nullptr;
		if ((*RoomObj)->TryGetArrayField(TEXT("grid_cells"), CellsArr) && CellsArr)
		{
			for (const auto& CellVal : *CellsArr)
			{
				const TArray<TSharedPtr<FJsonValue>>* Pair = nullptr;
				if (CellVal->TryGetArray(Pair) && Pair && Pair->Num() >= 2)
				{
					Room.GridCells.Add(FIntPoint(
						static_cast<int32>((*Pair)[0]->AsNumber()),
						static_cast<int32>((*Pair)[1]->AsNumber())));
				}
			}
		}

		OutRooms.Add(MoveTemp(Room));
	}
	return true;
}

bool FMonolithMeshBuildingActions::ParseDoors(const TArray<TSharedPtr<FJsonValue>>& DoorsArr,
	TArray<FDoorDef>& OutDoors, FString& OutError)
{
	for (int32 i = 0; i < DoorsArr.Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* DoorObj = nullptr;
		if (!DoorsArr[i]->TryGetObject(DoorObj) || !DoorObj || !(*DoorObj).IsValid())
		{
			OutError = FString::Printf(TEXT("doors[%d] is not an object"), i);
			return false;
		}

		FDoorDef Door;
		if (!(*DoorObj)->TryGetStringField(TEXT("door_id"), Door.DoorId))
		{
			Door.DoorId = FString::Printf(TEXT("door_%d"), i);
		}
		(*DoorObj)->TryGetStringField(TEXT("room_a"), Door.RoomA);
		(*DoorObj)->TryGetStringField(TEXT("room_b"), Door.RoomB);

		// Parse edge_start
		const TArray<TSharedPtr<FJsonValue>>* StartArr = nullptr;
		if ((*DoorObj)->TryGetArrayField(TEXT("edge_start"), StartArr) && StartArr && StartArr->Num() >= 2)
		{
			Door.EdgeStart = FIntPoint(
				static_cast<int32>((*StartArr)[0]->AsNumber()),
				static_cast<int32>((*StartArr)[1]->AsNumber()));
		}
		else
		{
			OutError = FString::Printf(TEXT("doors[%d] missing 'edge_start' [x,y]"), i);
			return false;
		}

		// Parse edge_end (defaults to edge_start for single-cell doors)
		const TArray<TSharedPtr<FJsonValue>>* EndArr = nullptr;
		if ((*DoorObj)->TryGetArrayField(TEXT("edge_end"), EndArr) && EndArr && EndArr->Num() >= 2)
		{
			Door.EdgeEnd = FIntPoint(
				static_cast<int32>((*EndArr)[0]->AsNumber()),
				static_cast<int32>((*EndArr)[1]->AsNumber()));
		}
		else
		{
			Door.EdgeEnd = Door.EdgeStart;
		}

		if ((*DoorObj)->HasField(TEXT("width")))
			Door.Width = static_cast<float>((*DoorObj)->GetNumberField(TEXT("width")));
		if ((*DoorObj)->HasField(TEXT("height")))
			Door.Height = static_cast<float>((*DoorObj)->GetNumberField(TEXT("height")));
		if ((*DoorObj)->HasField(TEXT("traversable")))
			Door.bTraversable = (*DoorObj)->GetBoolField(TEXT("traversable"));

		OutDoors.Add(MoveTemp(Door));
	}
	return true;
}

bool FMonolithMeshBuildingActions::ParseStairwells(const TArray<TSharedPtr<FJsonValue>>& StairArr,
	TArray<FStairwellDef>& OutStairwells, FString& OutError)
{
	for (int32 i = 0; i < StairArr.Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* StairObj = nullptr;
		if (!StairArr[i]->TryGetObject(StairObj) || !StairObj || !(*StairObj).IsValid())
		{
			OutError = FString::Printf(TEXT("stairwells[%d] is not an object"), i);
			return false;
		}

		FStairwellDef Stair;
		if (!(*StairObj)->TryGetStringField(TEXT("stairwell_id"), Stair.StairwellId))
		{
			Stair.StairwellId = FString::Printf(TEXT("stair_%d"), i);
		}

		if ((*StairObj)->HasField(TEXT("connects_floor_a")))
			Stair.ConnectsFloorA = static_cast<int32>((*StairObj)->GetNumberField(TEXT("connects_floor_a")));
		if ((*StairObj)->HasField(TEXT("connects_floor_b")))
			Stair.ConnectsFloorB = static_cast<int32>((*StairObj)->GetNumberField(TEXT("connects_floor_b")));

		const TArray<TSharedPtr<FJsonValue>>* CellsArr = nullptr;
		if ((*StairObj)->TryGetArrayField(TEXT("grid_cells"), CellsArr) && CellsArr)
		{
			for (const auto& CellVal : *CellsArr)
			{
				const TArray<TSharedPtr<FJsonValue>>* Pair = nullptr;
				if (CellVal->TryGetArray(Pair) && Pair && Pair->Num() >= 2)
				{
					Stair.GridCells.Add(FIntPoint(
						static_cast<int32>((*Pair)[0]->AsNumber()),
						static_cast<int32>((*Pair)[1]->AsNumber())));
				}
			}
		}

		// Parse vertical_access type (R2-C2: stairs/elevator/both)
		FString AccessStr;
		if ((*StairObj)->TryGetStringField(TEXT("vertical_access"), AccessStr))
		{
			if (AccessStr == TEXT("elevator"))
				Stair.VerticalAccess = EVerticalAccessType::Elevator;
			else if (AccessStr == TEXT("both"))
				Stair.VerticalAccess = EVerticalAccessType::Both;
			else
				Stair.VerticalAccess = EVerticalAccessType::Stairs;
		}

		OutStairwells.Add(MoveTemp(Stair));
	}
	return true;
}

// ============================================================================
// Wall Segment Building — The Core Algorithm
// ============================================================================

bool FMonolithMeshBuildingActions::IsDoorEdge(int32 FixedAxis, int32 RunPos, bool bVertical, const TArray<FDoorDef>& Doors)
{
	for (const FDoorDef& D : Doors)
	{
		if (bVertical)
		{
			// Vertical wall at fixed X = FixedAxis, running along Y
			// Door covers Y from min(EdgeStart.Y, EdgeEnd.Y) to max(EdgeStart.Y, EdgeEnd.Y)
			if (D.EdgeStart.X == FixedAxis || D.EdgeEnd.X == FixedAxis)
			{
				int32 MinY = FMath::Min(D.EdgeStart.Y, D.EdgeEnd.Y);
				int32 MaxY = FMath::Max(D.EdgeStart.Y, D.EdgeEnd.Y);
				if (RunPos >= MinY && RunPos <= MaxY) return true;
			}
		}
		else
		{
			// Horizontal wall at fixed Y = FixedAxis, running along X
			if (D.EdgeStart.Y == FixedAxis || D.EdgeEnd.Y == FixedAxis)
			{
				int32 MinX = FMath::Min(D.EdgeStart.X, D.EdgeEnd.X);
				int32 MaxX = FMath::Max(D.EdgeStart.X, D.EdgeEnd.X);
				if (RunPos >= MinX && RunPos <= MaxX) return true;
			}
		}
	}
	return false;
}

TArray<FMonolithMeshBuildingActions::FWallSegment> FMonolithMeshBuildingActions::BuildWallSegments(
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH, const TArray<FDoorDef>& Doors)
{
	TArray<FWallSegment> Segments;

	// Helper to get cell ID safely (-1 for out-of-bounds = exterior)
	auto GetCell = [&](int32 X, int32 Y) -> int32
	{
		if (X < 0 || X >= GridW || Y < 0 || Y >= GridH) return -1;
		return Grid[Y][X];
	};

	// --- Vertical walls (between columns X-1 and X) ---
	// For each column boundary X (0 to GridW), scan along Y
	for (int32 X = 0; X <= GridW; ++X)
	{
		int32 RunStart = -1;
		int32 RunLeftId = -1, RunRightId = -1;
		bool RunExterior = false;

		for (int32 Y = 0; Y < GridH; ++Y)
		{
			int32 LeftId = GetCell(X - 1, Y);
			int32 RightId = GetCell(X, Y);

			bool bNeedWall = (LeftId != RightId);
			// Don't break wall segments at door cells — let boolean cutter handle doors entirely.
			// Breaking here creates cell-aligned segment boundaries that don't match Door.Width,
			// producing 20cm wall stubs on both sides of every door opening.
			bool bIsDoor = false;

			// Also suppress wall if both sides are empty
			if (LeftId == -1 && RightId == -1) bNeedWall = false;

			bool bExterior = (LeftId == -1 || RightId == -1);

			// Can we extend the current run?
			bool bCanExtend = bNeedWall && !bIsDoor && RunStart >= 0
				&& LeftId == RunLeftId && RightId == RunRightId;

			if (!bCanExtend)
			{
				// Close current run
				if (RunStart >= 0)
				{
					FWallSegment Seg;
					Seg.FixedAxis = X;
					Seg.RunStart = RunStart;
					Seg.RunEnd = Y;
					Seg.LeftId = RunLeftId;
					Seg.RightId = RunRightId;
					Seg.bVertical = true;
					Seg.bExterior = RunExterior;
					Segments.Add(Seg);
					RunStart = -1;
				}

				// Start new run?
				if (bNeedWall && !bIsDoor)
				{
					RunStart = Y;
					RunLeftId = LeftId;
					RunRightId = RightId;
					RunExterior = bExterior;
				}
			}
		}

		// Close final run
		if (RunStart >= 0)
		{
			FWallSegment Seg;
			Seg.FixedAxis = X;
			Seg.RunStart = RunStart;
			Seg.RunEnd = GridH;
			Seg.LeftId = RunLeftId;
			Seg.RightId = RunRightId;
			Seg.bVertical = true;
			Seg.bExterior = RunExterior;
			Segments.Add(Seg);
		}
	}

	// --- Horizontal walls (between rows Y-1 and Y) ---
	for (int32 Y = 0; Y <= GridH; ++Y)
	{
		int32 RunStart = -1;
		int32 RunTopId = -1, RunBottomId = -1;
		bool RunExterior = false;

		for (int32 X = 0; X < GridW; ++X)
		{
			int32 TopId = GetCell(X, Y - 1);
			int32 BottomId = GetCell(X, Y);

			bool bNeedWall = (TopId != BottomId);
			// Don't break wall segments at door cells — boolean cutter handles doors.
			bool bIsDoor = false;

			if (TopId == -1 && BottomId == -1) bNeedWall = false;

			bool bExterior = (TopId == -1 || BottomId == -1);

			bool bCanExtend = bNeedWall && !bIsDoor && RunStart >= 0
				&& TopId == RunTopId && BottomId == RunBottomId;

			if (!bCanExtend)
			{
				if (RunStart >= 0)
				{
					FWallSegment Seg;
					Seg.FixedAxis = Y;
					Seg.RunStart = RunStart;
					Seg.RunEnd = X;
					Seg.LeftId = RunTopId;
					Seg.RightId = RunBottomId;
					Seg.bVertical = false;
					Seg.bExterior = RunExterior;
					Segments.Add(Seg);
					RunStart = -1;
				}

				if (bNeedWall && !bIsDoor)
				{
					RunStart = X;
					RunTopId = TopId;
					RunBottomId = BottomId;
					RunExterior = bExterior;
				}
			}
		}

		if (RunStart >= 0)
		{
			FWallSegment Seg;
			Seg.FixedAxis = Y;
			Seg.RunStart = RunStart;
			Seg.RunEnd = GridW;
			Seg.LeftId = RunTopId;
			Seg.RightId = RunBottomId;
			Seg.bVertical = false;
			Seg.bExterior = RunExterior;
			Segments.Add(Seg);
		}
	}

	return Segments;
}

// ============================================================================
// Geometry Generation
// ============================================================================

void FMonolithMeshBuildingActions::GenerateWallGeometry(UDynamicMesh* Mesh,
	const TArray<FWallSegment>& Segments, float CellSize, float FloorHeight, float FloorZ,
	float ExteriorT, float InteriorT, TArray<FExteriorFaceDef>& OutExteriorFaces, int32 FloorIndex,
	const TArray<FRoomDef>& Rooms, bool bOmitExteriorWalls)
{
	FGeometryScriptPrimitiveOptions Opts;

	for (const FWallSegment& Seg : Segments)
	{
		float WallT = Seg.bExterior ? ExteriorT : InteriorT;

		// Exterior walls get MaterialID 0, interior walls get MaterialID 1
		Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
		Opts.MaterialID = Seg.bExterior ? 0 : 1;

		float RunLen = static_cast<float>(Seg.RunEnd - Seg.RunStart) * CellSize;

		if (Seg.bVertical)
		{
			float WallX = static_cast<float>(Seg.FixedAxis) * CellSize;
			float WallYCenter = (static_cast<float>(Seg.RunStart) + static_cast<float>(Seg.RunEnd)) * 0.5f * CellSize;

			// Emit exterior wall geometry UNLESS omit flag is set
			if (!(bOmitExteriorWalls && Seg.bExterior))
			{
				FTransform WallXf(FRotator::ZeroRotator,
					FVector(WallX, WallYCenter, FloorZ),
					FVector::OneVector);

				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, WallXf,
					WallT, RunLen, FloorHeight,
					0, 0, 0,
					EGeometryScriptPrimitiveOriginMode::Base);
			}

			// ALWAYS record exterior face — facade needs this data even when geometry is omitted
			if (Seg.bExterior)
			{
				FExteriorFaceDef Face;
				if (Seg.LeftId == -1)
				{
					Face.Wall = TEXT("west");
					Face.Normal = FVector(-1.0f, 0.0f, 0.0f);
				}
				else
				{
					Face.Wall = TEXT("east");
					Face.Normal = FVector(1.0f, 0.0f, 0.0f);
				}
				Face.FloorIndex = FloorIndex;
				Face.WorldOrigin = FVector(WallX, static_cast<float>(Seg.RunStart) * CellSize, FloorZ);
				Face.Width = RunLen;
				Face.Height = FloorHeight;

				// Populate room type from the interior side
				int32 InteriorRoomId = (Seg.LeftId == -1) ? Seg.RightId : Seg.LeftId;
				Face.RoomId = InteriorRoomId;
				if (InteriorRoomId >= 0 && InteriorRoomId < Rooms.Num())
					Face.RoomType = Rooms[InteriorRoomId].RoomType;

				OutExteriorFaces.Add(Face);
			}
		}
		else
		{
			float WallY = static_cast<float>(Seg.FixedAxis) * CellSize;
			float WallXCenter = (static_cast<float>(Seg.RunStart) + static_cast<float>(Seg.RunEnd)) * 0.5f * CellSize;

			// Emit exterior wall geometry UNLESS omit flag is set
			if (!(bOmitExteriorWalls && Seg.bExterior))
			{
				FTransform WallXf(FRotator::ZeroRotator,
					FVector(WallXCenter, WallY, FloorZ),
					FVector::OneVector);

				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
					Mesh, Opts, WallXf,
					RunLen, WallT, FloorHeight,
					0, 0, 0,
					EGeometryScriptPrimitiveOriginMode::Base);
			}

			// ALWAYS record exterior face
			if (Seg.bExterior)
			{
				FExteriorFaceDef Face;
				if (Seg.LeftId == -1)
				{
					Face.Wall = TEXT("north");
					Face.Normal = FVector(0.0f, -1.0f, 0.0f);
				}
				else
				{
					Face.Wall = TEXT("south");
					Face.Normal = FVector(0.0f, 1.0f, 0.0f);
				}
				Face.FloorIndex = FloorIndex;
				Face.WorldOrigin = FVector(static_cast<float>(Seg.RunStart) * CellSize, WallY, FloorZ);
				Face.Width = RunLen;
				Face.Height = FloorHeight;

				// Populate room type from the interior side
				int32 InteriorRoomId = (Seg.LeftId == -1) ? Seg.RightId : Seg.LeftId;
				Face.RoomId = InteriorRoomId;
				if (InteriorRoomId >= 0 && InteriorRoomId < Rooms.Num())
					Face.RoomType = Rooms[InteriorRoomId].RoomType;

				OutExteriorFaces.Add(Face);
			}
		}
	}
}

void FMonolithMeshBuildingActions::GenerateSlabs(UDynamicMesh* Mesh,
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH,
	float CellSize, float SlabThickness, float ZPosition, int32 MaterialId, bool bSkipStairwells)
{
	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	Opts.MaterialID = MaterialId;

	// Merge adjacent cells with same room ID into rectangular runs for fewer boxes
	// Simple row-based greedy merge: for each row, merge consecutive cells of the same room
	TSet<int64> Visited;

	for (int32 Y = 0; Y < GridH; ++Y)
	{
		for (int32 X = 0; X < GridW; ++X)
		{
			int64 Key = static_cast<int64>(Y) * GridW + X;
			if (Visited.Contains(Key)) continue;

			int32 CellId = Grid[Y][X];
			if (CellId == -1) continue; // Empty — no slab
			if (bSkipStairwells && CellId == -2) continue; // Stairwell — suppress slab

			// Extend run along X as far as possible
			int32 RunEndX = X + 1;
			while (RunEndX < GridW)
			{
				int32 NextId = Grid[Y][RunEndX];
				if (NextId != CellId) break;
				int64 NextKey = static_cast<int64>(Y) * GridW + RunEndX;
				if (Visited.Contains(NextKey)) break;
				++RunEndX;
			}

			// Try to extend run downward (Y direction) for rectangular merge
			int32 RunEndY = Y + 1;
			while (RunEndY < GridH)
			{
				bool bRowMatches = true;
				for (int32 RX = X; RX < RunEndX; ++RX)
				{
					int32 NextId = Grid[RunEndY][RX];
					if (NextId != CellId)
					{
						bRowMatches = false;
						break;
					}
					int64 NextKey = static_cast<int64>(RunEndY) * GridW + RX;
					if (Visited.Contains(NextKey))
					{
						bRowMatches = false;
						break;
					}
				}
				if (!bRowMatches) break;
				++RunEndY;
			}

			// Mark all cells in rectangle as visited
			for (int32 RY = Y; RY < RunEndY; ++RY)
			{
				for (int32 RX = X; RX < RunEndX; ++RX)
				{
					Visited.Add(static_cast<int64>(RY) * GridW + RX);
				}
			}

			// Generate slab for this rectangle
			float SlabW = static_cast<float>(RunEndX - X) * CellSize;
			float SlabD = static_cast<float>(RunEndY - Y) * CellSize;
			float CenterX = (static_cast<float>(X) + static_cast<float>(RunEndX)) * 0.5f * CellSize;
			float CenterY = (static_cast<float>(Y) + static_cast<float>(RunEndY)) * 0.5f * CellSize;

			FTransform SlabXf(FRotator::ZeroRotator,
				FVector(CenterX, CenterY, ZPosition),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, SlabXf,
				SlabW, SlabD, SlabThickness,
				0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Base);
		}
	}
}

void FMonolithMeshBuildingActions::CutDoorOpenings(UDynamicMesh* Mesh, const TArray<FDoorDef>& Doors,
	float CellSize, float FloorZ, float ExteriorT, float InteriorT,
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH, bool& bHadBooleans)
{
	if (Doors.Num() == 0) return;

	FGeometryScriptPrimitiveOptions Opts;

	auto GetCell = [&](int32 X, int32 Y) -> int32
	{
		if (X < 0 || X >= GridW || Y < 0 || Y >= GridH) return -1;
		return Grid[Y][X];
	};

	for (const FDoorDef& Door : Doors)
	{
		// Determine wall orientation from edge position
		// The door edge_start and edge_end define positions on the grid boundary
		// Detect whether this is a vertical or horizontal wall edge

		bool bVerticalWall;
		float WallPos;     // Position of the wall on the fixed axis
		float DoorCenter;  // Center position along the run axis
		float DoorSpan;    // How many cells the door spans

		// If edge_start.X == edge_end.X, the door is on a vertical wall
		if (Door.EdgeStart.X == Door.EdgeEnd.X)
		{
			bVerticalWall = true;
			WallPos = static_cast<float>(Door.EdgeStart.X) * CellSize;
			float MinY = static_cast<float>(FMath::Min(Door.EdgeStart.Y, Door.EdgeEnd.Y));
			float MaxY = static_cast<float>(FMath::Max(Door.EdgeStart.Y, Door.EdgeEnd.Y)) + 1.0f;
			DoorCenter = (MinY + MaxY) * 0.5f * CellSize;
			DoorSpan = (MaxY - MinY);
		}
		else
		{
			bVerticalWall = false;
			WallPos = static_cast<float>(Door.EdgeStart.Y) * CellSize;
			float MinX = static_cast<float>(FMath::Min(Door.EdgeStart.X, Door.EdgeEnd.X));
			float MaxX = static_cast<float>(FMath::Max(Door.EdgeStart.X, Door.EdgeEnd.X)) + 1.0f;
			DoorCenter = (MinX + MaxX) * 0.5f * CellSize;
			DoorSpan = (MaxX - MinX);
		}

		// Determine wall thickness based on whether either side is exterior
		int32 SideA, SideB;
		if (bVerticalWall)
		{
			SideA = GetCell(Door.EdgeStart.X - 1, Door.EdgeStart.Y);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}
		else
		{
			SideA = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y - 1);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}
		bool bExterior = (SideA == -1 || SideB == -1);
		float WallT = bExterior ? ExteriorT : InteriorT;

		// Cutter box: must be wide enough to clear any perpendicular wall at the door position.
		// A perpendicular wall can be up to ExteriorT thick at a T-junction or corner.
		// Use max wall thickness + generous margin to ensure clean cut through any intersection.
		float CutterOvershoot = FMath::Max(ExteriorT, InteriorT) * 2.0f + 20.0f;

		// Clamp cutter bottom Z to FloorZ — on upper floors, never punch through the ceiling slab below
		float CutterBaseZ = FloorZ;

		FVector CutPos;
		float CutW, CutD;

		if (bVerticalWall)
		{
			CutPos = FVector(WallPos, DoorCenter, CutterBaseZ);
			CutW = CutterOvershoot; // Wide enough to cut through wall
			CutD = Door.Width;
		}
		else
		{
			CutPos = FVector(DoorCenter, WallPos, CutterBaseZ);
			CutW = Door.Width;
			CutD = CutterOvershoot;
		}

		UDynamicMesh* Cutter = NewObject<UDynamicMesh>(Pool);
		FTransform CutXf(FRotator::ZeroRotator, CutPos, FVector::OneVector);
		UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
			Cutter, Opts, CutXf,
			CutW, CutD, Door.Height,
			0, 0, 0,
			EGeometryScriptPrimitiveOriginMode::Base);

		FGeometryScriptMeshBooleanOptions BoolOpts;
		UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshBoolean(
			Mesh, FTransform::Identity, Cutter, FTransform::Identity,
			EGeometryScriptBooleanOperation::Subtract, BoolOpts);
		bHadBooleans = true;
	}
}

void FMonolithMeshBuildingActions::AddDoorTrim(UDynamicMesh* Mesh, const TArray<FDoorDef>& Doors,
	float CellSize, float FloorZ, float ExteriorT, float InteriorT,
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH)
{
	if (Doors.Num() == 0) return;

	FGeometryScriptPrimitiveOptions TrimOpts;
	TrimOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	TrimOpts.MaterialID = 3; // Trim material slot

	const float TrimW = 5.0f;  // Trim width

	auto GetCell = [&](int32 X, int32 Y) -> int32
	{
		if (X < 0 || X >= GridW || Y < 0 || Y >= GridH) return -1;
		return Grid[Y][X];
	};

	for (const FDoorDef& Door : Doors)
	{
		bool bVerticalWall = (Door.EdgeStart.X == Door.EdgeEnd.X);

		float WallPos;
		float DoorCenter;

		if (bVerticalWall)
		{
			WallPos = static_cast<float>(Door.EdgeStart.X) * CellSize;
			float MinY = static_cast<float>(FMath::Min(Door.EdgeStart.Y, Door.EdgeEnd.Y));
			float MaxY = static_cast<float>(FMath::Max(Door.EdgeStart.Y, Door.EdgeEnd.Y)) + 1.0f;
			DoorCenter = (MinY + MaxY) * 0.5f * CellSize;
		}
		else
		{
			WallPos = static_cast<float>(Door.EdgeStart.Y) * CellSize;
			float MinX = static_cast<float>(FMath::Min(Door.EdgeStart.X, Door.EdgeEnd.X));
			float MaxX = static_cast<float>(FMath::Max(Door.EdgeStart.X, Door.EdgeEnd.X)) + 1.0f;
			DoorCenter = (MinX + MaxX) * 0.5f * CellSize;
		}

		int32 SideA, SideB;
		if (bVerticalWall)
		{
			SideA = GetCell(Door.EdgeStart.X - 1, Door.EdgeStart.Y);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}
		else
		{
			SideA = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y - 1);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}
		float WallT = (SideA == -1 || SideB == -1) ? ExteriorT : InteriorT;
		float TrimD = WallT + 2.0f;

		UDynamicMesh* TrimMesh = NewObject<UDynamicMesh>(Pool);

		if (bVerticalWall)
		{
			// Left jamb
			FTransform LeftJambXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter - Door.Width * 0.5f - TrimW * 0.5f, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, LeftJambXf,
				TrimD, TrimW, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Right jamb
			FTransform RightJambXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter + Door.Width * 0.5f + TrimW * 0.5f, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, RightJambXf,
				TrimD, TrimW, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Header
			FTransform HeaderXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter, FloorZ + Door.Height),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, HeaderXf,
				TrimD, Door.Width + TrimW * 2.0f, TrimW,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
		}
		else
		{
			// Left jamb
			FTransform LeftJambXf(FRotator::ZeroRotator,
				FVector(DoorCenter - Door.Width * 0.5f - TrimW * 0.5f, WallPos, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, LeftJambXf,
				TrimW, TrimD, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Right jamb
			FTransform RightJambXf(FRotator::ZeroRotator,
				FVector(DoorCenter + Door.Width * 0.5f + TrimW * 0.5f, WallPos, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, RightJambXf,
				TrimW, TrimD, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Header
			FTransform HeaderXf(FRotator::ZeroRotator,
				FVector(DoorCenter, WallPos, FloorZ + Door.Height),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				TrimMesh, TrimOpts, HeaderXf,
				Door.Width + TrimW * 2.0f, TrimD, TrimW,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
		}

		UGeometryScriptLibrary_MeshBasicEditFunctions::AppendMesh(
			Mesh, TrimMesh, FTransform::Identity);
	}
}

// ============================================================================
// Entrance Door Frame Geometry (WP-3)
// ============================================================================

void FMonolithMeshBuildingActions::GenerateEntranceDoorFrames(UDynamicMesh* Mesh,
	const TArray<FDoorDef>& Doors, float CellSize, float FloorZ, float ExteriorT,
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH)
{
	auto GetCell = [&](int32 X, int32 Y) -> int32
	{
		if (X < 0 || X >= GridW || Y < 0 || Y >= GridH) return -1;
		return Grid[Y][X];
	};

	FGeometryScriptPrimitiveOptions FrameOpts;
	FrameOpts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	FrameOpts.MaterialID = 5; // Door frame material slot

	const float FrameWidth = 8.0f;      // Frame profile width per side
	const float FrameDepth = ExteriorT + 6.0f;  // Extends 3cm past wall on each face
	const float ThresholdHeight = 3.0f;  // Small threshold step
	const float ThresholdDepth = 30.0f;  // Threshold extends outward

	for (const FDoorDef& Door : Doors)
	{
		// Only process exterior doors (connecting to "exterior")
		bool bIsExterior = (Door.RoomB == TEXT("exterior") || Door.RoomA == TEXT("exterior"));
		if (!bIsExterior)
		{
			// Also check by grid cell — if either side of the door edge is -1 (empty/exterior)
			int32 SideA, SideB;
			bool bVerticalWall = (Door.EdgeStart.X == Door.EdgeEnd.X);
			if (bVerticalWall)
			{
				SideA = GetCell(Door.EdgeStart.X - 1, Door.EdgeStart.Y);
				SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
			}
			else
			{
				SideA = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y - 1);
				SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
			}
			bIsExterior = (SideA == -1 || SideB == -1);
		}

		if (!bIsExterior) continue;

		bool bVerticalWall = (Door.EdgeStart.X == Door.EdgeEnd.X);

		float WallPos;
		float DoorCenter;

		if (bVerticalWall)
		{
			WallPos = static_cast<float>(Door.EdgeStart.X) * CellSize;
			float MinY = static_cast<float>(FMath::Min(Door.EdgeStart.Y, Door.EdgeEnd.Y));
			float MaxY = static_cast<float>(FMath::Max(Door.EdgeStart.Y, Door.EdgeEnd.Y)) + 1.0f;
			DoorCenter = (MinY + MaxY) * 0.5f * CellSize;
		}
		else
		{
			WallPos = static_cast<float>(Door.EdgeStart.Y) * CellSize;
			float MinX = static_cast<float>(FMath::Min(Door.EdgeStart.X, Door.EdgeEnd.X));
			float MaxX = static_cast<float>(FMath::Max(Door.EdgeStart.X, Door.EdgeEnd.X)) + 1.0f;
			DoorCenter = (MinX + MaxX) * 0.5f * CellSize;
		}

		// Determine which side is exterior to orient the frame correctly
		int32 SideA, SideB;
		if (bVerticalWall)
		{
			SideA = GetCell(Door.EdgeStart.X - 1, Door.EdgeStart.Y);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}
		else
		{
			SideA = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y - 1);
			SideB = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
		}

		// Normal points outward toward exterior
		FVector OutwardNormal;
		if (bVerticalWall)
		{
			OutwardNormal = (SideA == -1) ? FVector(-1.0f, 0.0f, 0.0f) : FVector(1.0f, 0.0f, 0.0f);
		}
		else
		{
			OutwardNormal = (SideA == -1) ? FVector(0.0f, -1.0f, 0.0f) : FVector(0.0f, 1.0f, 0.0f);
		}

		UDynamicMesh* FrameMesh = NewObject<UDynamicMesh>(Pool);

		if (bVerticalWall)
		{
			// Left post (jamb)
			FTransform LeftPostXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter - Door.Width * 0.5f - FrameWidth * 0.5f, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, LeftPostXf,
				FrameDepth, FrameWidth, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Right post (jamb)
			FTransform RightPostXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter + Door.Width * 0.5f + FrameWidth * 0.5f, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, RightPostXf,
				FrameDepth, FrameWidth, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Lintel (header)
			FTransform LintelXf(FRotator::ZeroRotator,
				FVector(WallPos, DoorCenter, FloorZ + Door.Height),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, LintelXf,
				FrameDepth, Door.Width + FrameWidth * 2.0f, FrameWidth,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Threshold step on exterior side
			float ThresholdX = WallPos + OutwardNormal.X * (ExteriorT * 0.5f + ThresholdDepth * 0.5f);
			FTransform ThresholdXf(FRotator::ZeroRotator,
				FVector(ThresholdX, DoorCenter, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, ThresholdXf,
				ThresholdDepth, Door.Width + FrameWidth * 2.0f, ThresholdHeight,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
		}
		else
		{
			// Left post (jamb)
			FTransform LeftPostXf(FRotator::ZeroRotator,
				FVector(DoorCenter - Door.Width * 0.5f - FrameWidth * 0.5f, WallPos, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, LeftPostXf,
				FrameWidth, FrameDepth, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Right post (jamb)
			FTransform RightPostXf(FRotator::ZeroRotator,
				FVector(DoorCenter + Door.Width * 0.5f + FrameWidth * 0.5f, WallPos, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, RightPostXf,
				FrameWidth, FrameDepth, Door.Height,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Lintel (header)
			FTransform LintelXf(FRotator::ZeroRotator,
				FVector(DoorCenter, WallPos, FloorZ + Door.Height),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, LintelXf,
				Door.Width + FrameWidth * 2.0f, FrameDepth, FrameWidth,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);

			// Threshold step on exterior side
			float ThresholdY = WallPos + OutwardNormal.Y * (ExteriorT * 0.5f + ThresholdDepth * 0.5f);
			FTransform ThresholdXf(FRotator::ZeroRotator,
				FVector(DoorCenter, ThresholdY, FloorZ),
				FVector::OneVector);
			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				FrameMesh, FrameOpts, ThresholdXf,
				Door.Width + FrameWidth * 2.0f, ThresholdDepth, ThresholdHeight,
				0, 0, 0, EGeometryScriptPrimitiveOriginMode::Base);
		}

		UGeometryScriptLibrary_MeshBasicEditFunctions::AppendMesh(
			Mesh, FrameMesh, FTransform::Identity);

		UE_LOG(LogTemp, Log, TEXT("Generated entrance door frame for '%s' (%.0f x %.0f cm) at wall %s"),
			*Door.DoorId, Door.Width, Door.Height,
			bVerticalWall ? TEXT("vertical") : TEXT("horizontal"));
	}
}

void FMonolithMeshBuildingActions::GenerateStairGeometry(UDynamicMesh* Mesh,
	const TArray<FStairwellDef>& Stairwells, float CellSize, float FloorHeight, float FloorZ, float StairWidth)
{
	if (Stairwells.Num() == 0) return;

	FGeometryScriptPrimitiveOptions Opts;
	Opts.PolygroupMode = EGeometryScriptPrimitivePolygroupMode::PerFace;
	Opts.MaterialID = 2; // Floor material

	// IBC standard tread dimensions — gives ~32.7 degree angle
	const float TargetTreadDepth = 28.0f;  // 11 inches (IBC standard)
	const float TargetRiserHeight = 18.0f; // ~7 inches
	const float MinFlightWidth = 80.0f;    // Minimum stair width per flight
	const float LandingSlabThick = 3.0f;   // Landing platform thickness
	const float FlightGap = 10.0f;         // Gap between switchback flights

	for (const FStairwellDef& Stair : Stairwells)
	{
		if (Stair.GridCells.Num() == 0) continue;

		// R2-C2: Elevator shafts suppress floor/ceiling slabs but get NO stair geometry
		if (Stair.VerticalAccess == EVerticalAccessType::Elevator)
		{
			UE_LOG(LogTemp, Log, TEXT("Stairwell '%s' is elevator shaft — skipping stair geometry (slab suppression still active)"),
				*Stair.StairwellId);
			continue;
		}

		// Compute stairwell bounding box in grid coords
		int32 MinGX = INT32_MAX, MaxGX = INT32_MIN;
		int32 MinGY = INT32_MAX, MaxGY = INT32_MIN;
		for (const FIntPoint& C : Stair.GridCells)
		{
			MinGX = FMath::Min(MinGX, C.X);
			MaxGX = FMath::Max(MaxGX, C.X);
			MinGY = FMath::Min(MinGY, C.Y);
			MaxGY = FMath::Max(MaxGY, C.Y);
		}

		float WorldMinX = static_cast<float>(MinGX) * CellSize;
		float WorldMaxX = static_cast<float>(MaxGX + 1) * CellSize;
		float WorldMinY = static_cast<float>(MinGY) * CellSize;
		float WorldMaxY = static_cast<float>(MaxGY + 1) * CellSize;

		float AvailableDepth = WorldMaxY - WorldMinY;  // Stairs run along Y
		float AvailableWidth = WorldMaxX - WorldMinX;

		// Compute step count and actual riser from floor height
		int32 StepCount = FMath::Max(2, FMath::CeilToInt32(FloorHeight / TargetRiserHeight));
		float ActualRiser = FloorHeight / static_cast<float>(StepCount);
		float RequiredRun = static_cast<float>(StepCount) * TargetTreadDepth;

		if (AvailableDepth >= RequiredRun)
		{
			// ---- STRAIGHT STAIR: stairwell is long enough for a single flight ----
			float ActualWidth = FMath::Min(StairWidth, AvailableWidth);
			float CenterX = (WorldMinX + WorldMaxX) * 0.5f;

			FTransform StairXf(FRotator::ZeroRotator,
				FVector(CenterX - ActualWidth * 0.5f, WorldMinY, FloorZ),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendLinearStairs(
				Mesh, Opts, StairXf,
				ActualWidth, ActualRiser, TargetTreadDepth, StepCount,
				/*bFloating=*/false);
		}
		else if (AvailableWidth >= MinFlightWidth * 2.0f + FlightGap)
		{
			// ---- SWITCHBACK STAIR: two half-flights running in opposite Y directions ----
			int32 HalfSteps = StepCount / 2;
			int32 SecondHalfSteps = StepCount - HalfSteps;
			float HalfRun = static_cast<float>(HalfSteps) * TargetTreadDepth;
			float FlightWidth = FMath::Min(
				(AvailableWidth - FlightGap) * 0.5f,
				StairWidth);
			float LandingDepth = FMath::Min(FlightWidth, AvailableDepth - HalfRun);

			if (LandingDepth < 60.0f)
			{
				// Not enough room for landing — fall back to steep capped stair
				UE_LOG(LogTemp, Warning,
					TEXT("Stairwell '%s' too small for switchback (%.0fx%.0fcm). "
						"Minimum for 270cm floor: 200x300cm (4x6 cells at 50cm). "
						"Falling back to steepest walkable angle."),
					*Stair.StairwellId, AvailableWidth, AvailableDepth);

				float CappedTread = ActualRiser / FMath::Tan(FMath::DegreesToRadians(44.0f));
				float UseTread = FMath::Max(AvailableDepth / static_cast<float>(StepCount), CappedTread);
				float ActualWidth = FMath::Min(StairWidth, AvailableWidth);
				float CenterX = (WorldMinX + WorldMaxX) * 0.5f;

				FTransform StairXf(FRotator::ZeroRotator,
					FVector(CenterX - ActualWidth * 0.5f, WorldMinY, FloorZ),
					FVector::OneVector);

				UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendLinearStairs(
					Mesh, Opts, StairXf,
					ActualWidth, ActualRiser, UseTread, StepCount,
					/*bFloating=*/false);
				continue;
			}

			float MidZ = FloorZ + static_cast<float>(HalfSteps) * ActualRiser;

			// Flight 1: left side, going +Y
			float Flight1X = WorldMinX;
			FTransform Flight1Xf(FRotator::ZeroRotator,
				FVector(Flight1X, WorldMinY, FloorZ),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendLinearStairs(
				Mesh, Opts, Flight1Xf,
				FlightWidth, ActualRiser, TargetTreadDepth, HalfSteps,
				/*bFloating=*/false);

			// Landing platform at the far end, spanning full stairwell width
			float LandingY = WorldMinY + HalfRun;
			FTransform LandingXf(FRotator::ZeroRotator,
				FVector(WorldMinX + AvailableWidth * 0.5f, LandingY + LandingDepth * 0.5f, MidZ),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendBox(
				Mesh, Opts, LandingXf,
				AvailableWidth, LandingDepth, LandingSlabThick,
				0, 0, 0,
				EGeometryScriptPrimitiveOriginMode::Center);

			// Flight 2: right side, going -Y (rotated 180 about Z)
			float Flight2X = WorldMinX + FlightWidth + FlightGap;
			float Flight2StartY = LandingY + LandingDepth;

			FTransform Flight2Xf(FRotator(0.0f, 180.0f, 0.0f),
				FVector(Flight2X + FlightWidth, Flight2StartY, MidZ),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendLinearStairs(
				Mesh, Opts, Flight2Xf,
				FlightWidth, ActualRiser, TargetTreadDepth, SecondHalfSteps,
				/*bFloating=*/false);
		}
		else
		{
			// ---- FALLBACK: stairwell too small for switchback, cap at 44 degrees ----
			float CappedTread = ActualRiser / FMath::Tan(FMath::DegreesToRadians(44.0f));
			float MaxTread = AvailableDepth / static_cast<float>(StepCount);
			float UseTread = FMath::Max(MaxTread, CappedTread);
			float ActualAngle = FMath::RadiansToDegrees(FMath::Atan2(ActualRiser, UseTread));

			UE_LOG(LogTemp, Warning,
				TEXT("Stairwell '%s' too small for comfortable stairs (%.0fx%.0fcm, angle=%.1f deg). "
					"Minimum footprint for 270cm floor: 200x300cm (4x6 cells at 50cm)."),
				*Stair.StairwellId, AvailableWidth, AvailableDepth, ActualAngle);

			float ActualWidth = FMath::Min(StairWidth, AvailableWidth);
			float CenterX = (WorldMinX + WorldMaxX) * 0.5f;

			FTransform StairXf(FRotator::ZeroRotator,
				FVector(CenterX - ActualWidth * 0.5f, WorldMinY, FloorZ),
				FVector::OneVector);

			UGeometryScriptLibrary_MeshPrimitiveFunctions::AppendLinearStairs(
				Mesh, Opts, StairXf,
				ActualWidth, ActualRiser, UseTread, StepCount,
				/*bFloating=*/false);
		}
	}
}

// ============================================================================
// Descriptor Computation Helpers
// ============================================================================

void FMonolithMeshBuildingActions::ComputeRoomBounds(TArray<FRoomDef>& Rooms,
	float CellSize, float FloorHeight, float FloorZ, const FVector& WorldOrigin)
{
	for (FRoomDef& Room : Rooms)
	{
		if (Room.GridCells.Num() == 0) continue;

		int32 MinX = INT32_MAX, MaxX = INT32_MIN;
		int32 MinY = INT32_MAX, MaxY = INT32_MIN;
		for (const FIntPoint& C : Room.GridCells)
		{
			MinX = FMath::Min(MinX, C.X);
			MaxX = FMath::Max(MaxX, C.X);
			MinY = FMath::Min(MinY, C.Y);
			MaxY = FMath::Max(MaxY, C.Y);
		}

		FVector LocalMin(static_cast<float>(MinX) * CellSize, static_cast<float>(MinY) * CellSize, FloorZ);
		FVector LocalMax(static_cast<float>(MaxX + 1) * CellSize, static_cast<float>(MaxY + 1) * CellSize, FloorZ + FloorHeight);

		Room.LocalBounds = FBox(LocalMin, LocalMax);
		Room.WorldBounds = FBox(LocalMin + WorldOrigin, LocalMax + WorldOrigin);
	}
}

void FMonolithMeshBuildingActions::ComputeDoorPositions(TArray<FDoorDef>& Doors,
	float CellSize, float FloorZ, const FVector& WorldOrigin,
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH)
{
	auto GetCell = [&](int32 X, int32 Y) -> int32
	{
		if (X < 0 || X >= GridW || Y < 0 || Y >= GridH) return -1;
		return Grid[Y][X];
	};

	for (FDoorDef& Door : Doors)
	{
		bool bVerticalWall = (Door.EdgeStart.X == Door.EdgeEnd.X);

		if (bVerticalWall)
		{
			float WallX = static_cast<float>(Door.EdgeStart.X) * CellSize;
			float MinY = static_cast<float>(FMath::Min(Door.EdgeStart.Y, Door.EdgeEnd.Y));
			float MaxY = static_cast<float>(FMath::Max(Door.EdgeStart.Y, Door.EdgeEnd.Y)) + 1.0f;
			float CenterY = (MinY + MaxY) * 0.5f * CellSize;
			Door.WorldPosition = FVector(WallX, CenterY, FloorZ) + WorldOrigin;

			// Determine wall direction
			int32 LeftId = GetCell(Door.EdgeStart.X - 1, Door.EdgeStart.Y);
			int32 RightId = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
			// Wall faces perpendicular to X
			if (LeftId == -1)
				Door.Wall = TEXT("west");
			else if (RightId == -1)
				Door.Wall = TEXT("east");
			else
				Door.Wall = TEXT("east"); // Interior — convention
		}
		else
		{
			float WallY = static_cast<float>(Door.EdgeStart.Y) * CellSize;
			float MinX = static_cast<float>(FMath::Min(Door.EdgeStart.X, Door.EdgeEnd.X));
			float MaxX = static_cast<float>(FMath::Max(Door.EdgeStart.X, Door.EdgeEnd.X)) + 1.0f;
			float CenterX = (MinX + MaxX) * 0.5f * CellSize;
			Door.WorldPosition = FVector(CenterX, WallY, FloorZ) + WorldOrigin;

			int32 TopId = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y - 1);
			int32 BottomId = GetCell(Door.EdgeStart.X, Door.EdgeStart.Y);
			if (TopId == -1)
				Door.Wall = TEXT("north");
			else if (BottomId == -1)
				Door.Wall = TEXT("south");
			else
				Door.Wall = TEXT("south");
		}
	}
}

TArray<FVector2D> FMonolithMeshBuildingActions::ComputeFootprint(
	const TArray<TArray<int32>>& Grid, int32 GridW, int32 GridH, float CellSize)
{
	// Simple approach: axis-aligned bounding box of all non-empty cells
	int32 MinX = GridW, MaxX = -1, MinY = GridH, MaxY = -1;
	for (int32 Y = 0; Y < GridH; ++Y)
	{
		for (int32 X = 0; X < GridW; ++X)
		{
			if (Grid[Y][X] != -1)
			{
				MinX = FMath::Min(MinX, X);
				MaxX = FMath::Max(MaxX, X);
				MinY = FMath::Min(MinY, Y);
				MaxY = FMath::Max(MaxY, Y);
			}
		}
	}

	if (MaxX < 0)
	{
		// No occupied cells
		return TArray<FVector2D>();
	}

	// CCW rectangle
	float X0 = static_cast<float>(MinX) * CellSize;
	float X1 = static_cast<float>(MaxX + 1) * CellSize;
	float Y0 = static_cast<float>(MinY) * CellSize;
	float Y1 = static_cast<float>(MaxY + 1) * CellSize;

	TArray<FVector2D> Poly;
	Poly.Add(FVector2D(X0, Y0));
	Poly.Add(FVector2D(X1, Y0));
	Poly.Add(FVector2D(X1, Y1));
	Poly.Add(FVector2D(X0, Y1));
	return Poly;
}

// ============================================================================
// Merge Exterior Faces — combine per-segment faces into per-wall-side faces
// ============================================================================

static TArray<FExteriorFaceDef> MergeExteriorFaces(const TArray<FExteriorFaceDef>& Faces)
{
	TMap<FString, TArray<const FExteriorFaceDef*>> Groups;
	for (const FExteriorFaceDef& F : Faces)
	{
		FString Key = FString::Printf(TEXT("%s_%d"), *F.Wall, F.FloorIndex);
		Groups.FindOrAdd(Key).Add(&F);
	}

	TArray<FExteriorFaceDef> Merged;
	for (auto& Pair : Groups)
	{
		TArray<const FExteriorFaceDef*>& Group = Pair.Value;
		if (Group.Num() == 0) continue;

		bool bVertical = (Group[0]->Wall == TEXT("east") || Group[0]->Wall == TEXT("west"));
		Algo::Sort(Group, [bVertical](const FExteriorFaceDef* A, const FExteriorFaceDef* B)
		{
			return bVertical ? A->WorldOrigin.Y < B->WorldOrigin.Y
			                 : A->WorldOrigin.X < B->WorldOrigin.X;
		});

		FExteriorFaceDef Current = *Group[0];
		TArray<FRoomSpan> Spans;
		Spans.Add({ 0.0f, Current.Width, Current.RoomType, Current.RoomId });
		float RunningWidth = Current.Width;

		for (int32 i = 1; i < Group.Num(); ++i)
		{
			const FExteriorFaceDef* Next = Group[i];
			float NextPos = bVertical ? Next->WorldOrigin.Y : Next->WorldOrigin.X;
			float CurrentEnd = (bVertical ? Current.WorldOrigin.Y : Current.WorldOrigin.X) + RunningWidth;
			float Gap = NextPos - CurrentEnd;

			if (FMath::Abs(Gap) < 1.0f)
			{
				Spans.Add({ RunningWidth, Next->Width, Next->RoomType, Next->RoomId });
				RunningWidth += Next->Width;
			}
			else
			{
				Current.Width = RunningWidth;
				Current.RoomSpans = Spans;
				Merged.Add(Current);
				Current = *Next;
				Spans.Reset();
				Spans.Add({ 0.0f, Next->Width, Next->RoomType, Next->RoomId });
				RunningWidth = Next->Width;
			}
		}
		Current.Width = RunningWidth;
		Current.RoomSpans = Spans;
		Merged.Add(Current);
	}
	return Merged;
}

// ============================================================================
// Integrated Facade Generation — v3 Single-Pass Architecture
// ============================================================================

void FMonolithMeshBuildingActions::GenerateIntegratedFacade(UDynamicMesh* Mesh,
	const TArray<FExteriorFaceDef>& ExteriorFaces, float WallThickness,
	const FString& FacadeStyleName, int32 Seed, int32 MaxFloorIndex,
	FBuildingDescriptor& Descriptor, bool& bHadBooleans)
{
	using FFacadeStyle = FMonolithMeshFacadeActions::FFacadeStyle;
	using FWindowPlacement = FMonolithMeshFacadeActions::FWindowPlacement;
	using FDoorPlacement = FMonolithMeshFacadeActions::FDoorPlacement;

	// Load facade style
	FFacadeStyle Style;
	if (!FMonolithMeshFacadeActions::LoadFacadeStyle(FacadeStyleName, Style))
	{
		Style.Name = FacadeStyleName;
		Style.Description = TEXT("Default (no preset file found)");
	}

	Descriptor.FacadeStyle = FacadeStyleName;

	// Track ground floor window X positions per wall direction for vertical alignment
	TMap<FString, TArray<float>> GroundFloorWindowX;

	for (const FExteriorFaceDef& Face : ExteriorFaces)
	{
		bool bIsGroundFloor = (Face.FloorIndex == 0);
		float MinSpacing = FMath::Max(Style.WindowWidth * 0.6f, 100.0f); // At least 100cm between windows
		float Margin = Style.FrameWidth + Style.CornerWidth;

		// 1. Wall slab is built internally by CutOpeningsSelectionInset
		//    (it needs an isolated mesh for plane slicing to not affect other geometry)

		// 2. Compute window positions
		TArray<float> WinXPositions;

		if (bIsGroundFloor)
		{
			WinXPositions = FMonolithMeshFacadeActions::ComputeWindowPositions(
				Face.Width, Style.WindowWidth, Margin, MinSpacing);
			GroundFloorWindowX.FindOrAdd(Face.Wall) = WinXPositions;
		}
		else
		{
			// Upper floors: align with ground floor when possible
			const TArray<float>* GroundPositions = GroundFloorWindowX.Find(Face.Wall);
			if (GroundPositions && GroundPositions->Num() > 0)
			{
				WinXPositions = *GroundPositions;
			}
			else
			{
				WinXPositions = FMonolithMeshFacadeActions::ComputeWindowPositions(
					Face.Width, Style.WindowWidth, Margin, MinSpacing);
			}
		}

		// 2.5. Density cap: max ~1 window per 3 meters of wall
		{
			int32 MaxWindows = FMath::Max(1, FMath::FloorToInt32(Face.Width / 300.0f));
			if (WinXPositions.Num() > MaxWindows)
			{
				if (MaxWindows == 1)
				{
					// Keep the center-most window
					int32 MidIdx = WinXPositions.Num() / 2;
					float Mid = WinXPositions[MidIdx];
					WinXPositions.Reset();
					WinXPositions.Add(Mid);
				}
				else
				{
					TArray<float> Capped;
					float Step = static_cast<float>(WinXPositions.Num() - 1) / static_cast<float>(MaxWindows - 1);
					for (int32 i = 0; i < MaxWindows; ++i)
					{
						int32 Idx = FMath::Clamp(FMath::RoundToInt32(i * Step), 0, WinXPositions.Num() - 1);
						Capped.Add(WinXPositions[Idx]);
					}
					WinXPositions = Capped;
				}
			}
		}

		// 3. Build window placements
		TArray<FWindowPlacement> Windows;
		for (float XPos : WinXPositions)
		{
			FWindowPlacement Win;
			Win.CenterX = XPos;
			Win.Width = Style.WindowWidth;
			Win.Height = Style.WindowHeight;
			Win.SillZ = Style.SillHeight;
			Win.FloorIndex = Face.FloorIndex;
			Win.bIsGroundFloor = bIsGroundFloor;
			Windows.Add(Win);
		}

		// 3.5. Room-type-aware window filtering (skip windows behind corridors, closets, etc.)
		if (Face.RoomSpans.Num() > 0)
		{
			TArray<FWindowPlacement> FilteredWindows;
			for (const FWindowPlacement& Win : Windows)
			{
				// Convert from center-relative to start-relative offset
				float WinOffset = Win.CenterX + Face.Width * 0.5f;
				FString SpanRoomType;
				for (const FRoomSpan& Span : Face.RoomSpans)
				{
					if (WinOffset >= Span.StartOffset && WinOffset < Span.StartOffset + Span.Width)
					{
						SpanRoomType = Span.RoomType;
						break;
					}
				}
				// Skip windows for rooms that shouldn't have them
				if (SpanRoomType == TEXT("corridor") || SpanRoomType == TEXT("closet") ||
				    SpanRoomType == TEXT("utility") || SpanRoomType == TEXT("stairwell") ||
				    SpanRoomType == TEXT("walkway") || SpanRoomType == TEXT("supply_room") ||
				    SpanRoomType == TEXT("supply"))
					continue;
				FilteredWindows.Add(Win);
			}
			Windows = FilteredWindows;
		}

		// 4. Build door placements (ground floor only, if face is wide enough)
		TArray<FDoorPlacement> Doors;
		if (bIsGroundFloor && Face.Width >= Style.DoorWidth + 2.0f * Margin)
		{
			FRandomStream DoorRng(Seed + FCrc::StrCrc32(*Face.Wall));
			if (DoorRng.FRand() < 0.4f)
			{
				FDoorPlacement Door;
				Door.CenterX = 0.0f;
				Door.Width = Style.DoorWidth;
				Door.Height = Style.DoorHeight;
				Door.bStorefront = false;
				Doors.Add(Door);

				// Remove windows that overlap with the door (60cm minimum edge-to-edge clearance)
				float MinClearance = 60.0f;
				float DoorHalfW = Style.DoorWidth * 0.5f + MinClearance + Style.WindowWidth * 0.5f;
				Windows.RemoveAll([DoorHalfW](const FWindowPlacement& W)
				{
					return FMath::Abs(W.CenterX) < DoorHalfW;
				});
			}
		}

		// 5. Build wall slab + cut window/door openings via Selection+Inset
		//    CutOpeningsSelectionInset builds the wall in an isolated temp mesh,
		//    applies plane slices + selection + inset + deletion, then AppendMesh.
		FMonolithMeshFacadeActions::CutOpeningsSelectionInset(
			Mesh, Face, Windows, Doors, WallThickness, Style.FrameWidth,
			/*bUseSelectionInset=*/false, bHadBooleans); // Boolean fallback — Selection+Inset crashes GeometryCore, use pre-cut walls (Option D) later

		// 6. Add window frames
		FMonolithMeshFacadeActions::AddWindowFrames(Mesh, Face, Windows, Style, WallThickness);

		// 7. Add door frames
		FMonolithMeshFacadeActions::AddDoorFrames(Mesh, Face, Doors, Style, WallThickness);

		// 8. Add glass panes
		FMonolithMeshFacadeActions::AddGlassPanes(Mesh, Face, Windows, Style.GlassMaterialId);

		// 9. Belt course above ground floor
		if (bIsGroundFloor && MaxFloorIndex > 0)
		{
			FMonolithMeshFacadeActions::AddBeltCourse(Mesh, Face, Face.Height, Style);
		}

		// 10. Cornice on top floor
		if (Face.FloorIndex == MaxFloorIndex)
		{
			FMonolithMeshFacadeActions::AddCornice(Mesh, Face, Face.Height, Style);
		}

		// 11. Emit window metadata into descriptor
		FVector WidthAxis = FMonolithMeshFacadeActions::GetFaceWidthAxis(Face);
		FVector FaceCenter = Face.WorldOrigin + WidthAxis * (Face.Width * 0.5f);

		for (const FWindowPlacement& W : Windows)
		{
			FFacadeWindowPlacement WP;
			WP.CenterX = W.CenterX;
			WP.SillZ = W.SillZ;
			WP.Width = W.Width;
			WP.Height = W.Height;
			WP.FloorIndex = W.FloorIndex;
			WP.bIsGroundFloor = W.bIsGroundFloor;
			WP.Wall = Face.Wall;
			WP.WorldCenter = FaceCenter + WidthAxis * W.CenterX;
			WP.WorldCenter.Z = Face.WorldOrigin.Z + W.SillZ + W.Height * 0.5f;
			Descriptor.Windows.Add(MoveTemp(WP));
		}

		for (const FDoorPlacement& D : Doors)
		{
			FFacadeDoorPlacement DP;
			DP.CenterX = D.CenterX;
			DP.Width = D.Width;
			DP.Height = D.Height;
			DP.bStorefront = D.bStorefront;
			DP.Wall = Face.Wall;
			DP.WorldCenter = FaceCenter + WidthAxis * D.CenterX;
			DP.WorldCenter.Z = Face.WorldOrigin.Z + D.Height * 0.5f;
			Descriptor.EntranceDoors.Add(MoveTemp(DP));
		}
	}
}

// ============================================================================
// create_building_from_grid — The Main Action
// ============================================================================

FMonolithActionResult FMonolithMeshBuildingActions::CreateBuildingFromGrid(const TSharedPtr<FJsonObject>& Params)
{
	if (!Pool)
	{
		return FMonolithActionResult::Error(GS_ERROR_BUILDING);
	}

	// ---- Parse configuration ----
	float CellSize = Params->HasField(TEXT("cell_size")) ? static_cast<float>(Params->GetNumberField(TEXT("cell_size"))) : 50.0f;
	float ExteriorT = Params->HasField(TEXT("exterior_wall_thickness")) ? static_cast<float>(Params->GetNumberField(TEXT("exterior_wall_thickness"))) : 15.0f;
	float InteriorT = Params->HasField(TEXT("interior_wall_thickness")) ? static_cast<float>(Params->GetNumberField(TEXT("interior_wall_thickness"))) : 10.0f;
	float FloorHeight = Params->HasField(TEXT("floor_height")) ? static_cast<float>(Params->GetNumberField(TEXT("floor_height"))) : 270.0f;
	float FloorThick = Params->HasField(TEXT("floor_thickness")) ? static_cast<float>(Params->GetNumberField(TEXT("floor_thickness"))) : 3.0f;

	FString SavePath;
	if (!Params->TryGetStringField(TEXT("save_path"), SavePath) || SavePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: save_path"));
	}

	FString BuildingId;
	if (!Params->TryGetStringField(TEXT("building_id"), BuildingId))
	{
		BuildingId = FPaths::GetBaseFilename(SavePath);
	}

	FVector Location = FVector::ZeroVector;
	MonolithMeshUtils::ParseVector(Params, TEXT("location"), Location);

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);
	if (Label.IsEmpty()) Label = BuildingId;

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);
	if (Folder.IsEmpty()) Folder = FString::Printf(TEXT("CityBlock/Buildings/%s"), *BuildingId);

	// ---- Parse grid ----
	TArray<TArray<int32>> Grid;
	int32 GridW = 0, GridH = 0;
	FString ParseErr;
	if (!ParseGrid(Params, Grid, GridW, GridH, ParseErr))
	{
		return FMonolithActionResult::Error(ParseErr);
	}

	// ---- Parse rooms ----
	const TArray<TSharedPtr<FJsonValue>>* RoomsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("rooms"), RoomsArr) || !RoomsArr)
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: rooms"));
	}
	TArray<FRoomDef> Rooms;
	if (!ParseRooms(*RoomsArr, Rooms, ParseErr))
	{
		return FMonolithActionResult::Error(ParseErr);
	}

	// ---- Parse doors ----
	const TArray<TSharedPtr<FJsonValue>>* DoorsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("doors"), DoorsArr) || !DoorsArr)
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: doors"));
	}
	TArray<FDoorDef> Doors;
	if (!ParseDoors(*DoorsArr, Doors, ParseErr))
	{
		return FMonolithActionResult::Error(ParseErr);
	}

	// ---- Parse stairwells (optional) ----
	TArray<FStairwellDef> Stairwells;
	const TArray<TSharedPtr<FJsonValue>>* StairArr = nullptr;
	if (Params->TryGetArrayField(TEXT("stairwells"), StairArr) && StairArr)
	{
		if (!ParseStairwells(*StairArr, Stairwells, ParseErr))
		{
			return FMonolithActionResult::Error(ParseErr);
		}
	}

	// ---- Parse optional flags ----
	bool bOmitExteriorWalls = Params->HasField(TEXT("omit_exterior_walls"))
		? Params->GetBoolField(TEXT("omit_exterior_walls")) : false;

	// ---- Facade style (v3 integrated facade) ----
	FString FacadeStyleName;
	Params->TryGetStringField(TEXT("facade_style"), FacadeStyleName);
	bool bHasFacadeStyle = !FacadeStyleName.IsEmpty();
	int32 FacadeSeed = Params->HasField(TEXT("facade_seed"))
		? static_cast<int32>(Params->GetNumberField(TEXT("facade_seed"))) : 0;

	// When facade_style is provided, automatically omit exterior walls from the base generator
	// because the facade functions will generate the exterior walls WITH openings
	if (bHasFacadeStyle)
	{
		bOmitExteriorWalls = true;
	}

	// ---- Build geometry ----
	UDynamicMesh* Mesh = NewObject<UDynamicMesh>(Pool);
	if (!Mesh)
	{
		return FMonolithActionResult::Error(TEXT("Failed to allocate UDynamicMesh"));
	}

	bool bHadBooleans = false;
	FBuildingDescriptor Descriptor;
	Descriptor.BuildingId = BuildingId;
	Descriptor.AssetPath = SavePath;
	Descriptor.WorldOrigin = Location;
	Descriptor.GridCellSize = CellSize;
	Descriptor.ExteriorWallThickness = ExteriorT;
	Descriptor.InteriorWallThickness = InteriorT;

	int32 NumFloors = 1;
	const TArray<TSharedPtr<FJsonValue>>* FloorsArr = nullptr;
	if (Params->TryGetArrayField(TEXT("floors"), FloorsArr) && FloorsArr && FloorsArr->Num() > 0)
	{
		NumFloors = FloorsArr->Num();
	}

	// ---- Build per-floor grids with stairwell propagation ----
	// Each floor gets its own copy of the grid so stairwell cells can be
	// propagated to destination floors (suppressing floor slabs above stairs).
	TArray<TArray<TArray<int32>>> PerFloorGrids;
	PerFloorGrids.SetNum(NumFloors);
	for (int32 F = 0; F < NumFloors; ++F)
	{
		PerFloorGrids[F] = Grid; // Deep copy base grid
	}

	// Propagate stairwell cells to ALL floors they affect
	for (const FStairwellDef& Stair : Stairwells)
	{
		// Mark cells on the originating floor (ensure -2 even if caller set them)
		if (Stair.ConnectsFloorA >= 0 && Stair.ConnectsFloorA < NumFloors)
		{
			auto& GridA = PerFloorGrids[Stair.ConnectsFloorA];
			for (const FIntPoint& Cell : Stair.GridCells)
			{
				if (Cell.X >= 0 && Cell.X < GridW && Cell.Y >= 0 && Cell.Y < GridH)
					GridA[Cell.Y][Cell.X] = -2;
			}
		}

		// Mark cells on the destination floor — THE CRITICAL FIX:
		// Without this, the upper floor generates a solid slab above the stairs.
		if (Stair.ConnectsFloorB >= 0 && Stair.ConnectsFloorB < NumFloors)
		{
			auto& GridB = PerFloorGrids[Stair.ConnectsFloorB];
			for (const FIntPoint& Cell : Stair.GridCells)
			{
				if (Cell.X >= 0 && Cell.X < GridW && Cell.Y >= 0 && Cell.Y < GridH)
					GridB[Cell.Y][Cell.X] = -2;
			}
		}

		// For multi-floor stairwells (atriums), mark intermediate floors too
		for (int32 F = Stair.ConnectsFloorA + 1; F < Stair.ConnectsFloorB; ++F)
		{
			if (F >= 0 && F < NumFloors)
			{
				auto& GridMid = PerFloorGrids[F];
				for (const FIntPoint& Cell : Stair.GridCells)
				{
					if (Cell.X >= 0 && Cell.X < GridW && Cell.Y >= 0 && Cell.Y < GridH)
						GridMid[Cell.Y][Cell.X] = -2;
				}
			}
		}
	}

	for (int32 FloorIdx = 0; FloorIdx < NumFloors; ++FloorIdx)
	{
		float FloorZ = static_cast<float>(FloorIdx) * (FloorHeight + FloorThick);

		// Use per-floor grid (with stairwell propagation applied)
		TArray<TArray<int32>>& FloorGrid = PerFloorGrids[FloorIdx];
		TArray<FRoomDef>* FloorRooms = &Rooms;
		TArray<FDoorDef>* FloorDoors = &Doors;
		TArray<FStairwellDef>* FloorStairwells = &Stairwells;

		// 1. Build wall segments from per-floor grid (stairwell cells produce enclosure walls)
		TArray<FWallSegment> WallSegments = BuildWallSegments(FloorGrid, GridW, GridH, *FloorDoors);

		// 2. Generate wall geometry (respects omit_exterior_walls flag)
		TArray<FExteriorFaceDef> ExteriorFaces;
		GenerateWallGeometry(Mesh, WallSegments, CellSize, FloorHeight, FloorZ + FloorThick,
			ExteriorT, InteriorT, ExteriorFaces, FloorIdx, Rooms, bOmitExteriorWalls);

		// 3. Generate floor slab (skip stairwell cells — now properly propagated to upper floors)
		GenerateSlabs(Mesh, FloorGrid, GridW, GridH, CellSize, FloorThick, FloorZ, 2, true);

		// 4. Generate ceiling slab (skip stairwell cells)
		GenerateSlabs(Mesh, FloorGrid, GridW, GridH, CellSize, FloorThick,
			FloorZ + FloorThick + FloorHeight, 2, true);

		// 4.5 Merge exterior faces by wall direction for sane window density
		// (segments broken by room boundaries get merged into per-building-side faces)
		TArray<FExteriorFaceDef> MergedFaces = MergeExteriorFaces(ExteriorFaces);

		// Generate integrated facade with merged faces BEFORE door booleans
		// so that CutDoorOpenings can cut through the facade exterior walls.
		if (bHasFacadeStyle && MergedFaces.Num() > 0)
		{
			GenerateIntegratedFacade(Mesh, MergedFaces, ExteriorT,
				FacadeStyleName, FacadeSeed, NumFloors - 1, Descriptor, bHadBooleans);
		}

		// 5. Boolean-subtract door openings
		CutDoorOpenings(Mesh, *FloorDoors, CellSize, FloorZ + FloorThick,
			ExteriorT, InteriorT, FloorGrid, GridW, GridH, bHadBooleans);

		// 6. Add trim around door openings
		AddDoorTrim(Mesh, *FloorDoors, CellSize, FloorZ + FloorThick,
			ExteriorT, InteriorT, FloorGrid, GridW, GridH);

		// 6.5 Generate entrance door frames for exterior doors (WP-3)
		// Only on ground floor — exterior entrances don't exist on upper floors
		if (FloorIdx == 0)
		{
			GenerateEntranceDoorFrames(Mesh, *FloorDoors, CellSize, FloorZ + FloorThick,
				ExteriorT, FloorGrid, GridW, GridH);
		}

		// 7. Generate stair geometry for stairwells (only on the originating floor)
		float ActualStairWidth = CellSize;
		GenerateStairGeometry(Mesh, *FloorStairwells, CellSize, FloorHeight + FloorThick,
			FloorZ + FloorThick, ActualStairWidth);

		// 8. Compute room bounds and door positions for descriptor
		ComputeRoomBounds(*FloorRooms, CellSize, FloorHeight, FloorZ + FloorThick, Location);
		ComputeDoorPositions(*FloorDoors, CellSize, FloorZ + FloorThick, Location,
			FloorGrid, GridW, GridH);

		// Compute stairwell world positions
		for (FStairwellDef& S : *FloorStairwells)
		{
			if (S.GridCells.Num() > 0)
			{
				FVector Avg = FVector::ZeroVector;
				for (const FIntPoint& C : S.GridCells)
				{
					Avg += FVector((static_cast<float>(C.X) + 0.5f) * CellSize,
						(static_cast<float>(C.Y) + 0.5f) * CellSize,
						FloorZ + FloorThick);
				}
				Avg /= static_cast<float>(S.GridCells.Num());
				S.WorldPosition = Avg + Location;
			}
		}

		// 9. Build floor plan for descriptor
		FFloorPlan FloorPlan;
		FloorPlan.FloorIndex = FloorIdx;
		FloorPlan.ZOffset = FloorZ;
		FloorPlan.Height = FloorHeight;
		FloorPlan.Grid = FloorGrid;
		FloorPlan.Rooms = *FloorRooms;
		FloorPlan.Doors = *FloorDoors;
		FloorPlan.Stairwells = *FloorStairwells;
		Descriptor.Floors.Add(MoveTemp(FloorPlan));

		// Accumulate exterior faces
		for (FExteriorFaceDef& Face : ExteriorFaces)
		{
			Face.WorldOrigin += Location;
			Descriptor.ExteriorFaces.Add(MoveTemp(Face));
		}
	}

	// 10. Compute footprint polygon
	Descriptor.FootprintPolygon = ComputeFootprint(Grid, GridW, GridH, CellSize);

	// 11. Cleanup mesh (normals)
	FMonolithMeshProceduralActions::CleanupMesh(Mesh, bHadBooleans);

	// 12. Box UV projection
	{
		FGeometryScriptMeshSelection EmptySelection;
		FTransform UVBox = FTransform::Identity;
		UVBox.SetScale3D(FVector(100.0f));
		UGeometryScriptLibrary_MeshUVFunctions::SetMeshUVsFromBoxProjection(
			Mesh, 0, UVBox, EmptySelection, 2);
	}

	int32 TriCount = Mesh->GetTriangleCount();

	// 13. Save mesh to asset
	bool bOverwrite = Params->HasField(TEXT("overwrite")) ? Params->GetBoolField(TEXT("overwrite")) : false;
	FString SaveErr;
	if (!FMonolithMeshProceduralActions::SaveMeshToAsset(Mesh, SavePath, bOverwrite, SaveErr))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Mesh generated (%d tris) but save failed: %s"), TriCount, *SaveErr));
	}

	// 14. Place in scene
	FRotator Rotation = FRotator::ZeroRotator;
	bool bSnapToFloor = !Params->HasField(TEXT("snap_to_floor")) || Params->GetBoolField(TEXT("snap_to_floor"));
	AActor* Actor = FMonolithMeshProceduralActions::PlaceMeshInScene(SavePath, Location, Rotation, Label, bSnapToFloor, Folder);

	if (Actor)
	{
		Descriptor.ActorNames.Add(Actor->GetActorNameOrLabel());

		// Apply actor tags for downstream SP9 (Daredevil view)
		Actor->Tags.Add(FName(TEXT("BuildingFloor")));
		Actor->Tags.Add(FName(TEXT("BuildingCeiling")));
		Descriptor.TagsApplied.Add(TEXT("BuildingFloor"));
		Descriptor.TagsApplied.Add(TEXT("BuildingCeiling"));

		if (bHasFacadeStyle)
		{
			Actor->Tags.Add(FName(TEXT("BuildingFacade")));
			Actor->Tags.Add(FName(TEXT("Monolith.Procedural")));
			Descriptor.TagsApplied.Add(TEXT("BuildingFacade"));
		}
	}

	// 15. Build result JSON with full Building Descriptor
	auto Result = Descriptor.ToJson();
	Result->SetNumberField(TEXT("triangle_count"), TriCount);
	Result->SetNumberField(TEXT("wall_segment_count"), 0); // Will count below
	Result->SetNumberField(TEXT("door_count"), Doors.Num());
	Result->SetNumberField(TEXT("room_count"), Rooms.Num());
	Result->SetNumberField(TEXT("floor_count"), NumFloors);
	Result->SetNumberField(TEXT("grid_width"), GridW);
	Result->SetNumberField(TEXT("grid_height"), GridH);
	Result->SetBoolField(TEXT("had_booleans"), bHadBooleans);
	Result->SetStringField(TEXT("save_path"), SavePath);
	Result->SetNumberField(TEXT("floor_thickness"), FloorThick);
	Result->SetNumberField(TEXT("floor_height"), FloorHeight);

	if (bHasFacadeStyle)
	{
		Result->SetStringField(TEXT("facade_style"), FacadeStyleName);
		Result->SetNumberField(TEXT("window_count"), Descriptor.Windows.Num());
		Result->SetNumberField(TEXT("entrance_door_count"), Descriptor.EntranceDoors.Num());
		Result->SetBoolField(TEXT("integrated_facade"), true);
	}

	if (Actor)
	{
		Result->SetStringField(TEXT("actor_name"), Actor->GetActorNameOrLabel());
		Result->SetBoolField(TEXT("placed_in_scene"), true);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// create_grid_from_rooms — Helper Action
// ============================================================================

FMonolithActionResult FMonolithMeshBuildingActions::CreateGridFromRooms(const TSharedPtr<FJsonObject>& Params)
{
	const TArray<TSharedPtr<FJsonValue>>* RoomsArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("rooms"), RoomsArr) || !RoomsArr || RoomsArr->Num() == 0)
	{
		return FMonolithActionResult::Error(TEXT("Missing or empty 'rooms' array"));
	}

	float CellSize = Params->HasField(TEXT("cell_size")) ? static_cast<float>(Params->GetNumberField(TEXT("cell_size"))) : 50.0f;

	struct FRoomRect
	{
		FString RoomId;
		FString RoomType;
		int32 X, Y, Width, Height;
	};

	TArray<FRoomRect> RoomRects;
	int32 MaxX = 0, MaxY = 0;

	for (int32 i = 0; i < RoomsArr->Num(); ++i)
	{
		const TSharedPtr<FJsonObject>* RoomObj = nullptr;
		if (!(*RoomsArr)[i]->TryGetObject(RoomObj) || !RoomObj || !(*RoomObj).IsValid())
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("rooms[%d] is not an object"), i));
		}

		FRoomRect Rect;
		if (!(*RoomObj)->TryGetStringField(TEXT("room_id"), Rect.RoomId))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("rooms[%d] missing 'room_id'"), i));
		}
		(*RoomObj)->TryGetStringField(TEXT("room_type"), Rect.RoomType);

		if (!(*RoomObj)->HasField(TEXT("x")) || !(*RoomObj)->HasField(TEXT("y")) ||
			!(*RoomObj)->HasField(TEXT("width")) || !(*RoomObj)->HasField(TEXT("height")))
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("rooms[%d] missing x, y, width, or height"), i));
		}

		Rect.X = static_cast<int32>((*RoomObj)->GetNumberField(TEXT("x")));
		Rect.Y = static_cast<int32>((*RoomObj)->GetNumberField(TEXT("y")));
		Rect.Width = static_cast<int32>((*RoomObj)->GetNumberField(TEXT("width")));
		Rect.Height = static_cast<int32>((*RoomObj)->GetNumberField(TEXT("height")));

		if (Rect.Width <= 0 || Rect.Height <= 0)
		{
			return FMonolithActionResult::Error(FString::Printf(TEXT("rooms[%d] has invalid dimensions"), i));
		}

		MaxX = FMath::Max(MaxX, Rect.X + Rect.Width);
		MaxY = FMath::Max(MaxY, Rect.Y + Rect.Height);
		RoomRects.Add(MoveTemp(Rect));
	}

	// Build the 2D grid (initialize to -1 = empty)
	TArray<TArray<int32>> Grid;
	Grid.SetNum(MaxY);
	for (int32 Y = 0; Y < MaxY; ++Y)
	{
		Grid[Y].SetNumZeroed(MaxX);
		for (int32 X = 0; X < MaxX; ++X)
		{
			Grid[Y][X] = -1;
		}
	}

	// Fill grid with room indices
	TArray<TSharedPtr<FJsonValue>> RoomDefs;

	for (int32 i = 0; i < RoomRects.Num(); ++i)
	{
		const FRoomRect& Rect = RoomRects[i];
		TArray<TSharedPtr<FJsonValue>> CellsArr;

		for (int32 Y = Rect.Y; Y < Rect.Y + Rect.Height; ++Y)
		{
			for (int32 X = Rect.X; X < Rect.X + Rect.Width; ++X)
			{
				if (Grid[Y][X] != -1)
				{
					return FMonolithActionResult::Error(FString::Printf(
						TEXT("rooms[%d] ('%s') overlaps with room at cell (%d,%d)"), i, *Rect.RoomId, X, Y));
				}
				Grid[Y][X] = i;

				TArray<TSharedPtr<FJsonValue>> Pair;
				Pair.Add(MakeShared<FJsonValueNumber>(X));
				Pair.Add(MakeShared<FJsonValueNumber>(Y));
				CellsArr.Add(MakeShared<FJsonValueArray>(Pair));
			}
		}

		// Build room definition JSON
		auto RoomDef = MakeShared<FJsonObject>();
		RoomDef->SetStringField(TEXT("room_id"), Rect.RoomId);
		RoomDef->SetStringField(TEXT("room_type"), Rect.RoomType);
		RoomDef->SetArrayField(TEXT("grid_cells"), CellsArr);
		RoomDefs.Add(MakeShared<FJsonValueObject>(RoomDef));
	}

	// Build grid JSON
	TArray<TSharedPtr<FJsonValue>> GridArr;
	for (int32 Y = 0; Y < MaxY; ++Y)
	{
		TArray<TSharedPtr<FJsonValue>> RowArr;
		for (int32 X = 0; X < MaxX; ++X)
		{
			RowArr.Add(MakeShared<FJsonValueNumber>(Grid[Y][X]));
		}
		GridArr.Add(MakeShared<FJsonValueArray>(RowArr));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetArrayField(TEXT("grid"), GridArr);
	Result->SetArrayField(TEXT("rooms"), RoomDefs);
	Result->SetNumberField(TEXT("grid_width"), MaxX);
	Result->SetNumberField(TEXT("grid_height"), MaxY);
	Result->SetNumberField(TEXT("cell_size"), CellSize);
	Result->SetNumberField(TEXT("room_count"), RoomRects.Num());

	return FMonolithActionResult::Success(Result);
}

#endif // WITH_GEOMETRYSCRIPT
