using UnrealBuildTool;

public class ProceduralModelingToolkitEditor : ModuleRules
{
	public ProceduralModelingToolkitEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"AssetRegistry",
				"AssetTools",
				"CollectionManager",
				"EditorScriptingUtilities",
				"GeometryFramework",
				"GeometryScriptingCore",
				"Json",
				"JsonUtilities",
				"PCG",
				"Slate",
				"SlateCore",
				"ToolMenus",
				"UnrealEd",
			}
		);
	}
}
