#pragma once

#include "MonolithAIInternal.h"

class FMonolithAISmartObjectActions
{
public:
	static void RegisterActions(FMonolithToolRegistry& Registry);

#if WITH_SMARTOBJECTS
private:
	// Definition CRUD
	static FMonolithActionResult HandleCreateSmartObjectDefinition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetSmartObjectDefinition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListSmartObjectDefinitions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDeleteSmartObjectDefinition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleDuplicateSmartObjectDefinition(const TSharedPtr<FJsonObject>& Params);

	// Slot management
	static FMonolithActionResult HandleAddSOSlot(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSOSlot(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleConfigureSOSlot(const TSharedPtr<FJsonObject>& Params);

	// Behavior definitions
	static FMonolithActionResult HandleAddSOBehaviorDefinition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleRemoveSOBehaviorDefinition(const TSharedPtr<FJsonObject>& Params);

	// Tags
	static FMonolithActionResult HandleSetSOTags(const TSharedPtr<FJsonObject>& Params);

	// Component / Placement
	static FMonolithActionResult HandleAddSmartObjectComponent(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandlePlaceSmartObjectActor(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindSmartObjectsInLevel(const TSharedPtr<FJsonObject>& Params);

	// Utilities
	static FMonolithActionResult HandleValidateSmartObjectDefinition(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleCreateSOFromTemplate(const TSharedPtr<FJsonObject>& Params);

	// ── Helpers ──
	static class USmartObjectDefinition* LoadSODefinition(const TSharedPtr<FJsonObject>& Params, FString& OutAssetPath, FString& OutError);
	static TSharedPtr<FJsonObject> SlotToJson(const struct FSmartObjectSlotDefinition& Slot, int32 Index);
	static TSharedPtr<FJsonObject> DefinitionToJson(class USmartObjectDefinition* Def, const FString& AssetPath);
	static void ParseTagContainer(const TSharedPtr<FJsonObject>& Params, const FString& FieldName, struct FGameplayTagContainer& OutTags);
#endif // WITH_SMARTOBJECTS
};
