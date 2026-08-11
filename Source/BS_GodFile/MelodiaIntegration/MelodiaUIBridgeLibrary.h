#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaUIBridgeLibrary.generated.h"

/**
 * Convenience wrappers around UMelodiaUIBridgeSubsystem for any Blueprint
 * to show/hide Melodia battle UI without needing a subsystem reference.
 *
 * All functions route through the bridge subsystem's generic UUserWidget
 * variables -- no type compatibility issues with stock BP_BattleUI_C.
 */
UCLASS()
class BS_GODFILE_API UMelodiaUIBridgeLibrary final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static void ShowMelodiaBattleUI(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static void HideMelodiaBattleUI(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static void ToggleMelodiaBattleUI(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static bool CreateMelodiaBattleUI(const UObject* WorldContextObject, TSubclassOf<UUserWidget> WidgetClass);

	UFUNCTION(BlueprintCallable, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static void DestroyMelodiaBattleUI(const UObject* WorldContextObject);

	UFUNCTION(BlueprintPure, Category = "Melodia|UI|Bridge", meta = (WorldContext = "WorldContextObject"))
	static bool IsMelodiaUIActive(const UObject* WorldContextObject);
};
