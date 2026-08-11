// SPDX-License-Identifier: MIT
// MonolithReflectionIntel — Phases 1–3a of Reflection Intelligence (v0.17.0).
// Hosts:
//   Phase 1 — markdown decision-record indexer + `decision_query` namespace.
//   Phase 2 — git co-change / hotspot / conditional-gate indexers + `risk_query`.
//   Phase 3a — UHT-artefact reflection reader + IAssetRegistry asset-graph
//              joiner + `cppreflect_query` namespace (5 actions). NO tree-sitter
//              in Phase 3a — Phase 3b (deferred) will add the 2 native-tag
//              tables + `list_native_tags` action via tree-sitter vendoring.
// No optional / sibling plugin deps; the module loads unconditionally.
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md.

using UnrealBuildTool;

public class MonolithReflectionIntel : ModuleRules
{
	public MonolithReflectionIntel(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"MonolithCore",
			"SQLiteCore",
			// `DeveloperSettings` is its OWN module (NOT part of Engine) — see
			// `.claude/rules/scoped/cpp-code.md` § Module Dependencies. Required
			// for the UDeveloperSettings-derived UMonolithReflectionIntelSettings.
			"DeveloperSettings",
			"Json",
			"JsonUtilities",
			"Projects",
			// Phase 3a additions — IAssetRegistry / FAssetData / FAssetIdentifier.
			// Verified UE 5.7 module name = "AssetRegistry"
			// (C:/Program Files (x86)/UE_5.7/Engine/Source/Runtime/AssetRegistry/AssetRegistry.Build.cs).
			// We do NOT depend on AssetTools — Phase 3a only READS the registry.
			"AssetRegistry",
			// Shared-handle fix (2026-05-29): borrow UMonolithSourceSubsystem's
			// already-open EngineSource.db handle instead of opening a second
			// handle (rejected by UE 5.7's single-open `unreal-fs` SQLite VFS).
			//   MonolithSource   — UMonolithSourceSubsystem + FMonolithSourceDatabase.
			//   UnrealEd         — GEditor (Editor.h).
			//   EditorSubsystem  — GEditor->GetEditorSubsystem<>(). Dependency
			//                      direction RI -> MonolithSource is non-circular
			//                      (MonolithSource never references RI).
			"MonolithSource",
			"UnrealEd",
			"EditorSubsystem"
		});
	}
}
