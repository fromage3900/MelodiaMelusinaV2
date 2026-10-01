// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFEditorSettings.h"
#include "ACFAssetCreatorDataAsset.h"
#include "ACFEditorSubsystem.h"
#include "ACFPlacementDataAsset.h"
#include "GameplayTagContainer.h"

// ---------------------------------------------------------------------------
// Placement
// ---------------------------------------------------------------------------

TArray<FPlaceCategoryConfig> UACFEditorSettings::GetPlacementCategories() const
{
	TArray<FPlaceCategoryConfig> Result;

	for (const TSoftObjectPtr<UACFPlacementDataAsset>& AssetPtr : PlacementEntriesAssets)
	{
		if (AssetPtr.IsNull())
		{
			continue;
		}

		if (UACFPlacementDataAsset* Asset = AssetPtr.LoadSynchronous())
		{
			Result.Append(Asset->Categories);
		}
	}

	return Result;
}

// ---------------------------------------------------------------------------
// Core
// ---------------------------------------------------------------------------

void UACFEditorSettings::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	GEditor->GetEditorSubsystem<UACFEditorSubsystem>()->RefreshAll();
}

// ---------------------------------------------------------------------------
// Asset Creator — private helper
// ---------------------------------------------------------------------------

TArray<FAssetCreatorDefaultClassEntry> UACFEditorSettings::GetActiveAssetCreatorEntries() const
{
	if (!AssetCreatorConfigAsset.IsNull())
	{
		if (UACFAssetCreatorDataAsset* Asset = AssetCreatorConfigAsset.LoadSynchronous())
		{
			return Asset->DefaultClasses;
		}
	}
	return {};
}

// ---------------------------------------------------------------------------
// Asset Creator — public getters
// ---------------------------------------------------------------------------

bool UACFEditorSettings::GetAssetCreatorDefaultClassByTag(FGameplayTag Tag, TSubclassOf<UObject>& OutClass) const
{
	OutClass = nullptr;

	const TArray<FAssetCreatorDefaultClassEntry>& Entries = GetActiveAssetCreatorEntries();
	if (const FAssetCreatorDefaultClassEntry* Entry = Entries.FindByKey(Tag))
	{
		UClass* LoadedClass = Entry->Class.LoadSynchronous();
		if (LoadedClass)
		{
			OutClass = LoadedClass;
			return true;
		}
	}
	return false;
}

bool UACFEditorSettings::HasAssetCreatorDefaultClass(FGameplayTag Tag) const
{
	TSubclassOf<UObject> DummyClass;
	return GetAssetCreatorDefaultClassByTag(Tag, DummyClass);
}

bool UACFEditorSettings::GetAssetCreatorDefaultClassByIndex(int32 Index, FGameplayTag& OutTag, TSubclassOf<UObject>& OutClass) const
{
	OutTag = FGameplayTag();
	OutClass = nullptr;

	const TArray<FAssetCreatorDefaultClassEntry>& Entries = GetActiveAssetCreatorEntries();
	if (!Entries.IsValidIndex(Index))
	{
		return false;
	}

	const FAssetCreatorDefaultClassEntry& Entry = Entries[Index];
	OutTag = Entry.Tag;

	UClass* LoadedClass = Entry.Class.LoadSynchronous();
	if (LoadedClass)
	{
		OutClass = LoadedClass;
		return true;
	}
	return false;
}

bool UACFEditorSettings::GetAssetCreatorDisplayNameByTag(FGameplayTag Tag, FText& OutDisplayName) const
{
	const TArray<FAssetCreatorDefaultClassEntry>& Entries = GetActiveAssetCreatorEntries();
	if (const FAssetCreatorDefaultClassEntry* Entry = Entries.FindByKey(Tag))
	{
		OutDisplayName = Entry->DisplayName;
		return true;
	}
	return false;
}

bool UACFEditorSettings::GetAssetCreatorEntryByTag(FGameplayTag Tag, FAssetCreatorDefaultClassEntry& OutEntry) const
{
	const TArray<FAssetCreatorDefaultClassEntry>& Entries = GetActiveAssetCreatorEntries();
	if (const FAssetCreatorDefaultClassEntry* Found = Entries.FindByKey(Tag))
	{
		OutEntry = *Found;
		return true;
	}
	return false;
}

int32 UACFEditorSettings::GetAssetCreatorDefaultClassesNum() const
{
	return GetActiveAssetCreatorEntries().Num();
}

TMap<FGameplayTag, TSubclassOf<UObject>> UACFEditorSettings::GetAssetCreatorDefaultClasses() const
{
	const TArray<FAssetCreatorDefaultClassEntry>& Entries = GetActiveAssetCreatorEntries();
	TMap<FGameplayTag, TSubclassOf<UObject>> Result;
	Result.Reserve(Entries.Num());

	for (const FAssetCreatorDefaultClassEntry& Entry : Entries)
	{
		UClass* LoadedClass = Entry.Class.LoadSynchronous();
		if (LoadedClass)
		{
			Result.Add(Entry.Tag, LoadedClass);
		}
	}
	return Result;
}
