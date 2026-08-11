// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptSettings.h"

#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptInterpreter.h"
#include "Core/QuillscriptSubsystem.h"
#include "Engine/GameInstance.h"
#include "Utils/Lexer.h"
#include "Utils/Quill.h"
#include "Utils/Tools.h"
#include "Widgets/BackgroundBox.h"
#include "Widgets/SpriteBox.h"
#include "Widgets/DialogBox.h"
#include "Widgets/SelectionBox.h"


void UQuillscriptSettings::PostInitProperties()
{
	Super::PostInitProperties();

	// Enforce default values to all relevant settings.
	this->EnforceDefaults();
}


#if WITH_EDITOR

void UQuillscriptSettings::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	// Enforce default values to changed setting.
	this->EnforceDefaults(PropertyChangedEvent.Property->GetName());
}

FName UQuillscriptSettings::GetCategoryName() const
{
	return NAME_Game;
}

#endif


#pragma region Asset

const UQuillscriptSettings* UQuillscriptSettings::Get()
{
	const UQuillscriptSettings* Settings{ GetDefault<UQuillscriptSettings>() };

	if (Settings->SettingsAsset)
		return Settings->SettingsAsset;

	return Settings;
}

const UQuillscriptSettings* UQuillscriptSettings::Default()
{
	return GetDefault<UQuillscriptSettings>();
}

const UQuillscriptSettings* UQuillscriptSettings::Asset()
{
	return SettingsAsset;
}

void UQuillscriptSettings::UseSettingsAsset(const UObject* WorldContextObject, UQuillscriptSettings* NewSettingsAsset)
{
	if (WorldContextObject && NewSettingsAsset)
	{
		if (const TObjectPtr<UQuillscriptSubsystem> Subsystem{ WorldContextObject->GetWorld()->GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>() })
		{
			GetMutableDefault<UQuillscriptSettings>()->SettingsAsset = NewSettingsAsset;
			Subsystem->AppendDefaultValues(NewSettingsAsset->GetDefaultVariables(), NewSettingsAsset->GetDefaultScriptReferences());
		}
	}
}

void UQuillscriptSettings::ClearSettingsAsset()
{
	GetMutableDefault<UQuillscriptSettings>()->SettingsAsset = nullptr;
}

UQuillscriptSettings* UQuillscriptSettings::GetSettingsAssetByPath(FString Path)
{
	const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
	FSoftObjectPath AssetPath{ Path };

	if (const FAssetData AssetData{ AssetRegistryModule.Get().GetAssetByObjectPath(AssetPath) }; AssetData.GetAsset())
		if (TObjectPtr<UQuillscriptSettings> SettingsAssetRef{ Cast<UQuillscriptSettings>(AssetData.GetAsset()) })
			return SettingsAssetRef;

	UTools::Error("Invalid Settings Asset path: '" + Path + "'.");
	return nullptr;
}

void UQuillscriptSettings::SetSettingsAsset(const UObject* WorldContextObject, UQuillscriptSettings* Value)
{
	UseSettingsAsset(WorldContextObject, Value);
}

#pragma endregion Asset


#pragma region Data

bool UQuillscriptSettings::HasMultiplayer() const
{
	return false; // this->MultiplayerMode != EMultiplayerMode::None;
}

#pragma endregion Data


#pragma region Internal

void UQuillscriptSettings::EnforceDefaults(FString ChangedPropertyName)
{
	// Lambda to check if the changed property is the one we want to enforce.
	auto IsProperty = [ChangedPropertyName](const FString& PropertyName) -> bool
	{
		return ChangedPropertyName.IsEmpty() || ChangedPropertyName == PropertyName;
	};

	// Set defaults classes.
	if (!this->ScriptSettings.InterpreterClass)
		this->ScriptSettings.InterpreterClass = AQuillscriptInterpreter::StaticClass();

	if (!this->ScriptSettings.DialogBoxClass)
		this->ScriptSettings.DialogBoxClass = LoadClass<UDialogBox>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint'/Quillscript/Runtime/Widgets/DialogBoxBP.DialogBoxBP_C'"));

	if (!this->ScriptSettings.SelectionBoxClass)
		this->ScriptSettings.SelectionBoxClass = LoadClass<USelectionBox>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint'/Quillscript/Runtime/Widgets/SelectionBoxBP.SelectionBoxBP_C'"));

	if (!this->ScriptSettings.BackgroundBoxClass)
		this->ScriptSettings.BackgroundBoxClass = LoadClass<UBackgroundBox>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint'/Quillscript/Runtime/Widgets/BackgroundBoxBP.BackgroundBoxBP_C'"));

	if (!this->ScriptSettings.SpriteBoxClass)
		this->ScriptSettings.SpriteBoxClass = LoadClass<USpriteBox>(nullptr, TEXT("/Script/UMGEditor.WidgetBlueprint'/Quillscript/Runtime/Widgets/SpriteBoxBP.SpriteBoxBP_C'"));

	// Do NOT localize Quillscript syntax symbols, numbers and reserved words.
	if (IsProperty("DefaultVariables"))
		for (TPair<FName, FText>& Variable : this->DefaultVariables)
			FLexer::TurnOffLocalization(Variable.Value);

	// Update all script references.
	if (IsProperty("ReferencesSearchPaths"))
		for (UQuillscriptAsset* Script : UQuill::GetScripts())
			Script->UpdatePackagingReferences();
}

#pragma endregion Internal