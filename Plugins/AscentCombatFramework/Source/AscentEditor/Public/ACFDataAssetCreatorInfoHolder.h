// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorUtilityWidget.h"
#include "Engine/DataAsset.h"
#include "ACFDataAssetCreatorInfoHolder.generated.h"

class UDetailsView;

/**
 * Base class for Editor Utility Widgets that expose a live DetailsView panel for editing
 * a single UObject class (typically a UDataAsset or a Blueprint).
 *
 * Intended workflow:
 *  1. Call SetClassToDisplay (or LoadFromObject) to point the widget at a class.
 *     The DetailsView will show the Class Default Object (CDO) for that class.
 *  2. The user edits values directly in the DetailsView panel.
 *  3. Call CreateAssetFromData to persist the CDO values into a new asset on disk.
 *
 * To allow selective template-based filling, mark individual UPROPERTY fields in your
 * data asset subclasses with Meta = (CopyFromTemplate). Those fields can then be bulk-
 * copied from another asset of the same class via CopyPropertiesFromTemplate.
 *
 * Subclass this in Blueprint to bind the DetailsView widget and add custom UI logic.
 */
UCLASS(Blueprintable, BlueprintType)
class ASCENTEDITOR_API UACFDataAssetCreatorInfoHolder : public UEditorUtilityWidget
{
	GENERATED_BODY()

public:
	/** Refreshes the DetailsView whenever Blueprint properties are changed in the editor. */
	virtual void SynchronizeProperties() override;

	/**
	 * Sets the class whose CDO will be displayed and edited in the DetailsView.
	 * Passing nullptr clears the view.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor UI")
	void SetClassToDisplay(TSubclassOf<UObject> InClass);

	/**
	 * Loads an existing asset (or Blueprint) into the DetailsView for editing.
	 * The class is inferred from the object; its values are copied into the CDO
	 * so that subsequent CreateAssetFromData calls produce a correctly pre-filled asset.
	 * Handles both plain UObject assets and Blueprint assets (uses the generated class CDO).
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor UI")
	void LoadFromObject(UObject* ObjectToLoad);

	/**
	 * Saves the current CDO values as a new asset on disk.
	 * - If ClassToDisplay is a UDataAsset subclass, creates a DataAsset uasset.
	 * - Otherwise creates a Blueprint asset derived from the class.
	 *
	 * @param AssetName    Name of the new asset file (without extension).
	 * @param PackagePath  Content-browser path where the asset will be saved (e.g. "/Game/MyFolder").
	 * @return             The newly created UObject, or nullptr on failure.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor UI")
	UObject* CreateAssetFromData(FString AssetName, FString PackagePath);

	/**
	 * Copies all properties from TemplateAsset into CurrentEditingObject using
	 * UEngine::CopyPropertiesForUnrelatedObjects, which handles structs, arrays,
	 * soft pointers and subobjects reliably. The DetailsView is refreshed automatically.
	 * Supports plain UObject assets and Blueprint assets (resolved to their generated CDO).
	 *
	 * @param TemplateAsset  Asset to copy values from. Must be the same class as the current editing object.
	 * @return               True if the copy ran; false if TemplateAsset is null,
	 *                       no object is being edited, or the classes do not match.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor UI")
	bool CopyPropertiesFromTemplate(UObject* TemplateAsset);

	/** Returns the object currently displayed and edited in the DetailsView. */
	UFUNCTION(BlueprintPure, Category = "ACF|Editor UI")
	UObject* GetCurrentEditingObject() const { return CurrentEditingObject; }

protected:
	/** Sets CurrentEditingObject and updates the DetailsView to show it. */
	void SetCurrentEditingObject(UObject* NewObject);

	/** The class whose object is currently being displayed and edited. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Editor UI")
	TSubclassOf<UObject> ClassToDisplay;

	/**
	 * The object currently shown in the DetailsView — the single source of truth for all
	 * read/write operations (CopyPropertiesFromTemplate, CreateAssetFromData, etc.).
	 * Updated by every function that changes what the DetailsView displays.
	 */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "ACF|Editor UI")
	TObjectPtr<UObject> CurrentEditingObject;

	/** DetailsView panel bound in the Widget Blueprint. Must be named exactly "DetailsView". */
	UPROPERTY(meta = (BindWidget))
	UDetailsView* DetailsView;
};