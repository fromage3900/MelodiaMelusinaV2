// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "AssetTypeActions_Base.h"

class UQuillscriptAsset;

/**
 * Implements actions for Quillscript assets.
 */
class FQuillscriptAssetActions final : public FAssetTypeActions_Base
{
public:
	explicit FQuillscriptAssetActions(const uint32 InAssetCategory);

	/** FAssetTypeActions_Base implementation */
	virtual uint32 GetCategories() override;
	virtual FText GetName() const override;
	virtual UClass* GetSupportedClass() const override;
	virtual FColor GetTypeColor() const override;
	virtual bool HasActions(const TArray<UObject*>& InObjects) const override;
	virtual void GetActions(const TArray<UObject*>& InObjects, FMenuBuilder& MenuBuilder) override;

private:
	uint32 AssetCategory;

	/** FQuillScriptActions implementation */
	void Reimport(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects);
	void Export(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects);
	void OpenWithVSCode(const TArray<TWeakObjectPtr<UQuillscriptAsset>> Objects);
};