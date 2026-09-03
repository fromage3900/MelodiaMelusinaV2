#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Core discovery and status tool implementations.
 * These are registered under the "monolith" namespace.
 */
class FMonolithCoreTools
{
public:
	/** Register all core tools with the registry */
	static void RegisterAll();

	// --- Action Handlers ---

	/** monolith_discover — List available namespaces and their actions */
	static FMonolithActionResult HandleDiscover(const TSharedPtr<FJsonObject>& Params);

	/** monolith_status — Server health, version, index status */
	static FMonolithActionResult HandleStatus(const TSharedPtr<FJsonObject>& Params);

	/** monolith_update — Check or install updates */
	static FMonolithActionResult HandleUpdate(const TSharedPtr<FJsonObject>& Params);

	/** monolith_reindex — Trigger full project re-index */
	static FMonolithActionResult HandleReindex(const TSharedPtr<FJsonObject>& Params);
};
