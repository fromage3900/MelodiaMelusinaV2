// Copyright 2025 Tore Lervik. All Rights Reserved.

#pragma once
#include "Containers/Array.h"
#include "GameFramework/Actor.h"
#include "HAL/LowLevelMemTracker.h"
#include "Misc/EngineVersionComparison.h"

/**
 * Processing queue that stores elements in TArray chunks to reduce memory reallocations while still allowing efficient allocations within individual chunks.
 * Recommended size: 2048, 4096, 8192, 16384, 32768, 65536
 */
template <typename ElementType, uint32 TargetBytesPerChunk = 16384>
struct TChunkedProcessingQueue
{
	void Empty()
	{
		Chunks.Empty();
		ResetIndexToStart();
	}

	void Add(ElementType Item)
	{
		LLM_SCOPE_BYNAME(TEXT("MeshBlend/ChunkedQueue"));

		for (FChunk& Chunk : Chunks)
		{
			if (Chunk.Elements.Num() < NumElementsPerChunk)
			{
				Chunk.Elements.Add(Item);
				return;
			}
		}

		int32 TempChunkIndex = Chunks.Add(new FChunk);
		Chunks[TempChunkIndex].Elements.Reserve(NumElementsPerChunk);
		Chunks[TempChunkIndex].Elements.Add(Item);
	}

	void AddUnique(ElementType Item)
	{
		for (FChunk& Chunk : Chunks)
		{
			if (Chunk.Elements.Find(Item) != INDEX_NONE)
			{
				return;
			}
		}

		Add(Item);
	}

	bool Next(ElementType& Item)
	{
		// The last chunk/element overflows the ChunkIndex causing this to be true on the next call. Marking the end of the queue.
		if (ChunkIndex >= Chunks.Num() || ChunkElementIndex >= Chunks[ChunkIndex].Elements.Num())
		{
			ResetIndexToStart();
			return false;
		}

		check(ChunkIndex < Chunks.Num());
		FChunk& Chunk = Chunks[ChunkIndex];

		check(ChunkElementIndex < Chunk.Elements.Num());
		Item = Chunk.Elements[ChunkElementIndex];

		ChunkElementIndex += 1;

		if (ChunkElementIndex >= Chunk.Elements.Num())
		{
			ChunkIndex += 1;
			ChunkElementIndex = 0;
		}

		return true;
	}

	void ResetIndexToStart()
	{
		ChunkIndex = 0;
		ChunkElementIndex = 0;
	}

	void KeepCurrentAsNext()
	{
		ChunkElementIndex -= 1;

		if (ChunkElementIndex < 0)
		{
			ChunkIndex -= 1;

			if (ChunkIndex >= 0)
			{
				check(ChunkIndex < Chunks.Num());

				FChunk& Chunk = Chunks[ChunkIndex];
				ChunkElementIndex = FMath::Max(0, Chunk.Elements.Num() - 1);
			}
			else
			{
				ResetIndexToStart();
			}
		}
	}

	void RemoveCurrent()
	{
		LLM_SCOPE_BYNAME(TEXT("MeshBlend/ChunkedQueue"));

		KeepCurrentAsNext();

		check(ChunkIndex < Chunks.Num());

		FChunk& Chunk = Chunks[ChunkIndex];

		check(ChunkElementIndex < Chunk.Elements.Num());

#if UE_VERSION_OLDER_THAN(5, 5, 0)
		Chunk.Elements.RemoveAtSwap(ChunkElementIndex, 1, false);
#else
		Chunk.Elements.RemoveAtSwap(ChunkElementIndex, 1, EAllowShrinking::No);
#endif


		if (Chunk.Elements.Num() == 0 && Chunks.Num() == 1)
		{
			ResetIndexToStart();
		}
		else if (Chunk.Elements.Num() == 0)
		{
			Chunks.RemoveAt(ChunkIndex);
			ChunkIndex -= 1;

			if (ChunkIndex >= 0)
			{
				ChunkElementIndex = FMath::Max(0, Chunks[ChunkIndex].Elements.Num() - 1);
			}
			else
			{
				ResetIndexToStart();
			}
		}
		else if (ChunkElementIndex >= Chunk.Elements.Num())
		{
			ChunkIndex += 1;
			ChunkElementIndex = 0;
		}
	}

private:
	struct FChunk
	{
		TArray<ElementType> Elements = TArray<ElementType>();
	};

	TIndirectArray<FChunk, FDefaultAllocator> Chunks = TIndirectArray<FChunk, FDefaultAllocator>();
	int32 ChunkIndex = 0;
	int32 ChunkElementIndex = 0;

	enum { NumElementsPerChunk = TargetBytesPerChunk / sizeof(ElementType) };
};
