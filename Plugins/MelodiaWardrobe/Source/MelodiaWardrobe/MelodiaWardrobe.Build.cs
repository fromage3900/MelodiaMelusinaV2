// MelodiaWardrobe — Universal outfit collection + fashion gameplay.
// Re-host of the quarantined UMelodiaOutfitComponent algorithm (Decision 044).
// Depends on the game module BS_GodFile for the shared EMelodiaWardrobeSlot /
// FMelodiaNarrativeRecord vocabulary, and on MelodiaCore for the wallet API only.

using UnrealBuildTool;
using System.IO;

public class MelodiaWardrobe : ModuleRules
{
	public MelodiaWardrobe(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// Expose the game module's MelodiaIntegration folder so the wardrobe can
		// consume EMelodiaWardrobeSlot / FMelodiaNarrativeRecord directly.
		PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "../../../../Source/BS_GodFile/MelodiaIntegration"));

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"UMG",
			"Slate",
			"SlateCore",
			"Json",
			"JsonUtilities",
			"MelodiaCore",   // wallet (UMelodiaTokenWalletSubsystem) + EMelodiaSpellElement
			"BS_GodFile"     // EMelodiaWardrobeSlot, FMelodiaNarrativeRecord
		});
	}
}