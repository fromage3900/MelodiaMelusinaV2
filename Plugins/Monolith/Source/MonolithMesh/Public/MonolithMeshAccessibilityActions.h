#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 6: Accessibility Analysis Actions (6 actions)
 * Path width validation, navigation complexity, visual contrast,
 * rest point spacing, interactive reach validation, and comprehensive reports.
 * P0 priority — this game serves hospice patients.
 */
class FMonolithMeshAccessibilityActions
{
public:
	/** Register all 6 accessibility actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult ValidatePathWidth(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ValidateNavigationComplexity(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeVisualContrast(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindRestPoints(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ValidateInteractiveReach(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GenerateAccessibilityReport(const TSharedPtr<FJsonObject>& Params);
};
