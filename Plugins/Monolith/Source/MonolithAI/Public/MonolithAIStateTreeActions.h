#pragma once

#include "MonolithAIInternal.h"

class FMonolithAIStateTreeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

#if WITH_STATETREE
private:
	// CRUD
	static FMonolithActionResult HandleCreateStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListStateTrees(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCompileStateTree(const TSharedPtr<FJsonObject>& Params);

	// Schema
	static FMonolithActionResult HandleSetSTSchema(const TSharedPtr<FJsonObject>& Params);

	// State management
	static FMonolithActionResult HandleAddSTState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSTState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRenameSTState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleMoveSTState(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetSTStateProperties(const TSharedPtr<FJsonObject>& Params);

	// Tasks
	static FMonolithActionResult HandleAddSTTask(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSTTask(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetSTTaskProperty(const TSharedPtr<FJsonObject>& Params);

	// Enter conditions
	static FMonolithActionResult HandleAddSTEnterCondition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSTEnterCondition(const TSharedPtr<FJsonObject>& Params);

	// Transitions
	static FMonolithActionResult HandleAddSTTransition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSTTransition(const TSharedPtr<FJsonObject>& Params);

	// Bindings
	static FMonolithActionResult HandleAddSTPropertyBinding(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSTPropertyBinding(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetSTBindings(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetSTBindableProperties(const TSharedPtr<FJsonObject>& Params);

	// Discovery
	static FMonolithActionResult HandleListSTTaskTypes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListSTConditionTypes(const TSharedPtr<FJsonObject>& Params);

	// Advanced: transition conditions, considerations, validation, extensions
	static FMonolithActionResult HandleAddSTTransitionCondition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSTConsideration(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureSTConsideration(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateStateTree(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListSTExtensionTypes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddSTExtension(const TSharedPtr<FJsonObject>& Params);

	// Declarative build, export, diagram, auto-layout
	static FMonolithActionResult HandleBuildStateTreeFromSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleExportSTSpec(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGenerateSTDiagram(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAutoArrangeST(const TSharedPtr<FJsonObject>& Params);
#endif
};
