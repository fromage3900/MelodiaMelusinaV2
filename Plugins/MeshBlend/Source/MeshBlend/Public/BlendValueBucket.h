// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Containers/ChunkedArray.h"
#include "BlendValueBucket.generated.h"

constexpr float GMeshBlend_GridCellSize = 10000.0f;
constexpr float GMeshBlend_GridCellSizeInverse = 1 / GMeshBlend_GridCellSize;

USTRUCT()
struct MESHBLEND_API FGridCell
{
	GENERATED_BODY()

	TChunkedArray<FBox, 1024> MeshBounds;

	FGridCell()
	{
	}
};

USTRUCT()
struct MESHBLEND_API FBlendValueBucket
{
	GENERATED_BODY()

	UPROPERTY()
	TMap<FIntPoint, FGridCell> GridCells;

	FBlendValueBucket()
	{
	}

	bool Intersect(const FBox& InBox)
	{
		const int32 MinX = FMath::FloorToInt(InBox.Min.X * GMeshBlend_GridCellSizeInverse);
		const int32 MinY = FMath::FloorToInt(InBox.Min.Y * GMeshBlend_GridCellSizeInverse);
		const int32 MaxX = FMath::FloorToInt(InBox.Max.X * GMeshBlend_GridCellSizeInverse);
		const int32 MaxY = FMath::FloorToInt(InBox.Max.Y * GMeshBlend_GridCellSizeInverse);

		for (int32 X = MinX; X <= MaxX; ++X)
		{
			for (int32 Y = MinY; Y <= MaxY; ++Y)
			{
				const FIntPoint GridCoords(X, Y);
				if (const FGridCell* GridCell = GridCells.Find(GridCoords))
				{
					for (const FBox& Box : GridCell->MeshBounds)
					{
						if (Box.Intersect(InBox))
						{
							return true;
						}
					}
				}
			}
		}

		return false;
	}

	void Add(const FBox& InBox)
	{
		const int32 MinX = FMath::FloorToInt(InBox.Min.X * GMeshBlend_GridCellSizeInverse);
		const int32 MinY = FMath::FloorToInt(InBox.Min.Y * GMeshBlend_GridCellSizeInverse);
		const int32 MaxX = FMath::FloorToInt(InBox.Max.X * GMeshBlend_GridCellSizeInverse);
		const int32 MaxY = FMath::FloorToInt(InBox.Max.Y * GMeshBlend_GridCellSizeInverse);

		for (int32 X = MinX; X <= MaxX; ++X)
		{
			for (int32 Y = MinY; Y <= MaxY; ++Y)
			{
				const FIntPoint GridCoords(X, Y);

				FGridCell& Cell = GridCells.FindOrAdd(GridCoords);
				Cell.MeshBounds.AddElement(InBox);
			}
		}
	}
};
