#include "MonolithMeshAutoVolumeActions.h"
#include "MonolithMeshSpatialRegistry.h"
#include "MonolithMeshUtils.h"
#include "MonolithToolRegistry.h"
#include "MonolithParamSchema.h"
#include "MonolithJsonUtils.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "AI/Navigation/NavLinkDefinition.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "UObject/UObjectGlobals.h"
#include "Builders/CubeBuilder.h"
#include "ActorFactories/ActorFactory.h"

// ============================================================================
// Helpers
// ============================================================================

namespace AutoVolumeHelpers
{
	/** Make a JSON array from a FVector */
	TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V)
	{
		TArray<TSharedPtr<FJsonValue>> Arr;
		Arr.Add(MakeShared<FJsonValueNumber>(V.X));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
		Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
		return Arr;
	}

	/** Parse a [x,y,z] array from JSON params */
	bool ParseVectorFromArray(const TArray<TSharedPtr<FJsonValue>>& Arr, FVector& Out)
	{
		if (Arr.Num() < 3) return false;
		Out.X = Arr[0]->AsNumber();
		Out.Y = Arr[1]->AsNumber();
		Out.Z = Arr[2]->AsNumber();
		return true;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FMonolithMeshAutoVolumeActions::RegisterActions(FMonolithToolRegistry& Registry)
{
	// 1. auto_volumes_for_building
	Registry.RegisterAction(TEXT("mesh"), TEXT("auto_volumes_for_building"),
		TEXT("Auto-spawn NavMesh, Audio, Trigger volumes and NavLinkProxies for a building in the spatial registry. "
			"Reads room/door/floor data from SP6, delegates to spawn_volume for each volume type."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshAutoVolumeActions::AutoVolumesForBuilding),
		FParamSchemaBuilder()
			.Required(TEXT("building_id"), TEXT("string"), TEXT("Building ID in the spatial registry"))
			.Optional(TEXT("block_id"), TEXT("string"), TEXT("Block ID (default: 'default')"), TEXT("default"))
			.Optional(TEXT("spawn_navmesh"), TEXT("boolean"), TEXT("Spawn NavMeshBoundsVolume covering the building"), TEXT("true"))
			.Optional(TEXT("spawn_audio"), TEXT("boolean"), TEXT("Spawn AudioVolumes per room with reverb sizing"), TEXT("true"))
			.Optional(TEXT("spawn_triggers"), TEXT("boolean"), TEXT("Spawn TriggerVolumes at building entrances"), TEXT("true"))
			.Optional(TEXT("spawn_nav_links"), TEXT("boolean"), TEXT("Spawn NavLinkProxies at doors for AI nav"), TEXT("true"))
			.Optional(TEXT("navmesh_margin"), TEXT("number"), TEXT("Extra margin around building for navmesh (cm)"), TEXT("200"))
			.Optional(TEXT("reverb_preset_small"), TEXT("string"), TEXT("Reverb preset name for small rooms (<15 m^2)"), TEXT("SmallRoom"))
			.Optional(TEXT("reverb_preset_medium"), TEXT("string"), TEXT("Reverb preset name for medium rooms (15-40 m^2)"), TEXT("MediumRoom"))
			.Optional(TEXT("reverb_preset_large"), TEXT("string"), TEXT("Reverb preset name for large rooms (>40 m^2)"), TEXT("LargeHall"))
			.Optional(TEXT("reverb_preset_corridor"), TEXT("string"), TEXT("Reverb preset name for corridors"), TEXT("Corridor"))
			.Optional(TEXT("trigger_tag"), TEXT("string"), TEXT("Tag to apply to trigger volumes"), TEXT("BuildingEntrance"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder (default: auto from building)"))
			.Optional(TEXT("build_navmesh"), TEXT("boolean"), TEXT("Trigger navmesh rebuild after spawning"), TEXT("false"))
			.Build());

	// 2. auto_volumes_for_block
	Registry.RegisterAction(TEXT("mesh"), TEXT("auto_volumes_for_block"),
		TEXT("Auto-spawn volumes for ALL buildings in a block, plus a block-level NavMeshBoundsVolume. "
			"Iterates buildings in the spatial registry block and calls auto_volumes_for_building for each."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshAutoVolumeActions::AutoVolumesForBlock),
		FParamSchemaBuilder()
			.Optional(TEXT("block_id"), TEXT("string"), TEXT("Block ID (default: 'default')"), TEXT("default"))
			.Optional(TEXT("build_navmesh"), TEXT("boolean"), TEXT("Trigger navmesh rebuild after all volumes"), TEXT("true"))
			.OptionalAssetPathWithDefault(TEXT("folder"), TEXT("Outliner folder base"), TEXT("CityBlock/Volumes"))
			.Optional(TEXT("spawn_navmesh"), TEXT("boolean"), TEXT("Spawn NavMeshBoundsVolumes per building"), TEXT("true"))
			.Optional(TEXT("spawn_audio"), TEXT("boolean"), TEXT("Spawn AudioVolumes per room"), TEXT("true"))
			.Optional(TEXT("spawn_triggers"), TEXT("boolean"), TEXT("Spawn TriggerVolumes at entrances"), TEXT("true"))
			.Optional(TEXT("spawn_nav_links"), TEXT("boolean"), TEXT("Spawn NavLinkProxies at doors"), TEXT("true"))
			.Optional(TEXT("navmesh_margin"), TEXT("number"), TEXT("Extra margin around block for navmesh (cm)"), TEXT("200"))
			.Optional(TEXT("reverb_preset_small"), TEXT("string"), TEXT("Reverb preset for small rooms"), TEXT("SmallRoom"))
			.Optional(TEXT("reverb_preset_medium"), TEXT("string"), TEXT("Reverb preset for medium rooms"), TEXT("MediumRoom"))
			.Optional(TEXT("reverb_preset_large"), TEXT("string"), TEXT("Reverb preset for large rooms"), TEXT("LargeHall"))
			.Optional(TEXT("reverb_preset_corridor"), TEXT("string"), TEXT("Reverb preset for corridors"), TEXT("Corridor"))
			.Optional(TEXT("trigger_tag"), TEXT("string"), TEXT("Tag for trigger volumes"), TEXT("BuildingEntrance"))
			.Build());

	// 3. spawn_nav_link
	Registry.RegisterAction(TEXT("mesh"), TEXT("spawn_nav_link"),
		TEXT("Spawn a NavLinkProxy between two world points for AI navigation across disconnected navmesh regions (doors, stairwells, gaps)."),
		FMonolithActionHandler::CreateStatic(&FMonolithMeshAutoVolumeActions::SpawnNavLink),
		FParamSchemaBuilder()
			.Required(TEXT("start"), TEXT("array"), TEXT("Start point [x, y, z] in world space"))
			.Required(TEXT("end"), TEXT("array"), TEXT("End point [x, y, z] in world space"))
			.Optional(TEXT("bidirectional"), TEXT("boolean"), TEXT("Two-way link (default: true)"), TEXT("true"))
			.Optional(TEXT("label"), TEXT("string"), TEXT("Actor label for the NavLinkProxy"))
			.OptionalAssetPath(TEXT("folder"), TEXT("Outliner folder path"))
			.Build());
}

// ============================================================================
// Reverb Preset Helper
// ============================================================================

FString FMonolithMeshAutoVolumeActions::DetermineReverbPreset(
	const FString& RoomType, float AreaSquareMeters,
	const FString& SmallPreset, const FString& MediumPreset,
	const FString& LargePreset, const FString& CorridorPreset)
{
	if (RoomType.Equals(TEXT("corridor"), ESearchCase::IgnoreCase) ||
		RoomType.Equals(TEXT("hallway"), ESearchCase::IgnoreCase))
	{
		return CorridorPreset;
	}

	if (AreaSquareMeters < 15.0f)  return SmallPreset;
	if (AreaSquareMeters < 40.0f)  return MediumPreset;
	return LargePreset;
}

// ============================================================================
// Building Bounds Helper
// ============================================================================

FBox FMonolithMeshAutoVolumeActions::ComputeBuildingBounds(const FSpatialBlock& Block, const FSpatialBuilding& Building)
{
	FBox Bounds(ForceInit);

	for (const auto& FloorPair : Building.FloorToRoomIds)
	{
		for (const FString& RoomId : FloorPair.Value)
		{
			const FSpatialRoom* Room = Block.Rooms.Find(RoomId);
			if (Room && Room->WorldBounds.IsValid)
			{
				Bounds += Room->WorldBounds;
			}
		}
	}

	return Bounds;
}

// ============================================================================
// Wall Direction Helper
// ============================================================================

FVector FMonolithMeshAutoVolumeActions::WallToDirection(const FString& Wall)
{
	if (Wall.Equals(TEXT("north"), ESearchCase::IgnoreCase)) return FVector(0, -1, 0);
	if (Wall.Equals(TEXT("south"), ESearchCase::IgnoreCase)) return FVector(0, 1, 0);
	if (Wall.Equals(TEXT("east"), ESearchCase::IgnoreCase))  return FVector(1, 0, 0);
	if (Wall.Equals(TEXT("west"), ESearchCase::IgnoreCase))  return FVector(-1, 0, 0);
	return FVector::ZeroVector;
}

// ============================================================================
// NavLinkProxy Spawner (dynamic class load — no AIModule compile dependency)
// ============================================================================

AActor* FMonolithMeshAutoVolumeActions::SpawnNavLinkActor(
	UWorld* World, const FVector& Location,
	const FVector& LeftPoint, const FVector& RightPoint,
	bool bBidirectional, const FString& Label, const FString& Folder)
{
	if (!World) return nullptr;

	// Dynamically load ANavLinkProxy class from AIModule
	static UClass* NavLinkProxyClass = nullptr;
	if (!NavLinkProxyClass)
	{
		NavLinkProxyClass = StaticLoadClass(AActor::StaticClass(), nullptr,
			TEXT("/Script/AIModule.NavLinkProxy"));
	}

	if (!NavLinkProxyClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("AutoVolume: Could not load ANavLinkProxy class. Is AIModule enabled?"));
		return nullptr;
	}

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AActor* LinkActor = World->SpawnActor(NavLinkProxyClass, &Location, nullptr, SpawnParams);
	if (!LinkActor)
	{
		return nullptr;
	}

	// Set PointLinks via FProperty reflection
	// PointLinks is a TArray<FNavigationLink> — we need to set Left/Right on element 0
	FArrayProperty* PointLinksProp = CastField<FArrayProperty>(
		NavLinkProxyClass->FindPropertyByName(TEXT("PointLinks")));

	if (PointLinksProp)
	{
		void* ArrayPtr = PointLinksProp->ContainerPtrToValuePtr<void>(LinkActor);
		FScriptArrayHelper ArrayHelper(PointLinksProp, ArrayPtr);

		// Clear and add one element
		ArrayHelper.Resize(0);
		ArrayHelper.AddValue();

		void* ElementPtr = ArrayHelper.GetRawPtr(0);
		FStructProperty* InnerProp = CastField<FStructProperty>(PointLinksProp->Inner);

		if (InnerProp && ElementPtr)
		{
			UScriptStruct* LinkStruct = InnerProp->Struct;

			// Set Left (local space offset from actor location)
			FProperty* LeftProp = LinkStruct->FindPropertyByName(TEXT("Left"));
			if (LeftProp)
			{
				FVector LocalLeft = LeftPoint - Location;
				LeftProp->CopyCompleteValue(LeftProp->ContainerPtrToValuePtr<void>(ElementPtr), &LocalLeft);
			}

			// Set Right (local space offset from actor location)
			FProperty* RightProp = LinkStruct->FindPropertyByName(TEXT("Right"));
			if (RightProp)
			{
				FVector LocalRight = RightPoint - Location;
				RightProp->CopyCompleteValue(RightProp->ContainerPtrToValuePtr<void>(ElementPtr), &LocalRight);
			}

			// Set Direction via the base struct (FNavigationLinkBase)
			// Direction is an enum: 0 = BothWays, 1 = LeftToRight, 2 = RightToLeft
			FProperty* DirProp = LinkStruct->FindPropertyByName(TEXT("Direction"));
			if (DirProp)
			{
				uint8 DirValue = bBidirectional ? 0 : 1; // BothWays : LeftToRight
				FEnumProperty* EnumProp = CastField<FEnumProperty>(DirProp);
				FByteProperty* ByteProp = CastField<FByteProperty>(DirProp);

				if (EnumProp)
				{
					FNumericProperty* UnderlyingProp = EnumProp->GetUnderlyingProperty();
					void* ValuePtr = DirProp->ContainerPtrToValuePtr<void>(ElementPtr);
					UnderlyingProp->SetIntPropertyValue(ValuePtr, static_cast<int64>(DirValue));
				}
				else if (ByteProp)
				{
					void* ValuePtr = DirProp->ContainerPtrToValuePtr<void>(ElementPtr);
					ByteProp->SetIntPropertyValue(ValuePtr, static_cast<int64>(DirValue));
				}
			}
		}
	}

	// Set bSmartLinkIsRelevant = true via reflection
	FBoolProperty* SmartLinkProp = CastField<FBoolProperty>(
		NavLinkProxyClass->FindPropertyByName(TEXT("bSmartLinkIsRelevant")));
	if (SmartLinkProp)
	{
		SmartLinkProp->SetPropertyValue_InContainer(LinkActor, true);
	}

	// Label and folder
	if (!Label.IsEmpty())
	{
		LinkActor->SetActorLabel(Label);
	}

	if (!Folder.IsEmpty())
	{
		LinkActor->SetFolderPath(FName(*Folder));
	}
	else
	{
		LinkActor->SetFolderPath(FName(TEXT("Volumes/NavLinks")));
	}

	LinkActor->MarkPackageDirty();
	return LinkActor;
}

// ============================================================================
// 1. auto_volumes_for_building
// ============================================================================

FMonolithActionResult FMonolithMeshAutoVolumeActions::AutoVolumesForBuilding(const TSharedPtr<FJsonObject>& Params)
{
	FString BuildingId;
	if (!Params->TryGetStringField(TEXT("building_id"), BuildingId))
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: building_id"));
	}

	FString BlockId = TEXT("default");
	Params->TryGetStringField(TEXT("block_id"), BlockId);

	if (!FMonolithMeshSpatialRegistry::HasBlock(BlockId))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Block '%s' not found in spatial registry. Use load_block_descriptor or register_building first."), *BlockId));
	}

	FSpatialBlock& Block = FMonolithMeshSpatialRegistry::GetBlock(BlockId);
	const FSpatialBuilding* Building = Block.Buildings.Find(BuildingId);
	if (!Building)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Building '%s' not found in block '%s'. Registered buildings: %d"), *BuildingId, *BlockId, Block.Buildings.Num()));
	}

	// Parse options
	bool bSpawnNavmesh = true, bSpawnAudio = true, bSpawnTriggers = true, bSpawnNavLinks = true;
	Params->TryGetBoolField(TEXT("spawn_navmesh"), bSpawnNavmesh);
	Params->TryGetBoolField(TEXT("spawn_audio"), bSpawnAudio);
	Params->TryGetBoolField(TEXT("spawn_triggers"), bSpawnTriggers);
	Params->TryGetBoolField(TEXT("spawn_nav_links"), bSpawnNavLinks);

	double NavmeshMarginD = 200.0;
	Params->TryGetNumberField(TEXT("navmesh_margin"), NavmeshMarginD);
	float NavmeshMargin = static_cast<float>(NavmeshMarginD);

	FString SmallPreset = TEXT("SmallRoom"), MediumPreset = TEXT("MediumRoom");
	FString LargePreset = TEXT("LargeHall"), CorridorPreset = TEXT("Corridor");
	Params->TryGetStringField(TEXT("reverb_preset_small"), SmallPreset);
	Params->TryGetStringField(TEXT("reverb_preset_medium"), MediumPreset);
	Params->TryGetStringField(TEXT("reverb_preset_large"), LargePreset);
	Params->TryGetStringField(TEXT("reverb_preset_corridor"), CorridorPreset);

	FString TriggerTag = TEXT("BuildingEntrance");
	Params->TryGetStringField(TEXT("trigger_tag"), TriggerTag);

	FString BaseFolder;
	Params->TryGetStringField(TEXT("folder"), BaseFolder);
	if (BaseFolder.IsEmpty())
	{
		BaseFolder = FString::Printf(TEXT("CityBlock/%s/Volumes"), *BuildingId);
	}

	bool bBuildNavmesh = false;
	Params->TryGetBoolField(TEXT("build_navmesh"), bBuildNavmesh);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();

	// Track spawned volumes
	int32 NavmeshCount = 0, AudioCount = 0, TriggerCount = 0, NavLinkCount = 0;
	TArray<TSharedPtr<FJsonValue>> SpawnedActors;

	auto AddActorResult = [&SpawnedActors](const FString& ActorName, const FString& Type)
	{
		auto Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("actor_name"), ActorName);
		Entry->SetStringField(TEXT("type"), Type);
		SpawnedActors.Add(MakeShared<FJsonValueObject>(Entry));
	};

	// ---- NavMeshBoundsVolume covering the building ----
	if (bSpawnNavmesh)
	{
		FBox BuildingBounds = ComputeBuildingBounds(Block, *Building);
		if (BuildingBounds.IsValid)
		{
			FVector Center = BuildingBounds.GetCenter();
			FVector HalfExtent = BuildingBounds.GetExtent() + FVector(NavmeshMargin, NavmeshMargin, 100.0f);

			// spawn_volume doesn't support nav_mesh_bounds — spawn ANavMeshBoundsVolume directly
			FActorSpawnParameters SpawnParams;
			SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

			FVector SpawnLoc = Center;
			ANavMeshBoundsVolume* NavVol = Cast<ANavMeshBoundsVolume>(
				World->SpawnActor(ANavMeshBoundsVolume::StaticClass(), &SpawnLoc, nullptr, SpawnParams));

			if (NavVol)
			{
				// Create brush geometry
				UCubeBuilder* CubeBuilder = NewObject<UCubeBuilder>();
				CubeBuilder->X = HalfExtent.X * 2.0;
				CubeBuilder->Y = HalfExtent.Y * 2.0;
				CubeBuilder->Z = HalfExtent.Z * 2.0;
				UActorFactory::CreateBrushForVolumeActor(NavVol, CubeBuilder);

				NavVol->SetActorLabel(FString::Printf(TEXT("NavMesh_%s"), *BuildingId));
				NavVol->SetFolderPath(FName(*FString::Printf(TEXT("%s/NavMesh"), *BaseFolder)));
				NavVol->MarkPackageDirty();

				NavmeshCount++;
				AddActorResult(NavVol->GetActorNameOrLabel(), TEXT("NavMeshBoundsVolume"));
			}
		}
	}

	// ---- AudioVolumes per room ----
	if (bSpawnAudio)
	{
		for (const auto& FloorPair : Building->FloorToRoomIds)
		{
			int32 FloorIdx = FloorPair.Key;
			for (const FString& RoomId : FloorPair.Value)
			{
				const FSpatialRoom* Room = Block.Rooms.Find(RoomId);
				if (!Room || !Room->WorldBounds.IsValid) continue;

				FVector RoomCenter = Room->WorldBounds.GetCenter();
				FVector RoomExtent = Room->WorldBounds.GetExtent();

				// Compute room area in m²
				float AreaM2 = (Room->WorldBounds.Max.X - Room->WorldBounds.Min.X)
					* (Room->WorldBounds.Max.Y - Room->WorldBounds.Min.Y) / (100.0f * 100.0f);

				FString Preset = DetermineReverbPreset(Room->RoomType, AreaM2,
					SmallPreset, MediumPreset, LargePreset, CorridorPreset);

				auto AudioParams = MakeShared<FJsonObject>();
				AudioParams->SetStringField(TEXT("type"), TEXT("audio"));
				AudioParams->SetArrayField(TEXT("location"), AutoVolumeHelpers::VectorToJsonArray(RoomCenter));
				AudioParams->SetArrayField(TEXT("extent"), AutoVolumeHelpers::VectorToJsonArray(RoomExtent));
				AudioParams->SetStringField(TEXT("name"), FString::Printf(
					TEXT("Audio_%s_F%d_%s"), *BuildingId, FloorIdx, *RoomId));
				AudioParams->SetStringField(TEXT("folder"),
					FString::Printf(TEXT("%s/Audio"), *BaseFolder));

				// Audio properties: priority 1.0 (room-level)
				auto AudioProps = MakeShared<FJsonObject>();
				AudioProps->SetNumberField(TEXT("priority"), 1.0);
				AudioParams->SetObjectField(TEXT("properties"), AudioProps);

				FMonolithActionResult AudioResult = Registry.ExecuteAction(TEXT("mesh"), TEXT("spawn_volume"), AudioParams);
				if (AudioResult.bSuccess)
				{
					AudioCount++;
					FString ActorName;
					if (AudioResult.Result.IsValid())
					{
						AudioResult.Result->TryGetStringField(TEXT("actor_name"), ActorName);
					}
					AddActorResult(
						ActorName.IsEmpty() ? FString::Printf(TEXT("Audio_%s_F%d_%s"), *BuildingId, FloorIdx, *RoomId) : ActorName,
						FString::Printf(TEXT("AudioVolume (%s, %.0f m2, preset: %s)"), *Room->RoomType, AreaM2, *Preset));
				}
			}
		}
	}

	// ---- TriggerVolumes at building entrances (exterior doors) ----
	if (bSpawnTriggers)
	{
		for (const FString& DoorId : Building->ExteriorDoorIds)
		{
			const FSpatialDoor* Door = Block.Doors.Find(DoorId);
			if (!Door) continue;

			// Trigger volume at door position: door-width x 30cm depth x door-height
			FVector DoorExtent(Door->Width / 2.0f, 15.0f, Door->Height / 2.0f);

			// Orient the depth along the wall normal
			FVector WallDir = WallToDirection(Door->Wall);
			if (!WallDir.IsNearlyZero())
			{
				// Swap extent axes if door faces east/west (X-aligned wall)
				if (FMath::Abs(WallDir.X) > 0.5f)
				{
					DoorExtent = FVector(15.0f, Door->Width / 2.0f, Door->Height / 2.0f);
				}
			}

			// Position at door center, raised to half door height
			FVector TriggerLoc = Door->WorldPosition;
			if (TriggerLoc.Z == 0.0f)
			{
				TriggerLoc.Z += Door->Height / 2.0f;
			}

			auto TrigParams = MakeShared<FJsonObject>();
			TrigParams->SetStringField(TEXT("type"), TEXT("trigger"));
			TrigParams->SetArrayField(TEXT("location"), AutoVolumeHelpers::VectorToJsonArray(TriggerLoc));
			TrigParams->SetArrayField(TEXT("extent"), AutoVolumeHelpers::VectorToJsonArray(DoorExtent));
			TrigParams->SetStringField(TEXT("name"), FString::Printf(
				TEXT("TV_Enter_%s_%s"), *BuildingId, *DoorId));
			TrigParams->SetStringField(TEXT("folder"),
				FString::Printf(TEXT("%s/Triggers"), *BaseFolder));

			FMonolithActionResult TrigResult = Registry.ExecuteAction(TEXT("mesh"), TEXT("spawn_volume"), TrigParams);
			if (TrigResult.bSuccess)
			{
				TriggerCount++;
				FString ActorName;
				if (TrigResult.Result.IsValid())
				{
					TrigResult.Result->TryGetStringField(TEXT("actor_name"), ActorName);
				}
				AddActorResult(
					ActorName.IsEmpty() ? FString::Printf(TEXT("TV_Enter_%s_%s"), *BuildingId, *DoorId) : ActorName,
					FString::Printf(TEXT("TriggerVolume (entrance, tag: %s)"), *TriggerTag));
			}
		}
	}

	// ---- NavLinkProxies at all doors ----
	if (bSpawnNavLinks)
	{
		for (const auto& DoorPair : Block.Doors)
		{
			const FSpatialDoor& Door = DoorPair.Value;

			// Only process doors that belong to this building
			// Check if either room belongs to this building
			bool bBelongsToBuilding = false;
			for (const auto& FloorPair : Building->FloorToRoomIds)
			{
				for (const FString& RoomId : FloorPair.Value)
				{
					if (Door.RoomA == RoomId || Door.RoomB == RoomId)
					{
						bBelongsToBuilding = true;
						break;
					}
				}
				if (bBelongsToBuilding) break;
			}

			if (!bBelongsToBuilding) continue;

			// Compute nav link points: ~50cm offset from door center toward each room
			FVector DoorPos = Door.WorldPosition;
			FVector WallDir = WallToDirection(Door.Wall);
			FVector Perpendicular = WallDir.IsNearlyZero() ? FVector(1, 0, 0) : WallDir;

			// Left = 50cm toward RoomA (along wall normal), Right = 50cm toward RoomB (opposite)
			FVector LeftPoint = DoorPos + Perpendicular * 50.0f;
			FVector RightPoint = DoorPos - Perpendicular * 50.0f;

			// Ensure Z is at ground level (not mid-door)
			float GroundZ = DoorPos.Z;
			if (Door.Height > 0)
			{
				// Door world position may be at center or base — if it seems like center, adjust
				// The spatial registry stores position, not necessarily center
				GroundZ = DoorPos.Z;
			}
			LeftPoint.Z = GroundZ;
			RightPoint.Z = GroundZ;

			FString LinkLabel = FString::Printf(TEXT("NavLink_%s_%s"), *BuildingId, *DoorPair.Key);
			FString LinkFolder = FString::Printf(TEXT("%s/NavLinks"), *BaseFolder);

			AActor* NavLink = SpawnNavLinkActor(World, DoorPos, LeftPoint, RightPoint,
				/*bBidirectional=*/ true, LinkLabel, LinkFolder);

			if (NavLink)
			{
				NavLinkCount++;
				AddActorResult(NavLink->GetActorNameOrLabel(), TEXT("NavLinkProxy (door)"));
			}
		}
	}

	// ---- Optionally trigger navmesh build ----
	if (bBuildNavmesh && NavmeshCount > 0)
	{
		auto BuildParams = MakeShared<FJsonObject>();
		BuildParams->SetStringField(TEXT("mode"), TEXT("full"));
		Registry.ExecuteAction(TEXT("mesh"), TEXT("build_navmesh"), BuildParams);
	}

	// ---- Build result ----
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("building_id"), BuildingId);
	Result->SetStringField(TEXT("block_id"), BlockId);

	auto VolumeCounts = MakeShared<FJsonObject>();
	VolumeCounts->SetNumberField(TEXT("navmesh"), NavmeshCount);
	VolumeCounts->SetNumberField(TEXT("audio"), AudioCount);
	VolumeCounts->SetNumberField(TEXT("trigger"), TriggerCount);
	VolumeCounts->SetNumberField(TEXT("nav_links"), NavLinkCount);
	Result->SetObjectField(TEXT("volumes_spawned"), VolumeCounts);

	Result->SetNumberField(TEXT("total"), NavmeshCount + AudioCount + TriggerCount + NavLinkCount);
	Result->SetArrayField(TEXT("actors"), SpawnedActors);

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 2. auto_volumes_for_block
// ============================================================================

FMonolithActionResult FMonolithMeshAutoVolumeActions::AutoVolumesForBlock(const TSharedPtr<FJsonObject>& Params)
{
	FString BlockId = TEXT("default");
	Params->TryGetStringField(TEXT("block_id"), BlockId);

	if (!FMonolithMeshSpatialRegistry::HasBlock(BlockId))
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Block '%s' not found in spatial registry."), *BlockId));
	}

	FSpatialBlock& Block = FMonolithMeshSpatialRegistry::GetBlock(BlockId);
	if (Block.Buildings.Num() == 0)
	{
		return FMonolithActionResult::Error(FString::Printf(
			TEXT("Block '%s' has no buildings registered."), *BlockId));
	}

	bool bBuildNavmesh = true;
	Params->TryGetBoolField(TEXT("build_navmesh"), bBuildNavmesh);

	FString BaseFolder = TEXT("CityBlock/Volumes");
	Params->TryGetStringField(TEXT("folder"), BaseFolder);

	// Forward optional params
	bool bSpawnNavmesh = true, bSpawnAudio = true, bSpawnTriggers = true, bSpawnNavLinks = true;
	Params->TryGetBoolField(TEXT("spawn_navmesh"), bSpawnNavmesh);
	Params->TryGetBoolField(TEXT("spawn_audio"), bSpawnAudio);
	Params->TryGetBoolField(TEXT("spawn_triggers"), bSpawnTriggers);
	Params->TryGetBoolField(TEXT("spawn_nav_links"), bSpawnNavLinks);

	double NavmeshMarginD = 200.0;
	Params->TryGetNumberField(TEXT("navmesh_margin"), NavmeshMarginD);

	FString SmallPreset = TEXT("SmallRoom"), MediumPreset = TEXT("MediumRoom");
	FString LargePreset = TEXT("LargeHall"), CorridorPreset = TEXT("Corridor");
	Params->TryGetStringField(TEXT("reverb_preset_small"), SmallPreset);
	Params->TryGetStringField(TEXT("reverb_preset_medium"), MediumPreset);
	Params->TryGetStringField(TEXT("reverb_preset_large"), LargePreset);
	Params->TryGetStringField(TEXT("reverb_preset_corridor"), CorridorPreset);

	FString TriggerTag = TEXT("BuildingEntrance");
	Params->TryGetStringField(TEXT("trigger_tag"), TriggerTag);

	FMonolithToolRegistry& Registry = FMonolithToolRegistry::Get();
	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Track totals
	int32 BuildingsProcessed = 0;
	int32 TotalNavmesh = 0, TotalAudio = 0, TotalTrigger = 0, TotalNavLinks = 0;
	TArray<TSharedPtr<FJsonValue>> BuildingResults;

	// ---- Block-level NavMeshBoundsVolume covering ALL buildings ----
	if (bSpawnNavmesh)
	{
		FBox BlockBounds(ForceInit);
		for (const auto& BuildingPair : Block.Buildings)
		{
			FBox BBounds = ComputeBuildingBounds(Block, BuildingPair.Value);
			if (BBounds.IsValid)
			{
				BlockBounds += BBounds;
			}
		}

		if (BlockBounds.IsValid)
		{
			float Margin = static_cast<float>(NavmeshMarginD);
			FVector Center = BlockBounds.GetCenter();
			FVector HalfExtent = BlockBounds.GetExtent() + FVector(Margin, Margin, 100.0f);

			FActorSpawnParameters SpawnParams;
			SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

			FVector SpawnLoc = Center;
			ANavMeshBoundsVolume* BlockNavVol = Cast<ANavMeshBoundsVolume>(
				World->SpawnActor(ANavMeshBoundsVolume::StaticClass(), &SpawnLoc, nullptr, SpawnParams));

			if (BlockNavVol)
			{

				UCubeBuilder* CubeBuilder = NewObject<UCubeBuilder>();
				CubeBuilder->X = HalfExtent.X * 2.0;
				CubeBuilder->Y = HalfExtent.Y * 2.0;
				CubeBuilder->Z = HalfExtent.Z * 2.0;
				UActorFactory::CreateBrushForVolumeActor(BlockNavVol, CubeBuilder);

				BlockNavVol->SetActorLabel(FString::Printf(TEXT("NavMesh_Block_%s"), *BlockId));
				BlockNavVol->SetFolderPath(FName(*FString::Printf(TEXT("%s/NavMesh"), *BaseFolder)));
				BlockNavVol->MarkPackageDirty();

				TotalNavmesh++;
			}
		}
	}

	// ---- Per-building volumes ----
	for (const auto& BuildingPair : Block.Buildings)
	{
		const FString& BId = BuildingPair.Key;

		// Build params for auto_volumes_for_building — skip navmesh (block-level covers it)
		auto BuildingParams = MakeShared<FJsonObject>();
		BuildingParams->SetStringField(TEXT("building_id"), BId);
		BuildingParams->SetStringField(TEXT("block_id"), BlockId);
		BuildingParams->SetBoolField(TEXT("spawn_navmesh"), false); // Block-level covers it
		BuildingParams->SetBoolField(TEXT("spawn_audio"), bSpawnAudio);
		BuildingParams->SetBoolField(TEXT("spawn_triggers"), bSpawnTriggers);
		BuildingParams->SetBoolField(TEXT("spawn_nav_links"), bSpawnNavLinks);
		BuildingParams->SetBoolField(TEXT("build_navmesh"), false); // Build once at end
		BuildingParams->SetStringField(TEXT("folder"), FString::Printf(TEXT("%s/%s/Volumes"), *BaseFolder, *BId));
		BuildingParams->SetStringField(TEXT("reverb_preset_small"), SmallPreset);
		BuildingParams->SetStringField(TEXT("reverb_preset_medium"), MediumPreset);
		BuildingParams->SetStringField(TEXT("reverb_preset_large"), LargePreset);
		BuildingParams->SetStringField(TEXT("reverb_preset_corridor"), CorridorPreset);
		BuildingParams->SetStringField(TEXT("trigger_tag"), TriggerTag);

		FMonolithActionResult BuildingResult = Registry.ExecuteAction(TEXT("mesh"), TEXT("auto_volumes_for_building"), BuildingParams);

		if (BuildingResult.bSuccess && BuildingResult.Result.IsValid())
		{
			BuildingsProcessed++;

			// Sum up volume counts
			const TSharedPtr<FJsonObject>* VolObj = nullptr;
			if (BuildingResult.Result->TryGetObjectField(TEXT("volumes_spawned"), VolObj) && VolObj && (*VolObj).IsValid())
			{
				double N;
				if ((*VolObj)->TryGetNumberField(TEXT("audio"), N))     TotalAudio += static_cast<int32>(N);
				if ((*VolObj)->TryGetNumberField(TEXT("trigger"), N))   TotalTrigger += static_cast<int32>(N);
				if ((*VolObj)->TryGetNumberField(TEXT("nav_links"), N)) TotalNavLinks += static_cast<int32>(N);
			}

			auto BEntry = MakeShared<FJsonObject>();
			BEntry->SetStringField(TEXT("building_id"), BId);
			BEntry->SetBoolField(TEXT("success"), true);
			BuildingResults.Add(MakeShared<FJsonValueObject>(BEntry));
		}
		else
		{
			auto BEntry = MakeShared<FJsonObject>();
			BEntry->SetStringField(TEXT("building_id"), BId);
			BEntry->SetBoolField(TEXT("success"), false);
			BEntry->SetStringField(TEXT("error"), BuildingResult.ErrorMessage);
			BuildingResults.Add(MakeShared<FJsonValueObject>(BEntry));
		}
	}

	// ---- Trigger navmesh build at the end ----
	if (bBuildNavmesh && TotalNavmesh > 0)
	{
		auto BuildParams = MakeShared<FJsonObject>();
		BuildParams->SetStringField(TEXT("mode"), TEXT("full"));
		Registry.ExecuteAction(TEXT("mesh"), TEXT("build_navmesh"), BuildParams);
	}

	// ---- Build result ----
	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("block_id"), BlockId);
	Result->SetNumberField(TEXT("buildings_processed"), BuildingsProcessed);
	Result->SetNumberField(TEXT("buildings_total"), Block.Buildings.Num());

	auto TotalCounts = MakeShared<FJsonObject>();
	TotalCounts->SetNumberField(TEXT("navmesh"), TotalNavmesh);
	TotalCounts->SetNumberField(TEXT("audio"), TotalAudio);
	TotalCounts->SetNumberField(TEXT("trigger"), TotalTrigger);
	TotalCounts->SetNumberField(TEXT("nav_links"), TotalNavLinks);
	Result->SetObjectField(TEXT("total_volumes"), TotalCounts);

	Result->SetNumberField(TEXT("total"),
		TotalNavmesh + TotalAudio + TotalTrigger + TotalNavLinks);
	Result->SetArrayField(TEXT("buildings"), BuildingResults);

	if (bBuildNavmesh && TotalNavmesh > 0)
	{
		Result->SetBoolField(TEXT("navmesh_built"), true);
	}

	return FMonolithActionResult::Success(Result);
}

// ============================================================================
// 3. spawn_nav_link
// ============================================================================

FMonolithActionResult FMonolithMeshAutoVolumeActions::SpawnNavLink(const TSharedPtr<FJsonObject>& Params)
{
	// Parse start point
	const TArray<TSharedPtr<FJsonValue>>* StartArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("start"), StartArr) || !StartArr)
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: start (array of 3 numbers)"));
	}
	FVector StartPoint;
	if (!AutoVolumeHelpers::ParseVectorFromArray(*StartArr, StartPoint))
	{
		return FMonolithActionResult::Error(TEXT("Invalid start: expected [x, y, z]"));
	}

	// Parse end point
	const TArray<TSharedPtr<FJsonValue>>* EndArr = nullptr;
	if (!Params->TryGetArrayField(TEXT("end"), EndArr) || !EndArr)
	{
		return FMonolithActionResult::Error(TEXT("Missing required param: end (array of 3 numbers)"));
	}
	FVector EndPoint;
	if (!AutoVolumeHelpers::ParseVectorFromArray(*EndArr, EndPoint))
	{
		return FMonolithActionResult::Error(TEXT("Invalid end: expected [x, y, z]"));
	}

	bool bBidirectional = true;
	Params->TryGetBoolField(TEXT("bidirectional"), bBidirectional);

	FString Label;
	Params->TryGetStringField(TEXT("label"), Label);

	FString Folder;
	Params->TryGetStringField(TEXT("folder"), Folder);

	UWorld* World = MonolithMeshUtils::GetEditorWorld();
	if (!World)
	{
		return FMonolithActionResult::Error(TEXT("No editor world available"));
	}

	// Spawn at midpoint between start and end
	FVector MidPoint = (StartPoint + EndPoint) * 0.5f;

	AActor* NavLink = SpawnNavLinkActor(World, MidPoint, StartPoint, EndPoint,
		bBidirectional, Label, Folder);

	if (!NavLink)
	{
		return FMonolithActionResult::Error(TEXT("Failed to spawn NavLinkProxy. Ensure AIModule is enabled in your project."));
	}

	auto Result = MakeShared<FJsonObject>();
	Result->SetStringField(TEXT("actor_name"), NavLink->GetActorNameOrLabel());
	Result->SetArrayField(TEXT("start"), AutoVolumeHelpers::VectorToJsonArray(StartPoint));
	Result->SetArrayField(TEXT("end"), AutoVolumeHelpers::VectorToJsonArray(EndPoint));
	Result->SetBoolField(TEXT("bidirectional"), bBidirectional);

	return FMonolithActionResult::Success(Result);
}
