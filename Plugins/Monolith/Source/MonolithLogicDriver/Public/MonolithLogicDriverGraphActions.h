#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithLogicDriverGraphActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Read (Phase 1)
	static FMonolithActionResult HandleGetSMStructure(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNodeDetails(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetNodeConnections(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindNodesByType(const TSharedPtr<FJsonObject>& Params);

	// Read (Phase 2)
	static FMonolithActionResult HandleFindNodesByClass(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetSMStatistics(const TSharedPtr<FJsonObject>& Params);

	// Write (Phase 2)
	static FMonolithActionResult HandleAddState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddTransition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddConduit(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddStateMachineNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddAnyStateNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetNodeProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetInitialState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetEndState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetNodeClass(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRenameNode(const TSharedPtr<FJsonObject>& Params);

	// Write (Phase 3)
	static FMonolithActionResult HandleMoveNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAutoArrangeGraph(const TSharedPtr<FJsonObject>& Params);

	// Compile (Phase 1)
	static FMonolithActionResult HandleCompileStateMachine(const TSharedPtr<FJsonObject>& Params);
};
