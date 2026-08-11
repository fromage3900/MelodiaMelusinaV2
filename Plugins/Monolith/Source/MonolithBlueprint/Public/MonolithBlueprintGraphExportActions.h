#pragma once
#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithBlueprintGraphExportActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

	// Phase 5C — Graph export/import/copy
	static FMonolithActionResult HandleExportGraph(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCopyNodes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateGraph(const TSharedPtr<FJsonObject>& Params);

	// Verification loop — prove a graph edit landed rather than trusting the
	// write call's success flag. See MONOLITH_GUIDE.md "Prove a graph edit landed".
	static FMonolithActionResult HandleGetGraphFingerprint(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAssertGraphMatches(const TSharedPtr<FJsonObject>& Params);
};
