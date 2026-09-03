// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Actions/PCGExActionWriteValues.h"
#include "Factories/PCGExFactoryProvider.h"


#include "PCGPin.h"
#include "Containers/PCGExManagedObjects.h"
#include "Data/PCGExData.h"
#include "Data/Buffers/PCGExBufferProperty.h"
#include "Helpers/PCGExMetaHelpers.h"
#include "Types/PCGExAttributeIdentity.h"


#define LOCTEXT_NAMESPACE "PCGExWriteActionWriteValuess"
#define PCGEX_NAMESPACE PCGExWriteActionWriteValuess

bool FPCGExActionWriteValuesOperation::PrepareForData(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& InPointDataFacade)
{
	if (!FPCGExActionOperation::PrepareForData(InContext, InPointDataFacade))
	{
		return false;
	}

	for (const PCGExData::FAttributeIdentity& Identity : TypedFactory->CheckSuccessInfos->Identities)
	{
		const FPCGMetadataAttributeBase* AttributeBase = Identity.Attribute;
		if (!AttributeBase)
		{
			continue;
		}
		PCGExMetaHelpers::ExecuteWithRightType(
			AttributeBase,
			[&](auto DummyValue)
			{
				using T = decltype(DummyValue);
				TSharedPtr<PCGExData::TBuffer<T>> Writer = InPointDataFacade->GetWritable<T>(AttributeBase, PCGExData::EBufferInit::Inherit);
				SuccessAttributes.Add(AttributeBase);
				SuccessWriters.Add(Writer);
			},
			[&]()
			{
				// Property-backed: route through the generic GetWritableFromAttribute fallback.
				TSharedPtr<PCGExData::IBuffer> Writer = InPointDataFacade->GetWritableFromAttribute(AttributeBase, PCGExData::EBufferInit::Inherit);
				if (Writer)
				{
					SuccessAttributes.Add(AttributeBase);
					SuccessWriters.Add(Writer);
				}
			});
	}

	for (const PCGExData::FAttributeIdentity& Identity : TypedFactory->CheckFailInfos->Identities)
	{
		const FPCGMetadataAttributeBase* AttributeBase = Identity.Attribute;
		if (!AttributeBase)
		{
			continue;
		}
		PCGExMetaHelpers::ExecuteWithRightType(
			AttributeBase,
			[&](auto DummyValue)
			{
				using T = decltype(DummyValue);
				TSharedPtr<PCGExData::TBuffer<T>> Writer = InPointDataFacade->GetWritable<T>(AttributeBase, PCGExData::EBufferInit::Inherit);
				FailAttributes.Add(AttributeBase);
				FailWriters.Add(Writer);
			},
			[&]()
			{
				TSharedPtr<PCGExData::IBuffer> Writer = InPointDataFacade->GetWritableFromAttribute(AttributeBase, PCGExData::EBufferInit::Inherit);
				if (Writer)
				{
					FailAttributes.Add(AttributeBase);
					FailWriters.Add(Writer);
				}
			});
	}

	return true;
}

void FPCGExActionWriteValuesOperation::OnMatchSuccess(int32 Index)
{
	for (int i = 0; i < SuccessAttributes.Num(); i++)
	{
		const FPCGMetadataAttributeBase* AttributeBase = SuccessAttributes[i];
		PCGExMetaHelpers::ExecuteWithRightType(
			AttributeBase,
			[&](auto DummyValue)
			{
				using T = decltype(DummyValue);
				static_cast<PCGExData::TBuffer<T>*>(SuccessWriters[i].Get())->SetValue(Index, AttributeBase->GetValueFromItemKey<T>(PCGDefaultValueKey));
			},
			[&]()
			{
				// Property-backed: write source attribute's default value into target slot via FProperty.
				if (SuccessWriters[i] && SuccessWriters[i]->IsPropertyBacked())
				{
					const TSharedPtr<PCGExData::FPropertyArrayBuffer> PropBuf = StaticCastSharedPtr<PCGExData::FPropertyArrayBuffer>(SuccessWriters[i]);
					if (const void* SrcAddr = AttributeBase->GetReadAddressFromEntryKey_Unsafe(PCGDefaultValueKey))
					{
						PropBuf->SetFromVoidProperty(Index, SrcAddr);
					}
				}
			});
	}
}

void FPCGExActionWriteValuesOperation::OnMatchFail(int32 Index)
{
	for (int i = 0; i < FailAttributes.Num(); i++)
	{
		const FPCGMetadataAttributeBase* AttributeBase = FailAttributes[i];
		PCGExMetaHelpers::ExecuteWithRightType(
			AttributeBase,
			[&](auto DummyValue)
			{
				using T = decltype(DummyValue);
				static_cast<PCGExData::TBuffer<T>*>(FailWriters[i].Get())->SetValue(Index, AttributeBase->GetValueFromItemKey<T>(PCGDefaultValueKey));
			},
			[&]()
			{
				if (FailWriters[i] && FailWriters[i]->IsPropertyBacked())
				{
					const TSharedPtr<PCGExData::FPropertyArrayBuffer> PropBuf = StaticCastSharedPtr<PCGExData::FPropertyArrayBuffer>(FailWriters[i]);
					if (const void* SrcAddr = AttributeBase->GetReadAddressFromEntryKey_Unsafe(PCGDefaultValueKey))
					{
						PropBuf->SetFromVoidProperty(Index, SrcAddr);
					}
				}
			});
	}
}

#if WITH_EDITOR
FString UPCGExActionWriteValuesProviderSettings::GetDisplayName() const
{
	return TEXT("");
}
#endif

PCGEX_BITMASK_TRANSMUTE_CREATE_OPERATION(ActionWriteValues, {})

bool UPCGExActionWriteValuesFactory::Boot(FPCGContext* InContext)
{
	// Gather success/fail attributes

	SuccessAttributesFilter.bPreservePCGExData = false;
	FailAttributesFilter.bPreservePCGExData = false;

	SuccessAttributesFilter.Init();
	FailAttributesFilter.Init();

	CheckSuccessInfos = PCGExData::GatherAttributeInfos(InContext, PCGExActionWriteValues::SourceForwardSuccess, SuccessAttributesFilter, true);
	CheckFailInfos = PCGExData::GatherAttributeInfos(InContext, PCGExActionWriteValues::SourceForwardFail, FailAttributesFilter, true);

	if (!CheckSuccessInfos || !CheckFailInfos)
	{
		return false;
	}

	return true;
}

TArray<FPCGPinProperties> UPCGExActionWriteValuesProviderSettings::InputPinProperties() const
{
	TArray<FPCGPinProperties> PinProperties = Super::InputPinProperties();
	PCGEX_PIN_ANY(PCGExActionWriteValues::SourceForwardSuccess, "TBD", Normal)
	PCGEX_PIN_ANY(PCGExActionWriteValues::SourceForwardFail, "TBD", Normal)
	return PinProperties;
}

PCGEX_BITMASK_TRANSMUTE_CREATE_FACTORY(ActionWriteValues, { NewFactory->SuccessAttributesFilter = SuccessAttributesFilter; NewFactory->FailAttributesFilter = FailAttributesFilter; })


#undef LOCTEXT_NAMESPACE
#undef PCGEX_NAMESPACE
