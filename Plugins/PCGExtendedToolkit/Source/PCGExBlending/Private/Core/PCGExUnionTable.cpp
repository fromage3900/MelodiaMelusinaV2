// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Core/PCGExUnionTable.h"

#include "Containers/PCGExIndexLookup.h"
#include "Data/PCGExData.h"
#include "Math/PCGExMathDistances.h"
#include "Sorting/PCGExSortingHelpers.h"

namespace PCGExData
{
#pragma region FUnionTable

	bool FUnionTable::ContainsIO(const int32 EntryIndex, const int32 IO) const
	{
		for (const FElement& E : Get(EntryIndex))
		{
			if (E.IO == IO)
			{
				return true;
			}
		}
		return false;
	}

	TSet<int32> FUnionTable::GetIOSet(const int32 EntryIndex) const
	{
		TSet<int32> Result;
		for (const FElement& E : Get(EntryIndex))
		{
			Result.Add(E.IO);
		}
		return Result;
	}

	bool FUnionTable::IOIndexOverlap(const int32 EntryIndex, const TSet<int32>& InIndices) const
	{
		for (const FElement& E : Get(EntryIndex))
		{
			if (InIndices.Contains(E.IO))
			{
				return true;
			}
		}
		return false;
	}

	int32 FUnionTable::ComputeWeights(
		const int32 EntryIndex,
		const TArray<const UPCGBasePointData*>& Sources,
		const TSharedPtr<PCGEx::FIndexLookup>& IdxLookup,
		const FPoint& Target,
		const PCGExMath::IDistances* InDistances,
		TArray<FWeightedPoint>& OutWeightedPoints) const
	{
		return ComputeWeightsForSpan(Get(EntryIndex), Sources, IdxLookup, Target, InDistances, OutWeightedPoints);
	}

	int32 FUnionTable::ComputeWeightsForSpan(
		TConstArrayView<FElement> InElements,
		const TArray<const UPCGBasePointData*>& Sources,
		const TSharedPtr<PCGEx::FIndexLookup>& IdxLookup,
		const FPoint& Target,
		const PCGExMath::IDistances* InDistances,
		TArray<FWeightedPoint>& OutWeightedPoints)
	{
		return ComputeUnionWeights(InElements, Sources, IdxLookup, Target, InDistances, OutWeightedPoints);
	}

	void FUnionTable::Reset()
	{
		Offsets.Reset();
		Elements.Reset();
		Keys.Reset();
	}

#pragma endregion

#pragma region FUnionTableBuilder

	void FUnionTableBuilder::Compile(FUnionTable& OutTable)
	{
		TArray<int32> RecordToEntry;
		TArray<int32> ScopeOffsets;
		CompileWithMapping(OutTable, RecordToEntry, ScopeOffsets);
	}

	void FUnionTableBuilder::CompileWithMapping(FUnionTable& OutTable, TArray<int32>& OutRecordToEntry, TArray<int32>& OutScopeOffsets)
	{
		TRACE_CPUPROFILER_EVENT_SCOPE(FUnionTableBuilder::CompileWithMapping);

		const int32 NumScopesLocal = ScopedRecords.Num();

		OutScopeOffsets.SetNumUninitialized(NumScopesLocal + 1);
		OutScopeOffsets[0] = 0;
		for (int32 i = 0; i < NumScopesLocal; i++)
		{
			OutScopeOffsets[i + 1] = OutScopeOffsets[i] + ScopedRecords[i].Num();
		}

		const int32 TotalRecords = OutScopeOffsets[NumScopesLocal];

		OutTable.Reset();

		if (TotalRecords == 0)
		{
			OutTable.Offsets.Add(0);
			OutRecordToEntry.Reset();
			return;
		}

		// Concatenate scopes deterministically into a flat record array, then build a parallel
		// FIndexKey array for the radix sort. We need both: RadixSort moves the keys, not the records.
		TArray<FUnionStreamRecord> AllRecords;
		AllRecords.SetNumUninitialized(TotalRecords);

		TArray<PCGEx::FIndexKey> SortKeys;
		SortKeys.SetNumUninitialized(TotalRecords);

		for (int32 ScopeIdx = 0; ScopeIdx < NumScopesLocal; ScopeIdx++)
		{
			const int32 BaseOffset = OutScopeOffsets[ScopeIdx];
			const TArray<FUnionStreamRecord>& Scope = ScopedRecords[ScopeIdx];
			const int32 ScopeNum = Scope.Num();

			for (int32 i = 0; i < ScopeNum; i++)
			{
				const int32 GlobalIdx = BaseOffset + i;
				AllRecords[GlobalIdx] = Scope[i];
				SortKeys[GlobalIdx] = PCGEx::FIndexKey(GlobalIdx, Scope[i].Key);
			}
		}

		// Stable LSD radix sort by Key. Records with equal Key keep their original global-index
		// order, which is itself a deterministic function of (ScopeIndex, in-scope position).
		PCGExSortingHelpers::RadixSort(SortKeys);

		OutTable.Elements.SetNumUninitialized(TotalRecords);
		OutTable.Offsets.Reserve(TotalRecords + 1);
		OutTable.Keys.Reserve(TotalRecords);
		OutRecordToEntry.SetNumUninitialized(TotalRecords);

		const bool bDedupe = bDedupeElementsBySource;

		// Reused scratch set (one alloc for the whole compile), cleared per key group.
		TSet<FElement> SeenInGroup;
		if (bDedupe) { SeenInGroup.Reserve(8); }

		OutTable.Offsets.Add(0);
		uint64 CurrentKey = SortKeys[0].Key;
		OutTable.Keys.Add(CurrentKey);
		int32 EntryIndex = 0;
		int32 WriteCount = 0; // == i without dedup; lags by collapsed duplicates with it

		for (int32 i = 0; i < TotalRecords; i++)
		{
			const PCGEx::FIndexKey& Sorted = SortKeys[i];
			if (Sorted.Key != CurrentKey)
			{
				OutTable.Offsets.Add(WriteCount);
				CurrentKey = Sorted.Key;
				OutTable.Keys.Add(CurrentKey);
				EntryIndex++;
				if (bDedupe) { SeenInGroup.Reset(); }
			}

			const FUnionStreamRecord& Rec = AllRecords[Sorted.Index];
			OutRecordToEntry[Sorted.Index] = EntryIndex;

			const FElement Element(Rec.Index, Rec.IO);
			if (bDedupe)
			{
				bool bAlreadyInGroup = false;
				SeenInGroup.Add(Element, &bAlreadyInGroup);
				if (bAlreadyInGroup)
				{
					continue; // duplicate of a point already in this entry; still mapped above
				}
			}

			OutTable.Elements[WriteCount++] = Element;
		}

		OutTable.Offsets.Add(WriteCount);
		OutTable.Elements.SetNum(WriteCount, EAllowShrinking::No); // trim slack from collapsed dups
	}

#pragma endregion
}
