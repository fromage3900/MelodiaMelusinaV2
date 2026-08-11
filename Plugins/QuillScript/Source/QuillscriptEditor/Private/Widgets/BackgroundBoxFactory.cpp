// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/BackgroundBoxFactory.h"

#include "WidgetBlueprint.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/KismetEditorUtilities.h"

#include "Widgets/BackgroundBox.h"

UBackgroundBoxFactory::UBackgroundBoxFactory()
{
	this->SupportedClass = UBackgroundBox::StaticClass();
	this->bCreateNew = true;
	this->bEditAfterNew = true;
}

UObject* UBackgroundBoxFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	// Copy default dialog box.
	if (this->bUseDefault)
	{
		const FAssetRegistryModule& AssetRegistryModule{ FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry") };
		const FSoftObjectPath AssetPath{ "/Script/UMGEditor.WidgetBlueprint'/Quillscript/Runtime/Widgets/BackgroundBoxBP.BackgroundBoxBP'" };

		if (const FAssetData AssetData{ AssetRegistryModule.Get().GetAssetByObjectPath(AssetPath) }; AssetData.GetAsset())
			if (TObjectPtr<UObject> CopyDefault{ DuplicateObject(AssetData.GetAsset(), InParent, InName) })
				return CopyDefault;
	}

	// Create a new clean background box.
	return CastChecked<UWidgetBlueprint>(
		FKismetEditorUtilities::CreateBlueprint(
			UBackgroundBox::StaticClass(),
			InParent,
			InName,
			BPTYPE_Normal,
			UWidgetBlueprint::StaticClass(),
			UWidgetBlueprintGeneratedClass::StaticClass()
		)
	);
}

bool UBackgroundBoxFactory::ConfigureProperties()
{
	// Show dialog message.
	const EAppReturnType::Type Selection{
		FMessageDialog::Open(
			EAppMsgType::YesNoCancel,
			FText::FromString(
				"Copy built-in Background Box widget?\n"
				"\n"
				"( Yes = Copy widget )\n"
				"( No = New widget )"
			),
			FText::FromString("Use Template")
		)
	};

	// Create a copy of the default widget.
	if (Selection == EAppReturnType::Yes)
	{
		this->bUseDefault = true;
		return true;
	}

	// Create a new clean dialog box.
	if ( Selection== EAppReturnType::No)
	{
		this->bUseDefault = false;
		return true;
	}

	this->bUseDefault = false;
	return false;
}

bool UBackgroundBoxFactory::ShouldShowInNewMenu() const
{
	return true;
}