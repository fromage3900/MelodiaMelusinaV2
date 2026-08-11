#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PCGScaleWorldEditorLibrary.generated.h"

/**
 * Editor-only bridge for the official UE PCG Level-to-Asset exporter.
 *
 * The exporter itself is a native static API and is not reflected to Python
 * in UE 5.8. Keeping this thin wrapper in the project lets proof-level text
 * injection call the official exporter without inventing a second asset path.
 */
UCLASS()
class BS_GODFILE_API UPCGScaleWorldEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Exports an authored level into a UPCGDataAsset package.
	 *
	 * WorldAssetPath is a long package/object path and DestinationPath is a
	 * content-browser directory. AssetName is accepted for a stable injection
	 * contract; UE's stock exporter derives the final object name as
	 * <WorldName>_PCG. Returns the saved package name, or an ERROR: string.
	 */
	UFUNCTION(BlueprintCallable, Category = "PCG|Scale World")
	static FString ExportLevelToPCGDataAsset(
		const FString& WorldAssetPath,
		const FString& DestinationPath,
		const FString& AssetName);
};
