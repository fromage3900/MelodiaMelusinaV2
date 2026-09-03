// Copyright Bruno Caxito. All Rights Reserved.

using UnrealBuildTool;

public class QuillscriptEditor : ModuleRules
{
	public QuillscriptEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new []
			{
				"Core",
				"Quillscript",
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new []
			{
				"CoreUObject",
				"Blutility",
				"DesktopPlatform",
				"Engine",
				"Projects",
				"Slate",
				"SlateCore",
				"UMG",
				"UMGEditor",
				"UnrealEd"
			}
		);
	}
}