// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptAssetFactory.h"

#include "EditorFramework/AssetImportData.h"
#include "Misc/FileHelper.h"

#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptSettings.h"
#include "Utils/Quill.h"


UQuillscriptAssetFactory::UQuillscriptAssetFactory()
{
	this->Formats.Add("qsc;Quillscript");
	this->SupportedClass = UQuillscriptAsset::StaticClass();
	this->bEditorImport = true;
	this->bText = true;
}

UObject* UQuillscriptAssetFactory::FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled)
{
	if (FString FileContent; FFileHelper::LoadFileToString(FileContent, *Filename))
	{
		TObjectPtr<UQuillscriptAsset> QuillScript{ nullptr };

		// Check if asset already exists and update that asset instead.
		if (UQuillscriptSettings::Get()->GetPreserveSettingsOnReimport())
		{
			for (const TObjectPtr<UQuillscriptAsset> Script : UQuill::GetScripts())
			{
				if (Script->GetName() == InName.ToString() && Script->AssetImportData->GetFirstFilename() == Filename)
				{
					QuillScript = Script;
					break;
				}
			}
		}

		if (!QuillScript)
			QuillScript = NewObject<UQuillscriptAsset>(InParent, InClass, InName, Flags);

		QuillScript->SetContent(FileContent);
		QuillScript->AssetImportData->Update(Filename);

		return QuillScript;
	}

	return nullptr;
}

UObject* UQuillscriptAssetFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return NewObject<UQuillscriptAsset>(InParent, InClass, InName, Flags);
}

bool UQuillscriptAssetFactory::ShouldShowInNewMenu() const
{
	return true;
}

bool UQuillscriptAssetFactory::CanReimport(UObject* Obj, TArray<FString>& OutFilenames)
{
	if (const TObjectPtr<UQuillscriptAsset> QuillScript{ Cast<UQuillscriptAsset>(Obj) }; QuillScript && QuillScript->AssetImportData)
	{
		QuillScript->AssetImportData->ExtractFilenames(OutFilenames);
		return true;
	}

	return false;
}

void UQuillscriptAssetFactory::SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths)
{
	if (const TObjectPtr<UQuillscriptAsset> QuillScript{ Cast<UQuillscriptAsset>(Obj) }; QuillScript && ensure(NewReimportPaths.Num() == 1))
		QuillScript->AssetImportData->UpdateFilenameOnly(NewReimportPaths[0]);
}

EReimportResult::Type UQuillscriptAssetFactory::Reimport(UObject* Obj)
{
	const TObjectPtr<UQuillscriptAsset> QuillScript{ Cast<UQuillscriptAsset>(Obj) };

	// Check if object is valid.
	if (!QuillScript)
		return EReimportResult::Failed;

	// Make sure file is valid and exists.
	const FString Filename{ QuillScript->AssetImportData->GetFirstFilename() };

	if (!Filename.Len() || IFileManager::Get().FileSize(*Filename) == INDEX_NONE)
		return EReimportResult::Failed;

	// Run the import again.

	if (bool bOutCanceled{ false }; this->ImportObject(QuillScript->GetClass(), QuillScript->GetOuter(), *QuillScript->GetName(), EObjectFlags::RF_Public | EObjectFlags::RF_Standalone, Filename, nullptr, bOutCanceled) != nullptr)
	{
		QuillScript->AssetImportData->Update(Filename);

		// Try to find the outer package so we can dirty it up.
		if (QuillScript->GetOuter())
			QuillScript->GetOuter()->MarkPackageDirty();
		else
			QuillScript->MarkPackageDirty();

		return EReimportResult::Succeeded;
	}

	return EReimportResult::Failed;
}