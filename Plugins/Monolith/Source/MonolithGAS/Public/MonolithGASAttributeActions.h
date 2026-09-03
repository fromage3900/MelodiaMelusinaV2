#pragma once

#include "MonolithGASInternal.h"

class FMonolithGASAttributeActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Phase 1: Core CRUD
	static FMonolithActionResult HandleCreateAttributeSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddAttribute(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAttributeSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAttributeDefaults(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListAttributeSets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureAttributeClamping(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureMetaAttributes(const TSharedPtr<FJsonObject>& Params);

	// Phase 2: Productivity
	static FMonolithActionResult HandleCreateAttributeSetFromTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateAttributeInitDataTable(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateAttributeSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureAttributeReplication(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleLinkDataTableToASC(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleBulkEditAttributes(const TSharedPtr<FJsonObject>& Params);
	// Phase 3: Analysis
	static FMonolithActionResult HandleValidateAttributeSet(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindAttributeModifiers(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDiffAttributeSets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetAttributeDependencyGraph(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveAttribute(const TSharedPtr<FJsonObject>& Params);
	// Phase 4: Runtime
	static FMonolithActionResult HandleGetAttributeValue(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetAttributeValue(const TSharedPtr<FJsonObject>& Params);
};
