#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaSaveSlotLibrary.generated.h"

/** Why a canonical load call ended the way it did. Lets a menu distinguish
 *  "no slot exists", "refused", and "loaded, narrative degraded" instead of
 *  collapsing all three into one false. */
UENUM(BlueprintType)
enum class EMelodiaLoadSlotResult : uint8
{
	/** No save file exists at the requested slot. */
	Missing UMETA(DisplayName = "Missing"),
	/** A slot exists but the load was refused (incompatible record, no game instance). */
	Refused UMETA(DisplayName = "Refused"),
	/** Loaded; the narrative record was restored. */
	LoadedNarrativeRestored UMETA(DisplayName = "Loaded, Narrative Restored"),
	/** Loaded; stock state restored but the narrative record could not be restored. */
	LoadedNarrativeDegraded UMETA(DisplayName = "Loaded, Narrative Degraded")
};

/** Thin menu-facing adapter for the stock JRPG save transaction. */
UCLASS()
class BS_GODFILE_API UMelodiaSaveSlotLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Save", meta=(WorldContext="WorldContextObject"))
	static bool HasCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, int32 UserIndex = 0);

	UFUNCTION(BlueprintCallable, Category="Melodia|Save", meta=(WorldContext="WorldContextObject"))
	static bool LoadCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, int32 UserIndex = 0);

	/** Typed load result: distinguishes missing slot, refused load, and loaded
	 *  with narrative restored vs degraded. Single code path shared with
	 *  LoadCanonicalJRPGSlot. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save", meta=(WorldContext="WorldContextObject"))
	static EMelodiaLoadSlotResult LoadCanonicalJRPGSlotDetailed(const UObject* WorldContextObject, const FString& SlotName, int32 UserIndex = 0);

	/** Creates the stock JRPG save object, assigns it to the active GameInstance, and writes the selected canonical slot. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Save", meta=(WorldContext="WorldContextObject"))
	static bool CreateCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, int32 UserIndex = 0);
};
