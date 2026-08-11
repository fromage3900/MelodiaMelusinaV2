// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).

#include "MonolithReflectionIntelSettings.h"

UMonolithReflectionIntelSettings::UMonolithReflectionIntelSettings()
{
	// Sensible Leviathan-corpus defaults. Indexer also supplies these as a
	// fallback when the array is empty, so authoring is optional.
	DecisionMarkdownRoots.Add(TEXT("Docs"));
	DecisionMarkdownRoots.Add(TEXT("Plugins/Monolith/Docs"));
	DecisionMarkdownRoots.Add(TEXT(".claude/rules"));

	// Phase 2 risk noise filter — default fragments that should be excluded
	// from co-change weighting. The fragments are substring-matched
	// case-insensitively against project-relative file paths.
	GitMiningNoiseFilter.Add(TEXT("CHANGELOG.md"));
	GitMiningNoiseFilter.Add(TEXT(".uplugin"));
	GitMiningNoiseFilter.Add(TEXT("Docs/plans/"));
	GitMiningNoiseFilter.Add(TEXT("Docs/testing/"));
}

const UMonolithReflectionIntelSettings* UMonolithReflectionIntelSettings::Get()
{
	return GetDefault<UMonolithReflectionIntelSettings>();
}
