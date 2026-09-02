// Gaea Tools Library — automation-friendly wrapper around the Gaea landscape importer.
// Added 2026-09-02: UGaeaSubsystem / UImporterPanelSettings are not exposed to the
// Python glue (unlike GaeaLandscapeComponent), so automation could not call the
// importer. This library carries only simple, cleanly-wrappable parameter types.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "GaeaToolsLibrary.generated.h"

class ALandscape;
class UMaterialInterface;

UCLASS()
class GAEAUETOOLSEDITOR_API UGaeaToolsLibrary final : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Create an ALandscape from Gaea export files (heightmap r16/png/raw + definition.json
	 * + optional W_* weightmap PNGs), mirroring UGaeaSubsystem::CreateLandscapeActor but
	 * callable from Python/Blueprint without the importer window.
	 * Returns the spawned landscape actor (nullptr on failure; check log for reason).
	 */
	UFUNCTION(BlueprintCallable, Category = "Gaea Tools")
	static ALandscape* CreateLandscapeFromGaeaFiles(
		const FString& HeightmapFile,
		const FString& DefinitionFile,
		const TArray<FString>& WeightmapFiles,
		const TArray<FName>& LayerNames,
		const FString& LayerInfoFolderPath,
		UMaterialInterface* LandscapeMaterial,
		FVector Location,
		bool bFlipYAxis,
		bool bWorldPartition);

	/** XY = ScaleX*100/Resolution, Z = Height*100/512 — the GaeaUnrealTools scale formula. */
	UFUNCTION(BlueprintPure, Category = "Gaea Tools")
	static FVector GetGaeaLandscapeScale(float ScaleX, float ScaleY, float Height, int32 Resolution);

	/** Z = Height*100/2 — the plugin's default landscape location Z. */
	UFUNCTION(BlueprintPure, Category = "Gaea Tools")
	static float GetGaeaLandscapeLocationZ(float Height);
};
