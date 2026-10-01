// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using System.IO;
using UnrealBuildTool;

public class AscentEditorExtensions : ModuleRules {
    public AscentEditorExtensions(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
                Path.Combine(ModuleDirectory, "Public")
            });

        PrivateIncludePaths.AddRange(
            new string[] {

            });

        PublicDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "GameplayTags",
                "UnrealEd",
                "Kismet",
                "AssetTools",
                "PlacementMode",
                "EditorSubsystem",
                "EditorStyle",
                "InputCore",
                "UMGEditor",
                "AssetRegistry",  
                "Projects"

            });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "AIFramework",
                "AscentCombatFramework",
                "AscentGASRuntime",
                "InventorySystem",
                "ActionsSystem",
                "Core",
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "DeveloperSettings",
                "EditorFramework",
                "UnrealEd",
                "Projects",
                "AssetRegistry",
                "AscentTeams",
                "Json"
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {

            });
    }
}
