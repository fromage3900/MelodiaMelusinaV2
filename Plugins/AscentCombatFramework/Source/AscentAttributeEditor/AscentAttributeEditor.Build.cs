// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentAttributeEditor : ModuleRules
{
	public AscentAttributeEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new[]
		{
			"Core", 
			"CoreUObject", 
			"Engine", 
			"InputCore",
			"Projects",
			"Slate",
			"SlateCore",
			"ApplicationCore",
			"GameplayAbilities",
			"AscentAttributeGraphEditor",
		});
		
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UnrealEd",
			"GraphEditor",
			"BlueprintGraph",
			"AssetRegistry",
		});
	}
}