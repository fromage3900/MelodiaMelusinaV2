#include "MelodiaAfflictionTypes.h"

EMelodiaAffliction MelodiaAfflictionUtils::ElementToAffliction(EMelodiaSpellElement Element)
{
	switch (Element)
	{
	case EMelodiaSpellElement::Forte:   return EMelodiaAffliction::Burn;
	case EMelodiaSpellElement::Stone:   return EMelodiaAffliction::Petrify;
	case EMelodiaSpellElement::Umbral:  return EMelodiaAffliction::Shadow;
	case EMelodiaSpellElement::Arcane:  return EMelodiaAffliction::Arcane;
	case EMelodiaSpellElement::Radiant: return EMelodiaAffliction::Purify;
	case EMelodiaSpellElement::Gale:    return EMelodiaAffliction::Gust;
	case EMelodiaSpellElement::Tide:    return EMelodiaAffliction::Soak;
	default: return EMelodiaAffliction::None;
	}
}

FName MelodiaAfflictionUtils::GetAfflictionDisplayName(EMelodiaAffliction Affliction)
{
	switch (Affliction)
	{
	case EMelodiaAffliction::Burn:    return TEXT("Burn");
	case EMelodiaAffliction::Petrify: return TEXT("Petrify");
	case EMelodiaAffliction::Shadow:  return TEXT("Shadow");
	case EMelodiaAffliction::Arcane:  return TEXT("Arcane");
	case EMelodiaAffliction::Purify:  return TEXT("Purify");
	case EMelodiaAffliction::Gust:    return TEXT("Gust");
	case EMelodiaAffliction::Soak:    return TEXT("Soak");
	default: return TEXT("None");
	}
}

int32 MelodiaAfflictionUtils::GetAfflictionMaxStacks(EMelodiaAffliction Affliction)
{
	switch (Affliction)
	{
	case EMelodiaAffliction::Burn:    return 5;
	case EMelodiaAffliction::Petrify: return 3;
	case EMelodiaAffliction::Shadow:  return 4;
	case EMelodiaAffliction::Arcane:  return 3;
	case EMelodiaAffliction::Purify:  return 2;
	case EMelodiaAffliction::Gust:    return 3;
	case EMelodiaAffliction::Soak:    return 4;
	default: return 0;
	}
}

float MelodiaAfflictionUtils::GetAfflictionTickDamage(EMelodiaAffliction Affliction, int32 Stacks)
{
	switch (Affliction)
	{
	case EMelodiaAffliction::Burn:
		return 3.0f * static_cast<float>(Stacks);
	case EMelodiaAffliction::Arcane:
		return 2.0f * static_cast<float>(Stacks);
	default:
		return 0.0f;
	}
}
