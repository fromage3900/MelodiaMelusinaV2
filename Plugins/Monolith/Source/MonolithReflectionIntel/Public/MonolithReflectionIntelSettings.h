// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// API verification (per .claude/rules/always/ue57-api.md):
//   - `UDeveloperSettings` confirmed via source_query — lives in module
//     `DeveloperSettings` (NOT `Engine`). 14+ engine sites override
//     GetCategoryName() with the same `FName(TEXT("Plugins"))` pattern used here.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "MonolithReflectionIntelSettings.generated.h"

/**
 * Editor Preferences > Plugins > Monolith Reflection Intel.
 * Phase 1 surfaces the markdown decision-mining toggles.
 * Phase 2 (v0.17.0) adds risk-mining toggles — git co-change window, noise
 * filter, mass-commit file-count gate.
 */
UCLASS(config=MonolithSettings, defaultconfig, meta=(DisplayName="Monolith Reflection Intel"))
class MONOLITHREFLECTIONINTEL_API UMonolithReflectionIntelSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UMonolithReflectionIntelSettings();

	/** Cheap, allocation-free CDO accessor. */
	static const UMonolithReflectionIntelSettings* Get();

	// ----------------------------------------------------------------
	// Decision Mining (Phase 1 — v0.17.0)
	// ----------------------------------------------------------------

	/** Mine decision records from markdown corpora during indexing. */
	UPROPERTY(EditAnywhere, config, Category="Decision")
	bool bEnableDecisionMining = true;

	/** Minimum heuristic confidence to surface a record from list_decisions. */
	UPROPERTY(EditAnywhere, config, Category="Decision", meta=(ClampMin="0.0", ClampMax="1.0"))
	float DecisionMinConfidence = 0.6f;

	/**
	 * Markdown root paths the indexer scans. Each entry is resolved RELATIVE to
	 * the project root (FPaths::ProjectDir()) when not absolute. Empty array =
	 * sensible defaults: Docs/, Plugins/Monolith/Docs/, .claude/rules/.
	 */
	UPROPERTY(EditAnywhere, config, Category="Decision")
	TArray<FString> DecisionMarkdownRoots;

	// ----------------------------------------------------------------
	// Risk Mining (Phase 2 — v0.17.0)
	// ----------------------------------------------------------------

	/** Enable git co-change + hotspot + conditional-gate mining at index time. */
	UPROPERTY(EditAnywhere, config, Category="Risk")
	bool bEnableGitCoChangeMining = true;

	/** Co-change window size in commits — passed to `git log --max-count=N`. */
	UPROPERTY(EditAnywhere, config, Category="Risk", meta=(ClampMin="10", ClampMax="2000"))
	int32 MaxCoChangeWindowCommits = 200;

	/**
	 * File-path substrings whose hits are excluded from co-change pair
	 * counting. Default suppresses CHANGELOG / .uplugin / plan-doc thrash that
	 * otherwise dominates Monolith's nested-git history.
	 */
	UPROPERTY(EditAnywhere, config, Category="Risk")
	TArray<FString> GitMiningNoiseFilter;

	/**
	 * Skip commits touching more than N files. Mass-format / mass-rename /
	 * release commits otherwise poison co-change weights. Design-spec Q6.
	 */
	UPROPERTY(EditAnywhere, config, Category="Risk", meta=(ClampMin="5", ClampMax="200"))
	int32 MaxCommitFileCount = 20;

	// ----------------------------------------------------------------
	// CppReflect (Phase 3a — v0.17.0). UHT-artefact + IAssetRegistry only.
	// Phase 3b (deferred) adds tree-sitter for source-driven UCLASS sweeps
	// and the 2 native-tag tables; until then this section ships partial.
	// ----------------------------------------------------------------

	/**
	 * Include engine-plugin UHT artefacts in the scan. Default OFF — engine
	 * reflection footprint is large (~488K LOC); we mine project + Monolith
	 * plugins only unless the operator opts in. WISHLIST extension for
	 * Phase 3b: gate engine-plugin reflection behind a separate setting per
	 * design-spec risk row.
	 */
	UPROPERTY(EditAnywhere, config, Category="CppReflect")
	bool bIndexEnginePluginReflection = false;

	/**
	 * Include ENABLED project-plugin UHT artefacts in the scan. Default ON —
	 * this is the core value of the scan-scope expansion: cppreflect / network
	 * reflection then covers the whole project surface (e.g. InventorySystemX
	 * RPCs), not just the game module. Only plugins reporting
	 * EPluginLoadedFrom::Project are folded in, and only the editor target's
	 * Win64/UnrealEditor artefact tree under each plugin's base dir.
	 *
	 * Ignored when UHTArtefactRoot is set (explicit override replaces the
	 * auto-resolved root set).
	 */
	UPROPERTY(EditAnywhere, config, Category="CppReflect")
	bool bIndexProjectPluginReflection = true;

	/**
	 * Include ENABLED engine-installed MARKETPLACE-plugin UHT artefacts in the
	 * scan. Default OFF — gated because source-shipping marketplace plugins can
	 * be large (e.g. SMSystem / LogicDriver emit 90+ .gen.cpp). Only plugins
	 * reporting EPluginLoadedFrom::Engine whose on-disk base dir lives under the
	 * `/Plugins/Marketplace/` path segment are folded in; Epic built-in engine
	 * plugins are NEVER scanned regardless of this flag (engine reflection is
	 * owned by UE — no engine reindex).
	 *
	 * Ignored when UHTArtefactRoot is set (explicit override replaces the
	 * auto-resolved root set).
	 */
	UPROPERTY(EditAnywhere, config, Category="CppReflect")
	bool bIndexMarketplacePluginReflection = false;

	/**
	 * Override the UHT artefact root. Empty = auto-resolve via
	 * FPaths::ProjectIntermediateDir() / "Build" / "<Platform>" / ... at
	 * indexer runtime. Project-relative paths supported; absolute paths win.
	 *
	 * Tagged with v0.17.0 ergonomics EMonolithParamKind::DiskPath spirit —
	 * raw FString here, but MCP-surfaced params on the related actions are
	 * DiskPath-rewritten automatically.
	 */
	UPROPERTY(EditAnywhere, config, Category="CppReflect")
	FString UHTArtefactRoot;

	// ----------------------------------------------------------------
	// Network Replication Audit (Phase 4a — v0.17.0)
	// ----------------------------------------------------------------

	/** Enable the network-replication indexer at module load + reload. Off
	 *  disables the lazy bootstrap path; network_query actions still register
	 *  but their handlers return empty data. */
	UPROPERTY(EditAnywhere, config, Category="Network")
	bool bEnableNetworkReplicationAudit = true;

	// ----------------------------------------------------------------
	// Pipeline Composers (Phase 4a — v0.17.0)
	// ----------------------------------------------------------------

	/** Enable the pipeline_query composer surface. Off does NOT prevent
	 *  registration — handlers always register so the schema stays stable —
	 *  but composer fan-out into individual namespaces is skipped, returning
	 *  a minimal envelope. WISHLIST: Phase 4b will wire this through to a
	 *  registration-time gate. */
	UPROPERTY(EditAnywhere, config, Category="Network")
	bool bEnablePipelineComposers = true;

	// ----------------------------------------------------------------
	// UDeveloperSettings overrides
	// ----------------------------------------------------------------

	virtual FName GetCategoryName() const override { return TEXT("Plugins"); }
};
