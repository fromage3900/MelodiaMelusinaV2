// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/


// Cherry picker merges metadata from varied sources into one.
// Initially to handle metadata merging for Fuse Clusters

#include "Blenders/PCGExUnionBlender.h"

#include "Containers/PCGExIndexLookup.h"
#include "Core/PCGExMTCommon.h"
#include "Core/PCGExOpStats.h"
#include "Core/PCGExUnionData.h"
#include "Core/PCGExUnionTable.h"
#include "Data/PCGExData.h"
#include "Data/PCGExData.h"
#include "Data/PCGExDataTags.h"
#include "Data/PCGExDataTags.h"
#include "Data/PCGExPointIO.h"
#include "Data/PCGExPointIO.h"
#include "Data/Buffers/PCGExBufferProperty.h"
#include "Data/Utils/PCGExDataFilterDetails.h"
#include "Data/Utils/PCGExDataFilterDetails.h"
#include "Details/PCGExBlendingDetails.h"

namespace PCGExBlending
{
#pragma region FMultiSourceBlender

	FUnionBlender::FMultiSourceBlender::FMultiSourceBlender(const PCGExData::FAttributeIdentity& InIdentity, const TArray<TSharedPtr<PCGExData::FFacade>>& InSources)
		: Identity(InIdentity)
		  , Sources(InSources)
	{
	}

	FUnionBlender::FMultiSourceBlender::FMultiSourceBlender(const TArray<TSharedPtr<PCGExData::FFacade>>& InSources)
		: Sources(InSources)
	{
	}

	bool FUnionBlender::FMultiSourceBlender::Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& InTargetData, const PCGExData::EProxyFlags InProxyFlags)
	{
		check(InTargetData);

		TRACE_CPUPROFILER_EVENT_SCOPE(FUnionBlender::FMultiSourceBlender::Init)

		if (Param.Selector.GetSelection() == EPCGAttributePropertySelection::Attribute)
		{
			TRACE_CPUPROFILER_EVENT_SCOPE(Attribute)

			const EPCGMetadataTypes WorkingType = Identity.GetType();
			if (WorkingType == EPCGMetadataTypes::Unknown)
			{
				// Unknown attribute type
				return false;
			}

			const FPCGAttributeIdentifier Identifier = Identity.GetIdentifier();
			TSharedPtr<PCGExData::IBuffer> InitializationBuffer = nullptr;

			// FAttributeIdentity inherits from FPCGMetadataAttributeDesc -- use IsSameType for the
			// shape comparison instead of GetTypeId. Property-backed attributes both report Unknown
			// from FPCGMetadataAttributeBase::GetTypeId, so the legacy id check would false-positive
			// match a Struct against a TArray<float> against an Object on the target side.
			if (const FPCGMetadataAttributeBase* ExistingAttribute = InTargetData->FindConstAttribute(Identifier);
				ExistingAttribute && ExistingAttribute->GetAttributeDesc().IsSameType(Identity))
			{
				// This attribute exists on target already
				InitializationBuffer = InTargetData->GetWritable(WorkingType, ExistingAttribute, PCGExData::EBufferInit::Inherit);
			}
			else
			{
				// This attribute needs to be initialized
				InitializationBuffer = InTargetData->GetWritable(WorkingType, DefaultValue, PCGExData::EBufferInit::New);
			}

			if (!InitializationBuffer)
			{
				PCGE_LOG_C(Error, GraphAndLog, InContext, FText::Format(FTEXT("FMultiSourceBlender : Cannot create writable output for : \"{0}\""), FText::FromName(Identity.Name)));
				return false;
			}

			// Property-backed buffers cache an FProperty for container layout / deep-copy semantics.
			// IBuffer::GetSourceProperty returns null for typed TBuffer<T> -- no cast or gate needed.
			const FProperty* InitProperty = InitializationBuffer->GetSourceProperty();

			MainBlender = InitProperty
				? CreateProxyBlender(WorkingType, Param.Blending, true, InitProperty)
				: CreateProxyBlender(WorkingType, Param.Blending, true, Identity.ValueTypeObject);

			{
				TArray<int32> SupportedList(SupportedSources.Array());
				std::atomic<bool> bSubBlendersInitOk{true};
				PCGExMT::ParallelOrSequential(
					SupportedList.Num(),
					[&](const int32 i)
					{
					const int32 SourceIdx = SupportedList[i];

					TSharedPtr<FProxyDataBlender> SubBlender = InitProperty
					? CreateProxyBlender(WorkingType, Param.Blending, true, InitProperty)
					: CreateProxyBlender(WorkingType, Param.Blending, true, Identity.ValueTypeObject);

						SubBlenders[SourceIdx] = SubBlender;

						if (!SubBlender->InitFromParam(InContext, Param, InTargetData, Sources[SourceIdx], PCGExData::EIOSide::In, InProxyFlags))
						{
							bSubBlendersInitOk.store(false, std::memory_order_relaxed);
						}
					}, 32);

				if (!bSubBlendersInitOk.load(std::memory_order_relaxed))
				{
					return false;
				}
			}

			if (!MainBlender->InitFromParam(InContext, Param, InTargetData, InTargetData, PCGExData::EIOSide::Out, InProxyFlags))
			{
				return false;
			}
		}
		else if (Param.Selector.GetSelection() == EPCGAttributePropertySelection::Property)
		{
			TRACE_CPUPROFILER_EVENT_SCOPE(Property)

			const EPCGMetadataTypes WorkingType = PCGExMetaHelpers::GetPropertyType(Param.Selector.GetPointProperty());

			MainBlender = CreateProxyBlender(WorkingType, Param.Blending);

			{
				TArray<int32> SupportedList;
				if (SupportedSources.IsEmpty())
				{
					SupportedList.Reserve(Sources.Num());
					for (int32 j = 0; j < Sources.Num(); j++)
					{
						SupportedList.Add(j);
					}
				}
				else
				{
					SupportedList = SupportedSources.Array();
				}
				std::atomic<bool> bSubBlendersInitOk{true};
				PCGExMT::ParallelOrSequential(
					SupportedList.Num(),
					[&](const int32 i)
					{
						const int32 SourceIdx = SupportedList[i];
						TSharedPtr<FProxyDataBlender> SubBlender = CreateProxyBlender(WorkingType, Param.Blending);

						SubBlenders[SourceIdx] = SubBlender;

						if (!SubBlender->InitFromParam(InContext, Param, InTargetData, Sources[SourceIdx], PCGExData::EIOSide::In, InProxyFlags))
						{
							bSubBlendersInitOk.store(false, std::memory_order_relaxed);
						}
					}, 32);

				if (!bSubBlendersInitOk.load(std::memory_order_relaxed))
				{
					return false;
				}
			}

			if (!MainBlender->InitFromParam(InContext, Param, InTargetData, InTargetData, PCGExData::EIOSide::Out, InProxyFlags))
			{
				return false;
			}
		}
		else
		{
			return false;
		}


		return true;
	}

#pragma endregion

	FUnionBlender::FUnionBlender(const FPCGExBlendingDetails* InBlendingDetails, const FPCGExCarryOverDetails* InCarryOverDetails, const PCGExMath::IDistances* InDistanceDetails)
		: CarryOverDetails(InCarryOverDetails)
		  , BlendingDetails(InBlendingDetails)
		  , DistanceDetails(InDistanceDetails)
	{
		BlendingDetails->GetPointPropertyBlendingParams(PropertyParams);
	}

	FUnionBlender::~FUnionBlender()
	{
	}

	void FUnionBlender::AddSources(const TArray<TSharedRef<PCGExData::FFacade>>& InSources, const TSet<FName>* IgnoreAttributeSet, FGetSourceIdx GetSourceIdxFn, const TSet<int32>* RelevantIOIndices)
	{
		if (!GetSourceIdxFn)
		{
			GetSourceIdxFn = [](const TSharedRef<PCGExData::FFacade>& InFacade)
			{
				return InFacade->Source->IOIndex;
			};
		}

		TRACE_CPUPROFILER_EVENT_SCOPE(FUnionBlender::AddSources)

		int32 MaxIndex = 0;
		for (const TSharedRef<PCGExData::FFacade>& Src : InSources)
		{
			MaxIndex = FMath::Max(GetSourceIdxFn(Src), MaxIndex);
		}
		IOLookup = MakeShared<PCGEx::FIndexLookup>(MaxIndex + 1);

		const int32 NumSources = InSources.Num();
		Sources.Reserve(NumSources);
		SourcesData.SetNumUninitialized(NumSources);

		TMap<FPCGAttributeIdentifier, TSharedPtr<FMultiSourceBlender>> BlenderLookup;

		for (int i = 0; i < InSources.Num(); i++)
		{
			const TSharedRef<PCGExData::FFacade>& Facade = InSources[i];
			const int32 IOIndex = GetSourceIdxFn(Facade);

			Sources.Add(Facade);
			SourcesData[i] = Facade->GetIn();
			IOLookup->Set(IOIndex, i);

			// Track which source positions are relevant for property blending
			// If no filter provided, all sources are relevant
			if (!RelevantIOIndices || RelevantIOIndices->Contains(IOIndex))
			{
				RelevantSourcePositions.Add(i);
			}

			EnumAddFlags(AllocatedProperties, Facade->GetAllocations());

			UniqueTags.Append(Facade->Source->Tags->RawTags);

			TArray<PCGExData::FAttributeIdentity> SourceAttributes;
			GetFilteredIdentities(Facade->GetIn()->Metadata, SourceAttributes, BlendingDetails, CarryOverDetails, IgnoreAttributeSet);

			// Check of this new source' attributes
			// See if it adds any new, non-conflicting one
			for (const PCGExData::FAttributeIdentity& Identity : SourceAttributes)
			{
				// First, grab the Param for this attribute
				// Getting a fail means it's filtered out.
				FBlendingParam Param{};
				const FPCGAttributeIdentifier Identifier = Identity.GetIdentifier();
				if (!BlendingDetails->GetBlendingParam(Identifier, Param))
				{
					continue;
				}

				const FPCGMetadataAttributeBase* SourceAttribute = Facade->FindConstAttribute(Identifier);
				if (!SourceAttribute)
				{
					continue;
				}

				TSharedPtr<FMultiSourceBlender> MultiAttribute = BlenderLookup.FindRef(Identifier);

				if (MultiAttribute)
				{
					// A multi-source blender was found for this attribute!

					if (!MultiAttribute->Identity.IsSameType(Identity))
					{
						// Type mismatch, ignore for this source
						TypeMismatches.Add(Identity.Name.ToString());
						continue;
					}
				}
				else
				{
					// Initialize new multi attribute
					// We give it the first source attribute we found, this will be used
					// to set the underlying default value of the attribute (as a best guess kind of move)
					MultiAttribute = Blenders.Add_GetRef(MakeShared<FMultiSourceBlender>(Identity, Sources));
					MultiAttribute->Param = Param;
					MultiAttribute->DefaultValue = SourceAttribute;
					MultiAttribute->SetNum(NumSources);
					BlenderLookup.Add(Identifier, MultiAttribute);
				}

				check(MultiAttribute)

				MultiAttribute->SupportedSources.Add(i);
			}
		}
	}

	bool FUnionBlender::Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& TargetData, const PCGExData::EProxyFlags InProxyFlags)
	{
		TRACE_CPUPROFILER_EVENT_SCOPE(FUnionBlender::Init)

		CurrentTargetData = TargetData;

		if (!Validate(InContext, false))
		{
			return false;
		}

		// Create property blender at the last moment
		Blenders.Reserve(Blenders.Num() + PropertyParams.Num());
		for (const FBlendingParam& Param : PropertyParams)
		{
			if (!EnumHasAnyFlags(AllocatedProperties, PCGExMetaHelpers::GetPropertyNativeTypes(Param.Selector.GetPointProperty())))
			{
				// Don't create a blender for properties that no source has allocated
				continue;
			}

			TSharedPtr<FMultiSourceBlender> MultiAttribute = Blenders.Add_GetRef(MakeShared<FMultiSourceBlender>(Sources));
			MultiAttribute->Param = Param;
			MultiAttribute->SetNum(Sources.Num());
			MultiAttribute->SupportedSources = RelevantSourcePositions; // Optimization: only create blenders for relevant sources
		}

		{
			TRACE_CPUPROFILER_EVENT_SCOPE(InitBlenders)

			// Initialize all blending operations
			for (const TSharedPtr<FMultiSourceBlender>& MultiAttribute : Blenders)
			{
				if (!MultiAttribute->Init(InContext, CurrentTargetData, InProxyFlags))
				{
					return false;
				}
			}
		}

		return true;
	}

	bool FUnionBlender::Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& TargetData, const TSharedPtr<PCGExData::IUnionMetadata>& InUnionMetadata, const PCGExData::EProxyFlags InProxyFlags)
	{
		CurrentUnionMetadata = InUnionMetadata;
		return Init(InContext, TargetData, InProxyFlags);
	}

	int32 FUnionBlender::ComputeWeights(const int32 WriteIndex, const TSharedPtr<PCGExData::IUnionData>& InUnionData, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints) const
	{
		if (!InUnionData.IsValid())
		{
			return 0;
		}
		const PCGExData::FConstPoint Target = CurrentTargetData->Source->GetOutPoint(WriteIndex);
		return InUnionData->ComputeWeights(SourcesData, IOLookup, Target, DistanceDetails, OutWeightedPoints);
	}

	int32 FUnionBlender::ComputeWeights(const int32 WriteIndex, TConstArrayView<PCGExData::FElement> InElements, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints) const
	{
		const PCGExData::FConstPoint Target = CurrentTargetData->Source->GetOutPoint(WriteIndex);
		return PCGExData::FUnionTable::ComputeWeightsForSpan(InElements, SourcesData, IOLookup, Target, DistanceDetails, OutWeightedPoints);
	}

	int32 FUnionBlender::ComputeWeights(const int32 WriteIndex, const TSharedPtr<PCGExData::IUnionMetadata>& InMetadata, const int32 EntryIndex, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints) const
	{
		if (!InMetadata.IsValid())
		{
			return 0;
		}
		const PCGExData::FConstPoint Target = CurrentTargetData->Source->GetOutPoint(WriteIndex);
		return InMetadata->ComputeWeights(EntryIndex, SourcesData, IOLookup, Target, DistanceDetails, OutWeightedPoints);
	}

	void FUnionBlender::Blend(const int32 WriteIndex, const TArray<PCGExData::FWeightedPoint>& InWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const
	{
		if (InWeightedPoints.IsEmpty())
		{
			return;
		}

		// For each attribute/property we want to blend
		for (const TSharedPtr<FMultiSourceBlender>& MultiAttribute : Blenders)
		{
			PCGEx::FOpStats Tracking = MultiAttribute->MainBlender->BeginMultiBlend(WriteIndex);

			// For each point in the union, check if there is an attribute blender for that source; and if so, add it to the blend
			for (const PCGExData::FWeightedPoint& P : InWeightedPoints)
			{
				if (const TSharedPtr<FProxyDataBlender>& Blender = MultiAttribute->SubBlenders[P.IO])
				{
					Blender->MultiBlend(P.Index, WriteIndex, P.Weight, Tracking);
				}
			}

			MultiAttribute->MainBlender->EndMultiBlend(WriteIndex, Tracking);
		}
	}

	void FUnionBlender::MergeSingle(const int32 WriteIndex, const TSharedPtr<PCGExData::IUnionData>& InUnionData, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const
	{
		check(InUnionData)
		if (!ComputeWeights(WriteIndex, InUnionData, OutWeightedPoints))
		{
			return;
		}
		Blend(WriteIndex, OutWeightedPoints, Trackers);
	}

	void FUnionBlender::MergeSingle(const int32 UnionIndex, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const
	{
		// Resolves through the IUnionMetadata interface so the same code path serves both the legacy
		// FUnionMetadata (sparse, IUnionData-backed) and the new FUnionTable (dense, span-backed).
		if (!ComputeWeights(UnionIndex, CurrentUnionMetadata, UnionIndex, OutWeightedPoints))
		{
			return;
		}
		Blend(UnionIndex, OutWeightedPoints, Trackers);
	}

	bool FUnionBlender::Validate(FPCGExContext* InContext, const bool bQuiet) const
	{
		if (TypeMismatches.IsEmpty())
		{
			return true;
		}

		if (!bQuiet)
		{
			PCGE_LOG_C(Warning, GraphAndLog, InContext, FText::Format(FTEXT("The following attributes have the same name but different types, and will not blend as expected: {0}"), FText::FromString(FString::Join(TypeMismatches.Array(), TEXT(", ")))));
		}

		return true;
	}
}
