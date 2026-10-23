#include "MelodiaDressingCatalog.h"

const FMelodiaDressingFamily* UMelodiaDressingCatalog::FindFamily(const FGameplayTag& FamilyTag) const
{
	if (!FamilyTag.IsValid())
	{
		return nullptr;
	}
	return Families.FindByPredicate(
		[&FamilyTag](const FMelodiaDressingFamily& Family)
		{
			return Family.FamilyTag == FamilyTag;
		});
}

const FMelodiaDressingFamily* UMelodiaDressingCatalog::FindFamilyByArtistTag(const FName& ArtistTag) const
{
	if (ArtistTag.IsNone())
	{
		return nullptr;
	}
	const FMelodiaDressingFamily* Match = Families.FindByPredicate(
		[&ArtistTag](const FMelodiaDressingFamily& Family)
		{
			return Family.ArtistTag == ArtistTag;
		});
	if (Match)
	{
		return Match;
	}

	// Fall back to a normalised comparison, so "Room_bedroom" still finds the
	// family whose gameplay tag is "Melodia.Dressing.Room.Bedroom". The artist
	// works in the first vocabulary; the catalogue is keyed by the second.
	const FString Wanted = ArtistTag.ToString();
	FString WantedLeaf = Wanted;
	if (int32 Underscore = WantedLeaf.Find(TEXT("Room_"), ESearchCase::IgnoreCase); Underscore != INDEX_NONE)
	{
		WantedLeaf = WantedLeaf.RightChop(Underscore + 5);
	}

	for (const FMelodiaDressingFamily& Family : Families)
	{
		if (!Family.FamilyTag.IsValid())
		{
			continue;
		}
		FString TagLeaf = Family.FamilyTag.GetTagName().ToString();
		if (int32 Dot = TagLeaf.Find(TEXT("."), ESearchCase::IgnoreCase, ESearchDir::FromEnd); Dot != INDEX_NONE)
		{
			TagLeaf = TagLeaf.RightChop(Dot + 1);
		}
		if (TagLeaf.Equals(WantedLeaf, ESearchCase::IgnoreCase))
		{
			return &Family;
		}
	}
	return nullptr;
}

TArray<FMelodiaDressingProp> UMelodiaDressingCatalog::PropsForFamily(const FGameplayTag& FamilyTag) const
{
	const FMelodiaDressingFamily* Family = FindFamily(FamilyTag);
	return Family ? Family->Props : TArray<FMelodiaDressingProp>();
}

TArray<FGameplayTag> UMelodiaDressingCatalog::FamilyTags() const
{
	TArray<FGameplayTag> Tags;
	Tags.Reserve(Families.Num());
	for (const FMelodiaDressingFamily& Family : Families)
	{
		if (Family.FamilyTag.IsValid())
		{
			Tags.Add(Family.FamilyTag);
		}
	}
	return Tags;
}
