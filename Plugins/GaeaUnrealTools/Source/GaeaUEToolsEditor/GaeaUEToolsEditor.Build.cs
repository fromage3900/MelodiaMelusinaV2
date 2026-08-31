using System.IO;
using UnrealBuildTool;

public class GaeaUEToolsEditor : ModuleRules
{
    public GaeaUEToolsEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        var EngineDir = Path.GetFullPath(base.Target.RelativeEnginePath);
        PublicSystemIncludePaths.AddRange(new string[]
        
        {
            Path.Combine(EngineDir, "Source/Editor/LandscapeEditor/Private")
            }
        );

        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core", "Landscape", "EditorStyle",
            }
        );

        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "CoreUObject",
                "Engine",
                "Slate",
                "SlateCore",
                "InputCore",
                "LevelEditor",
                "Projects",
                "MaterialEditor", 
                "Landscape", 
                "UnrealEd", 
                "ToolMenus", 
                "EditorFramework",
                "EditorSubsystem", 
                "LandscapeEditor",
                "Foliage",
                "Json",
                "JsonUtilities",
                "AssetRegistry", "EditorScriptingUtilities"
            }
        );
    }
}