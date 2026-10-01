// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

using UnrealBuildTool;

public class AscentAttributeGraphEditor : ModuleRules
{
	public AscentAttributeGraphEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new[]
		{
			"Core", 
			"CoreUObject", 
			"Engine", 
		});
		
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UnrealEd",
			"GraphEditor",
		});
	}
}