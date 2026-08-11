using System.IO;
using UnrealBuildTool;

public class MonolithNiagara : ModuleRules
{
	public MonolithNiagara(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"MonolithCore",
			"UnrealEd",
			"Niagara",
			"NiagaraCore",
			"NiagaraEditor",
			"NiagaraShader",
			"Json",
			"JsonUtilities",
			"AssetTools",
			"Slate",
			"SlateCore"
		});

		// WITH_NIAGARA_WIZARD_PRIVATE — gates the create_module_from_hlsl ParameterMap bridge,
		// which forward-declares the engine-PRIVATE NiagaraEditor symbols
		// UE::Niagara::Wizard::Utilities::AddReadParameterPin / AddWriteParameterPin (defined only
		// in NiagaraEditor/Private/Widgets/DataChannel/NiagaraDataChannelWizard.cpp — no public
		// header). Default ON for dev; MONOLITH_RELEASE_BUILD=1 forces it OFF so the engine-private
		// linkage never ships and the bridge falls back to the strict typed-pin path.
		//
		// NOTE: NiagaraEditor is already a hard PrivateDependency above — this only widens
		// PrivateIncludePaths into its Private folder, it adds NO new module dependency. Therefore
		// WITH_NIAGARA_WIZARD_PRIVATE / the wizard symbols must NOT be added to make_release.ps1's
		// $LeakSentinels (that list is for OPTIONAL-plugin deps with no guaranteed load order; this
		// is engine-private source of an already-hard-dep module, gated OFF in release builds).
		bool bReleaseBuild = System.Environment.GetEnvironmentVariable("MONOLITH_RELEASE_BUILD") == "1";
		if (bReleaseBuild)
		{
			PublicDefinitions.Add("WITH_NIAGARA_WIZARD_PRIVATE=0");
		}
		else
		{
			PublicDefinitions.Add("WITH_NIAGARA_WIZARD_PRIVATE=1");
			PrivateIncludePaths.AddRange(new string[]
			{
				Path.Combine(EngineDirectory, "Plugins/FX/Niagara/Source/NiagaraEditor/Private")
			});
		}
	}
}
