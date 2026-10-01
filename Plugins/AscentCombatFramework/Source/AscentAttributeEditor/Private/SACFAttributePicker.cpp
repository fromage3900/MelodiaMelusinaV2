// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SACFAttributePicker.h"

#include "AbilitySystemComponent.h"
#include "ACFAttributeStrUtils.h"
#include "ACFAttributeUtils.h"
#include "SACFAttributeView.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Widgets/Input/SSearchBox.h"

namespace EasyGasAttributePickerLocal
{
	static bool IsTempClass(const UClass* InClass)
	{
		return InClass->GetName().StartsWith("SKEL_") || InClass->GetName().StartsWith("REINST_");
	}

	static bool IsAttributeClass(const UClass* InClass)
	{
		return InClass->IsChildOf(UAttributeSet::StaticClass())
			|| InClass->IsChildOf(UAbilitySystemComponent::StaticClass());
	}

	static void AddAttributeToStringArray(const FProperty& InProperty, TArray<FString>& OutStringArray)
	{
		const UClass* Class = InProperty.GetOwnerClass();
		if (IsAttributeClass(Class) && !IsTempClass(Class) && ACFAttributeUtils::IsAttributeType(&InProperty))
		{
			FACFAttributeWrapper Attribute(&InProperty);
			OutStringArray.Add(ACFAttributeStrUtils::ToString(Attribute));
		}
	}

	static bool IsChildOf(const IAssetRegistry& AssetRegistry, const TSet<FTopLevelAssetPath>& ParentClassFilter,
	                      const FAssetData& AssetData)
	{
		const auto ParentTag = AssetData.TagsAndValues.FindTag(TEXT("ParentClass"));
		if (!ParentTag.IsSet())
			return false;

		const FTopLevelAssetPath ParentAssetPath{FPackageName::ExportTextPathToObjectPath(ParentTag.AsString())};
		if (!ParentAssetPath.IsValid())
			return false;

		if (ParentClassFilter.Contains(ParentAssetPath))
			return true;

		TArray<FTopLevelAssetPath> Ancestors;
		AssetRegistry.GetAncestorClassNames(ParentAssetPath, Ancestors);

		for (const FTopLevelAssetPath& Ancestor : Ancestors)
		{
			if (ParentClassFilter.Contains(Ancestor))
				return true;
		}

		return false;
	}

	template <typename FuncType>
	void ForEachAttributeSourceClass(FuncType Func)
	{
		TSet<UClass*> Visited;
		bool bExists = false;

		using namespace EasyGasAttributePickerLocal;
		{
			TArray<UClass*> LoadedDerived{UAbilitySystemComponent::StaticClass()};
			GetDerivedClasses(UAttributeSet::StaticClass(), LoadedDerived, /*bRecursive=*/true);
			GetDerivedClasses(UAbilitySystemComponent::StaticClass(), LoadedDerived, /*bRecursive=*/true);
			for (UClass* Class : LoadedDerived)
			{
				if (!Class || Class->HasAnyClassFlags(CLASS_Abstract))
					continue;
				if (IsTempClass(Class))
					continue;
				Visited.Add(Class, &bExists);
				if (!bExists)
					Func(Class);
			}
		}

		{
			FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(
				"AssetRegistry");
			IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();

			FARFilter Filter;
			Filter.bRecursiveClasses = true;
			Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());

			TArray<FAssetData> Blueprints;
			AssetRegistry.GetAssets(Filter, Blueprints);
			const TSet<FTopLevelAssetPath> ParentClassFilter{
				UAttributeSet::StaticClass()->GetClassPathName(),
				UAbilitySystemComponent::StaticClass()->GetClassPathName(),
			};

			for (const FAssetData& AssetData : Blueprints)
			{
				if (!IsChildOf(AssetRegistry, ParentClassFilter, AssetData))
					continue;

				if (UBlueprint* Blueprint = Cast<UBlueprint>(AssetData.GetAsset()))
				{
					if (Blueprint->GeneratedClass->IsChildOf(UAttributeSet::StaticClass())
						|| Blueprint->GeneratedClass->IsChildOf(UAbilitySystemComponent::StaticClass()))
					{
						Visited.Add(Blueprint->GeneratedClass, &bExists);
						if (!bExists)
							Func(Blueprint->GeneratedClass);
					}
				}
			}
		}
	}
}

SACFAttributePicker::~SACFAttributePicker()
{
	if (OnAttributePicked.IsBound())
	{
		OnAttributePicked.Unbind();
	}
}

void SACFAttributePicker::Construct(const FArguments& InArgs)
{
	using namespace EasyGasAttributePickerLocal;

	FilterMetaData = InArgs._FilterMetaData;
	OnAttributePicked = InArgs._OnAttributePickedDelegate;
	WhiteList = InArgs._WhiteList;

	AttributeTextFilter = MakeShared<FAttributeTextFilter>(
		FAttributeTextFilter::FItemToStringArray::CreateStatic(&AddAttributeToStringArray));

	TSharedPtr<SWidget> ClassViewerContent;

	SAssignNew(ClassViewerContent, SVerticalBox)
	+ SVerticalBox::Slot()
	.AutoHeight()
	[
		SAssignNew(SearchBoxPtr, SSearchBox)
		.HintText(NSLOCTEXT("Abilities", "SearchBoxHint", "Search Attributes"))
		.OnTextChanged(this, &SACFAttributePicker::OnFilterTextChanged)
		.DelayChangeNotificationsWhileTyping(true)
	]

	+ SVerticalBox::Slot()
	.AutoHeight()
	[
		SNew(SSeparator)
		.Visibility(EVisibility::Collapsed)
	]

	+ SVerticalBox::Slot()
	.FillHeight(1.0f)
	[
		SAssignNew(AttributeView, SACFAttributeView)
		.Visibility(EVisibility::Visible)
		.Items(CreateAttributes())
		.OnSelectionChanged(this, &SACFAttributePicker::OnAttributeSelectionChanged)
	];


	ChildSlot
	[
		ClassViewerContent.ToSharedRef()
	];
}

TArray<TSharedPtr<FACFAttributeWrapper>> SACFAttributePicker::CreateAttributes() const
{
	TArray<TSharedPtr<FACFAttributeWrapper>> Attributes = {MakeShared<FACFAttributeWrapper>()};

	auto AddAttributes = [this, &Attributes](UClass* Class)
	{
		if (Class->IsChildOf(UAttributeSet::StaticClass()))
		{
			// Allow entire classes to be filtered globally
			if (Class->HasMetaData(TEXT("HideInDetailsView")))
			{
				return;
			}

			for (TFieldIterator<FProperty> PropertyIt(Class, EFieldIteratorFlags::ExcludeSuper); PropertyIt; ++
			     PropertyIt)
			{
				FProperty* Property = *PropertyIt;

				if (Property->HasMetaData(TEXT("HideInDetailsView")) || !ACFAttributeUtils::IsAttributeType(Property))
				{
					continue;
				}

				if (!FilterMetaData.IsEmpty() && Property->HasMetaData(*FilterMetaData))
				{
					continue;
				}

				if (AttributeTextFilter.IsValid() && !AttributeTextFilter->PassesFilter(*Property))
				{
					continue;
				}

				Attributes.Add(MakeShared<FACFAttributeWrapper>(Property));
			}
		}

		// UAbilitySystemComponent can add 'system' attributes
		if (Class->IsChildOf(UAbilitySystemComponent::StaticClass()) && !Class->ClassGeneratedBy)
		{
			for (TFieldIterator<FProperty> PropertyIt(Class, EFieldIteratorFlags::ExcludeSuper); PropertyIt; ++
			     PropertyIt)
			{
				FProperty* Property = *PropertyIt;

				// SystemAttributes have to be explicitly tagged
				if (Property->HasMetaData(TEXT("SystemGameplayAttribute")) == false)
				{
					continue;
				}

				// if we have a search string and this doesn't match, don't show it
				if (AttributeTextFilter.IsValid() && !AttributeTextFilter->PassesFilter(*Property))
				{
					continue;
				}

				Attributes.Add(MakeShared<FACFAttributeWrapper>(Property));
			}
		}
	};
	if (WhiteList.IsEmpty())
	{
		EasyGasAttributePickerLocal::ForEachAttributeSourceClass(AddAttributes);
	}
	else
	{
		for (UClass* Class : WhiteList)
			AddAttributes(Class);
	}

	return Attributes;
}

void SACFAttributePicker::OnFilterTextChanged(const FText& InFilterText)
{
	AttributeTextFilter->SetRawFilterText(InFilterText);
	SearchBoxPtr->SetError(AttributeTextFilter->GetFilterErrorText());

	AttributeView->SetHighlightText(InFilterText);
	AttributeView->SetItems(CreateAttributes());
}

void SACFAttributePicker::OnAttributeSelectionChanged(TSharedPtr<FACFAttributeWrapper> Item,
                                                      ESelectInfo::Type SelectInfo)
{
	if (Item)
		OnAttributePicked.ExecuteIfBound(*Item);
}
