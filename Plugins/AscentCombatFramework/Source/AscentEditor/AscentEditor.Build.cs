// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using UnrealBuildTool.Rules;

public class AscentEditor : ModuleRules
{
    public AscentEditor(ReadOnlyTargetRules Target)
        : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicIncludePaths.AddRange(
            new string[] {
                // ... add public include paths required here ...
            });

        PrivateIncludePaths.AddRange(
            new string[] {
                // ... add other private include paths required here ...
            });

        PublicDependencyModuleNames.AddRange(
            new string[] {
                "AscentEditorExtensions",
                "Core",
                "GameplayTags",
                "Blutility",
                "UMG",
                "UMGEditor",
                "UnrealEd",
                "Kismet",
                "AssetTools",
                "EditorSubsystem",
                "ScriptableEditorWidgets",
            });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Projects",
                "InputCore",
                "EditorFramework",
                "ToolMenus",
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "AnimGraph",
                "AnimGraphRuntime",
                "BlueprintGraph",
                "Persona",
                "AnimationEditMode",
                "AIFramework",
                "AscentCombatFramework",
                "CharacterController",
                "ActionsSystem",
                "AscentGASRuntime",
                "EditorScriptingUtilities",
                "AssetRegistry"
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {
                // ... add any modules that your module loads dynamically here ...
            });
    }
}