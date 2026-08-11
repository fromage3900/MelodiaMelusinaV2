#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 22: Polish & Remaining (9 actions)
 * Quality-of-life, naming validation, proxy mesh generation, HLOD setup,
 * texture budget analysis, framing/composition scoring, monster reveal evaluation,
 * co-op balance placeholder, and integration hook stubs.
 */
class FMonolithMeshQualityActions
{
public:
	/** Register all 9 quality/polish actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Naming & Organization ---
	static FMonolithActionResult ValidateNamingConventions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult BatchRenameAssets(const TSharedPtr<FJsonObject>& Params);

	// --- Proxy & HLOD ---
	static FMonolithActionResult GenerateProxyMesh(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SetupHlod(const TSharedPtr<FJsonObject>& Params);

	// --- Texture Budget ---
	static FMonolithActionResult AnalyzeTextureBudget(const TSharedPtr<FJsonObject>& Params);

	// --- Composition & Horror ---
	static FMonolithActionResult AnalyzeFraming(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult EvaluateMonsterReveal(const TSharedPtr<FJsonObject>& Params);

	// --- Co-op & Integration Stubs ---
	static FMonolithActionResult AnalyzeCoOpBalance(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult IntegrationHooksStub(const TSharedPtr<FJsonObject>& Params);

	// --- Helpers ---
	static TArray<TSharedPtr<FJsonValue>> VectorToJsonArray(const FVector& V);
};
