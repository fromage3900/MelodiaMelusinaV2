#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASTagActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: Tag CRUD
	static FMonolithActionResult HandleAddGameplayTags(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetTagHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSearchTagUsage(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Productivity
	static FMonolithActionResult HandleScaffoldTagHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRenameTag(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveGameplayTags(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateTagConsistency(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Advanced
	static FMonolithActionResult HandleAuditTagNaming(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleExportTagHierarchy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleImportTagHierarchy(const TSharedPtr<FJsonObject>& Params);
};
