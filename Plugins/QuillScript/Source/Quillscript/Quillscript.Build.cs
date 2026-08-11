// Copyright Bruno Caxito. All Rights Reserved.

using UnrealBuildTool;

public class Quillscript : ModuleRules
{
	public Quillscript(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new []
			{
				"Core"
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new []
			{
				"CoreUObject",
				"DeveloperSettings",
				"GameplayTags",
				"Engine",
				"Json",
				"Slate",
				"SlateCore",
				"UMG"
			}
		);

		// Include this module only on editor builds.
		if (Target.Type == TargetType.Editor)
			PrivateDependencyModuleNames.AddRange( new [] { "UnrealEd" } );
	}
}