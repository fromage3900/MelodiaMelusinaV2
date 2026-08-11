#include "ProceduralModelingToolkitPresetLibrary.h"

#include "ProceduralModelingToolkitEditorModule.h"
#include "ProceduralModelingToolkitModifierStack.h"

#include "JsonObjectConverter.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

FString UProceduralModelingToolkitPresetLibrary::GetDefaultPresetDirectory()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("ProceduralModelingToolkit"), TEXT("Presets"));
}

bool UProceduralModelingToolkitPresetLibrary::SavePreset(UProceduralModelingToolkitModifierStack* Stack, const FString& PresetPath, FString& OutSavedPath, FString& OutMessage)
{
	FProceduralModelingToolkitPresetDocument Document;
	if (!StackToDocument(Stack, Document, OutMessage))
	{
		return false;
	}

	OutSavedPath = ResolvePresetPath(PresetPath);
	Document.Name = FPaths::GetBaseFilename(OutSavedPath);

	FString Json;
	if (!FJsonObjectConverter::UStructToJsonObjectString(Document, Json))
	{
		OutMessage = TEXT("Failed to serialize preset document to JSON.");
		return false;
	}

	const FString PresetDirectory = FPaths::GetPath(OutSavedPath);
	if (!IFileManager::Get().MakeDirectory(*PresetDirectory, true))
	{
		OutMessage = FString::Printf(TEXT("Failed to create preset directory '%s'."), *PresetDirectory);
		return false;
	}

	if (!FFileHelper::SaveStringToFile(Json, *OutSavedPath))
	{
		OutMessage = FString::Printf(TEXT("Failed to save preset '%s'."), *OutSavedPath);
		return false;
	}

	Stack->PresetSourcePath = OutSavedPath;
	OutMessage = FString::Printf(TEXT("Saved preset '%s'."), *OutSavedPath);
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("%s"), *OutMessage);
	return true;
}

UProceduralModelingToolkitModifierStack* UProceduralModelingToolkitPresetLibrary::LoadPreset(const FString& PresetPath, UObject* Outer, FString& OutMessage)
{
	const FString ResolvedPath = ResolvePresetPath(PresetPath);

	FString Json;
	if (!FFileHelper::LoadFileToString(Json, *ResolvedPath))
	{
		OutMessage = FString::Printf(TEXT("Failed to load preset '%s'."), *ResolvedPath);
		return nullptr;
	}

	FProceduralModelingToolkitPresetDocument Document;
	if (!FJsonObjectConverter::JsonObjectStringToUStruct(Json, &Document, 0, 0))
	{
		OutMessage = FString::Printf(TEXT("Failed to parse preset JSON '%s'."), *ResolvedPath);
		return nullptr;
	}

	UProceduralModelingToolkitModifierStack* Stack = DocumentToStack(Document, Outer ? Outer : GetTransientPackageAsObject(), OutMessage);
	if (!Stack)
	{
		return nullptr;
	}

	Stack->PresetSourcePath = ResolvedPath;
	OutMessage = FString::Printf(TEXT("Loaded preset '%s'."), *ResolvedPath);
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("%s"), *OutMessage);
	return Stack;
}

bool UProceduralModelingToolkitPresetLibrary::DuplicatePreset(const FString& SourcePresetPath, const FString& DestinationPresetPath, FString& OutSavedPath, FString& OutMessage)
{
	const FString SourcePath = ResolvePresetPath(SourcePresetPath);
	OutSavedPath = ResolvePresetPath(DestinationPresetPath);

	if (!FPaths::FileExists(SourcePath))
	{
		OutMessage = FString::Printf(TEXT("Source preset does not exist: '%s'."), *SourcePath);
		return false;
	}

	const FString DestinationDirectory = FPaths::GetPath(OutSavedPath);
	if (!IFileManager::Get().MakeDirectory(*DestinationDirectory, true))
	{
		OutMessage = FString::Printf(TEXT("Failed to create preset directory '%s'."), *DestinationDirectory);
		return false;
	}

	if (!IFileManager::Get().Copy(*OutSavedPath, *SourcePath, true, true))
	{
		OutMessage = FString::Printf(TEXT("Failed to duplicate preset '%s' to '%s'."), *SourcePath, *OutSavedPath);
		return false;
	}

	OutMessage = FString::Printf(TEXT("Duplicated preset '%s' to '%s'."), *SourcePath, *OutSavedPath);
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("%s"), *OutMessage);
	return true;
}

bool UProceduralModelingToolkitPresetLibrary::DeletePreset(const FString& PresetPath, FString& OutMessage)
{
	const FString ResolvedPath = ResolvePresetPath(PresetPath);
	if (!FPaths::FileExists(ResolvedPath))
	{
		OutMessage = FString::Printf(TEXT("Preset does not exist: '%s'."), *ResolvedPath);
		return false;
	}

	if (!IFileManager::Get().Delete(*ResolvedPath, false, true))
	{
		OutMessage = FString::Printf(TEXT("Failed to delete preset '%s'."), *ResolvedPath);
		return false;
	}

	OutMessage = FString::Printf(TEXT("Deleted preset '%s'."), *ResolvedPath);
	UE_LOG(LogProceduralModelingToolkit, Log, TEXT("%s"), *OutMessage);
	return true;
}

bool UProceduralModelingToolkitPresetLibrary::StackToDocument(const UProceduralModelingToolkitModifierStack* Stack, FProceduralModelingToolkitPresetDocument& OutDocument, FString& OutMessage)
{
	if (!Stack)
	{
		OutMessage = TEXT("Cannot save preset: modifier stack is null.");
		return false;
	}

	OutDocument.Version = Stack->Version;
	OutDocument.Modifiers.Reset();

	for (const UProceduralModelingToolkitModifier* Modifier : Stack->Modifiers)
	{
		if (!Modifier)
		{
			continue;
		}

		FProceduralModelingToolkitPresetModifier PresetModifier;
		PresetModifier.ModifierClassPath = Modifier->GetClass()->GetPathName();
		PresetModifier.bEnabled = Modifier->bEnabled;
		PresetModifier.ModifierId = Modifier->ModifierId;
		PresetModifier.DisplayName = Modifier->DisplayName;
		PresetModifier.Parameters = Modifier->Parameters;
		OutDocument.Modifiers.Add(PresetModifier);
	}

	return true;
}

UProceduralModelingToolkitModifierStack* UProceduralModelingToolkitPresetLibrary::DocumentToStack(const FProceduralModelingToolkitPresetDocument& Document, UObject* Outer, FString& OutMessage)
{
	if (Document.Version <= 0)
	{
		OutMessage = FString::Printf(TEXT("Unsupported preset version %d."), Document.Version);
		return nullptr;
	}

	UProceduralModelingToolkitModifierStack* Stack = NewObject<UProceduralModelingToolkitModifierStack>(Outer ? Outer : GetTransientPackageAsObject(), NAME_None, RF_Transactional);
	Stack->Version = Document.Version;

	for (const FProceduralModelingToolkitPresetModifier& PresetModifier : Document.Modifiers)
	{
		UClass* ModifierClass = StaticLoadClass(UProceduralModelingToolkitModifier::StaticClass(), nullptr, *PresetModifier.ModifierClassPath);
		if (!ModifierClass)
		{
			OutMessage = FString::Printf(TEXT("Preset references unknown modifier class '%s'."), *PresetModifier.ModifierClassPath);
			return nullptr;
		}

		UProceduralModelingToolkitModifier* Modifier = Stack->AddModifier(ModifierClass);
		if (!Modifier)
		{
			OutMessage = FString::Printf(TEXT("Failed to create modifier '%s' while loading preset."), *PresetModifier.ModifierClassPath);
			return nullptr;
		}

		Modifier->bEnabled = PresetModifier.bEnabled;
		Modifier->ModifierId = PresetModifier.ModifierId;
		Modifier->DisplayName = PresetModifier.DisplayName;
		Modifier->Parameters = PresetModifier.Parameters;
	}

	return Stack;
}

FString UProceduralModelingToolkitPresetLibrary::ResolvePresetPath(const FString& PresetPath)
{
	FString CandidatePath = PresetPath;
	if (CandidatePath.IsEmpty())
	{
		CandidatePath = TEXT("UntitledPreset.json");
	}

	if (FPaths::IsRelative(CandidatePath))
	{
		CandidatePath = FPaths::Combine(GetDefaultPresetDirectory(), CandidatePath);
	}

	if (FPaths::GetExtension(CandidatePath).IsEmpty())
	{
		CandidatePath += TEXT(".json");
	}

	FPaths::NormalizeFilename(CandidatePath);
	return CandidatePath;
}
