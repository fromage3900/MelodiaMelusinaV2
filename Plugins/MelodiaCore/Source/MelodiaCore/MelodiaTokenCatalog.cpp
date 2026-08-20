// Melody Token catalog implementation.

#include "MelodiaTokenCatalog.h"

const FMelodiaTokenDefinition* UMelodiaTokenCatalog::FindByVariant(const FName VariantId) const
{
	if (VariantId.IsNone())
	{
		return nullptr;
	}
	return Tokens.FindByPredicate([VariantId](const FMelodiaTokenDefinition& Token)
	{
		return Token.VariantId == VariantId;
	});
}

FMelodiaTokenDefinition UMelodiaTokenCatalog::GetTokenByVariant(const FName VariantId, bool& bFound) const
{
	if (const FMelodiaTokenDefinition* Found = FindByVariant(VariantId))
	{
		bFound = true;
		return *Found;
	}
	// Fail visibly rather than returning a plausible default: a caller that ignores
	// bFound gets Value 0, which reads as free, and free is the failure this exists
	// to prevent.
	bFound = false;
	return FMelodiaTokenDefinition();
}

TArray<FMelodiaTokenDefinition> UMelodiaTokenCatalog::GetTokensForElement(const EMelodiaSpellElement Element) const
{
	TArray<FMelodiaTokenDefinition> Matches;
	for (const FMelodiaTokenDefinition& Token : Tokens)
	{
		if (Token.Element == Element)
		{
			Matches.Add(Token);
		}
	}
	return Matches;
}

bool UMelodiaTokenCatalog::ResolveCost(
	const TMap<FName, int32>& VariantCost,
	TMap<FName, int32>& OutElementCost,
	TArray<FName>& OutUnknownVariants) const
{
	OutElementCost.Reset();
	OutUnknownVariants.Reset();

	// Resolve everything first, then commit. A partially-resolved cost silently
	// undercharges, which is worse than refusing the whole transaction.
	TMap<FName, int32> Resolved;
	for (const TPair<FName, int32>& Entry : VariantCost)
	{
		const FMelodiaTokenDefinition* Token = FindByVariant(Entry.Key);
		if (!Token)
		{
			OutUnknownVariants.Add(Entry.Key);
			continue;
		}
		if (Entry.Value < 0)
		{
			// A negative price would grant on spend.
			OutUnknownVariants.Add(Entry.Key);
			continue;
		}

		const FName ElementName = StaticEnum<EMelodiaSpellElement>()
			? FName(*StaticEnum<EMelodiaSpellElement>()->GetNameStringByValue(static_cast<int64>(Token->Element)))
			: NAME_None;
		if (ElementName.IsNone())
		{
			OutUnknownVariants.Add(Entry.Key);
			continue;
		}

		// Several variants may share an element; costs accumulate.
		Resolved.FindOrAdd(ElementName) += Entry.Value;
	}

	if (OutUnknownVariants.Num() > 0)
	{
		return false;
	}

	OutElementCost = MoveTemp(Resolved);
	return true;
}

TArray<FName> UMelodiaTokenCatalog::FindDuplicateVariants() const
{
	TSet<FName> Seen;
	TArray<FName> Duplicates;
	for (const FMelodiaTokenDefinition& Token : Tokens)
	{
		if (Token.VariantId.IsNone())
		{
			continue;
		}
		if (Seen.Contains(Token.VariantId) && !Duplicates.Contains(Token.VariantId))
		{
			Duplicates.Add(Token.VariantId);
		}
		Seen.Add(Token.VariantId);
	}
	return Duplicates;
}

void UMelodiaTokenCatalog::PostLoad()
{
	Super::PostLoad();

#if WITH_EDITOR
	// Surface authoring mistakes in the editor, not when a price silently resolves
	// wrong at runtime. Same reasoning as the wardrobe catalog's dangling-form check.
	if (GIsEditor)
	{
		for (const FName Duplicate : FindDuplicateVariants())
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_TOKENS %s: duplicate VariantId '%s' — FindByVariant is ambiguous "
					 "and will return whichever row comes first."),
				*GetName(), *Duplicate.ToString());
		}

		for (const FMelodiaTokenDefinition& Token : Tokens)
		{
			if (Token.Value <= 0)
			{
				UE_LOG(LogTemp, Warning,
					TEXT("MELODIA_TOKENS %s: variant '%s' has Value %d. A zero-value token "
						 "contributes nothing to the stat economy."),
					*GetName(), *Token.VariantId.ToString(), Token.Value);
			}
		}

		if (Tokens.Num() == 0)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_TOKENS %s: catalog is empty. Regenerate from %s."),
				*GetName(), *GeneratedFrom);
		}
	}
#endif
}
