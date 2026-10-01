// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AscentComboGraphEditor : ModuleRules {
    public AscentComboGraphEditor(ReadOnlyTargetRules Target)
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
                "Core",
                "AGSGraphEditor",
                "GameplayTags",
                "UnrealEd",
                "AscentComboGraph",
                "AGSGraphRuntime",
                "UnrealEd", // Required for editor customizations
                "PropertyEditor", // Required for IDetailCustomization
                "InputCore", // For input events
                "Slate", // For Slate UI framework
                "SlateCore", // Core Slate module
                "EditorStyle", // For editor customization
                "GraphEditor", // For handling graph nodes and details
                "ApplicationCore" // For application-level functionality
                // ... add other public dependencies that you statically link with here ...
            });

        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                 "AscentComboGraph"
                // ... add private dependencies that you statically link with here ...
            });

        DynamicallyLoadedModuleNames.AddRange(
            new string[] {
                // ... add any modules that your module loads dynamically here ...
            });
    }
}
