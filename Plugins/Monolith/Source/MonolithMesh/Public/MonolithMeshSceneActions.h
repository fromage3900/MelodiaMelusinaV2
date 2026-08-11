#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 2: Scene Manipulation Actions (8 actions)
 * Actor CRUD operations - spawn, move, duplicate, delete, query info.
 * Foundation for blockout system.
 */
class FMonolithMeshSceneActions
{
public:
	/** Register all 8 scene manipulation actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

	/** True when batch_execute is running — sub-actions skip their own undo transactions */
	static bool bBatchTransactionActive;

private:
	static FMonolithActionResult GetActorInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SpawnActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult MoveActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult DuplicateActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult DeleteActors(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GroupActors(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SetActorProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult BatchExecute(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AlignActors(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SnapToFloor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ManageFolders(const TSharedPtr<FJsonObject>& Params);
};
