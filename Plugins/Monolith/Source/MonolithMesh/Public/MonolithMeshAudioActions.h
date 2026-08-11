#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 8: Audio & Acoustics Actions (14 actions)
 * Material-aware spatial audio analysis, Sabine RT60 reverb estimation,
 * horror stealth mechanics, audio volume management.
 *
 * Read-Only (7): get_audio_volumes, get_surface_materials, estimate_footstep_sound,
 *   analyze_room_acoustics, analyze_sound_propagation, find_loud_surfaces, find_sound_paths
 * Horror AI (4): can_ai_hear_from, get_stealth_map, find_quiet_path, suggest_audio_volumes
 * Write (3): create_audio_volume, set_surface_type, create_surface_datatable
 */
class FMonolithMeshAudioActions
{
public:
	/** Register all 14 audio actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Read-Only ---
	static FMonolithActionResult GetAudioVolumes(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetSurfaceMaterials(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult EstimateFootstepSound(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeRoomAcoustics(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult AnalyzeSoundPropagation(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindLoudSurfaces(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindSoundPaths(const TSharedPtr<FJsonObject>& Params);

	// --- Horror AI ---
	static FMonolithActionResult CanAiHearFrom(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetStealthMap(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult FindQuietPath(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SuggestAudioVolumes(const TSharedPtr<FJsonObject>& Params);

	// --- Write ---
	static FMonolithActionResult CreateAudioVolume(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SetSurfaceType(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateSurfaceDataTable(const TSharedPtr<FJsonObject>& Params);
};
