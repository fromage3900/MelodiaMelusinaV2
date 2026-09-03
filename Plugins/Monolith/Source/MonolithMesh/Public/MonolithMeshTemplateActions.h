#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * Phase 11: Room Templates & Mesh Validation (8 actions)
 * JSON-driven room templates for rapid blockout + game-readiness mesh validation.
 *
 * Template actions: list_room_templates, get_room_template, apply_room_template, create_room_template
 * Validation actions: validate_game_ready, suggest_lod_strategy, batch_validate, compare_lod_chain
 */
class FMonolithMeshTemplateActions
{
public:
	/** Register all 8 template + validation actions with the tool registry */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Template actions ---
	static FMonolithActionResult ListRoomTemplates(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult GetRoomTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult ApplyRoomTemplate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CreateRoomTemplate(const TSharedPtr<FJsonObject>& Params);

	// --- Validation actions ---
	static FMonolithActionResult ValidateGameReady(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult SuggestLodStrategy(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult BatchValidate(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult CompareLodChain(const TSharedPtr<FJsonObject>& Params);

	// --- Helpers ---

	/** Get the templates directory path (creates if missing) */
	static FString GetTemplatesDirectory();

	/** Load a template JSON file by name, returns nullptr and sets OutError on failure */
	static TSharedPtr<FJsonObject> LoadTemplate(const FString& TemplateName, FString& OutError);

	/** Save a JSON object as a template file */
	static bool SaveTemplate(const FString& TemplateName, const TSharedPtr<FJsonObject>& TemplateJson, FString& OutError);

	/** Parse a 3-element JSON array to FVector */
	static bool ParseJsonArrayToVector(const TArray<TSharedPtr<FJsonValue>>& Arr, FVector& Out);
};
