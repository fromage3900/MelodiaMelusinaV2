// Copyright (c) 2025 zolnoor. All rights reserved.

using UnrealBuildTool;

public class UEBlueprintMCP : ModuleRules
{
	public UEBlueprintMCP(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"Slate",
			"SlateCore",
			"InputCore",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UnrealEd",
			"EditorSubsystem",
			"BlueprintGraph",
			"Kismet",
			"KismetCompiler",
			"GraphEditor",
			"Json",
			"JsonUtilities",
			"Networking",
			"Sockets",
			"UMG",
			"UMGEditor",
			"EnhancedInput",
			"InputBlueprintNodes",
			"EditorScriptingUtilities",
			"AssetTools",
			"MaterialEditor",     // For UMaterialEditingLibrary and material expression manipulation
			"RenderCore",         // For material shader compilation
			"AnimGraph",          // For Animation Blueprint and State Machine graph editing
			"AnimGraphRuntime",   // For Skeletal Control and IK nodes
			"AudioEditor",        // For Sound Cue editor manipulation
			"MetasoundFrontend",  // For MetaSound graph definitions
			"MetasoundEngine",    // For MetaSound runtime integration
			"MetasoundGraphCore", // For MetaSound node connections
		});

		// Ensure proper RTTI/exceptions for crash handling
		bUseRTTI = true;
		bEnableExceptions = true;
	}
}
