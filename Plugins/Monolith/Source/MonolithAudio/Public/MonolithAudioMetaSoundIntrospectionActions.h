#pragma once

#include "CoreMinimal.h"

#if WITH_METASOUND

class FMonolithToolRegistry;
struct FMonolithActionResult;

/**
 * MetaSound document-introspection action pack (read-only).
 *
 * Ported from PR #18 by @alakangas. Walks on-disk MetaSound asset state via
 * IMetaSoundDocumentInterface::GetConstDocument(), returning structured JSON for
 * graph pages, nodes, edges, variables, user-parameters, dependencies, and
 * validation diagnostics. NO mutation of asset state — pure read side.
 *
 * Distinct from FMonolithAudioMetaSoundActions (Builder API write-side, 25 actions);
 * both register into the same `audio` namespace. See plan
 * Docs/plans/2026-05-03-metasound-indexer-integration.md § 4 (Q1) for action-name
 * disambiguation rationale.
 */
class FMonolithAudioMetaSoundIntrospectionActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// 12 read-only document-introspection handlers (Phase 3 of the integration plan).
	static FMonolithActionResult HandleListMetaSounds(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListMetaSoundDocuments(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundDocument(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundSummary(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleInspectMetaSoundNodeInstance(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundDocumentConnections(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundDocumentVariables(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundUserParameters(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleSearchMetaSoundDocumentNodes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundInfo(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetMetaSoundDependencies(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleValidateMetaSound(const TSharedPtr<FJsonObject>& Params);
};

#endif // WITH_METASOUND
