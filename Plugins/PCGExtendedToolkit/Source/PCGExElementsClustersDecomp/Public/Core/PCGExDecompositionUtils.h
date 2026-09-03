// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

namespace PCGExDecomposition
{
	/**
	 * Accumulate a per-cell integer-coordinate AABB and convert it to world-space box sizes.
	 * For each cell, size = (CoordMax - CoordMin + 1) * CellSize (inclusive integer span).
	 * Shared by every "box-like" decomposition (voxel grids, uniform grid partition) so the
	 * quantized-box math lives in one place.
	 *
	 * @param NumItems   number of items to iterate (voxels, nodes, ...)
	 * @param NumCells   number of cells; OutSizes is sized to this
	 * @param CellSize   world units per cell along each axis
	 * @param GetCell    item index -> CellID (return < 0 or >= NumCells to skip the item)
	 * @param GetCoord   item index -> its integer cell coordinate (only called for in-range cells)
	 * @param OutSizes   filled with NumCells entries; cells with no items get ZeroVector
	 */
	template <typename TGetCell, typename TGetCoord>
	void AccumulateQuantizedCellSizes(
		const int32 NumItems,
		const int32 NumCells,
		const FVector& CellSize,
		TGetCell GetCell,
		TGetCoord GetCoord,
		TArray<FVector>& OutSizes)
	{
		OutSizes.Reset();
		if (NumCells <= 0)
		{
			return;
		}

		TArray<FIntVector> CellMin;
		TArray<FIntVector> CellMax;
		CellMin.Init(FIntVector(MAX_int32, MAX_int32, MAX_int32), NumCells);
		CellMax.Init(FIntVector(MIN_int32, MIN_int32, MIN_int32), NumCells);

		for (int32 i = 0; i < NumItems; i++)
		{
			const int32 CellID = GetCell(i);
			if (CellID < 0 || CellID >= NumCells)
			{
				continue;
			}

			const FIntVector Coord = GetCoord(i);
			FIntVector& Min = CellMin[CellID];
			FIntVector& Max = CellMax[CellID];
			Min.X = FMath::Min(Min.X, Coord.X);
			Min.Y = FMath::Min(Min.Y, Coord.Y);
			Min.Z = FMath::Min(Min.Z, Coord.Z);
			Max.X = FMath::Max(Max.X, Coord.X);
			Max.Y = FMath::Max(Max.Y, Coord.Y);
			Max.Z = FMath::Max(Max.Z, Coord.Z);
		}

		OutSizes.SetNumUninitialized(NumCells);
		for (int32 c = 0; c < NumCells; c++)
		{
			if (CellMin[c].X > CellMax[c].X)
			{
				// Cell received no items.
				OutSizes[c] = FVector::ZeroVector;
				continue;
			}
			const FIntVector Span = CellMax[c] - CellMin[c] + FIntVector(1, 1, 1);
			OutSizes[c] = FVector(Span.X * CellSize.X, Span.Y * CellSize.Y, Span.Z * CellSize.Z);
		}
	}
}
