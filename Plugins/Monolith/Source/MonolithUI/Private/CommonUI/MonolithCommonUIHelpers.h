// MonolithCommonUIHelpers.h
// Shared authoring / mutation / runtime helpers for the CommonUI action pack.
// All symbols gated on WITH_COMMONUI — file compiles to empty TU when CommonUI is absent.
#pragma once

#if WITH_COMMONUI

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
#include "Dom/JsonObject.h"

class UWidget;
class UWidgetBlueprint;

namespace MonolithCommonUI
{
	/**
	 * Pattern 1: Create a UObject-derived asset at /Game path.
	 * Handles unique-name check (errors on collision), CreatePackage, NewObject, save + dirty-mark.
	 * @param AssetClass   UCLASS of the asset to create (e.g. UCommonButtonStyle::StaticClass())
	 * @param PackagePath  Folder path, e.g. /Game/UI/Styles (no trailing slash, no asset name)
	 * @param AssetName    Asset name, no extension (e.g. "BS_Primary")
	 * @param bSkipSave    Skip SavePackage (useful for test rigs)
	 * @param OutAsset     On success, populated with the created UObject
	 * @return Success JSON { asset_path, asset_name, class } or error
	 */
	MONOLITHUI_API FMonolithActionResult CreateAsset(
		UClass* AssetClass,
		const FString& PackagePath,
		const FString& AssetName,
		bool bSkipSave,
		UObject*& OutAsset);

	/**
	 * Pattern 2: Load an existing WBP and locate a named widget inside its WidgetTree.
	 * Caller is responsible for compiling + saving the WBP after mutation.
	 * @param WbpPath      Asset path to the Widget Blueprint
	 * @param WidgetName   FName of the widget to find in the tree
	 * @param OutWbp       On success, loaded WBP pointer
	 * @param OutWidget    On success, found widget pointer
	 * @return Success or error JSON
	 */
	MONOLITHUI_API FMonolithActionResult LoadWidgetForMutation(
		const FString& WbpPath,
		const FName& WidgetName,
		UWidgetBlueprint*& OutWbp,
		UWidget*& OutWidget);

	/**
	 * Compile + save a WBP that has been mutated in-place. Pair with LoadWidgetForMutation.
	 */
	MONOLITHUI_API FMonolithActionResult CompileAndSaveWidgetBlueprint(UWidgetBlueprint* Wbp);

	/**
	 * Pattern 3: Invoke a UFUNCTION on a runtime target via UObject::ProcessEvent.
	 * JSON params are marshalled onto the function's stack frame. Only works in editor-time / PIE.
	 * @param Target       UObject whose class exposes the UFUNCTION
	 * @param FunctionName Name of the function
	 * @param ParamsJson   JSON object of {name: value} for the function's named parameters
	 * @param OutResult    On success, return-value JSON (empty if function is void)
	 * @return Success or error
	 */
	MONOLITHUI_API FMonolithActionResult InvokeRuntimeFunction(
		UObject* Target,
		const FName& FunctionName,
		const TSharedPtr<FJsonObject>& ParamsJson,
		TSharedPtr<FJsonObject>& OutResult);

	/**
	 * Set an FProperty on a container object from a JSON value.
	 * Handles primitive types via ImportText_Direct, + special cases for:
	 *   - FLinearColor / FColor (nested struct)
	 *   - FMargin (nested struct)
	 *   - FSlateFontInfo (object ref + named fields — cannot ImportText reliably)
	 *   - FSlateBrush (ResourceObject + named fields — cannot ImportText reliably)
	 *   - TSubclassOf<T> (class path string)
	 * @return true on success, false on type mismatch or parse failure
	 */
	MONOLITHUI_API bool SetPropertyFromJson(
		UObject* Container,
		FProperty* Property,
		const TSharedPtr<FJsonValue>& JsonValue);

	/**
	 * Extract the widget blueprint path from action params.
	 * Accepts both "wbp_path" (CommonUI convention) and "asset_path" (base UMG convention) as aliases.
	 * Returns empty string if neither field is present.
	 */
	inline FString GetWbpPath(const TSharedPtr<FJsonObject>& Params)
	{
		FString Path;
		if (Params.IsValid())
		{
			if (!Params->TryGetStringField(TEXT("wbp_path"), Path))
			{
				Params->TryGetStringField(TEXT("asset_path"), Path);
			}
		}
		return Path;
	}

	/**
	 * Return the world used for runtime (PIE) actions. Returns nullptr outside PIE.
	 * Use at handler entry for [RUNTIME] actions: nullptr → FMonolithActionResult::Error(...).
	 */
	MONOLITHUI_API UWorld* GetPIEWorld();
}

#endif // WITH_COMMONUI
