// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AscentGASEditor : ModuleRules
{
    public AscentGASEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "UnrealEd",
            "GameplayAbilities",
            "GameplayTags",
           
            "Blutility"
        });

        PrivateDependencyModuleNames.AddRange(new string[] {
    "Engine",
    "UnrealEd",
    "UMGEditor",
    "Blutility",
    "CoreUObject",
    "InputCore",
    "BlueprintGraph",
    "EditorStyle",
    "EditorWidgets",
    "GraphEditor",
    "ToolMenus",
    "EditorFramework",
    "Projects",
    "ContentBrowser",
    "AssetTools",
    "WorkspaceMenuStructure",
    "ApplicationCore",
    "EditorSubsystem",
    "AscentGASRuntime",
    "AssetRegistry",
    "Slate",           
    "SlateCore",      
    "UMG"              
});
    }
}