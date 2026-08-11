// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/Collections/FPCGExCollectionTileDragDropOp.h"

#include "Core/PCGExAssetCollection.h"

TSharedRef<FPCGExCollectionTileDragDropOp> FPCGExCollectionTileDragDropOp::New(
	const TArray<int32>& InIndices,
	FName InSourceCategory,
	UPCGExAssetCollection* InSourceCollection)
{
	TSharedRef<FPCGExCollectionTileDragDropOp> Op = MakeShareable(new FPCGExCollectionTileDragDropOp());
	Op->DraggedIndices = InIndices;
	Op->SourceCategory = InSourceCategory;
	Op->SourceCollection = InSourceCollection;
	Op->RefreshHoverText(false);
	Op->Construct();
	return Op;
}
