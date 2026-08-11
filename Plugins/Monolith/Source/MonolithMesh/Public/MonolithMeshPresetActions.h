#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 20: Genre Preset System (8 actions)
 * Make Monolith's horror-specific systems genre-agnostic via JSON preset authoring.
 * All operations are pure JSON file I/O — no UE-specific APIs beyond file read/write.
 *
 * Storytelling pattern actions:
 *   list_storytelling_patterns   — List built-in + user-created patterns
 *   create_storytelling_pattern  — Author new pattern JSON
 *
 * Acoustic profile actions:
 *   list_acoustic_profiles       — List built-in + user-created acoustic profiles
 *   create_acoustic_profile      — Author acoustic property set for a genre
 *
 * Tension profile actions:
 *   create_tension_profile       — Define tension scoring weights for a genre
 *
 * Genre preset bundle actions:
 *   list_genre_presets            — List all available preset packs
 *   export_genre_preset           — Bundle everything into single JSON
 *   import_genre_preset           — Load a genre preset pack with merge modes
 */
class FMonolithMeshPresetActions
{
public:
	/** Register all 8 preset actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Storytelling patterns ---
	static FMonolithActionResult ListStorytellingPatterns(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateStorytellingPattern(const TSharedPtr<FJsonObject>& Params);

	// --- Acoustic profiles ---
	static FMonolithActionResult ListAcousticProfiles(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateAcousticProfile(const TSharedPtr<FJsonObject>& Params);

	// --- Tension profiles ---
	static FMonolithActionResult CreateTensionProfile(const TSharedPtr<FJsonObject>& Params);

	// --- Genre preset bundles ---
	static FMonolithActionResult ListGenrePresets(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ExportGenrePreset(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ImportGenrePreset(const TSharedPtr<FJsonObject>& Params);

	// --- Directory helpers ---
	static FString GetPatternsDirectory();
	static FString GetAcousticProfilesDirectory();
	static FString GetTensionProfilesDirectory();
	static FString GetPresetsDirectory();
	static FString GetTemplatesDirectory();
	static FString GetPropKitsDirectory();

	// --- JSON I/O helpers ---
	static TSharedPtr<FJsonObject> LoadJsonFile(const FString& FilePath, FString& OutError);
	static bool SaveJsonFile(const FString& FilePath, const TSharedPtr<FJsonObject>& JsonObj, FString& OutError);
	static TArray<FString> ListJsonFiles(const FString& Directory);

	// --- Serialization helpers ---
	static TSharedPtr<FJsonObject> StorytellingElementToJson(const struct FStorytellingElement& Elem);
	static TSharedPtr<FJsonObject> StorytellingPatternToJson(const struct FStorytellingPattern& Pattern);
	static TSharedPtr<FJsonObject> AcousticPropsToJson(const FString& SurfaceName, float Absorption, float TransmissionLossdB, float FootstepLoudness);

	// --- Validation helpers ---
	static bool ValidateStorytellingPatternJson(const TSharedPtr<FJsonObject>& Json, FString& OutError);
	static bool ValidateAcousticProfileJson(const TSharedPtr<FJsonObject>& Json, FString& OutError);
	static bool ValidateTensionProfileJson(const TSharedPtr<FJsonObject>& Json, FString& OutError);
	static bool ValidateGenrePresetJson(const TSharedPtr<FJsonObject>& Json, FString& OutError);
};
