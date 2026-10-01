// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFDataAssetCreatorInfoHolder.h"
#include "ACFEditorFunctionLibrary.h"
#include "Components/DetailsView.h"
#include "Engine/DataAsset.h"

void UACFDataAssetCreatorInfoHolder::SetCurrentEditingObject(UObject* NewObject)
{
	CurrentEditingObject = NewObject;
	if (DetailsView)
	{
		DetailsView->SetObject(CurrentEditingObject);
	}
}

void UACFDataAssetCreatorInfoHolder::SynchronizeProperties()
{
	Super::SynchronizeProperties();
	SetCurrentEditingObject(ClassToDisplay ? ClassToDisplay->GetDefaultObject() : nullptr);
}

void UACFDataAssetCreatorInfoHolder::SetClassToDisplay(TSubclassOf<UObject> InClass)
{
	ClassToDisplay = InClass;
	SetCurrentEditingObject(ClassToDisplay ? ClassToDisplay->GetDefaultObject() : nullptr);
}

void UACFDataAssetCreatorInfoHolder::LoadFromObject(UObject* ObjectToLoad)
{
	if (!ObjectToLoad)
	{
		UE_LOG(LogTemp, Warning, TEXT("LoadFromObject: Object is null"));
		return;
	}

	UClass* TargetClass = ObjectToLoad->GetClass();
	UObject* SourceData = ObjectToLoad;

	if (UBlueprint* BlueprintAsset = Cast<UBlueprint>(ObjectToLoad))
	{
		if (BlueprintAsset->GeneratedClass)
		{
			TargetClass = BlueprintAsset->GeneratedClass;
			SourceData = BlueprintAsset->GeneratedClass->GetDefaultObject();
		}
	}

	SetClassToDisplay(TargetClass);

	if (ClassToDisplay && SourceData)
	{
		UObject* TargetCDO = ClassToDisplay->GetDefaultObject();
		UEngine::CopyPropertiesForUnrelatedObjects(SourceData, TargetCDO);
		SetCurrentEditingObject(TargetCDO);
	}
}

bool UACFDataAssetCreatorInfoHolder::CopyPropertiesFromTemplate(UObject* TemplateAsset)
{
	if (!TemplateAsset)
	{
		UE_LOG(LogTemp, Error, TEXT("CopyPropertiesFromTemplate: TemplateAsset is null"));
		return false;
	}

	if (!CurrentEditingObject)
	{
		UE_LOG(LogTemp, Error, TEXT("CopyPropertiesFromTemplate: No object is currently being edited (call SetClassToDisplay or LoadFromObject first)"));
		return false;
	}

	// Resolve the real class and source object, handling Blueprint assets
	UClass* TemplateClass = TemplateAsset->GetClass();
	UObject* SourceObject = TemplateAsset;

	if (UBlueprint* BP = Cast<UBlueprint>(TemplateAsset))
	{
		if (BP->GeneratedClass)
		{
			TemplateClass = BP->GeneratedClass;
			SourceObject = BP->GeneratedClass->GetDefaultObject();
		}
	}

	if (TemplateClass != CurrentEditingObject->GetClass())
	{
		UE_LOG(LogTemp, Error,
			TEXT("CopyPropertiesFromTemplate: Template class '%s' does not match editing object class '%s'. Operation aborted."),
			*TemplateClass->GetName(), *CurrentEditingObject->GetClass()->GetName());
		return false;
	}

	UEngine::CopyPropertiesForUnrelatedObjects(SourceObject, CurrentEditingObject);

	UE_LOG(LogTemp, Log, TEXT("CopyPropertiesFromTemplate: Properties copied from '%s'"), *TemplateAsset->GetName());

	// Refresh the panel so the new values are visible immediately
	if (DetailsView)
	{
		DetailsView->SetObject(CurrentEditingObject);
	}

	return true;
}

UObject* UACFDataAssetCreatorInfoHolder::CreateAssetFromData(FString AssetName, FString PackagePath)
{
	if (!CurrentEditingObject)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateAssetFromData: No object is currently being edited"));
		return nullptr;
	}

	if (!ClassToDisplay)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateAssetFromData: No class selected"));
		return nullptr;
	}

	if (ClassToDisplay->IsChildOf(UDataAsset::StaticClass()))
	{
		UDataAsset* CreatedDataAsset = nullptr;
		return UACFEditorFunctionLibrary::CreateDataAssetFromPointer(Cast<UDataAsset>(CurrentEditingObject), AssetName, PackagePath, CreatedDataAsset) ? CreatedDataAsset : nullptr;
	}
	else
	{
		UBlueprint* CreatedBlueprint = nullptr;
		return UACFEditorFunctionLibrary::CreateBlueprintFromPointer(CurrentEditingObject, AssetName, PackagePath, CreatedBlueprint) ? CreatedBlueprint : nullptr;
	}
}