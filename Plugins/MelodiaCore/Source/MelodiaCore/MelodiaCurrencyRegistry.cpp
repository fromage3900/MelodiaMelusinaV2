// Melodia currency registry implementation.

#include "MelodiaCurrencyRegistry.h"

#include "UObject/UObjectGlobals.h"

UMelodiaCurrencyRegistry* UMelodiaCurrencyRegistry::FallbackSeedInstance = nullptr;

namespace
{
	/** Shorthand for building seed rows without nine near-identical blocks. */
	FMelodiaCurrencyDefinition MakeShardRow(
		const TCHAR* Id, const TCHAR* Display, const EMelodiaSpellElement Element, const int32 Sort)
	{
		FMelodiaCurrencyDefinition Row;
		Row.CurrencyId = FName(Id);
		Row.DisplayName = FText::FromString(Display);
		Row.Kind = EMelodiaCurrencyKind::Shard;
		Row.SortOrder = Sort;
		Row.bHasLegacyElement = true;
		Row.LegacyElement = Element;
		return Row;
	}
}

const TCHAR* UMelodiaCurrencyRegistry::GetRegistryAssetPath()
{
	return TEXT("/Game/Melodia/Data/DA_MelodiaCurrencyRegistry.DA_MelodiaCurrencyRegistry");
}

const UMelodiaCurrencyRegistry* UMelodiaCurrencyRegistry::GetFallbackSeed()
{
	if (FallbackSeedInstance)
	{
		return FallbackSeedInstance;
	}

	UMelodiaCurrencyRegistry* Seed = NewObject<UMelodiaCurrencyRegistry>(
		GetTransientPackage(), UMelodiaCurrencyRegistry::StaticClass(), TEXT("MelodiaCurrencyRegistryFallbackSeed"));

	// Order matches gmm/game/tokens.py TokenWallet.shards default keys, so a HUD built from
	// SortOrder reads the same left-to-right as every existing dump and test expectation.
	Seed->Currencies.Add(MakeShardRow(TEXT("Forte"),   TEXT("Forte Shard"),   EMelodiaSpellElement::Forte,   0));
	Seed->Currencies.Add(MakeShardRow(TEXT("Tide"),    TEXT("Tide Shard"),    EMelodiaSpellElement::Tide,    1));
	Seed->Currencies.Add(MakeShardRow(TEXT("Gale"),    TEXT("Gale Shard"),    EMelodiaSpellElement::Gale,    2));
	Seed->Currencies.Add(MakeShardRow(TEXT("Stone"),   TEXT("Stone Shard"),   EMelodiaSpellElement::Stone,   3));
	Seed->Currencies.Add(MakeShardRow(TEXT("Radiant"), TEXT("Radiant Shard"), EMelodiaSpellElement::Radiant, 4));
	Seed->Currencies.Add(MakeShardRow(TEXT("Umbral"),  TEXT("Umbral Shard"),  EMelodiaSpellElement::Umbral,  5));
	Seed->Currencies.Add(MakeShardRow(TEXT("Arcane"),  TEXT("Arcane Shard"),  EMelodiaSpellElement::Arcane,  6));

	{
		// Golden is premium currency: refundable, and deliberately NOT counted toward
		// TotalCollected, which is a "shards you have picked up" stat the HUD shows.
		FMelodiaCurrencyDefinition Golden;
		Golden.CurrencyId = TEXT("Golden");
		Golden.DisplayName = FText::FromString(TEXT("Golden Token"));
		Golden.Kind = EMelodiaCurrencyKind::Premium;
		Golden.bRefundable = true;
		Golden.bCountsTowardTotalCollected = false;
		Golden.SortOrder = 100;
		Seed->Currencies.Add(Golden);
	}

	{
		// Mana defaults mirror the wallet's own historical 50/100 initialisers.
		FMelodiaCurrencyDefinition Mana;
		Mana.CurrencyId = TEXT("Mana");
		Mana.DisplayName = FText::FromString(TEXT("Mana"));
		Mana.Kind = EMelodiaCurrencyKind::Resource;
		Mana.DefaultValue = 50.0f;
		Mana.MaxValue = 100.0f;
		Mana.bCountsTowardTotalCollected = false;
		Mana.SortOrder = 200;
		Seed->Currencies.Add(Mana);
	}

	Seed->AddToRoot();
	FallbackSeedInstance = Seed;
	return FallbackSeedInstance;
}

const UMelodiaCurrencyRegistry* UMelodiaCurrencyRegistry::Get(const UObject* /*WorldContextObject*/)
{
	// Static rather than per-call load: the registry is immutable at runtime, and the wallet
	// touches it on every transaction.
	static TWeakObjectPtr<const UMelodiaCurrencyRegistry> Cached;
	if (Cached.IsValid())
	{
		return Cached.Get();
	}

	const UMelodiaCurrencyRegistry* Loaded = LoadObject<UMelodiaCurrencyRegistry>(nullptr, GetRegistryAssetPath());
	if (Loaded)
	{
		Cached = Loaded;
		return Loaded;
	}

	// Never return null. A wallet with no currencies would reject every transaction, which
	// looks like a gameplay bug rather than a missing asset.
	static bool bWarned = false;
	if (!bWarned)
	{
		bWarned = true;
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_CURRENCY registry asset '%s' not found; using the built-in nine-row seed. "
				 "Restore it with Content/Python/author_melodia_currency_registry.py."),
			GetRegistryAssetPath());
	}
	return GetFallbackSeed();
}

const FMelodiaCurrencyDefinition* UMelodiaCurrencyRegistry::Find(const FName CurrencyId) const
{
	if (CurrencyId.IsNone())
	{
		return nullptr;
	}
	return Currencies.FindByPredicate([CurrencyId](const FMelodiaCurrencyDefinition& Row)
	{
		return Row.CurrencyId == CurrencyId;
	});
}

bool UMelodiaCurrencyRegistry::IsKnownCurrency(const FName CurrencyId) const
{
	return Find(CurrencyId) != nullptr;
}

FMelodiaCurrencyDefinition UMelodiaCurrencyRegistry::GetCurrency(const FName CurrencyId, bool& bFound) const
{
	if (const FMelodiaCurrencyDefinition* Found = Find(CurrencyId))
	{
		bFound = true;
		return *Found;
	}
	// Same reasoning as UMelodiaTokenCatalog::GetTokenByVariant: a plausible default here
	// would read as a real, free, uncapped currency.
	bFound = false;
	return FMelodiaCurrencyDefinition();
}

TArray<FMelodiaCurrencyDefinition> UMelodiaCurrencyRegistry::GetSortedCurrencies() const
{
	TArray<FMelodiaCurrencyDefinition> Sorted = Currencies;
	Sorted.Sort([](const FMelodiaCurrencyDefinition& A, const FMelodiaCurrencyDefinition& B)
	{
		if (A.SortOrder != B.SortOrder)
		{
			return A.SortOrder < B.SortOrder;
		}
		// Stable tiebreak so HUD row order cannot flap between runs on equal SortOrder.
		return A.CurrencyId.LexicalLess(B.CurrencyId);
	});
	return Sorted;
}

TArray<FName> UMelodiaCurrencyRegistry::GetCurrencyIds(const EMelodiaCurrencyKind Kind) const
{
	TArray<FName> Ids;
	for (const FMelodiaCurrencyDefinition& Row : GetSortedCurrencies())
	{
		if (Row.Kind == Kind && !Row.CurrencyId.IsNone())
		{
			Ids.Add(Row.CurrencyId);
		}
	}
	return Ids;
}

FName UMelodiaCurrencyRegistry::CurrencyIdForElement(const EMelodiaSpellElement Element) const
{
	for (const FMelodiaCurrencyDefinition& Row : Currencies)
	{
		if (Row.bHasLegacyElement && Row.LegacyElement == Element)
		{
			return Row.CurrencyId;
		}
	}
	return NAME_None;
}

TArray<FName> UMelodiaCurrencyRegistry::FindDuplicateCurrencyIds() const
{
	TSet<FName> Seen;
	TArray<FName> Duplicates;
	for (const FMelodiaCurrencyDefinition& Row : Currencies)
	{
		if (Row.CurrencyId.IsNone())
		{
			continue;
		}
		if (Seen.Contains(Row.CurrencyId) && !Duplicates.Contains(Row.CurrencyId))
		{
			Duplicates.Add(Row.CurrencyId);
		}
		Seen.Add(Row.CurrencyId);
	}
	return Duplicates;
}

void UMelodiaCurrencyRegistry::PostLoad()
{
	Super::PostLoad();

#if WITH_EDITOR
	// Surface authoring mistakes in the editor rather than as a transaction that silently
	// behaves wrong at runtime. Mirrors UMelodiaTokenCatalog::PostLoad.
	if (GIsEditor)
	{
		for (const FName Duplicate : FindDuplicateCurrencyIds())
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_CURRENCY %s: duplicate CurrencyId '%s' — Find is ambiguous and will "
					 "return whichever row comes first."),
				*GetName(), *Duplicate.ToString());
		}

		for (const FMelodiaCurrencyDefinition& Row : Currencies)
		{
			if (Row.CurrencyId.IsNone())
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_CURRENCY %s: a row has an empty CurrencyId and can never be "
						 "granted or spent."), *GetName());
				continue;
			}

			if (Row.Kind == EMelodiaCurrencyKind::Resource && Row.MaxValue <= 0.0f)
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_CURRENCY %s: Resource currency '%s' has MaxValue %.1f. It clamps "
						 "to zero, so every grant is a no-op."),
					*GetName(), *Row.CurrencyId.ToString(), Row.MaxValue);
			}

			if (Row.Kind != EMelodiaCurrencyKind::Resource && Row.MaxValue > 0.0f)
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_CURRENCY %s: '%s' is not a Resource but sets MaxValue %.1f, which "
						 "is ignored. Set Kind=Resource or clear MaxValue."),
					*GetName(), *Row.CurrencyId.ToString(), Row.MaxValue);
			}

			if (Row.Kind == EMelodiaCurrencyKind::Resource && Row.DefaultValue > Row.MaxValue)
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_CURRENCY %s: '%s' starts at %.1f above its MaxValue %.1f and will "
						 "be clamped down on first load."),
					*GetName(), *Row.CurrencyId.ToString(), Row.DefaultValue, Row.MaxValue);
			}
		}

		if (Currencies.Num() == 0)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_CURRENCY %s: registry is empty. Every wallet transaction will be "
					 "rejected. Restore it with author_melodia_currency_registry.py."),
				*GetName());
		}
	}
#endif
}
