// Copyright 2024 Tore Lervik. All Rights Reserved.

using UnrealBuildTool;

public class MeshBlendEditor : ModuleRules
{
	public MeshBlendEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		PrivatePCHHeaderFile = "Private/MeshBlendEditorPrivatePCH.h";
		bUseUnity = false;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core", "Blutility", "Blutility", "UMG", "MeshBlend",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
				"UnrealEd",
				"ToolMenus",
				"MeshBlend",
				"Projects",
				"Blutility",
				"UMGEditor"
			}
		);
	}
}