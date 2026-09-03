// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/Collections/PCGExLevelCollectionActions.h"

#include "Collections/PCGExLevelCollection.h"
#include "Details/Collections/PCGExCollectionEditorHelpers.h"
#include "Details/Collections/PCGExCollectionEditorTypeRegistry.h"
#include "Details/Collections/PCGExLevelCollectionEditor.h"
#include "Engine/World.h"

PCGEX_REGISTER_COLLECTION_EDITOR_TYPE(
	Level,
	UPCGExLevelCollection,
	UWorld,
	"SMC_NewLevelCollection",
	FLinearColor(FColor(255, 156, 0)),
	"Level Collection",
	"A weighted collection of level assets.",
	FPCGExLevelCollectionEditor)

namespace PCGExLevelCollectionActions
{
	void CreateCollectionFrom(const TArray<FAssetData>& SelectedAssets)
	{
		PCGExCollectionEditorHelpers::CreateCollectionFromTyped(SelectedAssets, UPCGExLevelCollection::StaticClass(), TEXT("SMC_NewLevelCollection"));
	}

	void UpdateCollectionsFrom(
		const TArray<TObjectPtr<UPCGExLevelCollection>>& SelectedCollections,
		const TArray<FAssetData>& SelectedAssets)
	{
		TArray<TObjectPtr<UPCGExAssetCollection>> AsBase;
		AsBase.Reserve(SelectedCollections.Num());
		for (const TObjectPtr<UPCGExLevelCollection>& C : SelectedCollections)
		{
			AsBase.Add(C);
		}
		PCGExCollectionEditorHelpers::UpdateCollectionsFromTyped(AsBase, SelectedAssets);
	}
}
