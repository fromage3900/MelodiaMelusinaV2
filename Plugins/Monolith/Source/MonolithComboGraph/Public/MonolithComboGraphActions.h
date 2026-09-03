#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class FMonolithComboGraphActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// Read/Inspect
	static FMonolithActionResult HandleListComboGraphs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetComboGraphInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetComboNodeEffects(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateComboGraph(const TSharedPtr<FJsonObject>& Params);

	// Create/Modify
	static FMonolithActionResult HandleCreateComboGraph(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddComboNode(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAddComboEdge(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetComboNodeEffects(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSetComboNodeCues(const TSharedPtr<FJsonObject>& Params);

	// Scaffolding
	static FMonolithActionResult HandleCreateComboAbility(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleLinkAbilityToComboGraph(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleScaffoldComboFromMontages(const TSharedPtr<FJsonObject>& Params);

	// Layout
	static FMonolithActionResult HandleLayoutComboGraph(const TSharedPtr<FJsonObject>& Params);
};
