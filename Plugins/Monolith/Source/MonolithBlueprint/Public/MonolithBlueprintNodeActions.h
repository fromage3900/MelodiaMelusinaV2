#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintNodeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	static FMonolithActionResult HandleAddNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConnectPins(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDisconnectPins(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetPinDefault(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetNodePosition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetNodeProperty(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBatchExecute(const TSharedPtr<FJsonObject>& Params);

	// Wave 3 — Discovery & Resolution
	static FMonolithActionResult HandleResolveNode(const TSharedPtr<FJsonObject>& Params);

	// Wave 4 — Bulk Node Operations
	static FMonolithActionResult HandleAddNodesBulk(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConnectPinsBulk(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetPinDefaultsBulk(const TSharedPtr<FJsonObject>& Params);

	// Wave 5 — Scaffolding & Templates
	static FMonolithActionResult HandleAddTimeline(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddEventNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddCommentNode(const TSharedPtr<FJsonObject>& Params);

	// Phase 3A — Timeline read/edit
	static FMonolithActionResult HandleGetTimelineData(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddTimelineTrack(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetTimelineKeys(const TSharedPtr<FJsonObject>& Params);

	// Wave 7 — Advanced
	static FMonolithActionResult HandlePromotePinToVariable(const TSharedPtr<FJsonObject>& Params);

	// Phase 1 (gap #11) — Cross-class property access (foreign-class VariableGet/Set)
	static FMonolithActionResult HandleAddPropertyAccess(const TSharedPtr<FJsonObject>& Params);

	// Genuine thread-safe Property Access — reflective UK2Node_PropertyAccess authoring.
	// Unlike add_property_access (which emits a foreign-member VariableGet with a self
	// pin, non-thread-safe), this spawns a real K2Node_PropertyAccess whose path-based
	// read is resolved thread-safe (or game-thread-cached) by the AnimBP property-access
	// compiler. The class is MinimalAPI/unlinkable, so it is created reflectively.
	static FMonolithActionResult HandleAddPropertyAccessNode(const TSharedPtr<FJsonObject>& Params);
};
