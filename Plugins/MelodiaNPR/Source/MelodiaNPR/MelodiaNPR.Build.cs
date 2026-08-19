// MelodiaNPR — toon rendering + modular clothing blendshape sync (Decisions 037/044).
//
// Runtime-only on purpose. The toon applier drives a UMaterialInstanceDynamic rather
// than deriving from UMaterialInstanceConstant, so this module needs no UnrealEd
// dependency and survives cooking — which the `package_launch` gate requires.
//
// The wallet is deliberately NOT a dependency here: currency stays a single authority
// in MelodiaCore, reached through MelodiaWardrobe (Decision 020/029g).

using UnrealBuildTool;

public class MelodiaNPR : ModuleRules
{
	public MelodiaNPR(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Self-contained on purpose. The scaffold references MelodiaWardrobe only in
		// comments -- no includes, no symbols -- so declaring the dependency would chain
		// this module's build onto MelodiaWardrobe -> BS_GodFile for nothing. Add it back
		// the moment the clothing bridge actually consumes a cosmetic type.
		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine"
		});
	}
}
