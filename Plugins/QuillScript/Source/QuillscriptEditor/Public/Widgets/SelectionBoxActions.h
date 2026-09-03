// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "AssetTypeActions_Base.h"

/**
 * Implements an editor actions for Selection Box assets.
 */
class FSelectionBoxActions final : public FAssetTypeActions_Base
{
public:
	explicit FSelectionBoxActions(const uint32 InAssetCategory);

	/* FAssetTypeActions_Base */
	virtual uint32 GetCategories() override;
	virtual FText GetName() const override;
	virtual UClass* GetSupportedClass() const override;
	virtual FColor GetTypeColor() const override;

private:
	uint32 AssetCategory;
};