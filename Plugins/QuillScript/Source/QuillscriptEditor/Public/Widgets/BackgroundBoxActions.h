// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "AssetTypeActions_Base.h"

/**
 * Implements an editor actions for Background Box assets.
 */
class FBackgroundBoxActions final : public FAssetTypeActions_Base
{
public:
	explicit FBackgroundBoxActions(const uint32 InAssetCategory);

	/* FAssetTypeActions_Base */
	virtual uint32 GetCategories() override;
	virtual FText GetName() const override;
	virtual UClass* GetSupportedClass() const override;
	virtual FColor GetTypeColor() const override;

private:
	uint32 AssetCategory;
};