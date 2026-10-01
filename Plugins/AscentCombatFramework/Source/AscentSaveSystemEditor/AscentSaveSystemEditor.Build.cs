// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentSaveSystemEditor : ModuleRules
{
	public AscentSaveSystemEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"CoreUObject",
			"Engine",
			"Slate",
			"SlateCore",
			"EditorFramework",
			"UnrealEd",
			"LevelEditor",
			"ToolMenus",
			"AscentSaveSystem",
			"DeveloperSettings",
			"InputCore",
			"EditorStyle",
		});
	}
}
