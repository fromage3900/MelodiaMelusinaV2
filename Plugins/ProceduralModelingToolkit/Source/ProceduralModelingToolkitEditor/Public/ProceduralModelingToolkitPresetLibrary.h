#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ProceduralModelingToolkitModifier.h"
#include "ProceduralModelingToolkitPresetLibrary.generated.h"

class UProceduralModelingToolkitModifierStack;

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitPresetModifier
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FString ModifierClassPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FName ModifierId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FProceduralModelingToolkitModifierParameters Parameters;
};

USTRUCT(BlueprintType)
struct FProceduralModelingToolkitPresetDocument
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	int32 Version = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FString ToolkitVersion = TEXT("0.1");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Preset")
	TArray<FProceduralModelingToolkitPresetModifier> Modifiers;
};

UCLASS()
class UProceduralModelingToolkitPresetLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Procedural Presets")
	static FString GetDefaultPresetDirectory();

	UFUNCTION(BlueprintCallable, Category = "Procedural Presets")
	static bool SavePreset(UProceduralModelingToolkitModifierStack* Stack, const FString& PresetPath, FString& OutSavedPath, FString& OutMessage);

	UFUNCTION(BlueprintCallable, Category = "Procedural Presets")
	static UProceduralModelingToolkitModifierStack* LoadPreset(const FString& PresetPath, UObject* Outer, FString& OutMessage);

	UFUNCTION(BlueprintCallable, Category = "Procedural Presets")
	static bool DuplicatePreset(const FString& SourcePresetPath, const FString& DestinationPresetPath, FString& OutSavedPath, FString& OutMessage);

	UFUNCTION(BlueprintCallable, Category = "Procedural Presets")
	static bool DeletePreset(const FString& PresetPath, FString& OutMessage);

private:
	static bool StackToDocument(const UProceduralModelingToolkitModifierStack* Stack, FProceduralModelingToolkitPresetDocument& OutDocument, FString& OutMessage);
	static UProceduralModelingToolkitModifierStack* DocumentToStack(const FProceduralModelingToolkitPresetDocument& Document, UObject* Outer, FString& OutMessage);
	static FString ResolvePresetPath(const FString& PresetPath);
};
